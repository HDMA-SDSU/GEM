# Geocoding Engine Machine (GEM) 
#### Developed by Chris Allen, the Center for Human Dynamics in the Mobile Age, San Diego State University. 2017
## Synopsis

The geocoding engine machine (GEM) is a python library and command-line tool that can be used to geocode text-based location descriptions.  

Note: The placename database is pre-loaded with US cities.

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

## Installation

To install, simply clone the GEM repository to a directory that is in the PYTHONPATH.
