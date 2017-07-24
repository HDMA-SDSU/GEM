#!/usr/bin/env python

import sqlite3
import re

GEONAMES_DUMP_URL = 'http://download.geonames.org/export/dump/{}.zip'
GAZETTEER_PATH = './gazetteer.db'

connection = sqlite3.connect(GAZETTEER_PATH)
connection.text_factory = str
cursor = connection.cursor()

def _import_table(country_code, reset=False):
    """Import a GeoNames table based on the country code.
    """
    import urllib, zipfile, csv

    if reset:
        cursor.execute("DROP TABLE places")

    cursor.execute("""CREATE TABLE IF NOT EXISTS places (name text, country text, state text, 
                   latitude real, longitude real, population integer, country_code text)""")

    # first, grab the file from geonames
    filehandle, _ = urllib.urlretrieve(GEONAMES_DUMP_URL.format(country_code))

    # unzip the appropriate file and read it
    zipped = zipfile.ZipFile(filehandle, 'r')
    file_stream = zipped.open("{}.txt".format(country_code))
    text = file_stream.read()

    # parse with csv.reader
    reader = csv.reader(text.splitlines(), delimiter='\t', quotechar="'")

    # go through each row and grab necessary columns
    for row in reader:
        state = row[10]
        country = row[8]
        lat = row[4]
        lon = row[5]
        population = row[14]

        # row[1] is official name and row[3] is a list of the alternative names
        names = row[3].split(',') + [row[1]]

        for name in names:
            cursor.execute("INSERT INTO places VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (name, country, state, lat, lon, population, country_code))

    # commit changes
    connection.commit()


def _geocode_csv(input_path, output_path, location_column='location'):
    """Geocode each row in the input and output the geocoded information.
    """
    import csv

    reader = csv.reader(open(input_path).readlines(),
                        delimiter=',',
                        quotechar='"')
    columns = reader.next()

    if columns.count(location_column) == 0:
        raise ValueError("Location column is invalid.")

    location_index = columns.count(location_column)

    output_file = open(output_path, 'wb')
    writer = csv.writer(output_file, delimiter=',', quotechar='"')
    writer.writerow(columns + ['code_placename', 'code_longitude', 'code_latitude'])

    for row in reader:
        loc = row[location_index]

        result = geocode_location(loc)

        placename = "{}, {}, {}".format(*result[:3])

        longitude = result[4]
        latitude = result[3]

        row_output = row + ([] * 3 if not result else [placename, longitude, latitude])
        writer.writerow(row_output)

    output_file.close()


def geocode_location(location):
    """Return a place name, state, country, latitude, and longitude for the given location
    string.

    TODO: State and country fields only using codes right now (eg, CA rather than California)
    """

    query_template = "SELECT name, state, country, latitude, longitude FROM PLACES WHERE {}"

    location = location.title()
    # remove weird unicode characters 
    location = location.encode('ascii', 'ignore')
    # remove punctuation
    location = re.sub(r'[^,\w\s]', '', location)
    # remove any remaining whitespace
    location = location.strip()

    # 1) Is this Washington DC?
    if re.findall(r'washington', location, re.I) and re.findall(r'\bdc\b', location, re.I):
        where = "name = 'Washington' ORDER BY population DESC"

        result = cursor.execute(query_template.format(where)).fetchone()

        if result:
            return result


    # 2) Is this in the format Name, Country/State/etc
    if ',' in location:
        name, state = location.rsplit(',', 1)
        name = name.strip()
        state = state.strip().upper()

        where = "name = ? AND (state = ? OR country = ?) ORDER BY population DESC"

        result = cursor.execute(query_template.format(where), (name, state, state)).fetchone()

        if result:
            return result


    # 3) Lastly, try just matching the entire location name
    where = "name = ? ORDER BY population DESC"
    return cursor.execute(query_template.format(where), (location, )).fetchone()


if __name__ == '__main__':
    import sys
    from optparse import OptionParser

    parser = OptionParser(usage="Usage: %prog [options] arg1 arg2")
    parser.add_option("--in", "--input", dest="input_path")
    parser.add_option("--loc", "--location", dest="location_column")
    parser.add_option("--out", "--output", dest="output_path")

    options, args = parser.parse_args()
    input_path = options.input_path
    output_path = options.output_path
    location_column = options.location_column or 'location'

    if input_path and output_path:
        _geocode_csv(input_path, output_path, location_column)

    print "Done!"
