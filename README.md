# Geocoding Engine Machine (GEM) 
#### Developed by Chris Allen, the Center for Human Dynamics in the Mobile Age, San Diego State University. 2017
## Synopsis

The geocoding engine machine (GEM) is a python library and command-line tool that can be used to geocode text-based location descriptions.  

Note: The placename database is pre-loaded with US and major international cities.  The results will be ordered by population, so a query for "Paris" will return "Paris, France" rather than "Paris, Texas" (unless a country or state is specified).

Note: GEM is currently only compatible with __Python 2.\*__

## Usage

GEM can be run as a Python package or through a command-line interface (CLI).  

To use as a Python package, import the GEM and use the geocode_location() function: 

~~~~
import gem

location = "San Diego, CA"

place, city, state, longitude, latitude = gem.geocode_location(location)
~~~~

To use as a CLI, run gem.py with the input and output file paths (note: use the --h flag for usage help):

~~~~
python gem.py --in test.csv --out test-out.csv
~~~~

By default, GEM will assume the location column is called "location," but it's possible to specify a different location column by using the "--location" flag:

~~~~
python gem.py --in example.csv --out example-out.csv --location "loc"
~~~~

## Installation

To install, simply clone or download the GEM zip file and unzip it.  Navigate to the unzipped folder (where setup.py lives):

~~~~
python setup.py install
~~~~

Note that in most cases, running the setup.py file will require administrative priviledges.  On Windows, this requires opening the terminal as an administrator.  On \*nix systems (including MacOS), this requires using the "sudo command:

~~~~
sudo python setup.py install
~~~~

