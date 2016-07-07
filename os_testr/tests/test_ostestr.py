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
import io
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

    def test_call_subunit_run_pretty(self):
        '''Test call_subunit_run

        Test ostestr call_subunit_run function when:
        Pretty is True
        '''
        pretty = True
        subunit = False

        with mock.patch('subprocess.Popen', autospec=True) as mock_popen:
            mock_popen.return_value.returncode = 0
            mock_popen.return_value.stdout = io.BytesIO()

            os_testr.call_subunit_run('project.tests.foo', pretty, subunit)

            # Validate Popen was called three times
            self.assertTrue(mock_popen.called, 'Popen was never called')
            count = mock_popen.call_count
            self.assertEqual(3, count, 'Popen was called %s'
                             ' instead of 3 times' % count)

            # Validate Popen called the right functions
            called = mock_popen.call_args_list
            msg = "Function %s not called"
            function = ['python', '-m', 'subunit.run', 'project.tests.foo']
            self.assertIn(function, called[0][0], msg % 'subunit.run')
            function = ['testr', 'load', '--subunit']
            self.assertIn(function, called[1][0], msg % 'testr load')
            function = ['subunit-trace', '--no-failure-debug', '-f']
            self.assertIn(function, called[2][0], msg % 'subunit-trace')

    def test_call_subunit_run_sub(self):
        '''Test call_subunit run

        Test ostestr call_subunit_run function when:
        Pretty is False and Subunit is True
        '''
        pretty = False
        subunit = True

        with mock.patch('subprocess.Popen', autospec=True) as mock_popen:
            os_testr.call_subunit_run('project.tests.foo', pretty, subunit)

            # Validate Popen was called once
            self.assertTrue(mock_popen.called, 'Popen was never called')
            count = mock_popen.call_count
            self.assertEqual(1, count, 'Popen was called more than once')

            # Validate Popen called the right function
            called = mock_popen.call_args
            function = ['testr', 'load', '--subunit']
            self.assertIn(function, called[0], "testr load not called")

    def test_call_subunit_run_testtools(self):
        '''Test call_subunit_run

        Test ostestr call_subunit_run function when:
        Pretty is False and Subunit is False
        '''
        pretty = False
        subunit = False

        with mock.patch('testtools.run.main', autospec=True) as mock_run:
            os_testr.call_subunit_run('project.tests.foo', pretty, subunit)

            # Validate testtool.run was called once
            self.assertTrue(mock_run.called, 'testtools.run was never called')
            count = mock_run.call_count
            self.assertEqual(1, count, 'testtools.run called more than once')
