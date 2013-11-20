#f2e-5ba10d3482d6 vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the 'License'); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from testtools import skipIf

from heat.common import exception
from heat.common import template_format
from heat.engine import clients
from heat.engine import resource
from heat.engine import scheduler
from heat.engine.resources.neutron import network_gateway
from heat.openstack.common.importutils import try_import
from heat.tests import fakes
from heat.tests import utils
from heat.tests.common import HeatTestCase
from mox import IsA

neutronclient = try_import('neutronclient.v2_0.client')
neutronV20 = try_import('neutronclient.neutron.v2_0')

qe = try_import('neutronclient.common.exceptions')

gw_template = '''
{
  'AWSTemplateFormatVersion': '2010-09-09',
  'Description': 'Template to test Network Gateway resource',
  'Parameters': {},
  'Resources': {
    'NetworkGateway': {
      'Type': 'OS::Neutron::NetworkGateway',
      'Properties': {
        'name': 'NetworkGateway',
        'tenant_id': '96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
        'devices': [{'id': 'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb',
        'interface_name': 'breth1'}]
      }
    }
  }
}
'''

gwc_template = '''
{
  'AWSTemplateFormatVersion': '2010-09-09',
  'Description': 'Template to test Network Gateway Connection resource',
  'Parameters': {},
  'Resources': {
    'NetworkGatewayConnection': {
      'Type': 'OS::Neutron::NetworkGatewayConnection',
      'Properties': {
        'network_id': '6af055d3-26f6-48dd-a597-7611d7e58d35',
        'network_gateway_id': 'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
        'segmentation_type': 'vlan',
        'segmentation_id': 10,
      }
    }
  }
}
'''

lng = {
    'network_gateways': [{
        'name': 'NetworkGateway',
        'default': False,
        'tenant_id': '96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
        'devices': [{
            'interface_name': 'breth1',
            'id': 'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb'}],
        'id': 'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
        'ports': [{
            'segmentation_type': 'vlan',
            'port_id': '32acc49c-899e-44ea-8177-6f4157e12eb4',
            'segmentation_id': 10}]
    }]
}


@skipIf(neutronclient is None, 'neutronclient unavailable')
class NeutronNetworkGatewayTest(HeatTestCase):
    @skipIf(neutronV20 is None, 'Missing Neutron v2_0')
    def setUp(self):
        super(NeutronNetworkGatewayTest, self).setUp()
        self.m.StubOutWithMock(neutronclient.Client, 'create_network_gateway')
        self.m.StubOutWithMock(neutronclient.Client, 'list_network_gateways')
        self.m.StubOutWithMock(neutronclient.Client, 'delete_network_gateway')
        self.m.StubOutWithMock(neutronclient.Client, 'connect_network_gateway')
        self.m.StubOutWithMock(neutronclient.Client,
                               'disconnect_network_gateway')
        self.m.StubOutWithMock(neutronclient.Client, 'list_networks')
        self.m.StubOutWithMock(neutronV20, 'find_resourceid_by_name_or_id')
        self.m.StubOutWithMock(clients.OpenStackClients, 'keystone')
        utils.setup_dummy_db()

    def prepare_create_network_gateway(self):
        clients.OpenStackClients.keystone().AndReturn(
            fakes.FakeKeystoneClient())
        neutronclient.Client.create_network_gateway({
            'network_gateway': {
                'name': u'NetworkGateway',
                'tenant_id': u'96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
                'devices': [{'id': u'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb',
                             'interface_name': u'breth1'}]
            }
        }
        ).AndReturn({
            'network_gateway': {
                'name': 'NetworkGateway',
                'default': False,
                'tenant_id': '96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
                'devices': [{
                    'interface_name': 'breth1',
                    'id': 'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb'}
                ],
                'id': 'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
            }
        }
        )

        t = template_format.parse(gw_template)
        stack = utils.parse_stack(t)
        rsrc = network_gateway.NetworkGateway(
            'test_network_gateway',
            t['Resources']['NetworkGateway'], stack)
        return rsrc

    def prepare_create_gateway_connection(self):
        clients.OpenStackClients.keystone().AndReturn(
            fakes.FakeKeystoneClient())
        neutronV20.find_resourceid_by_name_or_id(
            IsA(neutronclient.Client()),
            u'network',
            u'6af055d3-26f6-48dd-a597-7611d7e58d35'
        ).AndReturn('6af055d3-26f6-48dd-a597-7611d7e58d35')
        neutronclient.Client.connect_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', {
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'segmentation_id': 10,
                'segmentation_type': u'vlan'
            }
        ).AndReturn({
            'connection_info': {
                'network_gateway_id': u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'port_id': u'32acc49c-899e-44ea-8177-6f4157e12eb4'
            }
        })
        t = template_format.parse(gwc_template)
        stack = utils.parse_stack(t)
        rsrc = network_gateway.NetworkGatewayConnection(
            'test_network_gateway_connection',
            t['Resources']['NetworkGatewayConnection'], stack)
        return rsrc

    def test_network_gateway(self):
        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn(lng)

        neutronclient.Client.disconnect_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', {
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'segmentation_id': 10,
                'segmentation_type': u'vlan'
            }
        ).AndReturn(None)

        neutronclient.Client.disconnect_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', {
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'segmentation_id': 10,
                'segmentation_type': u'vlan'
            }
        ).AndReturn(qe.NeutronClientException(status_code=404))

        neutronclient.Client.delete_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn(None)

        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn(lng)

        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn({'network_gateways': []})

        neutronclient.Client.delete_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndRaise(qe.NeutronClientException(status_code=404))

        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn({'network_gateways': []})

        rsrc = self.prepare_create_network_gateway()
        rsrc_con = self.prepare_create_gateway_connection()
        self.m.ReplayAll()

        rsrc.validate()
        scheduler.TaskRunner(rsrc.create)()
        rsrc_con.validate()
        scheduler.TaskRunner(rsrc_con.create)()

        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.assertEqual((rsrc_con.CREATE, rsrc_con.COMPLETE), rsrc_con.state)

        ref_id = rsrc.FnGetRefId()
        self.assertEqual(u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', ref_id)
        self.assertEqual('NetworkGateway', rsrc.FnGetAtt('name'))

        self.assertRaises(
            exception.InvalidTemplateAttribute, rsrc.FnGetAtt, 'Foo')
        self.assertRaises(
            exception.InvalidTemplateAttribute, rsrc_con.FnGetAtt, 'Foo')

        self.assertRaises(resource.UpdateReplace,
                          rsrc.handle_update, {}, {}, {})
        self.assertRaises(resource.UpdateReplace,
                          rsrc_con.handle_update, {}, {}, {})

        self.assertEqual(scheduler.TaskRunner(rsrc_con.delete)(), None)
        self.assertEqual((rsrc_con.DELETE, rsrc_con.COMPLETE), rsrc_con.state)
        rsrc_con.state_set(rsrc_con.CREATE, rsrc_con.COMPLETE,
                           'to delete again')
        scheduler.TaskRunner(rsrc_con.delete)()
        self.assertEqual((rsrc_con.DELETE, rsrc_con.COMPLETE), rsrc_con.state)

        self.assertEqual(scheduler.TaskRunner(rsrc.delete)(), None)
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        rsrc.state_set(rsrc.CREATE, rsrc.COMPLETE, 'to delete again')
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_network_gateway_with_flat(self):
        rsrc = self.prepare_create_network_gateway()
        clients.OpenStackClients.keystone().AndReturn(
            fakes.FakeKeystoneClient())
        neutronV20.find_resourceid_by_name_or_id(
            IsA(neutronclient.Client()),
            u'network',
            u'6af055d3-26f6-48dd-a597-7611d7e58d35'
        ).AndReturn('6af055d3-26f6-48dd-a597-7611d7e58d35')
        neutronclient.Client.connect_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', {
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'segmentation_type': u'flat'
            }
        ).AndReturn({
            'connection_info': {
                'network_gateway_id': u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'port_id': u'32acc49c-899e-44ea-8177-6f4157e12eb4'
            }
        })
        lng_flat = {
            'network_gateways': [{
                'name': 'NetworkGateway',
                'default': False,
                'tenant_id': '96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
                'devices': [{
                    'interface_name': 'breth1',
                    'id': 'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb'}],
                'id': 'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                'ports': [{
                    'segmentation_type': 'flat',
                    'port_id': '32acc49c-899e-44ea-8177-6f4157e12eb4'}]
            }]
        }

        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn(lng_flat)

        neutronclient.Client.disconnect_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', {
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'segmentation_type': u'flat'
            }
        ).AndReturn(None)

        gwc_template_flat = '''
        {
          'AWSTemplateFormatVersion': '2010-09-09',
          'Description':
            'Template to test Network Gateway Connection resource',
          'Parameters': {},
          'Resources': {
            'NetworkGatewayConnection': {
              'Type': 'OS::Neutron::NetworkGatewayConnection',
              'Properties': {
                'network_id': '6af055d3-26f6-48dd-a597-7611d7e58d35',
                'network_gateway_id': 'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                'segmentation_type': 'flat'
              }
            }
          }
        }
        '''

        neutronclient.Client.delete_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn(None)

        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn({'network_gateways': []})

        t = template_format.parse(gwc_template_flat)
        stack = utils.parse_stack(t)
        rsrc_con = network_gateway.NetworkGatewayConnection(
            'test_network_gateway_connection',
            t['Resources']['NetworkGatewayConnection'], stack)

        self.m.ReplayAll()

        rsrc.validate()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        rsrc_con.validate()
        scheduler.TaskRunner(rsrc_con.create)()
        self.assertEqual((rsrc_con.CREATE, rsrc_con.COMPLETE), rsrc_con.state)

        scheduler.TaskRunner(rsrc_con.delete)()
        self.assertEqual((rsrc_con.DELETE, rsrc_con.COMPLETE), rsrc_con.state)
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)

        self.m.VerifyAll()

    def test_network_gatway_create_failed(self):
        clients.OpenStackClients.keystone().AndReturn(
            fakes.FakeKeystoneClient())
        neutronclient.Client.create_network_gateway({
            'network_gateway': {
                'name': u'NetworkGateway',
                'tenant_id': u'96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
                'devices': [{'id': u'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb',
                            'interface_name': u'breth1'}]
            }
        }
        ).AndRaise(network_gateway.NeutronClientException)
        self.m.ReplayAll()

        t = template_format.parse(gw_template)
        stack = utils.parse_stack(t)
        rsrc = network_gateway.NetworkGateway(
            'network_gateway', t['Resources']['NetworkGateway'], stack)
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_gateway_connection_create_failed(self):
        clients.OpenStackClients.keystone().AndReturn(
            fakes.FakeKeystoneClient())
        neutronV20.find_resourceid_by_name_or_id(
            IsA(neutronclient.Client()),
            u'network',
            u'6af055d3-26f6-48dd-a597-7611d7e58d35'
        ).AndReturn('6af055d3-26f6-48dd-a597-7611d7e58d35')
        neutronclient.Client.connect_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', {
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'segmentation_id': 10,
                'segmentation_type': u'vlan'}
        ).AndRaise(network_gateway.NeutronClientException)

        t = template_format.parse(gwc_template)
        stack = utils.parse_stack(t)
        rsrc = network_gateway.NetworkGatewayConnection(
            'test_network_gateway_connection',
            t['Resources']['NetworkGatewayConnection'], stack)
        self.m.ReplayAll()

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_gateway_delete_failed(self):
        neutronclient.Client.delete_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndRaise(qe.NeutronClientException(status_code=404))

        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn(lng)

        rsrc = self.prepare_create_network_gateway()
        self.m.ReplayAll()

        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_gateway_disconnect_failed(self):
        neutronclient.Client.disconnect_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', {
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'segmentation_id': 10,
                'segmentation_type': u'vlan'}
        ).AndRaise(qe.NeutronClientException())

        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn({
            u'network_gateways': [{
                'name': u'NetworkGateway',
                'default': False,
                'tenant_id': u'96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
                'devices': [{
                    'interface_name': u'breth1',
                    'id': u'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb'}],
                'id': u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                'ports': [
                    {
                        'segmentation_type': u'vlan',
                        'port_id': u'61334f85-0646-4c2a-af2e-5ba10d3482d6',
                        'segmentation_id': 50
                    }
                ]
            }]
        })

        neutronclient.Client.disconnect_network_gateway(
            u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37', {
                'network_id': u'6af055d3-26f6-48dd-a597-7611d7e58d35',
                'segmentation_id': 10,
                'segmentation_type': u'vlan'
            }
        ).AndRaise(qe.NeutronClientException())

        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).AndReturn({
            u'network_gateways': [{
                'name': u'NetworkGateway',
                'default': False,
                'tenant_id': u'96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
                'devices': [{
                    'interface_name': u'breth1',
                    'id': u'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb'}],
                'id': u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                'ports': [
                    {
                        'segmentation_type': u'vlan',
                        'port_id': u'61334f85-0646-4c2a-af2e-5ba10d3482d6',
                        'segmentation_id': 50
                    },
                    {
                        'segmentation_type': u'vlan',
                        'port_id': u'32acc49c-899e-44ea-8177-6f4157e12eb4',
                        'segmentation_id': 10
                    }
                ]
            }]
        })

        rsrc = self.prepare_create_gateway_connection()
        self.m.ReplayAll()

        scheduler.TaskRunner(rsrc.create)()

        self.assertEqual(scheduler.TaskRunner(rsrc.delete)(), None)
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)

        rsrc.state_set(rsrc.CREATE, rsrc.COMPLETE, 'to delete again')

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_gateway_validate_failed(self):
        gwc_template_err = '''
        {
          'AWSTemplateFormatVersion': '2010-09-09',
          'Description': 'Template to test Gateway Connection resource',
          'Parameters': {},
          'Resources': {
            'NetworkGatewayConnection': {
              'Type': 'OS::Neutron::NetworkGatewayConnection',
              'Properties': {
                'network_id': '6af055d3-26f6-48dd-a597-7611d7e58d35',
                'network_gateway_id': 'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                'segmentation_type': 'vlan'
              }
            }
          }
        }
        '''
        gwc_template_err2 = '''
        {
          'AWSTemplateFormatVersion': '2010-09-09',
          'Description': 'Template to test Gateway Connection resource',
          'Parameters': {},
          'Resources': {
            'NetworkGatewayConnection': {
              'Type': 'OS::Neutron::NetworkGatewayConnection',
              'Properties': {
                'network_id': '6af055d3-26f6-48dd-a597-7611d7e58d35',
                'network_gateway_id': 'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                'segmentation_type': 'flat',
                'segmentation_id': 50
              }
            }
          }
        }
        '''

        t1 = template_format.parse(gwc_template_err)
        stack1 = utils.parse_stack(t1)
        rsrc1 = network_gateway.NetworkGatewayConnection(
            'test_network_gateway_connection',
            t1['Resources']['NetworkGatewayConnection'], stack1)

        t2 = template_format.parse(gwc_template_err2)
        stack2 = utils.parse_stack(t2)
        rsrc2 = network_gateway.NetworkGatewayConnection(
            'test_network_gateway_connection',
            t2['Resources']['NetworkGatewayConnection'], stack2)
        self.m.ReplayAll()
        error = self.assertRaises(exception.StackValidationFailed,
                                  scheduler.TaskRunner(rsrc1.validate))
        self.assertEqual(
            'segmentation_id must be specified for using vlan',
            str(error))

        error = self.assertRaises(exception.StackValidationFailed,
                                  scheduler.TaskRunner(rsrc2.validate))
        self.assertEqual(
            'segmentation_id must not be specified for using flat',
            str(error))
        self.m.VerifyAll()

    def test_network_gateway_attribute(self):
        neutronclient.Client.list_network_gateways(
            id=u'ed4c03b9-8251-4c09-acc4-e59ee9e6aa37'
        ).MultipleTimes().AndReturn(lng)
        rsrc = self.prepare_create_network_gateway()
        self.m.ReplayAll()

        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual('NetworkGateway', rsrc.FnGetAtt('name'))
        self.assertEqual(u'96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
                         rsrc.FnGetAtt('tenant_id'))
        self.assertEqual([{'id': u'e52148ca-7db9-4ec3-abe6-2c7c0ff316eb',
                         'interface_name': u'breth1'}],
                         rsrc.FnGetAtt('devices'))
        self.assertEqual(False, rsrc.FnGetAtt('default'))

        error = self.assertRaises(exception.InvalidTemplateAttribute,
                                  rsrc.FnGetAtt, 'hoge')
        self.assertEqual(
            'The Referenced Attribute (test_network_gateway hoge) is '
            'incorrect.', str(error))

        self.m.VerifyAll()

    def test_gateway_connection_attribute(self):
        rsrc = self.prepare_create_gateway_connection()
        self.m.ReplayAll()

        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual('ed4c03b9-8251-4c09-acc4-e59ee9e6aa37',
                         rsrc.FnGetAtt('network_gateway_id'))
        self.assertEqual('6af055d3-26f6-48dd-a597-7611d7e58d35',
                         rsrc.FnGetAtt('network_id'))
        self.assertEqual('32acc49c-899e-44ea-8177-6f4157e12eb4',
                         rsrc.FnGetAtt('port_id'))

        error = self.assertRaises(exception.InvalidTemplateAttribute,
                                  rsrc.FnGetAtt, 'hoge')
        self.assertEqual(
            'The Referenced Attribute (test_network_gateway_connection hoge) '
            'is incorrect.', str(error))

        self.m.VerifyAll()
