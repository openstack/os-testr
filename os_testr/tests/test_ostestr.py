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

import mock

from os_testr import ostestr as os_testr
from os_testr.tests import base


class TestGetParser(base.TestCase):
    def test_pretty(self):
        namespace = os_testr.get_parser(['--pretty'])
        self.assertEqual(True, namespace[0].pretty)
        namespace = os_testr.get_parser(['--no-pretty'])
        self.assertEqual(False, namespace[0].pretty)
        self.assertRaises(SystemExit, os_testr.get_parser,
                          ['--no-pretty', '--pretty'])

    def test_slowest(self):
        namespace = os_testr.get_parser(['--slowest'])
        self.assertEqual(True, namespace[0].slowest)
        namespace = os_testr.get_parser(['--no-slowest'])
        self.assertEqual(False, namespace[0].slowest)
        self.assertRaises(SystemExit, os_testr.get_parser,
                          ['--no-slowest', '--slowest'])

    def test_parallel(self):
        namespace = os_testr.get_parser(['--parallel'])
        self.assertEqual(True, namespace[0].parallel)
        namespace = os_testr.get_parser(['--serial'])
        self.assertEqual(False, namespace[0].parallel)
        self.assertRaises(SystemExit, os_testr.get_parser,
                          ['--parallel', '--serial'])


class TestCallers(base.TestCase):
    def test_no_discover(self):
        namespace = os_testr.get_parser(['-n', 'project.tests.foo'])

        def _fake_exit(arg):
            self.assertTrue(arg)

        def _fake_run(*args, **kwargs):
            return 'project.tests.foo' in args

        with mock.patch.object(os_testr, 'exit', side_effect=_fake_exit), \
                mock.patch.object(os_testr, 'get_parser', return_value=namespace), \
                mock.patch.object(os_testr,
                                  'call_subunit_run',
                                  side_effect=_fake_run):
            os_testr.main()

    def test_no_discover_path(self):
        namespace = os_testr.get_parser(['-n', 'project/tests/foo'])

        def _fake_exit(arg):
            self.assertTrue(arg)

        def _fake_run(*args, **kwargs):
            return 'project.tests.foo' in args

        with mock.patch.object(os_testr, 'exit', side_effect=_fake_exit), \
                mock.patch.object(os_testr, 'get_parser', return_value=namespace), \
                mock.patch.object(os_testr,
                                  'call_subunit_run',
                                  side_effect=_fake_run):
            os_testr.main()

    def test_pdb(self):
        namespace = os_testr.get_parser(['--pdb', 'project.tests.foo'])

        def _fake_exit(arg):
            self.assertTrue(arg)

        def _fake_run(*args, **kwargs):
            return 'project.tests.foo' in args

        with mock.patch.object(os_testr, 'exit', side_effect=_fake_exit), \
                mock.patch.object(os_testr, 'get_parser', return_value=namespace), \
                mock.patch.object(os_testr,
                                  'call_subunit_run',
                                  side_effect=_fake_run):
            os_testr.main()

    def test_pdb_path(self):
        namespace = os_testr.get_parser(['--pdb', 'project/tests/foo'])

        def _fake_exit(arg):
            self.assertTrue(arg)

        def _fake_run(*args, **kwargs):
            return 'project.tests.foo' in args

        with mock.patch.object(os_testr, 'exit', side_effect=_fake_exit), \
                mock.patch.object(os_testr, 'get_parser', return_value=namespace), \
                mock.patch.object(os_testr,
                                  'call_subunit_run',
                                  side_effect=_fake_run):
            os_testr.main()
