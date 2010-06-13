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
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((REDIS_HOST, REDIS_PORT))
    fp = s.makefile('r')
    s.sendall('info\n')

    info_data = []
    while True:
        data = fp.readline()
        if data[0] == '$':
            continue
        if data == '\r\n':
            break
        data = data[:-2] # remove \r\n
        info_data.append(data)

    s.close()
    return parse_info(info_data)

def parse_info(info_lines):
    """Parse info response from Redis"""
    info = {}
    for line in info_lines:
        key, val = line.split(':')

        # handle multi-value keys (for dbs)
        if ',' in val:
            split_val = val.split(',')
            val = {}
            for sub_val in split_val:
                k, v = sub_val.split('=')
                val[k] = v

        info[key] = val
    return info

def configure_callback(conf):
    global REDIS_HOST, REDIS_PORT
    for node in conf.children:
        if node.key == 'Host':
            REDIS_HOST = node.values[0]
        elif node.key == 'Port':
            REDIS_PORT = int(node.values[0])
        else:
            collectd.warning('redis plugin: Unknown config key: %s.'
                             % node.key)

def read_callback():
    info = fetch_info()

    # commands_processed
    val = collectd.Values()
    val.plugin = 'redis'
    val.type = 'counter'
    val.type_instance = 'commands_processed'
    val.values = [int(info['total_commands_processed'])]
    val.dispatch()

    # connected_clients
    val = collectd.Values()
    val.plugin = 'redis'
    val.type = 'gauge'
    val.type_instance = 'connected_clients'
    val.values = [int(info['connected_clients'])]
    val.dispatch()

    # used_memory
    val = collectd.Values()
    val.plugin = 'redis'
    val.type = 'bytes'
    val.type_instance = 'used_memory'
    val.values = [int(info['used_memory'])]
    val.dispatch()

    # database stats
    # TODO: Do we need to support more than 1k databases?
    for i in range(0, 1000):
        key = 'db%d' % i
        # I don't think it's possible to have nonsequential database
        # numbers, so break as soon as we don't find one.
        if key not in info:
            break
        val = collectd.Values()
        val.plugin = 'redis'
        val.type = 'gauge'
        val.type_instance = '%s-keys' % key
        val.values = [int(info[key]['keys'])]
        val.dispatch()


# register callbacks
collectd.register_config(configure_callback)
collectd.register_read(read_callback)

