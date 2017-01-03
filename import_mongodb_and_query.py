#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
My task in this script has two steps:

- Use python to automatically import cleaned open street map data into local mongodb database
- Run mongo queries to test results of data cleaning and get a whole picture of this cleaned dataset

Usage:
>>> python import_mongodb_and_query.py 
"""
import os
import subprocess
from pymongo import MongoClient

db_name = 'openStreetMap'

# Connect to Mongodb
client = MongoClient('localhost:27017')
db = client[db_name]

# Build mongoimport command
collection = 'shanghai'
json_file = 'shanghai_china.osm.json'

mongoimport_cmd = 'mongoimport -h 127.0.0.1:27017 ' + \
                  '--db ' + db_name + \
                  ' --collection ' + collection + \
                  ' --file ' + json_file

# Before importing, drop collection if it is already running 
if collection in db.collection_names():
    print 'Dropping collection: ' + collection
    db[collection].drop()

# Execute the command
print 'Executing: ' + mongoimport_cmd
subprocess.call(mongoimport_cmd.split())

shanghai = db[collection]

print 'The original OSM file is {} MB'.format(os.path.getsize('shanghai_china.osm')/1.0e6) # convert from bytes to megabytes
print 'The JSON file is {} MB'.format(os.path.getsize(json_file)/1.0e6) # convert from bytes to megabytes

# Begin to run queries

# First part: display general statistic info of whole dataset
print "Total number of records:"
total_num_records = shanghai.find().count()
print(total_num_records)

print "Total number of unique users:"
unique_num_users = len(shanghai.find().distinct("created.user"))
print(unique_num_users)

print "Total number of nodes:"
total_num_nodes = shanghai.find({'type':'node'}).count()
print(total_num_nodes)

print "Total number of ways:"
total_num_ways = shanghai.find({'type':'way'}).count()
print(total_num_ways)

# Second part: confirm dataset meets data cleaning criteria
print "Display postcodes:"
postcodes = shanghai.find().distinct("address.postcode")
print(list(postcodes))

# print "Display street names:"
# street_names = shanghai.find().distinct("address.street")
# print(list(street_names)) # Only English name is human readable.

# print "Display names:"
# names = shanghai.find().distinct("name")
# print(list(names)) # Only English name is human readable.

print "Display phone numbers:"
phones = shanghai.find().distinct("contact:phone")
print(list(phones))

# Third part: dig into and think more about this dataset
print "Top three most mentioned amenity:"
amenity_top_three = shanghai.aggregate([
	{"$match":{"amenity":{"$exists":1}}},
	{"$group":{"_id":"$amenity", "count":{"$sum":1}}},
	{"$sort": {"count": -1}},
	{"$limit": 3}
])
print(list(amenity_top_three))

print "Number of amenities only appear once:"
num_amenity_only_once = shanghai.aggregate([
	{"$group": {"_id":"$amenity", "count": {"$sum": 1}}},
	{"$group": {"_id":"$count", "num_amenity":{"$sum":1}}},
	{"$sort": {"_id":1}},
	{"$limit": 1}
])
print(list(num_amenity_only_once))






