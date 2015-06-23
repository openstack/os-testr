# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

import os
import shutil
import subprocess
import tempfile

import testtools

from os_testr.tests import base
from six import StringIO

DEVNULL = open(os.devnull, 'wb')


class TestReturnCodes(base.TestCase):
    def setUp(self):
        super(TestReturnCodes, self).setUp()
        # Setup test dirs
        self.directory = tempfile.mkdtemp(prefix='ostestr-unit')
        self.addCleanup(shutil.rmtree, self.directory)
        self.test_dir = os.path.join(self.directory, 'tests')
        os.mkdir(self.test_dir)
        # Setup Test files
        self.testr_conf_file = os.path.join(self.directory, '.testr.conf')
        self.setup_cfg_file = os.path.join(self.directory, 'setup.cfg')
        self.passing_file = os.path.join(self.test_dir, 'test_passing.py')
        self.failing_file = os.path.join(self.test_dir, 'test_failing.py')
        self.init_file = os.path.join(self.test_dir, '__init__.py')
        self.setup_py = os.path.join(self.directory, 'setup.py')
        shutil.copy('os_testr/tests/files/testr-conf', self.testr_conf_file)
        shutil.copy('os_testr/tests/files/passing-tests', self.passing_file)
        shutil.copy('os_testr/tests/files/failing-tests', self.failing_file)
        shutil.copy('setup.py', self.setup_py)
        shutil.copy('os_testr/tests/files/setup.cfg', self.setup_cfg_file)
        shutil.copy('os_testr/tests/files/__init__.py', self.init_file)

        self.stdout = StringIO()
        self.stderr = StringIO()
        # Change directory, run wrapper and check result
        self.addCleanup(os.chdir, os.path.abspath(os.curdir))
        os.chdir(self.directory)

    def assertRunExit(self, cmd, expected, subunit=False):
        p = subprocess.Popen(
            "%s" % cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        if not subunit:
            self.assertEqual(
                p.returncode, expected,
                "Stdout: %s; Stderr: %s" % (out, err))
        else:
            self.assertEqual(p.returncode, expected,
                             "Expected return code: %s doesn't match actual "
                             "return code of: %s" % (expected, p.returncode))

    def test_default_passing(self):
        self.assertRunExit('ostestr --regex passing', 0)

    def test_default_fails(self):
        self.assertRunExit('ostestr', 1)

    def test_default_passing_no_slowest(self):
        self.assertRunExit('ostestr --no-slowest --regex passing', 0)

    def test_default_fails_no_slowest(self):
        self.assertRunExit('ostestr --no-slowest', 1)

    def test_default_serial_passing(self):
        self.assertRunExit('ostestr --serial --regex passing', 0)

    def test_default_serial_fails(self):
        self.assertRunExit('ostestr --serial', 1)

    def test_testr_subunit_passing(self):
        self.assertRunExit('ostestr --no-pretty --subunit --regex passing', 0,
                           subunit=True)

    @testtools.skip('Skipped because of testrepository lp bug #1411804')
    def test_testr_subunit_fails(self):
        self.assertRunExit('ostestr --no-pretty --subunit', 1, subunit=True)

    def test_testr_no_pretty_passing(self):
        self.assertRunExit('ostestr --no-pretty --regex passing', 0)

    def test_testr_no_pretty_fails(self):
        self.assertRunExit('ostestr --no-pretty', 1)

    def test_list(self):
        self.assertRunExit('ostestr --list', 0)
