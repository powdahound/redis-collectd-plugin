# collectd-redis-plugin - redis.py
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


# Host to connect to. Override in config by specifying 'Host'.
REDIS_HOST = 'localhost'

# Port to connect on. Override in config by specifying 'Port'.
REDIS_PORT = 6379


def fetch_info():
    """Connect to Redis server and request info"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((REDIS_HOST, REDIS_PORT))
    except socket.error, e:
        collectd.error('redis plugin: Error connecting to %s:%d - %r'
                       % (REDIS_HOST, REDIS_PORT, e))
        return None
    fp = s.makefile('r')
    s.sendall('info\n')

    info_data = []
    while True:
        data = fp.readline().strip()
        if data == '':
            break
        if data[0] == '$':
            continue
        info_data.append(data)

    s.close()
    return parse_info(info_data)

def parse_info(info_lines):
    """Parse info response from Redis"""
    info = {}
    for line in info_lines:
        if ':' not in line:
            collectd.warning('redis plugin: Bad format for info line: %s'
                             % line)
            continue

        key, val = line.split(':')

        # Handle multi-value keys (for dbs).
        # db lines look like "db0:keys=10,expire=0"
        if ',' in val:
            split_val = val.split(',')
            val = {}
            for sub_val in split_val:
                k, v = sub_val.split('=')
                val[k] = v

        info[key] = val
    return info

def configure_callback(conf):
    """Receive configuration block"""
    global REDIS_HOST, REDIS_PORT
    for node in conf.children:
        if node.key == 'Host':
            REDIS_HOST = node.values[0]
        elif node.key == 'Port':
            REDIS_PORT = int(node.values[0])
        else:
            collectd.warning('redis plugin: Unknown config key: %s.'
                             % node.key)

def dispatch_value(info, key, type, type_instance=None):
    """Read a key from info response data and dispatch a value"""
    if key not in info:
        collectd.warning('redis plugin: Info key not found: %s' % key)
        return

    if not type_instance:
        type_instance = key

    val = collectd.Values(plugin='redis')
    val.type = type
    val.type_instance = type_instance
    val.values = [int(info[key])]
    val.dispatch()

def read_callback():
    info = fetch_info()
    if not info:
        collectd.error('redis plugin: No info received')
        return

    # send high-level values
    dispatch_value(info, 'total_commands_processed', 'counter',
                   'commands_processed')
    dispatch_value(info, 'connected_clients', 'gauge')
    dispatch_value(info, 'used_memory', 'bytes')

    # database stats
    for key in info:
        if not key.startswith('db'):
            continue
        val = collectd.Values(plugin='redis')
        val.type = 'gauge'
        val.type_instance = '%s-keys' % key
        val.values = [int(info[key]['keys'])]
        val.dispatch()


# register callbacks
collectd.register_config(configure_callback)
collectd.register_read(read_callback)

