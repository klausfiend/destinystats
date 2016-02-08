# destinystats

A tool for tracking K/D ratio in Destiny using InfluxDB

If you want to use this, you need to create an .ini file that lives in the same
directory as the destinystats.py script itself. It follows standard INI
conventions and uses the native Python module for parsing. You will need to
provide the following attributes:

<pre>
[api]
root_url=https://www.bungie.net/platform/destiny/
api_key=&lt;your API key&gt;
membership_type=&lt;1 or 2 (XBL = 1, PSN = 2)&gt;

[user]
display_name=&lt;your XBL or PSN name&gt;
my_activity_types=&lt;a space-separated list of tracked activities&gt;

[influx]
dbhost=&lt;InfluxDB host&gt;
dbport=&lt;InfluxDB port&gt;
dbuser=&lt;InfluxDB user with write privileges&gt;
dbpass=&lt;password for this InfluxDB user&gt;
dbname=&lt;InfluxDB database name&gt;
</pre>

Once you've created the appropriate INI file and have a running InfluxDB
backend, populate the database by running 'destinystats.py' (see
http://bit.ly/1K8tcPW for list of supported activity types.)

By default, the script will pull statistics for yesterday, and only yesterday
(whatever day that may actually be); to specify a different day, use the '-i'
option to set an offset:

Pull daily stats for the day one week prior:

<pre>destinystats.py -i 7</pre>

Pull daily stats for the day one year prior.
<pre>destinystats.py -i 365</pre>

Enable debug output (such as it is):
<pre>destinystats.py -d</pre>

