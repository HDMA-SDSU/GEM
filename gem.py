#!/usr/bin/env python

import sqlite3
import re

GEONAMES_DUMP_URL = 'http://download.geonames.org/export/dump/{}.zip'

connection = sqlite3.connect('./gazetteer.db')
connection.text_factory = str
cursor = connection.cursor()

POPULATE = False
#disabling this, since we will pre-populate the db with US data...
if POPULATE:
	cursor.execute("DROP TABLE places")
	cursor.execute("CREATE TABLE places (name text, country text, state text, latitude real, longitude real, population integer, country_code text)")


def _import_table(country_code):
	import urllib, zipfile, csv

	#first, grab the file from geonames
	filehandle, _ = urllib.urlretrieve(GEONAMES_DUMP_URL.format(country_code))

	#unzip the appropriate file and read it
	zipped = zipfile.ZipFile(filehandle, 'r')
	file_stream = zipped.open("{}.txt".format(country_code))
	text = file_stream.read()

	##parse with csv.reader
	reader = csv.reader(text.splitlines(), delimiter='\t', quotechar="'")

	##go through each row
	for row in reader:
		lat = row[4]
		lon = row[5]
		population = row[14]
		state = row[10] 
		country = row[8] 
		
		#row[1] is the official name and row[3] is a comma-separated list of the alternative names
		names = row[3].split(',') + [ row[1] ]

		for name in names:
			cursor.execute("INSERT INTO places VALUES (?, ?, ?, ?, ?, ?, ?)", (name, country, state, lat, lon, population, country_code))

	##commit changes
	connection.commit()


def _geocode_csv(input_path, output_path, location_column='location'):
	import csv

	reader = csv.reader(open(input_path).readlines(), delimiter=',', quotechar='"')
	columns = reader.next()

	if columns.count(location_column) == 0:
		raise ValueError("Location column is invalid.")

	location_index = columns.count(location_column)

	output_file = open(output_path, 'wb')
	writer = csv.writer(output_file, delimiter=',', quotechar='"')
	writer.writerow(columns + [ 'code_longitude', 'code_latitude' ])

	for row in reader:
		loc = row[location_index]

		result = geocode_location(loc)
		row_output = row + ([ '', '' ] if not result else [ result[4], result [3] ])
		writer.writerow(row_output)
		
	output_file.close()
			
			
def geocode_location(location):
	''' TODO: State and country fields only using codes right now (eg, CA rather than California)'''

	location = location.title()
	#remove weird unicode characters (something's not working with this, so disabling for now...)
	#location = re.sub(r'[\u00FF-\uFFFF]', '', location)
	#remove punctuation
	location = re.sub(r'[^,\w\s]', '', location)
	#remove any remaining whitespace
	location = location.strip()
	
	#1) Is this Washington DC?
	if re.findall(r'washington', location, re.I) and re.findall(r'\bdc\b', location, re.I):
		query = "SELECT name, country, latitude, longitude FROM places WHERE name = 'Washington'"

		result = cursor.execute(query).fetchone()
		
		if result:
			return result


	#2) Is this in the format Name, Country/State/etc
	if re.findall(',', location):
		name, state = location.rsplit(',', 1)
		name = name.strip()
		state = state.strip().upper()
		
		query = "SELECT name, country, state, latitude, longitude FROM places WHERE name = ? AND (state = ? OR country = ?) ORDER BY population DESC"

		result = cursor.execute(query, (name, state, state)).fetchone()

		if result:
			return result


	#3) Lastly, try just matching the entire location name
	return cursor.execute("SELECT name, country, state, latitude, longitude FROM places WHERE name = ? ORDER BY population DESC", (location, )).fetchone()


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
