redis-collectd-plugin
=====================

A [Redis](http://redis.google.code.com) plugin for [collectd](http://collectd.org) using collectd's [Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

Install
-------
Soemthing...

Configuration
-------------
Add the following to your collectd config or use the included redis.conf.

    <LoadPlugin python>
      Globals true
    </LoadPlugin>
    
    <Plugin python>
      ModulePath "/opt/collectd/lib/collectd/plugins/python/"
      LogTraces true
      Interactive false
      Import "redis"
    
      <Module redis>
        Host "localhost"
        Port 6379
      </Module>
    </Plugin>

