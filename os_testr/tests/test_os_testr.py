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
import six

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
        namespace = os_testr.get_parser(['--pretty'])
        self.assertEqual(True, namespace.pretty)
        namespace = os_testr.get_parser(['--no-pretty'])
        self.assertEqual(False, namespace.pretty)
        self.assertRaises(SystemExit, os_testr.get_parser,
                          ['--no-pretty', '--pretty'])

    def test_slowest(self):
        namespace = os_testr.get_parser(['--slowest'])
        self.assertEqual(True, namespace.slowest)
        namespace = os_testr.get_parser(['--no-slowest'])
        self.assertEqual(False, namespace.slowest)
        self.assertRaises(SystemExit, os_testr.get_parser,
                          ['--no-slowest', '--slowest'])

    def test_parallel(self):
        namespace = os_testr.get_parser(['--parallel'])
        self.assertEqual(True, namespace.parallel)
        namespace = os_testr.get_parser(['--serial'])
        self.assertEqual(False, namespace.parallel)
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


class TestConstructRegex(base.TestCase):
    def test_regex_passthrough(self):
        result = os_testr.construct_regex(None, None, 'fake_regex', False)
        self.assertEqual(result, 'fake_regex')

    def test_blacklist_regex_with_comments(self):
        blacklist_file = six.StringIO()
        for i in range(4):
            blacklist_file.write('fake_regex_%s # A Comment\n' % i)
        blacklist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=blacklist_file):
            result = os_testr.construct_regex('fake_path', None, None, False)
        self.assertEqual(
            result,
            "(?!.*fake_regex_3|fake_regex_2|fake_regex_1|fake_regex_0|)")

    def test_blacklist_regex_without_comments(self):
        blacklist_file = six.StringIO()
        for i in range(4):
            blacklist_file.write('fake_regex_%s\n' % i)
        blacklist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=blacklist_file):
            result = os_testr.construct_regex('fake_path', None, None, False)
        self.assertEqual(
            result,
            "(?!.*fake_regex_3|fake_regex_2|fake_regex_1|fake_regex_0|)")

    def test_blacklist_regex_with_comments_and_regex(self):
        blacklist_file = six.StringIO()
        for i in range(4):
            blacklist_file.write('fake_regex_%s # Comments\n' % i)
        blacklist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=blacklist_file):
            result = os_testr.construct_regex('fake_path', None,
                                              'fake_regex', False)

            expected_regex = ("(?!.*fake_regex_3|fake_regex_2|fake_regex_1|"
                              "fake_regex_0|)fake_regex")
            self.assertEqual(result, expected_regex)

    def test_blacklist_regex_without_comments_and_regex(self):
        blacklist_file = six.StringIO()
        for i in range(4):
            blacklist_file.write('fake_regex_%s\n' % i)
        blacklist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=blacklist_file):
            result = os_testr.construct_regex('fake_path', None,
                                              'fake_regex', False)

            expected_regex = ("(?!.*fake_regex_3|fake_regex_2|fake_regex_1|"
                              "fake_regex_0|)fake_regex")
            self.assertEqual(result, expected_regex)

    @mock.patch.object(os_testr, 'print_skips')
    def test_blacklist_regex_with_comment_print_skips(self, print_mock):
        blacklist_file = six.StringIO()
        for i in range(4):
            blacklist_file.write('fake_regex_%s # Comment\n' % i)
        blacklist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=blacklist_file):
            result = os_testr.construct_regex('fake_path', None,
                                              None, True)

        expected_regex = ("(?!.*fake_regex_3|fake_regex_2|fake_regex_1|"
                          "fake_regex_0|)")
        self.assertEqual(result, expected_regex)
        calls = print_mock.mock_calls
        self.assertEqual(len(calls), 4)
        args = list(map(lambda x: x[1], calls))
        self.assertIn(('fake_regex_0', 'Comment'), args)
        self.assertIn(('fake_regex_1', 'Comment'), args)
        self.assertIn(('fake_regex_2', 'Comment'), args)
        self.assertIn(('fake_regex_3', 'Comment'), args)

    @mock.patch.object(os_testr, 'print_skips')
    def test_blacklist_regex_without_comment_print_skips(self, print_mock):
        blacklist_file = six.StringIO()
        for i in range(4):
            blacklist_file.write('fake_regex_%s\n' % i)
        blacklist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=blacklist_file):
            result = os_testr.construct_regex('fake_path', None,
                                              None, True)

        expected_regex = ("(?!.*fake_regex_3|fake_regex_2|fake_regex_1|"
                          "fake_regex_0|)")
        self.assertEqual(result, expected_regex)
        calls = print_mock.mock_calls
        self.assertEqual(len(calls), 4)
        args = list(map(lambda x: x[1], calls))
        self.assertIn(('fake_regex_0', ''), args)
        self.assertIn(('fake_regex_1', ''), args)
        self.assertIn(('fake_regex_2', ''), args)
        self.assertIn(('fake_regex_3', ''), args)


class TestWhitelistFile(base.TestCase):
    def test_read_whitelist_file(self):
        file_contents = """regex_a
regex_b"""
        whitelist_file = six.StringIO()
        whitelist_file.write(file_contents)
        whitelist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=whitelist_file):
            regex = os_testr.get_regex_from_whitelist_file('/path/to/not_used')
        self.assertEqual('regex_a|regex_b', regex)

    def test_whitelist_regex_without_comments_and_regex(self):
        file_contents = """regex_a
regex_b"""
        whitelist_file = six.StringIO()
        whitelist_file.write(file_contents)
        whitelist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=whitelist_file):
            result = os_testr.construct_regex(None, 'fake_path',
                                              None, False)

            expected_regex = 'regex_a|regex_b'
            self.assertEqual(result, expected_regex)
