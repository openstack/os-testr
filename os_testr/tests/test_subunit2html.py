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
