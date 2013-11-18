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
  "AWSTemplateFormatVersion": "2010-09-09",
  "Description": "Template to test Network Gateway resource",
  "Parameters": {},
  "Resources": {
    "NetworkGateway": {
      "Type": "OS::Neutron::NetworkGateway",
      "Properties": {
        "name": "NetworkGateway",
        "tenant_id": "96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f",
        "devices": [{"id": "e52148ca-7db9-4ec3-abe6-2c7c0ff316eb",
        "interface_name": "breth1"}]
      }
    }
  }
}
'''

gwc_template = '''
{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Description": "Template to test Network Gateway Connection resource",
  "Parameters": {},
  "Resources": {
    "NetworkGatewayConnection": {
      "Type": "OS::Neutron::NetworkGatewayConnection",
      "Properties": {
        "network_id": "6af055d3-26f6-48dd-a597-7611d7e58d35",
        "network_gateway_id": "ed4c03b9-8251-4c09-acc4-e59ee9e6aa37",
        "segmentation_type": "vlan",
        "segmentation_id": 10,
      }
    }
  }
}
'''


@skipIf(neutronclient is None, 'neutronclient unavailable')
class NeutronNetworkGatewayTest(HeatTestCase):
    @skipIf(neutronV20 is None, "Missing Neutron v2_0")
    def setUp(self):
        super(NeutronNetworkGatewayTest, self).setUp()
        self.m.StubOutWithMock(neutronclient.Client, 'create_network_gateway')
        self.m.StubOutWithMock(neutronclient.Client, 'show_network_gateway')
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
            "network_gateway": {
                "name": u"NetworkGateway",
                "tenant_id": u"96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f",
                "devices": [{"id": u"e52148ca-7db9-4ec3-abe6-2c7c0ff316eb",
                             "interface_name": u"breth1"}]
            }
        }
        ).AndReturn({
            "network_gateway": {
                "name": "NetworkGateway",
                "default": False,
                "tenant_id": "96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f",
                "devices": [{
                    "interface_name": "breth1",
                    "id": "e52148ca-7db9-4ec3-abe6-2c7c0ff316eb"}
                ],
                "id": "a1349845-80ff-49bf-82bf-6be454d41560"
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
            u"ed4c03b9-8251-4c09-acc4-e59ee9e6aa37", {
                "network_id": "6af055d3-26f6-48dd-a597-7611d7e58d35",
                "segmentation_id": 10,
                "segmentation_type": u"vlan"
            }
        ).AndReturn({
            "connection_info": {
                "network_gateway_id": "ed4c03b9-8251-4c09-acc4-e59ee9e6aa37",
                "network_id": "6af055d3-26f6-48dd-a597-7611d7e58d35",
                "port_id": "b22828ff-2abc-453e-9162-e4179240199b"
            }
        })
        t = template_format.parse(gwc_template)
        stack = utils.parse_stack(t)
        rsrc = network_gateway.NetworkGatewayConnection(
            'test_network_gateway_connection',
            t['Resources']['NetworkGatewayConnection'], stack)
        return rsrc

    def test_network_gateway(self):
        sng = {
            "network_gateway":
            {
                "name": "NetworkGateway",
                "default": False,
                "tenant_id": "96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f",
                "devices":
                [{
                    "interface_name": "breth1",
                    "id": "e52148ca-7db9-4ec3-abe6-2c7c0ff316eb"
                }],
                "id": "a1349845-80ff-49bf-82bf-6be454d41560"
            }
        }

        neutronclient.Client.show_network_gateway(
            'a1349845-80ff-49bf-82bf-6be454d41560'
        ).AndReturn(sng)

        neutronclient.Client.disconnect_network_gateway(
            u"ed4c03b9-8251-4c09-acc4-e59ee9e6aa37", {
                "network_id": u"6af055d3-26f6-48dd-a597-7611d7e58d35",
                "segmentation_id": 10,
                "segmentation_type": u"vlan"
            }
        ).AndReturn(None)

        neutronclient.Client.disconnect_network_gateway(
            u"ed4c03b9-8251-4c09-acc4-e59ee9e6aa37", {
                "network_id": u"6af055d3-26f6-48dd-a597-7611d7e58d35",
                "segmentation_id": 10,
                "segmentation_type": u"vlan"
            }
        ).AndRaise(qe.NeutronClientException(status_code=404))

        neutronclient.Client.delete_network_gateway(
            'a1349845-80ff-49bf-82bf-6be454d41560'
        ).AndReturn(None)

        neutronclient.Client.show_network_gateway(
            'a1349845-80ff-49bf-82bf-6be454d41560'
        ).AndRaise(qe.NeutronClientException(status_code=404))

        neutronclient.Client.delete_network_gateway(
            'a1349845-80ff-49bf-82bf-6be454d41560'
        ).AndRaise(qe.NeutronClientException(status_code=404))

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
        self.assertEqual(u'a1349845-80ff-49bf-82bf-6be454d41560', ref_id)
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
        rsrc_con.state_set(rsrc_con.CREATE, rsrc_con.COMPLETE,
                           'to delete again')
        scheduler.TaskRunner(rsrc_con.delete)()

        self.assertEqual(scheduler.TaskRunner(rsrc.delete)(), None)
        rsrc.state_set(rsrc.CREATE, rsrc.COMPLETE, 'to delete again')
        scheduler.TaskRunner(rsrc.delete)()
        self.m.VerifyAll()

    def test_network_gatway_create_failed(self):
        clients.OpenStackClients.keystone().AndReturn(
            fakes.FakeKeystoneClient())
        neutronclient.Client.create_network_gateway({
            "network_gateway": {
                "name": u"NetworkGateway",
                "tenant_id": u"96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f",
                "devices": [{"id": u"e52148ca-7db9-4ec3-abe6-2c7c0ff316eb",
                            "interface_name": u"breth1"}]
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
            u"ed4c03b9-8251-4c09-acc4-e59ee9e6aa37", {
                "network_id": "6af055d3-26f6-48dd-a597-7611d7e58d35",
                "segmentation_id": 10,
                "segmentation_type": u"vlan"}
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
            'a1349845-80ff-49bf-82bf-6be454d41560'
        ).AndRaise(network_gateway.NeutronClientException)

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
            u"ed4c03b9-8251-4c09-acc4-e59ee9e6aa37", {
                "network_id": u"6af055d3-26f6-48dd-a597-7611d7e58d35",
                "segmentation_id": 10,
                "segmentation_type": u"vlan"}
        ).AndRaise(network_gateway.NeutronClientException)

        rsrc = self.prepare_create_gateway_connection()
        self.m.ReplayAll()

        scheduler.TaskRunner(rsrc.create)()
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
          "AWSTemplateFormatVersion": "2010-09-09",
          "Description": "Template to test Gateway Connection resource",
          "Parameters": {},
          "Resources": {
            "NetworkGatewayConnection": {
              "Type": "OS::Neutron::NetworkGatewayConnection",
              "Properties": {
                "network_id": "6af055d3-26f6-48dd-a597-7611d7e58d35",
                "network_gateway_id": "ed4c03b9-8251-4c09-acc4-e59ee9e6aa37",
                "segmentation_type": "vlan"
              }
            }
          }
        }
        '''
        t = template_format.parse(gwc_template_err)
        stack = utils.parse_stack(t)
        rsrc = network_gateway.NetworkGatewayConnection(
            'test_network_gateway_connection',
            t['Resources']['NetworkGatewayConnection'], stack)
        self.m.ReplayAll()
        error = self.assertRaises(exception.StackValidationFailed,
                                  scheduler.TaskRunner(rsrc.validate))
        self.assertEqual(
            'segmentation_id must be specified for using vlan',
            str(error))
        self.m.VerifyAll()

    def test_network_gateway_attribute(self):
        sng = {
            "network_gateway": {
                "name": "NetworkGateway",
                "default": False,
                "tenant_id": "96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f",
                "devices":
                [{
                    "interface_name": "breth1",
                    "id": "e52148ca-7db9-4ec3-abe6-2c7c0ff316eb"
                }],
                "id": "a1349845-80ff-49bf-82bf-6be454d41560"
            }
        }
        neutronclient.Client.show_network_gateway(
            'a1349845-80ff-49bf-82bf-6be454d41560'
        ).MultipleTimes().AndReturn(sng)
        rsrc = self.prepare_create_network_gateway()
        self.m.ReplayAll()

        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual('NetworkGateway', rsrc.FnGetAtt('name'))
        self.assertEqual('96ba52dc-c5c5-44c6-9a9d-d3ba1a03f77f',
                         rsrc.FnGetAtt('tenant_id'))
        self.assertEqual([{"id": u"e52148ca-7db9-4ec3-abe6-2c7c0ff316eb",
                         "interface_name": u"breth1"}],
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
        self.assertEqual('b22828ff-2abc-453e-9162-e4179240199b',
                         rsrc.FnGetAtt('port_id'))

        error = self.assertRaises(exception.InvalidTemplateAttribute,
                                  rsrc.FnGetAtt, 'hoge')
        self.assertEqual(
            'The Referenced Attribute (test_network_gateway_connection hoge) '
            'is incorrect.', str(error))

        self.m.VerifyAll()
