# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_os_testr
----------------------------------

Tests for `os_testr` module.
"""

from os_testr import os_testr
from os_testr.tests import base


class TestPathToRegex(base.TestCase):

    def test_file_name(self):
        result = os_testr.path_to_regex("tests/network/v2/test_net.py")
        self.assertEqual("tests.network.v2.test_net", result)
        result = os_testr.path_to_regex("openstack/tests/network/v2")
        self.assertEqual("openstack.tests.network.v2", result)


class TestGetParser(base.TestCase):
    def test_pretty(self):
        namespace = os_testr.get_parser().parse_args(['--pretty'])
        self.assertEqual(True, namespace.pretty)
        namespace = os_testr.get_parser().parse_args(['--no-pretty'])
        self.assertEqual(False, namespace.pretty)
        self.assertRaises(SystemExit, os_testr.get_parser().parse_args,
                          ['--no-pretty', '--pretty'])

    def test_slowest(self):
        namespace = os_testr.get_parser().parse_args(['--slowest'])
        self.assertEqual(True, namespace.slowest)
        namespace = os_testr.get_parser().parse_args(['--no-slowest'])
        self.assertEqual(False, namespace.slowest)
        self.assertRaises(SystemExit, os_testr.get_parser().parse_args,
                          ['--no-slowest', '--slowest'])

    def test_parallel(self):
        namespace = os_testr.get_parser().parse_args(['--parallel'])
        self.assertEqual(True, namespace.parallel)
        namespace = os_testr.get_parser().parse_args(['--serial'])
        self.assertEqual(False, namespace.parallel)
        self.assertRaises(SystemExit, os_testr.get_parser().parse_args,
                          ['--parallel', '--serial'])
