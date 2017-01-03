#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import codecs
import json
"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if the second level tag "k" value contains problematic characters, it should be ignored
- if the second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if the second level tag "k" value does not start with "addr:", but contains ":", you can
  process it in a way that you feel is best. For example, you might split it into a two-level
  dictionary like with "addr:", or otherwise convert the ":" to create a valid key.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]

---------------------------------------------------------------------------------------------------
Note I also add some new codes. For detail please see function descriptions and code comments.
Usage:
>>> python data.py
"""


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
postcode_re = re.compile(r'^\d{6}$') # Valid postcode should only contains 6 continual digits
street_type_re = re.compile(r'(\b\S+lu.*|\b\S+\.?$)', re.IGNORECASE) # Note that "lu" in Chinese PingYin means English word road

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", u"路"] # "路" means road in Chinese

mapping = { "St.": "Street",
            "St": "Street",
            "Ave": "Avenue",
            "Rd.": "Road",
            "Rd": "Road",
            "Raod": "Road",
            "road": "Road",
            "rd": "Road",
            "Lu": "Road",
            "lu": "Road",
            "street": "Street",
            "avenue": "Avenue"
            }

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
COUNT = 0

def inc():
    """
    Print out progress
    """
    global COUNT
    COUNT = COUNT+1
    if (COUNT % 10000) == 0: # Print out every 10000 records to show the conversion progress.
        print "......{}".format(COUNT)

def format_street_name(name, mapping):
    """
    Update an unformatted street name to a unified formatted ones using a given mapping

    Args:
        param_1(string): street name string
        param_2(dictionary): Keys are ill formatted street name parts
                             Values are good formatted street name parts accordingly
    Returns:
        string: Formatted new street name of given old street name
    """
    betterName = ""
    prevLen = 0 # Find and replace only the longest format, for example, if "rd." exists, replace it with "road" but not "road."
    for key in mapping:
        if key in name:
            if len(key) > prevLen:
                betterName = name.replace(key, mapping[key])
                prevLen = len(key)
    if prevLen == 0: # Original street name is already formatted
        betterName = name
    return betterName

def is_address_shanghai(city):
    """
    If element contains city info, check whether it is Shanghai?
    """
    return (city == "Shanghai") or (city == "shanghai") or (city == u"上海") or (city == u"上海市") # Last two is Chinese version of Shanghai

def isInfo(dict):
    """
    Check whether a given dictionary contains enough information that I need the data
    A data dictionary is informative if and only if it shows that its city is not not in Shanghai,
    and it contains fields more than "pos", "_id", "type", "id", "created", "created_by".

    Args:
        param_1(dictionary): a given dictionary containing one data extracted from xml file
    Returns:
        boolean: whether this data is informative or not
    """
    keys = dict.keys()
    cntUninfoKeys = 0
    if "pos" in keys:
        cntUninfoKeys += 1
    if "_id" in keys:
        cntUninfoKeys += 1
    if "type" in keys:
        cntUninfoKeys += 1
    if "id" in keys:
        cntUninfoKeys += 1
    if "created" in keys:
        cntUninfoKeys += 1
    if "created_by" in keys:
        cntUninfoKeys += 1
    if "not_in_Shanghai" in keys: # Not in Shanghai, so not informative
        return False
    target = len(keys)
    return target > cntUninfoKeys

def contactPhoneFormat(str):
    """
    Extract useful information and reformat the phone number to a unified format.

    Args:
        param_1(string): phone number string
    Returns:
        Formatted phone number string 
    """
    strLen = len(str)
    tmp = ""
    for i in range(0, strLen):
        if str[i].isdigit():
            tmp = tmp + str[i]
    return tmp[-11:]

def shape_element(element):
    """
    Shape element to a good format or discard a not valid element.
    This function contains following parts:
    1) Add "CREATED" and change format of longtitude and latitude to floats
    2) Add all valid sub tags
        i)      Format phone number
        ii)     Discard k with strange characters
        iii)    If English name exists, replace (or add) name field with the English name
        iv)     Format street names
        v)      Discard unvalid postcode field and not in shanghai whole data
    3) Add type - node or way

    Note: No two ":" allowed in keys (discard), put all keys start with "addr:" into address field and all other conditions just 
    put into key-value pairs as in xml file. Also if you want to see what field in data has been changed in progress, please uncomment 
    all the related print statements.

    Args:
        param_1(string): element wait to be formatted
    Returns:
        dictionary: formatted element, none if this element is not valid 
    """
    rst = {}
    if element.tag == "node" or element.tag == "way":
        # If you do not want to see progress number, comment next line
        inc()
        createdDict = {}
        posArr = []
        addressDict = {}
        node_refs = []
        for key in element.attrib:
            if key in CREATED:
                createdDict[key] = element.attrib[key]
            elif key in ['lon', 'lat']:
                posArr.append(float(element.attrib[key]))
            else:
                rst[key] = element.attrib[key]
        if len(posArr) != 0:
            posArr[0], posArr[1] = posArr[1], posArr[0]
        # Add all valid sub tags
        for node in element.findall('tag'):
            valK = node.attrib['k']
            if problemchars.match(valK):
                continue
            elif valK == 'contact:phone': # Format ill formatted phone number
                # Uncomment next four lines of codes if you want to see changes in progress.
                # print "==========Original Phone Format: "
                # print node.attrib['v']
                # print "==========Converted Phone Format: "
                # print contactPhoneFormat(node.attrib['v'])
                rst[valK] = contactPhoneFormat(node.attrib['v'])
            elif valK == 'name:en': # If an English name is already exists, replace or add "name" using the English name
                # Uncomment next four commant lines of codes if you want to see changes in progress
                # print "==========name:en is "
                # print node.attrib['v']
                rst['name'] = node.attrib['v']
                # print "==========name is "
                # print rst['name']
            elif valK[:5] == "addr:":
                realKey = valK[5:]
                if ":" in realKey: # No two ":" allowed in keys
                    continue
                else:
                    if realKey == "postcode" and not postcode_re.search(node.attrib['v']): # Filter unvalid postcode
                        # print Uncomment next two commant lines of codes if you want to see changes in progress
                        # print "==========Unvalid postcode: "
                        # print node.attrib['v']
                        continue
                    elif realKey == "city" and not is_address_shanghai(node.attrib['v']):
                        # print Uncomment next two commant lines of codes if you want to see changes in progress 
                        # print "==========Not in Shanghai: "
                        # print node.attrib['v']
                        rst['not_in_Shanghai'] = True # Flag not in Shanghai
                        continue
                    elif realKey == "street" and street_type_re.search(node.attrib['v']): # Properly format English street name
                        # print Uncomment next four commant lines of codes if you want to see changes in progress
                        # print "==========Original Street Name: "
                        # print node.attrib['v']
                        # print "==========Formatted Street Name: "
                        # print format_street_name(node.attrib['v'], mapping)
                        addressDict[valK[5:]] = format_street_name(node.attrib['v'], mapping)
                        continue
                    else:
                        addressDict[valK[5:]] = node.attrib['v']
            else:
                rst[node.attrib['k']] = node.attrib['v']
        # Add all valid sub nds
        if element.tag == "way":
            rst['type'] = 'way'
            for nds in element.findall('nd'):
                node_refs.append(nds.attrib['ref'])
        else:
            rst['type'] = 'node'
            for nds in element.findall('nd'):
                node_refs.append(nds.attrib['ref'])
        if len(node_refs) != 0:
            rst['node_refs'] = node_refs
        if len(addressDict) != 0:
            rst['address'] = addressDict
        if len(posArr) != 0:
            rst['pos'] = posArr
        if len(createdDict) != 0:
            rst['created'] = createdDict
        return rst
    else:
        return None


def process_map(file_in, pretty = False):
    """
    Read in xml from a given input file, format data and output formatted data to an output file,
    and output total input data number and total output data number.

    Args:
        param_1(string): input file name string
        param_2(boolean): output in pretty format(True) or not(False), default False.
    Returns:
        None
    """
    file_out = "{0}.json".format(file_in)
    countTotal = 0
    countAdmit = 0
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            countTotal += 1
            el = shape_element(element)
            if el and isInfo(el): # Filter those records who are not informative
                countAdmit += 1
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    print "=========Total records number is {}".format(countTotal)
    print "=========Total admit records number is {}".format(countAdmit)

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    process_map('shanghai_china.osm', False)

if __name__ == "__main__":
    test()


