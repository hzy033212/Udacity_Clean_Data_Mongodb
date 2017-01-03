#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mapparser.py is used to get a whole picture of what I will face in the cleaning of open street map data
and then decide what steps I will need to do later in cleaning data.
Usage:
>>> python mapparser.py
"""

import xml.etree.cElementTree as ET
import pprint
import re

def count_keys(filename):
    """
    Count different keys in 'tag' in a xml file. 
    I use this function to get a whole picture of what kinds of key values this xml data contains.

    For usage, please refer to test() at the end of this python script.

    Args:
        param_1(string): Input xml file name.
    Returns:
        dictionary: Keys are the distinct k value of node whose tag is 'tag';
                    Values are their corresponding appearance.
    """
    fields = {}
    count = 0
    for _, node in ET.iterparse(filename):
        if node.tag == 'tag':
            for tag in node.iter('tag'):
                k = tag.get('k')
                if k in fields.keys():
                    fields[k] = fields[k] + 1
                else:
                    fields[k] = 1
                count += 1
                # Uncomment following two lines to show progress
                if (count % 10000) == 0:
                    print "count_keys=> {}".format(count)
    return fields

def count_tags(filename):
    """
    Count different tags in a xml file. 
    I use this function to get a whole picture of what kinds of tag values this xml data contains.

    For usage, please refer to test() at the end of this python script.

    Args:
        param_1(string): Input xml file name.
    Returns:
        dictionary: Keys are the distinct tags;
                    Values are their corresponding appearance.
    """
    tags = {}
    count = 0
    for _, node in ET.iterparse(filename):
        tag = node.tag
        if tag not in tags:
            tags[tag] = 1
        else:
            tags[tag] = tags[tag] + 1
        count += 1
        # Uncomment following two lines to show progress
        if (count % 10000) == 0:
            print "count_tags=> {}".format(count)
    return tags

def test():
    tags = count_tags('shanghai_china.osm')
    keys = count_keys('shanghai_china.osm')
    print "==========Different TAGs and their counts=========="
    pprint.pprint(tags)
    print "==========Different fields and their counts=========="
    pprint.pprint(keys)   

if __name__ == "__main__":
    test()

