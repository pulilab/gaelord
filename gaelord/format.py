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
try:
    from google.appengine.dist import use_library
    use_library('django', '1.2')
except:
    pass

from django import conf

template_dir = os.path.join(os.path.dirname(__file__), 'templates')

conf.settings.configure(DEBUG=True, TEMPLATE_DEBUG=True,
                        TEMPLATE_DIRS=(template_dir,))

from django.template.loader import render_to_string as render_to_string_

render_to_string = render_to_string_
