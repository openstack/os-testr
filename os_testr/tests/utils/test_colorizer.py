# Copyright 2016 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
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

import six
import sys

from ddt import data
from ddt import ddt
from ddt import unpack

from os_testr.tests import base
from os_testr.utils import colorizer


@ddt
class TestNullColorizer(base.TestCase):

    @data(None, "foo", sys.stdout, )
    def test_supported_always_true(self, stream):
        self.assertTrue(colorizer.NullColorizer.supported(stream))

    @data(("foo", "red"), ("foo", "bar"))
    @unpack
    def test_write_string_ignore_color(self, text, color):
        output = six.StringIO()
        c = colorizer.NullColorizer(output)
        c.write(text, color)
        self.assertEqual(text, output.getvalue())

    @data((None, "red"), (None, None))
    @unpack
    def test_write_none_exception(self, text, color):
        c = colorizer.NullColorizer(sys.stdout)
        self.assertRaises(TypeError, c.write, text, color)


@ddt
class TestAnsiColorizer(base.TestCase):

    def test_supported_false(self):
        # NOTE(masayukig): This returns False because our unittest env isn't
        #  interactive
        self.assertFalse(colorizer.AnsiColorizer.supported(sys.stdout))

    @data(None, "foo")
    def test_supported_error(self, stream):
        self.assertRaises(AttributeError,
                          colorizer.AnsiColorizer.supported, stream)

    @data(("foo", "red", "31"), ("foo", "blue", "34"))
    @unpack
    def test_write_string_valid_color(self, text, color, color_code):
        output = six.StringIO()
        c = colorizer.AnsiColorizer(output)
        c.write(text, color)
        self.assertIn(text, output.getvalue())
        self.assertIn(color_code, output.getvalue())

    @data(("foo", None), ("foo", "invalid_color"))
    @unpack
    def test_write_string_invalid_color(self, text, color):
        output = six.StringIO()
        c = colorizer.AnsiColorizer(output)
        self.assertRaises(KeyError, c.write, text, color)
