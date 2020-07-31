# Copyright 2015 SUSE Linux GmbH
# All Rights Reserved.
#
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

from datetime import datetime as dt
import io
import os
import subprocess
import sys
from unittest.mock import patch

from ddt import data
from ddt import ddt
from ddt import unpack
import six

from os_testr import subunit_trace
from os_testr.tests import base


@ddt
class TestSubunitTrace(base.TestCase):

    @data(([dt(2015, 4, 17, 22, 23, 14, 111111),
            dt(2015, 4, 17, 22, 23, 14, 111111)],
           "0.000000s"),
          ([dt(2015, 4, 17, 22, 23, 14, 111111),
            dt(2015, 4, 17, 22, 23, 15, 111111)],
           "1.000000s"),
          ([dt(2015, 4, 17, 22, 23, 14, 111111),
            None],
           ""))
    @unpack
    def test_get_durating(self, timestamps, expected_result):
        self.assertEqual(subunit_trace.get_duration(timestamps),
                         expected_result)

    @data(([dt(2015, 4, 17, 22, 23, 14, 111111),
            dt(2015, 4, 17, 22, 23, 14, 111111)],
           0.0),
          ([dt(2015, 4, 17, 22, 23, 14, 111111),
            dt(2015, 4, 17, 22, 23, 15, 111111)],
           1.0),
          ([dt(2015, 4, 17, 22, 23, 14, 111111),
            None],
           0.0))
    @unpack
    def test_run_time(self, timestamps, expected_result):
        patched_res = {
            0: [
                {'timestamps': timestamps}
            ]
        }
        with patch.dict(subunit_trace.RESULTS, patched_res, clear=True):
            self.assertEqual(subunit_trace.run_time(), expected_result)

    def test_return_code_all_skips(self):
        skips_stream = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'sample_streams/all_skips.subunit')
        p = subprocess.Popen(['subunit-trace'], stdin=subprocess.PIPE)
        with open(skips_stream, 'rb') as stream:
            p.communicate(stream.read())
        self.assertEqual(1, p.returncode)

    def test_return_code_normal_run(self):
        regular_stream = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'sample_streams/successful.subunit')
        p = subprocess.Popen(['subunit-trace'], stdin=subprocess.PIPE)
        with open(regular_stream, 'rb') as stream:
            p.communicate(stream.read())
        self.assertEqual(0, p.returncode)

    def test_trace(self):
        regular_stream = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'sample_streams/successful.subunit')
        bytes_ = io.BytesIO()
        with open(regular_stream, 'rb') as stream:
            bytes_.write(six.binary_type(stream.read()))
        bytes_.seek(0)
        stdin = io.TextIOWrapper(io.BufferedReader(bytes_))
        returncode = subunit_trace.trace(stdin, sys.stdout)
        self.assertEqual(0, returncode)
