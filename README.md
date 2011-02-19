redis-collectd-plugin
=====================

A [Redis](http://redis.google.code.com) plugin for [collectd](http://collectd.org) using collectd's [Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

Data captured includes:

 * Memory used
 * Commands processed per second
 * Number of connected clients and slaves
 * Number of blocked clients
 * Number of keys stored (per database)
 * Uptime
 * Changes since last save

Install
-------
 1. Place redis_info.py in /opt/collectd/lib/collectd/plugins/python (assuming you have collectd installed to /opt/collectd).
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
      Import "redis_info"
    
      <Module redis_info>
        Host "localhost"
        Port 6379
        Verbose false
      </Module>
    </Plugin>

Graph examples
--------------
These graphs were created using collectd's [rrdtool plugin](http://collectd.org/wiki/index.php/Plugin:RRDtool) and [drraw](http://web.taranis.org/drraw/).

![Clients connected](https://github.com/powdahound/redis-collectd-plugin/raw/master/screenshots/graph_clients_connected.png)
![Commands/sec](https://github.com/powdahound/redis-collectd-plugin/raw/master/screenshots/graph_commands_per_sec.png)
![db0 keys](https://github.com/powdahound/redis-collectd-plugin/raw/master/screenshots/graph_db0_keys.png)
![Memory used](https://github.com/powdahound/redis-collectd-plugin/raw/master/screenshots/graph_memory_used.png)

Requirements
------------
 * collectd 4.9+
