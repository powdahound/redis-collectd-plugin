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
 * Replication delay (per slave)

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

### Multiple Redis instances

You can configure to monitor multiple redis instances by the same machine by repeating the <Module> section, such as:

```
<Plugin python>
  ModulePath "/opt/collectd_plugins"
  Import "redis_info"

  <Module redis_info>
    Host "127.0.0.1"
    Port 9100
    Verbose true
  </Module>

  <Module redis_info>
    Host "127.0.0.1"
    Port 9101
    Verbose true
  </Module>
  
  <Module redis_info>
    Host "127.0.0.1"
    Port 9102
    Verbose true
  </Module>
</Plugin>
```

These 3 redis instances listen on different ports, they have different plugin_instance combined by Host and Port:

```
"plugin_instance" => "127.0.0.1:9100",
"plugin_instance" => "127.0.0.1:9101",
"plugin_instance" => "127.0.0.1:9102",
```

These values will be part of the metric name emitted by collectd, e.g. ```collectd.redis_info.127.0.0.1:9100.bytes.used_memory```

If you want to set a static value for the plugin instance, use the ```Instance``` configuration option:

```
...
  <Module redis_info>
    Host "127.0.0.1"
    Port 9102
    Instance "redis-prod"
  </Module>
...
```
This will result in metric names like: ```collectd.redis_info.redis-prod.bytes.used_memory```

```Instance``` can be empty, in this case the name of the metric will not contain any reference to the host/port. If it is omitted, the host:port value is added to the metric name.

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
