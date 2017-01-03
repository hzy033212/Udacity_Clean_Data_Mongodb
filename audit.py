#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
My task in this script has two steps:

- audit the shanghai_china.osm and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
Usage:
>>> python audit.py 
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "shanghai_china.osm"
street_type_re = re.compile(r'(\b\S+lu.*|\b\S+\.?$)', re.IGNORECASE) # Note that "lu" in Chinese PingYin means English word road
postcode_re = re.compile(r'^\d{6}$') # Valid postcode should only contains 6 continual digits

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

def is_address_city(elem):
    """
    Check whether element contains city info.
    """
    return elem.attrib['k'] == "addr:city"

def is_address_shanghai(elem):
    """
    If element contains city info, check whether it is Shanghai?
    """
    city = elem.attrib['v']
    return (city == "Shanghai") or (city == "shanghai") or (city == u"上海") or (city == u"上海市") # Last two is Chinese version of Shanghai

def is_address_postcode(elem):
    """
    Check whether element contains postcode info.
    """
    return (elem.attrib['k'] == "addr:postcode")

def is_valid_postcode(elem):
    """
    If element contains postcode, check whether it is in valid format?
    """
    return postcode_re.search(elem.attrib['v'])

def is_phone_number(elem):
    """
    Check whether element contains phone info.
    """
    return (elem.attrib['k'] == "contact:phone")

def audit_phone_format(phone, phoneDict):
    """
    Extract useful information and reformat the phone number to a unified format.

    Args:
        param_1(string): phone number string
        param_2(dictionary): Keys are original phone numbers
                             Values are convertted unified format phone numbers
    Returns:
        None
    """
    phoneLen = len(phone)
    tmp = ""
    for i in range(0, phoneLen):
        if phone[i].isdigit():
            tmp = tmp + phone[i]
    phoneDict[phone] = tmp[-11:]

def is_street_name(elem):
    """
    Check whether element contains street info.
    """
    return (elem.attrib['k'] == "addr:street")

def audit_street_type(street_types, street_name):
    """
    Add all may not formatted street name to a dictionary

    Args:
        param_1(dictionary): Keys are street types
                             Values are street names meets street types
        param_2(string): street name string
    Returns:
        None
    """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def audit(osmfile):
    """
    Audit xml file. It contains following steps:
    1) Audit street name to unified format;
    2) Audit phone number to unified format;
    3) Audit postcode to extract all ill formatted postcodes;
    4) Audit city to extract all not in shanghai cities;

    Args:
        param_1(string): target xml file name
    Returns:
        street_types => a dictionary mapping old unformatted street name to unified formatted street name
        phone_dict => a dictionary mapping old unformatted phone number to unified formatted phone number
        not_in_shanghai => a set contains all tags whose city is not in Shanghai
        not_valid_postcode => a set contains all tags whose postcode is not valid 
    """
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    phone_dict = defaultdict(set)
    not_in_shanghai = set()
    not_valid_postcode = set()
    count = 0
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                elif is_phone_number(tag):
                    audit_phone_format(tag.attrib['v'], phone_dict)
                elif is_address_postcode(tag) and not is_valid_postcode(tag):
                    not_valid_postcode.add(tag)
                elif is_address_city(tag) and not is_address_shanghai(tag):
                    print tag.attrib['v'] # Test whether it is right to omit this record, uncomment to avoid output
                    not_in_shanghai.add(tag.attrib['v'])
            count += 1
            # Uncomment following two lines to show progress
            # if (count % 10000) == 0:
            #     print "Audit to record #{}".format(count)
    osm_file.close()
    return street_types, phone_dict, not_in_shanghai, not_valid_postcode


def update_name(name, mapping):
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


def test():
    st_types, phone_dict, not_in_shanghai, not_valid_postcode = audit(OSMFILE)

    print "==========Begin to print street name and the formatted ones=========="
    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping)
            print name, "=>", better_name

    print "==========Begin to print phone number and the formatted ones=========="
    for phone, right_format_phone in phone_dict.iteritems():
        print phone, "=>", right_format_phone

    print "==========Begin to print not valid postcode=========="
    for postcode in not_valid_postcode:
        print postcode.attrib['v']

    print "==========Begin to print not in Shanghai data records=========="
    for records in not_in_shanghai:
        pprint.pprint(records) # Only English characters are human readable. Others can be checked via previously output.


if __name__ == '__main__':
    test()

