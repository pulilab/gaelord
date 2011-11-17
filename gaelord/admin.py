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

import os
import simplejson

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from gaelord import filters, models, channel
from gaelord.format import render_to_string
from gaelord.conf import URL_PREFIX

class Landing(webapp.RequestHandler):
    """Admin console landing page"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        user = users.get_current_user()

        template_values = {
            'email': user.email(),
            'subscriber': filters.is_subscriber(user.email()),
            'logout_url': users.create_logout_url(URL_PREFIX),
            'login_url': users.create_login_url(URL_PREFIX),
            'url_prefix': URL_PREFIX,
            }
        
        self.response.out.write(render_to_string('landing.html',
                                                 template_values))

class Wall(webapp.RequestHandler):
    """List of log records with real-time update"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        user = users.get_current_user()

        template_values = {
            'subscriber': filters.is_subscriber(user.email()),
            'token' : channel.register_channel(user.user_id()),
            'url_prefix': URL_PREFIX,
            }

        self.response.out.write(render_to_string('wall.html',
                                                 template_values))

class AddFilter(webapp.RequestHandler):
    def get(self):
        """'Add filter' form"""
        template_values = {
            'filename': self.request.get('filename') or '^$',
            'funcname': self.request.get('funcname') or '^$',
            'levelname': self.request.get('levelname') or 'INFO',
            'lineno': self.request.get('lineno') or '^$',
            'message': self.request.get('message') or '^$',
            'url_prefix': URL_PREFIX,
            }

        self.response.out.write(render_to_string('filter_add.html',
                                                 template_values))

    def post(self):
        """Store a newly created filter"""
        try:
            filters.add_filter(
                users.get_current_user().email(),
                fileName = self.request.get('fileName'),
                funcName = self.request.get('funcName'),
                levelName = self.request.get('levelName'),
                lineNo = self.request.get('lineNo'),
                message = self.request.get('message'))
        except filters.NotSubscribedError, e:
            resp = e.msg
        else:
            resp = 'Filter added'
            
        self.response.out.write(resp)


class DeleteFilter(webapp.RequestHandler):
    """Remove a filter pointed by a key"""
    def get(self):
        key = self.request.get('key')
        resp = ''
        if key:
            try:
                filters.remove_filter(key)
            except filters.NonexistentFilterError, e:
                resp = e.msg
        else:
            resp = 'No key specified'
            
        self.response.out.write(resp)


class Subscribe(webapp.RequestHandler):
    """Subscribe the currently logged in user"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        try:
            filters.subscribe(users.get_current_user().email())
            resp = 'Subscribed'
        except filters.AlreadySubscribedError, e:
            resp = e.msg

        self.response.out.write(resp)


class ManageFilters(webapp.RequestHandler):
    """Show a list of the user's filters"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'

        template_values = {
            'subscriptions': {},
            'url_prefix': URL_PREFIX
            }

        jid = users.get_current_user().email()
        template_values['subscriptions'][jid] = filters.subscriptions()[jid]

        self.response.out.write(render_to_string('filters.html',
                                                 template_values))



class FlushQueue(webapp.RequestHandler):
    """Send the records from the queue to the chanel identified by
    the token parameter.
    """
    def post(self):
        token = self.request.get('token')
        try:
            if token:
                channel.flush_queue(token)
        except channel.InvalidTokenError, e:
            self.response.out.write(e)
        
application = webapp.WSGIApplication([(URL_PREFIX,
                                       Landing),
                                      (URL_PREFIX + 'subscribe',
                                       Subscribe),
                                      (URL_PREFIX + 'filters',
                                       ManageFilters),
                                      (URL_PREFIX + 'filter/add',
                                       AddFilter),
                                      (URL_PREFIX + 'filter/delete',
                                       DeleteFilter),
                                      (URL_PREFIX + 'flush',
                                       FlushQueue),
                                      (URL_PREFIX + 'wall',
                                       Wall)],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
