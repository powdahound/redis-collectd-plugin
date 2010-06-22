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

Graph examples
--------------
These graphs were created using collectd's [rrdtool plugin](http://collectd.org/wiki/index.php/Plugin:RRDtool) and [drraw](http://web.taranis.org/drraw/).

![Clients connected](http://github.com/powdahound/redis-collectd-plugin/raw/master/screenshots/graph_clients_connected.png)
![Commands/sec](http://github.com/powdahound/redis-collectd-plugin/raw/master/screenshots/graph_commands_per_sec.png)
![db0 keys](http://github.com/powdahound/redis-collectd-plugin/raw/master/screenshots/graph_db0_keys.png)
![Memory used](http://github.com/powdahound/redis-collectd-plugin/raw/master/screenshots/graph_memory_used.png)

TODO
----
 * Install script (is there a correct place for Python plugins?)
 * Include & show some example RRD graphs
