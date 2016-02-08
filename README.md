# destinystats

A tool for tracking K/D ratio in Destiny using InfluxDB

If you want to use this, you need to create an .ini file that lives in the same
directory as the destinystats.py script itself. It follows standard INI
conventions and uses the native Python module for parsing. You will need to
provide the following attributes:

[api]
root_url=https://www.bungie.net/platform/destiny/
api_key=<your API key>
membership_type=<1 or 2 (XBL = 1, PSN = 2)>

[user]
display_name=<your XBL or PSN name>
my_activity_types=<a space-separated list of activities to track; see http://bit.ly/1K8tcPW for list of supported types>

[influx]
dbhost=<InfluxDB host>
dbport=<InfluxDB port>
dbuser=<InfluxDB user with write privileges>
dbpass=<password for this InfluxDB user>
dbname=<InfluxDB database name>

Once you've created the appropriate INI file and have a running InfluxDB
backend, populate the database by running 'destinystats.py'. By default, it
will pull statistics for yesterday, and only yesterday (whatever day that may
actually be); to specify a different day, use the '-i' option to set an offset,
e.g., <i>destinystats.py -i 7</i> will pull daily stats for the day one week
prior, <i>destinystats.py -i 365</i> will pull daily stats for the day one year
prior.
