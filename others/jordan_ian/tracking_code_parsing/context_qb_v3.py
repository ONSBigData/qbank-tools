""" Author - Ian Edward"""

from functools import reduce
import operator
import os
import copy
from sys import argv
import csv
import json
from os.path import basename


os.chdir("/Users/edwari/Documents/Exercises/Python/json/json/")
json_file = "350.json" # Selection of Json file passed in as an argument
 # Set the name of the CSV file

with open(json_file,  encoding="utf8") as data_file:
    data_202 = json.load(data_file)

# Function traversing through json file collecting the json paths
def traverse(d, path = []):
    if isinstance(d, dict):
        iterator = d.items()
    else:
        iterator = enumerate(d) # Add count to the path

    # For loop to seperate the keys and values
    for k, v in iterator:
        yield path + [k], v
        if isinstance(v, (dict, list)):
            for k, v in traverse(v, path + [k]):
                yield k, v
full_list = [] # List containing the paths
for pat, nods in traverse(data_202):
    full_list.append(pat)

stored_paths = []

#For loop to select every path with tracking_code as key



for line in full_list:
     if ('tracking_code' in line) and ('cells' not in line):
         print(line)
         thistuple = []
         thistuple.append(line)
         newlist = copy.deepcopy(line)
         # For loop to remove the last element from the paths
         for element in range(0, len(line)-0):
             newlist.pop()
             thistuple.append(copy.copy(newlist))
         stored_paths.append(thistuple)

no_ext = os.path.splitext(json_file)[0]

#Function to append data to keys
def getFromDict(dataDict, *mapList):
    tempInfo = []
    for arg in mapList:
        for mapper in arg:
            for maped in mapper:
                res = reduce(operator.getitem, maped, dataDict)
                if type(res) == dict:
                    print("\n")
                    for x in res.keys():
                        skipLevels = ("segment", "question", "notes")
                        if x not in skipLevels:
                            tempInfo.append((x, res[x]))
            print(tempInfo)
            # Function to write the parsed data to csv file
            with open('/Users/edwari/Documents/Exercises/Python/json/csv-files/i_{0}.csv'.format(no_ext), 'a') as out:
                csv_out=csv.writer(out)
                for row in tempInfo:
                    csv_out.writerow(row)
                csv_out.writerow([])
            tempInfo[:] = []

getFromDict(data_202, stored_paths)