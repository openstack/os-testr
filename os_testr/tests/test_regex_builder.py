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

import io
from unittest import mock

from os_testr import regex_builder as os_testr
from os_testr.tests import base


class TestPathToRegex(base.TestCase):

    def test_file_name(self):
        result = os_testr.path_to_regex("tests/network/v2/test_net.py")
        self.assertEqual("tests.network.v2.test_net", result)
        result = os_testr.path_to_regex("openstack/tests/network/v2")
        self.assertEqual("openstack.tests.network.v2", result)


class TestConstructRegex(base.TestCase):
    def test_regex_passthrough(self):
        result = os_testr.construct_regex(None, None, 'fake_regex', False)
        self.assertEqual(result, '^.*(fake_regex).*$')

    def test_blacklist_regex_with_comments(self):
        with io.StringIO() as blacklist_file:
            for i in range(4):
                blacklist_file.write(u'fake_regex_%s # A Comment\n' % i)
            blacklist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=blacklist_file):
                result = os_testr.construct_regex(
                    'fake_path', None, None, False)
            self.assertEqual(result, "^(?!fake_regex_3|fake_regex_2|"
                                     "fake_regex_1|fake_regex_0).*().*$")

    def test_whitelist_regex_with_comments(self):
        with io.StringIO() as whitelist_file:
            for i in range(4):
                whitelist_file.write(u'fake_regex_%s # A Comment\n' % i)
            whitelist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=whitelist_file):
                result = os_testr.construct_regex(
                    None, 'fake_path', None, False)
            self.assertEqual(
                result,
                "^.*(fake_regex_0|fake_regex_1|fake_regex_2|fake_regex_3).*$")

    def test_blacklist_regex_without_comments(self):
        with io.StringIO() as blacklist_file:
            for i in range(4):
                blacklist_file.write(u'fake_regex_%s\n' % i)
            blacklist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=blacklist_file):
                result = os_testr.construct_regex(
                    'fake_path', None, None, False)
            self.assertEqual(result, "^(?!fake_regex_3|fake_regex_2|"
                                     "fake_regex_1|fake_regex_0).*().*$")

    def test_blacklist_regex_with_comments_and_regex(self):
        with io.StringIO() as blacklist_file:
            for i in range(4):
                blacklist_file.write(u'fake_regex_%s # Comments\n' % i)
            blacklist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=blacklist_file):
                result = os_testr.construct_regex('fake_path', None,
                                                  'fake_regex', False)

                expected_regex = (
                    "^(?!fake_regex_3|fake_regex_2|fake_regex_1|"
                    "fake_regex_0).*(fake_regex).*$")
                self.assertEqual(result, expected_regex)

    def test_blacklist_regex_without_comments_and_regex(self):
        with io.StringIO() as blacklist_file:
            for i in range(4):
                blacklist_file.write(u'fake_regex_%s\n' % i)
            blacklist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=blacklist_file):
                result = os_testr.construct_regex('fake_path', None,
                                                  'fake_regex', False)

                expected_regex = (
                    "^(?!fake_regex_3|fake_regex_2|fake_regex_1|"
                    "fake_regex_0).*(fake_regex).*$")
                self.assertEqual(result, expected_regex)

    @mock.patch.object(os_testr, 'print_skips')
    def test_blacklist_regex_with_comment_print_skips(self, print_mock):
        with io.StringIO() as blacklist_file:
            for i in range(4):
                blacklist_file.write(u'fake_regex_%s # Comment\n' % i)
            blacklist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=blacklist_file):
                result = os_testr.construct_regex('fake_path', None,
                                                  None, True)

            expected_regex = ("^(?!fake_regex_3|fake_regex_2|fake_regex_1|"
                              "fake_regex_0).*().*$")
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
        with io.StringIO() as blacklist_file:
            for i in range(4):
                blacklist_file.write(u'fake_regex_%s\n' % i)
            blacklist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=blacklist_file):
                result = os_testr.construct_regex('fake_path', None,
                                                  None, True)

            expected_regex = ("^(?!fake_regex_3|fake_regex_2|"
                              "fake_regex_1|fake_regex_0).*().*$")
        self.assertEqual(result, expected_regex)
        calls = print_mock.mock_calls
        self.assertEqual(len(calls), 4)
        args = list(map(lambda x: x[1], calls))
        self.assertIn(('fake_regex_0', ''), args)
        self.assertIn(('fake_regex_1', ''), args)
        self.assertIn(('fake_regex_2', ''), args)
        self.assertIn(('fake_regex_3', ''), args)

    def test_whitelist_regex_without_comments_and_regex_passthrough(self):
        file_contents = u"""regex_a
regex_b"""
        with io.StringIO() as whitelist_file:
            whitelist_file.write(file_contents)
            whitelist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=whitelist_file):
                result = os_testr.construct_regex(None, 'fake_path',
                                                  None, False)

                expected_regex = '^.*(regex_a|regex_b).*$'
                self.assertEqual(result, expected_regex)

    def test_whitelist_regex_without_comments_with_regex_passthrough(self):
        file_contents = u"""regex_a
regex_b"""
        with io.StringIO() as whitelist_file:
            whitelist_file.write(file_contents)
            whitelist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=whitelist_file):
                result = os_testr.construct_regex(None, 'fake_path',
                                                  'fake_regex', False)

                expected_regex = '^.*(fake_regex|regex_a|regex_b).*$'
                self.assertEqual(result, expected_regex)

    def test_blacklist_whitelist_and_regex_passthrough_at_once(self):
        with io.StringIO() as blacklist_file, io.StringIO() as whitelist_file:
            for i in range(4):
                blacklist_file.write(u'fake_regex_%s\n' % i)
            blacklist_file.seek(0)
            whitelist_file.write(u'regex_a\n')
            whitelist_file.write(u'regex_b\n')
            whitelist_file.seek(0)

            with mock.patch('six.moves.builtins.open',
                            side_effect=[blacklist_file, whitelist_file]):
                result = os_testr.construct_regex('fake_path_1', 'fake_path_2',
                                                  'fake_regex', False)

                expected_regex = (
                    "^(?!fake_regex_3|fake_regex_2|fake_regex_1|"
                    "fake_regex_0).*(fake_regex|regex_a|regex_b).*$")
                self.assertEqual(result, expected_regex)


class TestGetRegexFromListFile(base.TestCase):
    def test_get_regex_from_whitelist_file(self):
        file_contents = u"""regex_a
regex_b"""
        with io.StringIO() as whitelist_file:
            whitelist_file.write(file_contents)
            whitelist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=whitelist_file):
                regex = os_testr.get_regex_from_whitelist_file(
                    '/path/to/not_used')
            self.assertEqual('regex_a|regex_b', regex)

    def test_get_regex_from_blacklist_file(self):
        with io.StringIO() as blacklist_file:
            for i in range(4):
                blacklist_file.write(u'fake_regex_%s\n' % i)
            blacklist_file.seek(0)
            with mock.patch('six.moves.builtins.open',
                            return_value=blacklist_file):
                regex = os_testr.get_regex_from_blacklist_file(
                    '/path/to/not_used')
            self.assertEqual('(?!fake_regex_3|fake_regex_2'
                             '|fake_regex_1|fake_regex_0)', regex)


class TestGetTestList(base.TestCase):
    def test__get_test_list(self):
        test_list = os_testr._get_test_list('test__get_test_list')
        self.assertIn('test__get_test_list', test_list[0])

    def test__get_test_list_regex_is_empty(self):
        test_list = os_testr._get_test_list('')
        self.assertIn('', test_list[0])

    def test__get_test_list_regex_is_none(self):
        test_list = os_testr._get_test_list(None)
        # NOTE(masayukig): We should get all of the tests. So we should have
        # more than one test case.
        self.assertGreater(len(test_list), 1)
        self.assertIn('os_testr.tests.test_regex_builder.'
                      'TestGetTestList.test__get_test_list_regex_is_none',
                      test_list)
