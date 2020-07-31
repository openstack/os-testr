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

import re
from unittest import mock

import six

from os_testr import testlist_builder as list_builder
from os_testr.tests import base


class TestBlackReader(base.TestCase):
    def test_black_reader(self):
        blacklist_file = six.StringIO()
        for i in range(4):
            blacklist_file.write('fake_regex_%s\n' % i)
            blacklist_file.write('fake_regex_with_note_%s # note\n' % i)
        blacklist_file.seek(0)
        with mock.patch('six.moves.builtins.open',
                        return_value=blacklist_file):
            result = list_builder.black_reader('fake_path')
        self.assertEqual(2 * 4, len(result))
        note_cnt = 0
        # not assuming ordering, mainly just testing the type
        for r in result:
            self.assertEqual(r[2], [])
            if r[1] == 'note':
                note_cnt += 1
            self.assertIn('search', dir(r[0]))  # like a compiled regex
        self.assertEqual(note_cnt, 4)


class TestConstructList(base.TestCase):
    def test_simple_re(self):
        test_lists = ['fake_test(scen)[tag,bar])', 'fake_test(scen)[egg,foo])']
        with mock.patch('os_testr.regex_builder._get_test_list',
                        return_value=test_lists):
            result = list_builder.construct_list(None,
                                                 None,
                                                 'foo',
                                                 None,
                                                 False)
        self.assertEqual(list(result), ['fake_test(scen)[egg,foo])'])

    def test_simple_black_re(self):
        test_lists = ['fake_test(scen)[tag,bar])', 'fake_test(scen)[egg,foo])']
        with mock.patch('os_testr.regex_builder._get_test_list',
                        return_value=test_lists):
            result = list_builder.construct_list(None,
                                                 None,
                                                 None,
                                                 'foo',
                                                 False)
        self.assertEqual(list(result), ['fake_test(scen)[tag,bar])'])

    def test_blacklist(self):
        black_list = [(re.compile('foo'), 'foo not liked', [])]
        test_lists = ['fake_test(scen)[tag,bar])', 'fake_test(scen)[egg,foo])']
        with mock.patch('os_testr.regex_builder._get_test_list',
                        return_value=test_lists):
            with mock.patch('os_testr.testlist_builder.black_reader',
                            return_value=black_list):
                result = list_builder.construct_list('file',
                                                     None,
                                                     'fake_test',
                                                     None,
                                                     False)
        self.assertEqual(list(result), ['fake_test(scen)[tag,bar])'])

    def test_whitelist(self):
        white_list = 'fake_test1|fake_test2'
        test_lists = ['fake_test1[tg]', 'fake_test2[tg]', 'fake_test3[tg]']
        white_getter = 'os_testr.regex_builder.get_regex_from_whitelist_file'
        with mock.patch('os_testr.regex_builder._get_test_list',
                        return_value=test_lists):
            with mock.patch(white_getter,
                            return_value=white_list):
                result = list_builder.construct_list(None,
                                                     'file',
                                                     None,
                                                     None,
                                                     False)
        self.assertEqual(set(result),
                         set(('fake_test1[tg]', 'fake_test2[tg]')))

    def test_whitelist_blacklist_re(self):
        white_list = 'fake_test1|fake_test2'
        test_lists = ['fake_test1[tg]', 'fake_test2[spam]',
                      'fake_test3[tg,foo]', 'fake_test4[spam]']
        black_list = [(re.compile('spam'), 'spam not liked', [])]
        white_getter = 'os_testr.regex_builder.get_regex_from_whitelist_file'
        with mock.patch('os_testr.regex_builder._get_test_list',
                        return_value=test_lists):
            with mock.patch(white_getter,
                            return_value=white_list):
                with mock.patch('os_testr.testlist_builder.black_reader',
                                return_value=black_list):
                    result = list_builder.construct_list('black_file',
                                                         'white_file',
                                                         'foo',
                                                         None,
                                                         False)
        self.assertEqual(set(result),
                         set(('fake_test1[tg]', 'fake_test3[tg,foo]')))

    def test_overlapping_black_regex(self):

        black_list = [(re.compile('compute.test_keypairs.KeypairsTestV210'),
                       '', []),
                      (re.compile('compute.test_keypairs.KeypairsTestV21'),
                       '', [])]
        test_lists = [
            'compute.test_keypairs.KeypairsTestV210.test_create_keypair',
            'compute.test_keypairs.KeypairsTestV21.test_create_keypair',
            'compute.test_fake.FakeTest.test_fake_test']
        with mock.patch('os_testr.regex_builder._get_test_list',
                        return_value=test_lists):
            with mock.patch('os_testr.testlist_builder.black_reader',
                            return_value=black_list):
                result = list_builder.construct_list('file',
                                                     None,
                                                     'fake_test',
                                                     None,
                                                     False)
        self.assertEqual(
            list(result), ['compute.test_fake.FakeTest.test_fake_test'])
