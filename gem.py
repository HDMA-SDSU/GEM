import sqlite3
import re

GEONAMES_DUMP_URL = 'http://download.geonames.org/export/dump/{}.zip'

connection = sqlite3.connect('gazeteer.db')
connection.text_factory = str
cursor = connection.cursor()

#disabling this, since we will pre-populate the db with US data...
#cursor.execute("DROP TABLE places")
#cursor.execute("CREATE TABLE places (name text, latitude real, longitude real, population integer, country_code text)")
 
def _import_table(country_code):
	import urllib, zipfile, csv

	#first, grab the file from geonames
	filehandle, _ = urllib.urlretrieve(GEONAMES_DUMP_URL.format(country_code))

	#unzip the appropriate file and read it
	zipped = zipfile.ZipFile(filehandle, 'r')
	file_stream = zipped.open("{}.txt".format(country_code))
	text = file_stream.read()

	#parse with csv.reader
	reader = csv.reader(text.splitlines(), delimiter='\t', quotechar="'")

	#go through each row
	for row in reader:
		lat = row[4]
		lon = row[5]
		population = row[14]

		#row[1] is the official name and row[3] is a comma-separated list of the alternative names
		names = row[3].split(',') + [row[1]]

		for name in names:
			cursor.execute("INSERT INTO places VALUES (?, ?, ?, ?, ?)", (name, lat, lon, population, country_code))

	#commit changes
	connection.commit()

def _geocode_csv(input_path, output_path, location_column='location'):
	import csv

	reader = csv.reader(open(input_path).readlines(), delimiter='\t', quotechar='"')
	columns = reader.next()
	location_index = columns.index(location_column)

	if location_index == -1:
		raise ValueError("Location column is invalid.")

	output_file = open(output_path, 'wb')
	writer = csv.writer(output_file, delimiter='\t', quotechar='"')
	writer.writerow(columns + [ 'code_longitude', 'code_latitude' ])

	for row in reader:
		loc = row[location_index]

		result = geocode_location(loc)
		row_output = row + [ '', '' ] if not result else [ result[1], result [2] ]
		writer.writeRow(row_output)
		
	output_file.close()
			
def geocode_location(location, country_code='US'):
	#if this is not a valid country code, ignore
	if not cursor.execute("SELECT * FROM places WHERE country_code = ?", country_code): 	
		raise ValueError("Invaid country code.")

	location = location.title()
	#remove weird unicode characters
	location = re.sub(r'[\u00FF-\UFFFF]', '', location)
	#remove punctuation
	location = re.sub(r'[^\w\s]', '', location)
	#remove any remaining whitespace
	location = location.strip()

	#3) Does the location match? 
	
	#1) Is this Washington DC?
	if re.match(r'washington', location, re.I) and re.match(r'\bdc\b', location, re.I):
		query = "SELECT name, latitude, longitude FROM places where name = Washington DC" 	
		
		return cursor.execut(query)

	#2) Is this in the format Name, Country/State/etc
	result = cursor.execute(query, (location,)).fetchone()

	#3) Does the location match? 
	

	return 'No Match'


if __name__ == '__main__':
	import sys

	print geocode_location(sys.argv[1])
