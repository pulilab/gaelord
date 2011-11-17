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

from google.appengine.ext import db
import pickle

class ObjectProperty(db.BlobProperty):
        def validate(self, value):
		try:
			pickle.dumps(value)
			return value
		except pickle.PicklingError:
			return super(ObjectProperty, self).validate(value)

        def get_value_for_datastore(self, model_instance):
		result = super(ObjectProperty, self).get_value_for_datastore(model_instance)
		result = pickle.dumps(result)
		return db.Blob(result)

	def make_value_from_datastore(self, value):
		try:
			value = pickle.loads(str(value))
		except:
			pass
		return super(ObjectProperty, self).make_value_from_datastore(value)

class Subscription(db.Model):
        user = db.UserProperty(required=True)

class Filter(db.Model):
        subscription = db.ReferenceProperty(Subscription, collection_name='filter_set', required=True)
        recordFilter = ObjectProperty(required=True)
