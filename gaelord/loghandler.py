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

import logging
import logging.handlers

from gaelord import filters, bot, channel, queue

class LogDispatcherHandler(logging.Handler):
    """Loghandler class"""
    def __init__(self):
        logging.Handler.__init__(self)
        self.is_logging = False
  
    @classmethod
    def register_handler(self):
        """Register the logging handler"""

        if hasattr(logging.handlers, 'LogDispatcherHandler'):
            return

        # store the instance in the logging module's namespace
        logging.handlers.LogDispatcherHandler = self
        handler = logging.handlers.LogDispatcherHandler()

        handler.setLevel(logging.INFO)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        filters.update_subscriptions()

    def emit(self, record):
        """Dispatch log messages"""

        # prevent recursive logging
        if self.is_logging:
            return

        self.is_logging = True

        # sets record.message
        record.message = self.format(record)

        # publish record
        queue.add(record)
        channel.push(record)
        [bot.send(record, jid) for jid in
         filters.get_recipients(record)]

        self.is_logging = False
