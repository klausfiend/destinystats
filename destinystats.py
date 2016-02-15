#!/usr/bin/env python
#
# This is a trivial application that extracts information from the Destiny
# database for a given user and uses it to populate a TSDB in InfluxDB. All
# configuration information is kept in an .ini file, see the README for more
# information on what needs to be in there.

# Imports
from influxdb import client as influxdb
import argparse
import ConfigParser
import datetime
import json
import os
import sys
import urllib2


# Function definitions go here.
def ConfigSectionMap(section):
    section_dict = {}
    options = Config.options(section)
    for option in options:
        try:
            section_dict[option] = Config.get(section, option)
            if section_dict[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            section_dict[option] = None
    return section_dict


def uncapitalize(string):
    first_part = string[:1]
    last_part = string[1:]
    return first_part.lower() + last_part


# Standard defaults that live here.
character_types = ('titan', 'hunter', 'warlock')
activity_types = ('None', 'Story', 'Strike', 'Raid', 'AllPvP', 'Patrol',
                  'AllPvE', 'PvPIntroduction', 'ThreeVsThree', 'Control',
                  'Lockdown', 'Team', 'FreeForAll', 'Nightfall', 'Heroic',
                  'AllStrikes', 'IronBanner', 'AllArena', 'Arena',
                  'ArenaChallenge', 'TrialsOfOsiris', 'Elimination', 'Rift',
                  'Mayhem', 'ZoneControl', 'Racing')

# Parse an INI-style config file in the same directory as the script itself
config_file = os.path.dirname(sys.argv[0]) + '/destinystats.ini'
Config = ConfigParser.ConfigParser()
Config.read(config_file)

# Config file defaults
root_url = ConfigSectionMap('api')['root_url']
api_key = ConfigSectionMap('api')['api_key']
membership_type = ConfigSectionMap('api')['membership_type']
display_name = ConfigSectionMap('user')['display_name']
my_activity_types = ConfigSectionMap('user')['my_activity_types'].split()
dbhost = ConfigSectionMap('influx')['dbhost']
dbport = ConfigSectionMap('influx')['dbport']
dbuser = ConfigSectionMap('influx')['dbuser']
dbpass = ConfigSectionMap('influx')['dbpass']
dbname = ConfigSectionMap('influx')['dbname']

# Sanity check activity types to make sure they're known to the Destiny API
for activity_type in my_activity_types:
    if not set([activity_type]).issubset(set(activity_types)):
       print "Unsupported activity in config file: %s" % activity_type
       sys.exit(1)

# Option processing happens here.
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action='store_true', help="print debug information")
parser.add_argument("-i", "--interval", type=int, help="process <interval> days prior instead of yesterday")
args = parser.parse_args()
if args.interval:
    interval = args.interval
else:
    interval = 1
if args.debug:
    debug = True
else:
    debug = False

# Connect to the InfluxDB instance so it's ready for use later.
db = influxdb.InfluxDBClient(dbhost, dbport, dbuser, dbpass, dbname)

# Fetch membership ID (used to fetch character IDs and thus stats)
query_url = root_url + membership_type + '/Stats/GetMembershipIdByDisplayName/' + display_name
request = urllib2.build_opener()
request.addheaders = [('X-API-Key', api_key)]
response = request.open(query_url)
answer = json.loads(response.read())
if answer['ErrorStatus'] != 'Success':
    print "Invalid response from Destiny servers: %s" % answer['ErrorStatus']
    sys.exit(1)
else:
    membership_id = str(answer['Response'])

# Fetch character ID(s) based on the membership ID
query_url = root_url + membership_type + '/Account/' + membership_id
response = request.open(query_url)
answer = json.loads(response.read())
if answer['ErrorStatus'] != 'Success':
    print "Unable to find characters associated with membership ID %s" % membership_id
    sys.exit(1)
else:
    # 'data' is the key, its' value is the response payload
    characters = answer['Response']['data']

# Inventory characters to identify class type (nothing else is of interest yet)
character_info = [{'id': str(c['characterBase']['characterId']),
                   'class': character_types[c['characterBase']['classType']]} for c in characters['characters']]

# Fetch character activity stats from (today - interval days) for each character.
date_in_sec = int(datetime.date.fromordinal(datetime.date.today().toordinal() - interval).strftime("%s"))
date = datetime.date.fromtimestamp(date_in_sec).strftime("%F")
date_in_nsec = date_in_sec * 1000000000
for c in character_info:
    query_url = root_url + 'Stats/' + membership_type + '/' + membership_id + '/' + c['id'] + \
            '/?periodType=1&daystart=' + date + '&dayend=' + date + '&modes=' + ','.join(my_activity_types)
    if debug == True:
        print query_url
    # Create the skeletal data point
    influx_data = [ { 'measurement': c['class'] + '_' + c['id'], 'time': date_in_nsec, 'fields': {} } ]
    response = request.open(query_url)
    answer = json.loads(response.read())
    if answer['ErrorStatus'] != 'Success':
        print "Problem reading back activity information for character ID %s, skipping it ..." % c['id']
        continue
    else:
        c['activity'] = answer['Response']
        for activity in my_activity_types:
            a = uncapitalize(activity)
            if len(c['activity'][a]) > 0:
                kills = float(c['activity'][a]['daily'][0]['values']['kills']['basic']['value'])
                deaths = float(c['activity'][a]['daily'][0]['values']['deaths']['basic']['value'])
                ratio = kills/deaths if deaths != 0 else kills
                # Flesh out the data point with actual results
                influx_data[0]['fields'][a] = ratio
                if debug == True:
                    print "%s %s kills: %.2f deaths: %.2f" % (c['class'], a, kills, deaths)
                    print "\t%s KD ratio: %.2f" % (a, ratio)
        # Write the data point now that it's fully fleshed out.
        if len(influx_data[0]['fields']) > 0:
            db.write_points(influx_data)
