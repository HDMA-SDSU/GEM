#!/usr/bin/env python

import sqlite3
import re
import os

GEONAMES_DUMP_URL = 'http://download.geonames.org/export/dump/{}.zip'
GAZETTEER_PATH = os.path.join(os.path.dirname(__file__), 'gazetteer.db')

# Mapping of state full-names (eg, 'California') to abbreviations (eg, 'CA')
STATE_FULL_TO_ABBR = {
    'ALABAMA': 'AL',
    'ALASKA': 'AK',
    'ARIZONA': 'AZ',
    'ARKANSAS': 'AR',
    'CALIFORNIA': 'CA',
    'COLORADO': 'CO',
    'CONNECTICUT': 'CT',
    'DELAWARE': 'DE',
    'FLORIDA': 'FL',
    'GEORGIA': 'GA',
    'HAWAII': 'HI',
    'IDAHO': 'ID',
    'ILLINOIS': 'IL',
    'INDIANA': 'IN',
    'IOWA': 'IA',
    'KANSAS': 'KS',
    'KENTUCKY': 'KY',
    'LOUISIANA': 'LA',
    'MAINE': 'ME',
    'MARYLAND': 'MD',
    'MASSACHUSETTS': 'MA',
    'MICHIGAN': 'MI',
    'MINNESOTA': 'MN',
    'MISSISSIPPI': 'MS',
    'MISSOURI': 'MO',
    'MONTANA': 'MT',
    'NEBRASKA': 'NE',
    'NEVADA': 'NV',
    'NEW HAMPSHIRE': 'NH',
    'NEW JERSEY': 'NJ',
    'NEW MEXICO': 'NM',
    'NEW YORK': 'NY',
    'NORTH CAROLINA': 'NC',
    'NORTH DAKOTA': 'ND',
    'OHIO': 'OH',
    'OKLAHOMA': 'OK',
    'OREGON': 'OR',
    'PENNSYLVANIA': 'PA',
    'RHODE ISLAND': 'RI',
    'SOUTH CAROLINA': 'SC',
    'SOUTH DAKOTA': 'SD',
    'TENNESSEE': 'TN',
    'TEXAS': 'TX',
    'UTAH': 'UT',
    'VERMONT': 'VT',
    'VIRGINIA': 'VA',
    'WASHINGTON': 'WA',
    'WEST VIRGINIA': 'WV',
    'WISCONSIN': 'WI',
    'WYOMING': 'WY'
}
        
connection = sqlite3.connect(GAZETTEER_PATH)
connection.text_factory = str
cursor = connection.cursor()


def _import_table(country_code, reset=False):
    """Import a GeoNames table based on the country code."""

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
    """Geocode each row in the input and output the geocoded information."""

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
    """Return a place name, state, country, latitude, and longitude for the 
    given location string.
    """

    query_template = """SELECT name, state, country, latitude, longitude
            FROM places WHERE {} ORDER BY population DESC"""

    location = location.title()
    # remove weird unicode characters 
    location = location.encode('ascii', 'ignore')
    # remove punctuation
    location = re.sub(r'[^,\w\s]', '', location)
    # remove any remaining whitespace
    location = location.strip()

    # 1) Is this Washington DC?
    if re.findall(r'washington', location, re.I) and re.findall(r'\bdc\b', location, re.I):
        where = "name = 'Washington'"

        result = cursor.execute(query_template.format(where)).fetchone()

        if result:
            return result


    # 2) Is this in the format "Name, Country/State/etc"
    if ',' in location:
        name, state = location.rsplit(',', 1)
        name = name.strip()
        state = state.strip().upper()

        if len(state) > 2:
            state = STATE_FULL_TO_ABBR.get(state, '')

        if state:
            where = "name = ? AND (state = ? OR country = ?)"

            result = cursor.execute(query_template.format(where), (name, state, state)).fetchone()

            if result:
                return result


    # 3) Last, try just matching the entire location name
    where = "name = ?"
    return cursor.execute(query_template.format(where), (location, )).fetchone()


if __name__ == '__main__':
    import sys
    from optparse import OptionParser

    parser = OptionParser(usage="Usage: %prog")
    parser.add_option("--in", "--input", dest="input_path", help="Input file path.")
    parser.add_option("--out", "--output", dest="output_path", help="Output file path.")
    parser.add_option("--loc", "--location", dest="location_column", 
            help="Name of location column (will default to 'location').")
    
    options, args = parser.parse_args()
    input_path = options.input_path
    output_path = options.output_path
    location_column = options.location_column or 'location'

    if input_path and output_path:
        _geocode_csv(input_path, output_path, location_column)
    else:
        parser.error("Need at least input and ouput paths. Use --h flag for options.")

    print "Geocoding complete!  Ouput file stored at {}".format(output_path)
