# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from heat.engine import resource
from heat.engine import signal_responder

from heat.openstack.common import log as logging
from heat.openstack.common.gettextutils import _

logger = logging.getLogger(__name__)


class GenericResource(resource.Resource):
    '''
    Dummy resource for use in tests
    '''
    properties_schema = {}
    attributes_schema = {'foo': 'A generic attribute',
                         'Foo': 'Another generic attribute'}

    def handle_create(self):
        logger.warning(_('Creating generic resource (Type "%s")') %
                       self.type())

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        logger.warning(_('Updating generic resource (Type "%s")') %
                       self.type())

    def handle_delete(self):
        logger.warning(_('Deleting generic resource (Type "%s")') %
                       self.type())

    def _resolve_attribute(self, name):
        return self.name

    def handle_suspend(self):
        logger.warning(_('Suspending generic resource (Type "%s")') %
                       self.type())

    def handle_resume(self):
        logger.warning(_('Resuming generic resource (Type "%s")') %
                       self.type())


class ResourceWithProps(GenericResource):
    properties_schema = {'Foo': {'Type': 'String'}}


class ResourceWithComplexAttributes(GenericResource):
    attributes_schema = {'list': 'A list',
                         'flat_dict': 'A flat dictionary',
                         'nested_dict': 'A nested dictionary',
                         'simple_object': 'An object',
                         'complex_object': 'A really complex object',
                         'none': 'A None'
                         }

    list = ['foo', 'bar']
    flat_dict = {'key1': 'val1', 'key2': 'val2', 'key3': 'val3'}
    nested_dict = {'list': [1, 2, 3],
                   'string': 'abc',
                   'dict': {'a': 1, 'b': 2, 'c': 3}}

    class AnObject(object):
        def __init__(self, first, second, third):
            self.first = first
            self.second = second
            self.third = third

    simple_object = AnObject('a', 'b', 'c')
    complex_object = AnObject('a', flat_dict, simple_object)

    def _resolve_attribute(self, name):
        if name == 'list':
            return self.list
        if name == 'flat_dict':
            return self.flat_dict
        if name == 'nested_dict':
            return self.nested_dict
        if name == 'simple_object':
            return self.simple_object
        if name == 'complex_object':
            return self.complex_object
        if name == 'none':
            return None


class ResourceWithRequiredProps(GenericResource):
    properties_schema = {'Foo': {'Type': 'String',
                                 'Required': True}}


class SignalResource(signal_responder.SignalResponder):
    properties_schema = {}
    attributes_schema = {'AlarmUrl': 'Get a signed webhook'}

    def handle_create(self):
        super(SignalResource, self).handle_create()
        self.resource_id_set(self._get_user_id())

    def handle_signal(self, details=None):
        logger.warning(_('Signaled resource (Type "%(type)s") %(details)s')
                       % {'type': self.type(), 'details': details})

    def _resolve_attribute(self, name):
        if name == 'AlarmUrl' and self.resource_id is not None:
            return unicode(self._get_signed_url())
