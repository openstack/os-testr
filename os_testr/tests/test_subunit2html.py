# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys

from ddt import data
from ddt import ddt
from subunit import RemotedTestCase
from testtools import PlaceHolder

from os_testr import subunit2html
from os_testr.tests import base


@ddt
class TestSubunit2html(base.TestCase):
    @data(RemotedTestCase, PlaceHolder)
    def test_class_parsing(self, test_cls):
        """Tests that the class paths are parsed for v1 & v2 tests"""
        test_ = test_cls("example.path.to.test.method")
        obj_ = subunit2html.HtmlOutput()
        cls_ = []
        obj_._add_cls({}, cls_, test_, ())
        self.assertEqual("example.path.to.test", cls_[0].name)

    @data(RemotedTestCase, PlaceHolder)
    def test_result_sorting(self, test_cls):
        tests = []
        for i in range(9):
            tests.append(test_cls('example.path.to.test%d.method' % i))
        # addFailure, addError, and addSkip need the real exc_info
        try:
            raise Exception('fake')
        except Exception:
            err = sys.exc_info()
        obj = subunit2html.HtmlOutput()
        obj.addSuccess(tests[3])
        obj.addSuccess(tests[1])
        # example.path.to.test2 has a failure
        obj.addFailure(tests[2], err)
        obj.addSkip(tests[0], err)
        obj.addSuccess(tests[8])
        # example.path.to.test5 has a failure (error)
        obj.addError(tests[5], err)
        # example.path.to.test4 has a failure
        obj.addFailure(tests[4], err)
        obj.addSuccess(tests[7])
        # example.path.to.test6 has a success, a failure, and a success
        obj.addSuccess(tests[6])
        obj.addFailure(tests[6], err)
        obj.addSuccess(tests[6])
        sorted_result = obj._sortResult(obj.result)
        # _sortResult returns a list of results of format:
        #   [(class, [test_result_tuple, ...]), ...]
        # sorted by str(class)
        #
        # Classes with failures (2, 4, 5, and 6) should be sorted separately
        # at the top. The rest of the classes should be in sorted order after.
        expected_class_order = ['example.path.to.test2',
                                'example.path.to.test4',
                                'example.path.to.test5',
                                'example.path.to.test6',
                                'example.path.to.test0',
                                'example.path.to.test1',
                                'example.path.to.test3',
                                'example.path.to.test7',
                                'example.path.to.test8']
        for i, r in enumerate(sorted_result):
            self.assertEqual(expected_class_order[i], str(r[0]))

    @data(RemotedTestCase, PlaceHolder)
    def test_generate_report_with_no_ascii_characters(self, test_cls):
        # The test examines a case where an error containing no ascii
        # characters is received.
        test = test_cls(u'example.path.to.test1.method')
        try:
            raise Exception('\xe2\x82\xa5')
        except Exception:
            err = sys.exc_info()
        obj = subunit2html.HtmlOutput()
        # Add failure that contains no ascii characters
        obj.addFailure(test, err)
        obj._generate_report()
