#!/usr/bin/python
#
#  Copyright (c) 2016, The OpenThread Authors.
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#  3. Neither the name of the copyright holder nor the
#     names of its contributors may be used to endorse or promote products
#     derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#

import time
import unittest

import node

CHANNEL_INIT = 19
PANID_INIT = 0xface

NETWORK_NAME_FINAL = 'threadCert'
PANID_FINAL = 0xabcd

COMMISSIONER = 1
LEADER = 2
ROUTER1 = 3
ROUTER2 = 4

class Cert_9_2_16_ActivePendingPartition(unittest.TestCase):
    def setUp(self):
        self.nodes = {}
        for i in range(1,5):
            self.nodes[i] = node.Node(i)

        self.nodes[COMMISSIONER].set_active_dataset(1, channel=CHANNEL_INIT, panid=PANID_INIT)
        self.nodes[COMMISSIONER].set_mode('rsdn')
        self.nodes[COMMISSIONER].add_whitelist(self.nodes[LEADER].get_addr64())
        self.nodes[COMMISSIONER].enable_whitelist()
        self.nodes[COMMISSIONER].set_router_selection_jitter(1)

        self.nodes[LEADER].set_active_dataset(1, channel=CHANNEL_INIT, panid=PANID_INIT)
        self.nodes[LEADER].set_mode('rsdn')
        self.nodes[LEADER].set_partition_id(0xffffffff)
        self.nodes[LEADER].add_whitelist(self.nodes[COMMISSIONER].get_addr64())
        self.nodes[LEADER].add_whitelist(self.nodes[ROUTER1].get_addr64())
        self.nodes[LEADER].enable_whitelist()
        self.nodes[LEADER].set_router_selection_jitter(1)

        self.nodes[ROUTER1].set_active_dataset(1, channel=CHANNEL_INIT, panid=PANID_INIT)
        self.nodes[ROUTER1].set_mode('rsdn')
        self.nodes[ROUTER1].add_whitelist(self.nodes[LEADER].get_addr64())
        self.nodes[ROUTER1].add_whitelist(self.nodes[ROUTER2].get_addr64())
        self.nodes[ROUTER1].enable_whitelist()
        self.nodes[ROUTER1].set_router_selection_jitter(1)

        self.nodes[ROUTER2].set_active_dataset(1, channel=CHANNEL_INIT, panid=PANID_INIT)
        self.nodes[ROUTER2].set_mode('rsdn')
        self.nodes[ROUTER2].add_whitelist(self.nodes[ROUTER1].get_addr64())
        self.nodes[ROUTER2].enable_whitelist()
        self.nodes[ROUTER2].set_router_selection_jitter(1)

    def tearDown(self):
        for node in list(self.nodes.values()):
            node.stop()
        del self.nodes

    def test(self):
        self.nodes[LEADER].start()
        self.nodes[LEADER].set_state('leader')
        self.assertEqual(self.nodes[LEADER].get_state(), 'leader')

        self.nodes[COMMISSIONER].start()
        time.sleep(5)
        self.assertEqual(self.nodes[COMMISSIONER].get_state(), 'router')

        self.nodes[ROUTER1].start()
        time.sleep(5)
        self.assertEqual(self.nodes[ROUTER1].get_state(), 'router')

        self.nodes[COMMISSIONER].send_mgmt_pending_set(pending_timestamp=10,
                                                       active_timestamp=10,
                                                       delay_timer=600000,
                                                       mesh_local='fd00:0db9::')
        time.sleep(5)

        self.nodes[ROUTER2].start()
        time.sleep(5)
        self.assertEqual(self.nodes[ROUTER2].get_state(), 'router')

        self.nodes[ROUTER2].stop()

        self.nodes[COMMISSIONER].send_mgmt_pending_set(pending_timestamp=20,
                                                       active_timestamp=20,
                                                       delay_timer=200000,
                                                       mesh_local='fd00:0db7::',
                                                       panid=PANID_FINAL)
        time.sleep(5)

        self.nodes[COMMISSIONER].send_mgmt_active_set(active_timestamp=15,
                                                      network_name='threadCert')
        time.sleep(100)

        self.nodes[ROUTER2].start()
        time.sleep(5)
        self.assertEqual(self.nodes[ROUTER2].get_state(), 'router')

        self.assertEqual(self.nodes[COMMISSIONER].get_network_name(), NETWORK_NAME_FINAL)
        self.assertEqual(self.nodes[LEADER].get_network_name(), NETWORK_NAME_FINAL)
        self.assertEqual(self.nodes[ROUTER1].get_network_name(), NETWORK_NAME_FINAL)
        self.assertEqual(self.nodes[ROUTER2].get_network_name(), NETWORK_NAME_FINAL)

        time.sleep(100)

        self.assertEqual(self.nodes[COMMISSIONER].get_panid(), PANID_FINAL)
        self.assertEqual(self.nodes[LEADER].get_panid(), PANID_FINAL)
        self.assertEqual(self.nodes[ROUTER1].get_panid(), PANID_FINAL)
        self.assertEqual(self.nodes[ROUTER2].get_panid(), PANID_FINAL)

        ipaddrs = self.nodes[ROUTER2].get_addrs()
        for ipaddr in ipaddrs:
            if ipaddr[0:4] != 'fe80':
                break
        self.assertTrue(self.nodes[LEADER].ping(ipaddr))

if __name__ == '__main__':
    unittest.main()
