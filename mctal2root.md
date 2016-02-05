# Introduction #

With the **mctal2root** converter, ASCII MCTAL files produced by MCNPX are converted into binary ROOT files containing a set of **[THnSparseF](http://root.cern.ch/root/html/THnSparse.html)**, one for each tally.

Many features are supported:

  * all possible binnings
  * macrobodies
  * mesh tallies
  * radiograph tallies

Known unsupported features are:

  * `pert` card
  * KCODE output
  * (for tests only) NaN values in MCTAL files are correctly exported to ROOT, but tests on these files will fail

# Installation #

## Software requirements ##

This software is required for the converter to work:

  1. 2.7 <= [Python](http://www.python.org/download/releases/2.7.6/) < 3 (Python 2.6 can be used, but the **[argparse](http://docs.python.org/dev/library/argparse.html)** module must be installed manually)
  1. [ROOT Data Analysis Framework ](http://root.cern.ch/drupal/content/downloading-root)

This tool provides also the possibility to test the reading and the conversion of MCTAL files. Test routines use the **[ndiff](http://www.math.utah.edu/~beebe/software/ndiff/)** package.
Developers wishing to improve the code must have this package installed for their tests.
## Download ##

DEB --> System wide
SVN --> Local and developers

### Deb package installation ###

  1. download from link
  1. dpkg -i package\_name.deb

### Installation from source code ###

  1. svn co
  1. ./configure make install
  1. export PYHTONPATH and PATH

# Converting #

For quick help about converter usage, option -h is available:

` mctal2root -h `

Assuming that the MCTAL output is stored in the `mctal` file, the conversion script command-line syntax is the following:

`mctal2root mctal`

This will create a ROOT file with the same name of the input MCTAL and a `.root` extension (in this case, the file name will be
`mctal.root`).
The converted file will be saved in the same directory of the input MCTAL. A different file name for the converted file can be requested by
adding the desired file name after the input MCTAL.

Detailed information about the conversion process is available with the option `-v`.

The ROOT file will contain one or more **[THnSparseF](http://root.cern.ch/root/html/THnSparse.html)**, one for each tally. Each object is named accordingly to the tally type and number:

  * `f` followed by tally number for standard tallies (e.g. `f4`)
  * `r/c/smesh` followed by tally number for mesh tallies (e.g. `rmesh1`)
  * `pi`, `tir`, `tic` followed by tally number for radiograph tallies (e.g. `tir5`)

For both standard and radiograph tallies, the data structure is based on a **8D** sparse histograms, whereas `i`, `j` and `k` axes used in mesh tallies require the use of a **11D** data structure for this tally type.

# Basic THnSparse usage tips #

First import the converted file into ROOT:

`TFile *f = new TFile("mctal.root");`

Then select the desired tally (e.g. tally 15):

`THnSparseF *hs = f->Get("f15");`

Projection of the **THnSparseF** to a **[TH1F](http://root.cern.ch/root/html/TH1F.html)**, **[TH2F](http://root.cern.ch/root/html/TH2F.html)** or **[TH3F](http://root.cern.ch/root/html/TH3F.html)** can be obtained (e.g. projection of axis 6):

`TH1F *h1 = hs->Projection(6)`

The following table shows the correspondence between axis names and axis numbers:

| **Axis name** | **Axis number** |
|:--------------|:----------------|
| `f` | 0 |
| `d` | 1 |
| `u` | 2 |
| `s` | 3 |
| `m` | 4 |
| `c` | 5 |
| `e` | 6 |
| `t` | 7 |
| `i` | 8 |
| `j` | 9 |
| `k` | 10 |

A smaller range of bins on a certain axis can be also selected:

`hs->GetAxis(7)->SetRange(1,10)`

# Examples #

Look at the Examples folder