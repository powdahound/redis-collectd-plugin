redis-collectd-plugin
=====================

A [Redis](http://redis.google.code.com) plugin for [collectd](http://collectd.org) using collectd's [Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

Data captured includes:

 * Memory used
 * Commands processed per second
 * Number of connected clients
 * Number of keys stored (per database)

Install
-------
 1. Place redis.py in /opt/collectd/lib/collectd/plugins/python (assuming you have collectd installed to /opt/collectd).
 2. Configure the plugin (see below).
 3. Restart collectd.

Configuration
-------------
Add the following to your collectd config **or** use the included redis.conf.

    <LoadPlugin python>
      Globals true
    </LoadPlugin>
    
    <Plugin python>
      ModulePath "/opt/collectd/lib/collectd/plugins/python"
      Import "redis"
    
      <Module redis>
        Host "localhost"
        Port 6379
        Verbose false
      </Module>
    </Plugin>

TODO
----
 * Install script (is there a correct place for Python plugins?)
 * Include & show some example RRD graphs
