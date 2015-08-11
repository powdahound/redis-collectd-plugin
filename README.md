redis-collectd-plugin
=====================

A [Redis](http://redis.io) plugin for [collectd](http://collectd.org) using collectd's [Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

You can capture any kind of Redis metrics like:

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

```
    # Configure the redis_info-collectd-plugin

    <LoadPlugin python>
      Globals true
    </LoadPlugin>

    <Plugin python>
      ModulePath "/opt/collectd/lib/collectd/plugins/python"
      Import "redis_info"

      <Module redis_info>
        Host "localhost"
        Port 6379
        # Un-comment to use AUTH
        #Auth "1234"
        Verbose false
        #Instance "instance_1"
        # Catch Redis metrics (prefix with Redis_)
        Redis_uptime_in_seconds "gauge"
        Redis_uptime_in_days "gauge"
        Redis_lru_clock "counter"
        Redis_connected_clients "gauge"
        Redis_connected_slaves "gauge"
        Redis_blocked_clients "gauge"
        Redis_evicted_keys "gauge"
        Redis_used_memory "bytes"
        Redis_used_memory_peak "bytes"
        Redis_changes_since_last_save "gauge"
        Redis_instantaneous_ops_per_sec "gauge"
        Redis_rdb_bgsave_in_progress "gauge"
        Redis_total_connections_received "counter"
        Redis_total_commands_processed "counter"
        Redis_keyspace_hits "derive"
        Redis_keyspace_misses "derive"
        #Redis_master_repl_offset "gauge"
        #Redis_master_last_io_seconds_ago "gauge"
        #Redis_slave_repl_offset "gauge"
      </Module>
    </Plugin>
```

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
    Instance "instance_9100"
    Redis_uptime_in_seconds "gauge"
    Redis_used_memory "bytes"
    Redis_used_memory_peak "bytes"
  </Module>

  <Module redis_info>
    Host "127.0.0.1"
    Port 9101
    Verbose true
    Instance "instance_9101"
    Redis_uptime_in_seconds "gauge"
    Redis_used_memory "bytes"
    Redis_used_memory_peak "bytes"
    Redis_master_repl_offset "gauge"
  </Module>
  
  <Module redis_info>
    Host "127.0.0.1"
    Port 9102
    Verbose true
    Instance "instance_9102"
    Redis_uptime_in_seconds "gauge"
    Redis_used_memory "bytes"
    Redis_used_memory_peak "bytes"
    Redis_slave_repl_offset "gauge"
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
