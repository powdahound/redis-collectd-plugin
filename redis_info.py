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
# Contributors:
#   Pierre Mavro <p.mavro@criteo.com> / Deimosfr <deimos at deimos.fr>
#   https://github.com/powdahound/redis-collectd-plugin/graphs/contributors
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


def fetch_info(conf):
    """Connect to Redis server and request info"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((conf['host'], conf['port']))
        log_verbose('Connected to Redis at %s:%s' % (conf['host'], conf['port']))
    except socket.error, e:
        collectd.error('redis_info plugin: Error connecting to %s:%d - %r'
                       % (conf['host'], conf['port'], e))
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
                           % (conf['host'], conf['port'], status_line))
            return None

    log_verbose('Sending info command')
    s.sendall('info\r\n')

    status_line = fp.readline()

    if status_line.startswith('-'):
        collectd.error('redis_info plugin: Error response from %s:%d - %r'
                       % (conf['host'], conf['port'], status_line))
        s.close()
        return None

    content_length = int(status_line[1:-1])  # status_line looks like: $<content_length>
    data = fp.read(content_length)
    log_verbose('Received data: %s' % data)

    # process 'info commandstats'
    log_verbose('Sending info commandstats command')
    s.sendall('info commandstats\r\n')
    fp.readline()  # skip first line in the response because it is empty
    status_line = fp.readline()
    log_verbose('Received line: %s' % status_line)
    content_length = int(status_line[1:-1])  # status_line looks like: $<content_length>
    datac = fp.read(content_length)  # fetch commandstats to different data buffer
    log_verbose('Received data: %s' % datac)
    
    # process 'cluster info'
    log_verbose('Sending cluster info command')
    s.sendall('cluster info\r\n')
    fp.readline()  # skip first line in the response because it is empty
    status_line = fp.readline()
    log_verbose('Received line: %s' % status_line)
    content_length = int(status_line[1:-1])  # status_line looks like: $<content_length>
    datacluster = fp.read(content_length)  # fetch cluster info to different data buffer
    log_verbose('Received data: %s' % datacluster)

    s.close()

    linesep = '\r\n' if '\r\n' in data else '\n'  # assuming all is done in the same connection...
    data_dict = parse_info(data.split(linesep))
    datac_dict = parse_info(datac.split(linesep))
    datacluster_dict = parse_info(datacluster.split(linesep))

    # let us see more raw data just in case
    log_verbose('Data: %s' % len(data_dict))
    log_verbose('Datac: %s' % len(datac_dict))
    log_verbose('Datacluster: %s' % len(datacluster_dict))

    # merge three data sets into one
    data_full = data_dict.copy()
    data_full.update(datac_dict)
    data_full.update(datacluster_dict)

    log_verbose('Data Full: %s' % len(data_full))

    # this generates hundreds of lines but helps in debugging a lot
    if VERBOSE_LOGGING:
        for key in data_full:
            log_verbose('Data Full detail: %s = %s' % (key, data_full[key]))

    return data_full


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
            for sub_val in split_val:
                k, _, v = sub_val.rpartition('=')
                sub_key = "{0}_{1}".format(key, k)
                info[sub_key] = v
        else:
            info[key] = val

    # compatibility with pre-2.6 redis (used changes_since_last_save)
    info["changes_since_last_save"] = info.get("changes_since_last_save", info.get("rdb_changes_since_last_save"))

    return info


def configure_callback(conf):
    """Receive configuration block"""
    host = None
    port = None
    auth = None
    instance = None
    redis_info = {}

    for node in conf.children:
        key = node.key.lower()
        val = node.values[0]
        log_verbose('Analyzing config %s key (value: %s)' % (key, val))
        searchObj = re.search(r'redis_(.*)$', key, re.M|re.I)

        if key == 'host':
            host = val
        elif key == 'port':
            port = int(val)
        elif key == 'auth':
            auth = val
        elif key == 'verbose':
            global VERBOSE_LOGGING
            VERBOSE_LOGGING = bool(node.values[0]) or VERBOSE_LOGGING
        elif key == 'instance':
            instance = val
        elif searchObj:
            log_verbose('Matching expression found: key: %s - value: %s' % (searchObj.group(1), val))
            redis_info[searchObj.group(1), val] = True
        else:
            collectd.warning('redis_info plugin: Unknown config key: %s.' % key)
            continue

    log_verbose('Configured with host=%s, port=%s, instance name=%s, using_auth=%s, redis_info_len=%s' % (host, port, instance, auth!=None, len(redis_info)))

    CONFIGS.append({'host': host, 'port': port, 'auth': auth, 'instance': instance, 'redis_info': redis_info})


def dispatch_value(info, key, type, plugin_instance=None, type_instance=None):
    """Read a key from info response data and dispatch a value"""

    if key not in info:
        collectd.warning('redis_info plugin: Info key not found: %s, Instance: %s' % (key, plugin_instance))
        return

    if plugin_instance is None:
        plugin_instance = 'unknown redis'
        collectd.error('redis_info plugin: plugin_instance is not set, Info key: %s' % key)

    if not type_instance:
        type_instance = key

    try:
        value = int(info[key])
    except ValueError:
        value = float(info[key])
    except TypeError:
        log_verbose('No info for key: %s' % key)
        return

    log_verbose('Sending value: %s=%s' % (type_instance, value))

    val = collectd.Values(plugin='redis_info')
    val.type = type
    val.type_instance = type_instance
    val.plugin_instance = plugin_instance
    val.values = [value]
    val.dispatch()


def read_callback():
    for conf in CONFIGS:
        get_metrics(conf)


def get_metrics(conf):
    info = fetch_info(conf)

    if not info:
        collectd.error('redis plugin: No info received')
        return

    plugin_instance = conf['instance']
    if plugin_instance is None:
        plugin_instance = '{host}:{port}'.format(host=conf['host'], port=conf['port'])

    for keyTuple, val in conf['redis_info'].iteritems():
        key, val = keyTuple

        if key == 'total_connections_received' and val == 'counter':
            dispatch_value(info, 'total_connections_received', 'counter', plugin_instance, 'connections_received')
        elif key == 'total_commands_processed' and val == 'counter':
            dispatch_value(info, 'total_commands_processed', 'counter', plugin_instance, 'commands_processed')
        else:
            dispatch_value(info, key, val, plugin_instance)


def log_verbose(msg):
    if not VERBOSE_LOGGING:
        return
    collectd.info('redis plugin [verbose]: %s' % msg)


# register callbacks
collectd.register_config(configure_callback)
collectd.register_read(read_callback)
