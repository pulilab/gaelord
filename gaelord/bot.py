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

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import xmpp_handlers
from google.appengine.api import xmpp
from google.appengine.api import app_identity

from gaelord import filters
from gaelord.format import render_to_string

FROM_JID = '%s@appspot.com' % app_identity.get_application_id()

_input_values = {}
_input_fields = ['fileName',
                 'funcName',
                 'levelName',
                 'lineNo',
                 'message']
_input_index = 0
_is_input = False

def _sender_jid(message):
    """Get sender jid from message, without /app"""
    return message.sender.split('/')[0]

class XmppHandler(xmpp_handlers.CommandHandler):
    def filters_command(self, message=None):
        """Command handler for /filters
        
        Shows a list of the sender's filters.
        """
        jid = _sender_jid(message)

        template_values = {
            'jid' : jid,
            'filters' : filters.subscriptions()[jid]
            }

        message.reply(render_to_string('filters.plain',
                                       template_values))

    def delete_command(self, message=None):
        """Command handler for /delete i

        i -- the index from the filters' list

        Deletes the filter given by the index.
        """
        jid = message.sender.split('/')[0]

        try:
            i = int(message.arg)
            key = filters.subscriptions()[jid][i-1][1]
        except ValueError, IndexError:
            message.reply('Invalid index: %s' % message.arg or 'None')
        else:
            filters.remove_filter(key)
            message.reply('Deleted')

    def add_command(self, message=None):
        """Command handler for /add

        Starts the interactive filter creation.
        """
        global _is_input
        _is_input = True
        self.text_message(message)

    def _add_input_handler(self, message=None):
        """Interactive filter creation. The function populates a
        dictionary with the user's replies which is used to construct
        the RecordFilter object.
        """
        global _input_index, _is_input

        fields = len(_input_fields)

        if _input_index <= fields:
            # first question, no previous answer
            if _input_index > 0:
                # store answer for previous question
                _input_values[_input_fields[_input_index - 1]] = message.body

        if _input_index < fields:
            # show next message
            template_values = {'i': _input_index}
            message.reply(render_to_string('filter_add.plain',
                                           template_values))
            _input_index += 1

        elif _input_index == fields:
            # end of questions
            jid = _sender_jid(message)
            filters.add_filter(jid, **_input_values)
            _is_input = False
            _input_index = 0
            message.reply('Filter added')
            
 
    def text_message(self, message=None):
        """Basic handler for text replies"""
        
        # if input mode is active, use input handler
        if _is_input:
            self._add_input_handler(message)

    def unhandled_command(self, message=None):
        """Fallback handler"""
        message.reply(render_to_string('bot_usage.plain',
                                       {}))


def send(record, jid):
    """Send a log record to the given jid"""
    if xmpp.get_presence(jid, FROM_JID):
        template_values = {
            'message': record.message,
            'filename': record.filename,
            'funcname': record.funcName,
            'levelname': record.levelname,
            'lineno' : record.lineno
            }

        xmpp.send_message(jid,
                          render_to_string('bot_log_record.plain',
                                           template_values),
                          FROM_JID)


application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/',
                                       XmppHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
