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

import re
import simplejson

from google.appengine.api import users, memcache

from gaelord import models

"""
Local copy of the entities from the datastore in a dictionary.
{'jid' : [(RecordFilter, Key),  (RecordFilter, Key)], }
"""
_subscriptions = {}

"""Init flag for the datastore entities."""
_init = False

def subscriptions(new=None):
    """Local copy wrapper"""
    global _init
    if not _init:
        update_subscriptions()

    global _subscriptions
    if new:
        _subscriptions = new
        return

    return _subscriptions


class RecordFilter:
    """Object representation of a filter.

    The pattern string are regular expressions and a compiled version
    of the patterns is stored in memory.
    """
    def __init__(self,
                 fileName=None,
                 funcName=None,
                 levelName=None,
                 lineNo=None,
                 message=None):

        self.patterns = {}
        self.patterns['fileName'] = fileName or '^$'
        self.patterns['funcName'] = funcName or '^$'
        self.patterns['levelName'] = levelName or '(INFO|DEBUG)'
        self.patterns['lineNo'] = lineNo or '^$'
        self.patterns['message'] = message or '^$'
        self.compiled = False
        self.compiled_patterns = {}
        self.compile_patterns()

    def compile_patterns(self, force=False):
        """Compile patterns into compiled regexps"""

        if self.compiled and not force:
            return

        for k, v in self.patterns.iteritems():
            self.compiled_patterns[k] = re.compile(v)
        
        self.compiled = True


def update_subscriptions(jid=None):
    """Update local subscriptions dictionary from datastore.

    jid -- if supplied, only the subscription associated with the jid
    will be updated
    """
    global _subscriptions
    subscriptions_query = models.Subscription.all()
    updated_subscriptions = {}
    
    if jid:
        subscriptions_query.filter('user = ', users.User(jid))
        # copy existing data for other jids
        updated_subscriptions = _subscriptions

    for subscription in subscriptions_query:
        updated_subscriptions[subscription.user.email()] = []

        for f in subscription.filter_set:
            updated_subscriptions[subscription.user.email()].append(
                (RecordFilter(**f.recordFilter), f.key()))

    _subscriptions = updated_subscriptions
    global _init
    if not _init:
        _init = True

    _recompile_filters()


def _recompile_filters():
    """Update the compiled patterns in all filters"""
    [[f.compile_patterns(force=True) for f, k in filter_set]
     for filter_set in subscriptions().values()]


def subscribe(jid):
    """Subscribe a jid: add to the datastore, then update local copy.

    Raises AlreadySubscribedError
    """
    if is_subscriber(jid):
        raise AlreadySubscribedError(jid)
    
    models.Subscription(user=users.User(jid)).put()
    update_subscriptions(jid)


def is_subscriber(jid):
    """True, if the jid is in the local copy, false otherwise"""
    return subscriptions().has_key(jid)


def add_filter(jid, fileName=None, funcName=None, levelName=None,
               lineNo=None, message=None):
    """Add a filter to the datastore

    Appends to the list of filters of the subscription associated with
    jid, then updates the local copy only for that jid

    Raises NotSubscribedError
    """

    subscription = models.Subscription.all().filter(
        'user = ', users.User(jid)).fetch(1)

    if subscription == []:
        raise NotSubscribedError(jid)
    
    subscription = subscription[0]
    
    models.Filter(subscription=subscription,
                  recordFilter=RecordFilter(fileName,
                                            funcName,
                                            levelName,
                                            lineNo,
                                            message).patterns).put()

    update_subscriptions()


def remove_filter(key):
    """Removes a key from the datastore.

    Raises NonexistentFilterError
    """

    filter_ = models.Filter.get(key)

    if filter_:
        filter_.delete()
    else:
        raise NonexistentFilterError(key)

    update_subscriptions()
    

def get_recipients(record):
    """Get a list of jids for the record to be sent to"""
    return filter(
        lambda jid: not _run_filters(subscriptions()[jid], record),
        subscriptions().keys())


def _run_filters(filters, record):
    """Run filters on record"""
    for f, k in filters:
        if _filter_record(f, record):
            return True

    return False


def _filter_record(record_filter, record):
    """Match patterns from a filter against fileds in a record"""
    return (record_filter.compiled_patterns['fileName']
            .search(record.filename)
            and record_filter.compiled_patterns['funcName']
            .search(record.funcName)
            and record_filter.compiled_patterns['levelName']
            .search(record.levelname)
            and record_filter.compiled_patterns['lineNo']
            .search('%d' % record.lineno)
            and record_filter.compiled_patterns['message']
            .search(record.message))


class Error(Exception):
    """Base class for exceptions in this module"""
    def __init__(self, msg):
        self.msg = msg

class SubscriptionError(Error):
    """Base class for subscription-related exceptions"""
    def __init__(self, jid, msg):
        self.jid = jid
        super().__init__(msg)

class NotSubscribedError(SubscriptionError):
    def __init__(self, jid):
        super().__init__(jid, 'This user is not subscribed')

class AlreadySubscribedError(SubscriptionError):
    def __init__(self, jid):
        super().__init__(jid, 'This user is already subscribed')

class NonexistentFilterError(Error):
    def __init__(self, key):
        self.key = key
        super().__init__('This filter does not exist')
