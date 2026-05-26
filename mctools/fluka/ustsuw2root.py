#!/usr/bin/env python3

import sys, argparse, struct
from os import path
import numpy as np
from math import isclose
from mctools import fluka, getLogBins, getLinBins
from mctools.fluka.io.readers import FlukaBinaryFile, DetectorRecord, unpack_floats
from mctools.fluka.io.recordio import read_record, skip_record
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

def getAxesTitle(det):
    # differential energy fluence/current
    # FLUKA manual: USRTRACK section
    energy = (208, 211) # ENERGY or EM-ENERGY
    ytitle = fluka.particle.get(det.dist, "undefined")
    if int(det.dist) in energy:
        ytitle += " tracklength [cm]" if isclose(det.volume, 1.0) else " energy fluence [cm^{-2}]"
    else:
        ytitle += " tracklength [cm/GeV]" if isclose(det.volume, 1.0) else " fluence [1/GeV/cm^{2}]"

    return ";Energy [GeV];" + ytitle

def getEbins(det):
    """ Return lin or log energy bins depending on the value of i """

    if det.type == -1:
        return getLogBins(det.ne, det.elow, det.ehigh)
    else:
        return getLinBins(det.ne, det.elow, det.ehigh)

def hist(det):
    """ Create histogram for the given detector """

    if det.ne == 0:
        print(f"WARNING: Not saving detector {det.name} into ROOT file since it has 0 energy bins: {det.elow} < E < {det.ehigh}")
        print("         This happens for neutron-contributing estimators if max scoring energy is below groupwise max energy, 20 MeV.")
        return None

    title = fluka.particle.get(det.dist, "undefined")
    title += " #diamond "
    title += "all regions" if int(det.reg) == -1 else "reg %d" % det.reg
    title += " #diamond "
    title += "%g cm^{3}" % det.volume
    title += " #diamond "
    title += "%g < E < %g GeV" % (det.elow, det.ehigh)
    title += getAxesTitle(det)

    return ROOT.TH1F(det.name, title, det.ne, getEbins(det))

def histN(det):
    """Create histogram for the given detector with low energy neutrons

    """
    if det.lowneu:
        name = det.name + "_lowneu"
        title = name + getAxesTitle(det)
        return ROOT.TH1F(name, title, det.ngroup, np.array(det.egroup[::-1]))
    else:
        return 0

class Usrtrack(FlukaBinaryFile):
    """ Reads the ustsuw binary output
        (USRTRACK / USRCOLL estimators)
    """
    def read_header(self, filename):
        """ Reads the file header info
            Based on Data.Usrbdx
        """
        f = super().read_header(filename)
#        self.describe_header()

        while True:
            data = read_record(f)
            if data is None: break
            size = len(data)
#            print("size: ", size)

            if size == 14 and data.decode('utf8')[:10] == "STATISTICS":
                self.stats_offset = f.tell()
                for det in self.detectors:
                    data = unpack_floats(read_record(f))
                    det.total = data[0]
                    det.totalerror = data[1]
#                    for j in range(6):
#                        fortran.skip(f)
                break

            if size != 50: raise IOError("Invalid USRTRACK/USRCOLL file %d " % size)

            header = struct.unpack("=i10siiififfif", data)

            det = DetectorRecord()
            det.nb = header[0]
            det.name = header[1].decode('utf8').strip() # titutc - track/coll name
            det.type = header[2] # itustc - type of binning: 1 - linear energy etc
            det.dist = header[3] # idustc = distribution to be scored
            det.reg  = header[4] # nrustc = region
            det.volume = header[5] # vusrtc = volume (cm**3) of the detector
            det.lowneu = header[6] # llnutc = low energy neutron flag
            det.elow = header[7] # etclow = minimum energy [GeV]
            det.ehigh = header[8] # etchgh = maximum energy [GeV]
            det.ne = header[9] # netcbn = number of energy intervals
            det.de = header[10] # detcbn = energy bin width

            self.detectors.append(det)

            if det.lowneu:
                data = read_record(f)
                det.ngroup = struct.unpack("=i",data[:4])[0]
                det.egroup = struct.unpack("=%df"%(det.ngroup+1), data[4:])
                print(f"{det.name}: Low energy neutrons scored with {det.ngroup} groups")
            else:
                det.ngroup = 0
                det.egroup = ()

            size  = (det.ngroup+det.ne) * 4
            if size != skip_record(f):
                raise IOError("Invalid USRTRACK file")
        f.close()

    def describe_detector(self, i):
        """Describe one detector block."""
        det = self.detectors[i]
        print("Detector:", det.name)
        print(" binning type: ", det.type)
        print(" distribution to be scored:", det.dist)
        print(" region:", det.reg)
        print(" volume:", det.volume)
        print(" low energy neutrons:", det.lowneu)
        print(" %g < E < %g GeV / %d bins; bin width: %g" % (det.elow, det.ehigh, det.ne, det.de))

    def read_statistics(self, det, lowneu):
        """ Read detector # det statistical data """
        if self.stats_offset < 0: return None
        with open(self.filename,"rb") as f:
            f.seek(self.stats_offset)
            for i in range(det+3): # check that 3 gives correct errors with 1 USRTRACK detector
                skip_record(f) # skip previous detectors
            data = read_record(f)
        return data

    def read_detector_data(self, det, lowneu):
        """Read detector det data structure

        """
        f = open(self.filename,"rb")
        skip_record(f) # Skip header
        for i in range(2*det):
            skip_record(f)     # Detector Header & Data
        skip_record(f)         # Detector Header
        if lowneu:
            skip_record(f) # skip low enery neutron data
        data = read_record(f)
        f.close()
        return data

def main():
    """ Converts ustsuw output into a ROOT TH1F histogram """

    parser = argparse.ArgumentParser(description=main.__doc__,
                                     epilog="Homepage: https://github.com/kbat/mc-tools")
    parser.add_argument('usrtrack', type=str, help='ustsuw binary output')
    parser.add_argument('root', type=str, nargs='?', help='output ROOT file name', default="")
    parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose', help='print what is being done')

    args = parser.parse_args()

    if not path.isfile(args.usrtrack):
        print("ustsuw2root: File %s does not exist." % args.usrtrack, file=sys.stderr)
        return 1

    if args.root == "":
        rootFileName = "%s%s" % (args.usrtrack,".root")
    else:
        rootFileName = args.root

    b = Usrtrack()
    b.read_header(args.usrtrack)

    ND = len(b.detectors)
    # print("ND:",ND)

    if args.verbose:
        #b.describe_header()
        for i in range(ND):
            b.describe_detector(i)
            print("")

    fout = ROOT.TFile(rootFileName, "recreate")
    for i in range(ND):
        det = b.detectors[i]
        val = unpack_floats(b.read_detector_data(i, det.lowneu))
        err = unpack_floats(b.read_statistics(i, det.lowneu))

        # print("val",val, len(err))
        # print("err",err, len(err))
        assert len(val) == len(err), "val and err length are different: %d %d" % (len(val), len(err))

        h = hist(det)
        hn = histN(det) # filled only if det.lowneu

        if h:
            n = h.GetNbinsX()
            assert n == det.ne, "n != det.ne"

            # print(i,n, len(val))
            for i in range(n):
                h.SetBinContent(i+1, val[i])
                h.SetBinError(i+1,   err[n-i-1]*val[i])

            h.SetEntries(b.weight)
            h.Write()

# not implemented - bugs with theINFN FLUKA, but it seems works with the CERN FLUKA
        if det.lowneu:
            # val_lowneu = val[det.ne::][::-1]
            # err_lowneu = err[det.ne::][::-1]
            n = hn.GetNbinsX()
            assert n == det.ngroup, "n != det.ngroup"
            # print(n, len(val_lowneu), len(err_lowneu))
            for i in range(n):
                hn.SetBinContent(i+1, val[-i-1])
                hn.SetBinError(i+1,   err[-i-1]*val[-i-1])

            hn.SetEntries(b.weight)
            hn.Write()

    fout.Close()

if __name__=="__main__":
    sys.exit(main())
