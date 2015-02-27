# redis-collectd-plugin - redis_info.py
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# Authors:
#   Garret Heaton <powdahound at gmail.com>
#
# About this plugin:
#   This plugin uses collectd's Python plugin to record Redis information.
#
# collectd:
#   http://collectd.org
# Redis:
#   http://redis.googlecode.com
# collectd-python:
#   http://collectd.org/documentation/manpages/collectd-python.5.shtml

import collectd
import socket
import re

# Verbose logging on/off. Override in config by specifying 'Verbose'.
VERBOSE_LOGGING = False

CONFIGS = []

def fetch_info( conf ):
    """Connect to Redis server and request info"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((conf[ 'host' ], conf['port']))
        log_verbose('Connected to Redis at %s:%s' % (conf[ 'host' ], conf['port']))
    except socket.error, e:
        collectd.error('redis_info plugin: Error connecting to %s:%d - %r'
                       % (conf[ 'host' ], conf['port'], e))
        return None

    fp = s.makefile('r')

    if conf['auth'] is not None:
        log_verbose('Sending auth command')
        s.sendall('auth %s\r\n' % (conf['auth']))

        status_line = fp.readline()
        if not status_line.startswith('+OK'):
            # -ERR invalid password
            # -ERR Client sent AUTH, but no password is set
            collectd.error('redis_info plugin: Error sending auth to %s:%d - %r'
                           % (conf[ 'host' ], conf['port'], status_line))
            return None

    log_verbose('Sending info command')
    s.sendall('info\r\n')

    status_line = fp.readline()
    content_length = int(status_line[1:-1]) # status_line looks like: $<content_length>
    data = fp.read(content_length)
    log_verbose('Received data: %s' % data)
    s.close()

    linesep = '\r\n' if '\r\n' in data else '\n'
    return parse_info(data.split(linesep))


def parse_info(info_lines):
    """Parse info response from Redis"""
    info = {}
    for line in info_lines:
        if "" == line or line.startswith('#'):
            continue

        if ':' not in line:
            collectd.warning('redis_info plugin: Bad format for info line: %s'
                             % line)
            continue

        key, val = line.split(':')

        # Handle multi-value keys (for dbs and slaves).
        # db lines look like "db0:keys=10,expire=0"
        # slave lines look like "slave0:ip=192.168.0.181,port=6379,state=online,offset=1650991674247,lag=1"
        if ',' in val:
            split_val = val.split(',')
            val = {}
            for sub_val in split_val:
                k, _, v = sub_val.rpartition('=')
                val[k] = v

        info[key] = val

    info["changes_since_last_save"] = info.get("changes_since_last_save", info.get("rdb_changes_since_last_save"))

    # For each slave add an additional entry that is the replication delay
    regex = re.compile("slave\d+")
    for key in info:
        if regex.match(key):
            info[key]['delay'] = int(info['master_repl_offset']) - int(info[key]['offset'])

    return info

def configure_callback(conf):
    """Receive configuration block"""
    host = None
    port = None
    auth = None

    for node in conf.children:
        key = node.key.lower()
        val = node.values[0]

        if key == 'host':
            host = val
        elif key == 'port':
            port = int(val)
        elif key == 'auth':
            auth = val
        elif key == 'verbose':
            global VERBOSE_LOGGING
            VERBOSE_LOGGING = bool(node.values[0]) or VERBOSE_LOGGING
        else:
            collectd.warning('redis_info plugin: Unknown config key: %s.' % key )
            continue

    log_verbose('Configured with host=%s, port=%s, using_auth=%s' % ( host, port, auth!=None))

    CONFIGS.append( { 'host': host, 'port': port, 'auth':auth } )

def dispatch_value(info, key, type, plugin_instance=None, type_instance=None):
    """Read a key from info response data and dispatch a value"""
    if key not in info:
        collectd.warning('redis_info plugin: Info key not found: %s' % key)
        return

    if not plugin_instance:
        plugin_instance = 'unknown redis'

    if not type_instance:
        type_instance = key

    value = int(info[key])
    log_verbose('Sending value: %s=%s' % (type_instance, value))

    val = collectd.Values(plugin='redis_info')
    val.type = type
    val.type_instance = type_instance
    val.plugin_instance = plugin_instance
    val.values = [value]
    val.dispatch()

def read_callback():
    for conf in CONFIGS:
        get_metrics( conf )

def get_metrics( conf ):
    info = fetch_info( conf )

    if not info:
        collectd.error('redis plugin: No info received')
        return

    plugin_instance = '{host}:{port}'.format(host=conf['host'], port=conf['port'])

    # send high-level values
    dispatch_value(info, 'uptime_in_seconds','gauge', plugin_instance)
    dispatch_value(info, 'connected_clients', 'gauge', plugin_instance)
    dispatch_value(info, 'connected_slaves', 'gauge', plugin_instance)
    dispatch_value(info, 'blocked_clients', 'gauge', plugin_instance)
    dispatch_value(info, 'evicted_keys', 'gauge', plugin_instance)
    dispatch_value(info, 'used_memory', 'bytes', plugin_instance)
    dispatch_value(info, 'changes_since_last_save', 'gauge', plugin_instance)
    dispatch_value(info, 'total_connections_received', 'counter', plugin_instance,
                   'connections_received')
    dispatch_value(info, 'total_commands_processed', 'counter', plugin_instance,
                   'commands_processed')

    # send replication stats, but only if they exist (some belong to master only, some to slaves only)
    if 'master_repl_offset' in info: dispatch_value(info, 'master_repl_offset', 'gauge', plugin_instance)
    if 'master_last_io_seconds_ago' in info: dispatch_value(info, 'master_last_io_seconds_ago', 'gauge', plugin_instance)
    if 'slave_repl_offset' in info: dispatch_value(info, 'slave_repl_offset', 'gauge', plugin_instance)

    # database and vm stats
    for key in info:
        if key.startswith('repl_'):
            dispatch_value(info, key, 'gauge', plugin_instance)
        if key.startswith('vm_stats_'):
            dispatch_value(info, key, 'gauge', plugin_instance)
        if key.startswith('db'):
            dispatch_value(info[key], 'keys', 'gauge', plugin_instance, '%s-keys' % key)
        if key.startswith('slave'):
            dispatch_value(info[key], 'delay', 'gauge', plugin_instance, '%s-delay' % key)

def log_verbose(msg):
    if not VERBOSE_LOGGING:
        return
    collectd.info('redis plugin [verbose]: %s' % msg)


# register callbacks
collectd.register_config(configure_callback)
collectd.register_read(read_callback)
