# This file is part of gaelord.
#
#  gaelord is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  gaelord is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with gaelord.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2011 Marton Somogyi <s@pulilab.com>, pulilab.com

import simplejson
import cgi

from google.appengine.api import channel, memcache

from gaelord import queue
from gaelord.format import render_to_string
from gaelord.conf import URL_PREFIX

def push(record, channel_id=None):
    """Send a log record via channel API.
    
    record -- log record to push
    channel_id

    If channel_id is supplied, the message will only be sent to the
    corresponding channel.
    """

    template_values = {
        'message': cgi.escape(record.message),
        'filename': cgi.escape(record.filename),
        'funcname': cgi.escape(record.funcName),
        'levelname': cgi.escape(record.levelname),
        'lineno': str(record.lineno),
        }

    data = {
        'html' : render_to_string('log_record_li.html',
                                  template_values)
        }

    if channel_id:
        channel.send_message(channel_id, simplejson.dumps(data))
    else:
        [channel.send_message(channel_id, simplejson.dumps(data))
         for channel_id in _get_channels()]


def _get_channel_id(token):
    """Lookup a key in the channels dictionary."""
    try:
        [key for key, value
         in _get_channels().iteritems()
         if value == token][0]
    except IndexError:
        raise InvalidTokenError(token)
        

def flush_queue(token):
    """Push all records from the queue"""
    [push(record, _get_channel_id(token)) for record
     in queue.records_queue]


def _get_channels():
    """Get channels dictionary from memcache"""
    return simplejson.loads(memcache.get('channels') or '{}')


def _set_channels(channels):
    """Set channels dictionary in memcache"""
    memcache.set('channels', simplejson.dumps(channels))


def register_channel(channel_id):
    """Create and save a new channel with token"""
    token = channel.create_channel(channel_id)
    channels = _get_channels()
    channels[channel_id] = token
    _set_channels(channels)
    return token


class Error(Exception):
    def __init__(self, msg):
        self.msg = msg

class ChannelError(Error):
    pass

class InvalidTokenError(ChannelError):
    def __init__(self, token, msg):
        self.token = token
        super().__init__('Invalid channel token')
