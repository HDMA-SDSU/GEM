## Synopsis

The geocoding engine machine (GEM) is a python library and command-line tool that can be used to geocode text-based location descriptions.  

## Code Example

~~~~
import gem

location = "San Diego, CA"

place, city, state, longitude, latitude = gem.geocode_location(location)
~~~~

## Installation

To install, simply place the GEM files under a directory that in the PYTHONPATH.
