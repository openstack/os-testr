#!/usr/bin/env python2
# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
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

import copy
import os
import subprocess

import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description='Tool to run openstack tests')
    parser.add_argument('--blacklist_file', '-b',
                        help='Path to a blacklist file, this file contains a'
                             ' separate regex exclude on each newline')
    parser.add_argument('--regex', '-r',
                        help='A normal testr selection regex. If a blacklist '
                             'file is specified, the regex will be appended '
                             'to the end of the generated regex from that '
                             'file')
    parser.add_argument('--pretty', '-p', default=True,
                        help='Print pretty output from subunit-trace. This is '
                             'mutually exclusive with --subunit')
    parser.add_argument('--subunit', '-s', action='store_true',
                        help='output the raw subunit v2 from the test run '
                             'this is mutuall exclusive with --pretty')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all the tests which will be run.')
    parser.add_argument('--no-discover', '-n',
                        help="Takes in a single test to bypasses test "
                             "discover and just excute the test specified")
    parser.add_argument('--slowest', default=True,
                        help="after the test run print the slowest tests")
    parser.add_argument('--pdb',
                        help='Run a single test that has pdb traces added')
    opts = parser.parse_args()
    return opts


def construct_regex(blacklist_file, regex):
    if not blacklist_file:
        exclude_regex = ''
    else:
        black_file = open(blacklist_file, 'r')
        exclude_regex = ''
        for line in black_file:
            regex = line.strip()
            exclude_regex = '|'.join([regex, exclude_regex])
        if exclude_regex:
            exclude_regex = "'(?!.*" + exclude_regex + ")"
    if regex:
        exclude_regex += regex
    return exclude_regex


def call_testr(regex, subunit, pretty, list_tests, slowest):
    cmd = ['testr', 'run', '--parallel']

    if list_tests:
        cmd = ['testr', 'list-tests']
    elif subunit or pretty:
        cmd.append('--subunit')
    cmd.append(regex)
    env = copy.deepcopy(os.environ)
    if pretty and not list_tests:
        ps = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
        proc = subprocess.Popen(['subunit-trace', '--no-failure-debug', '-f'],
                                env=env, stdin=ps.stdout)
        ps.stdout.close()
    else:
        proc = subprocess.Popen(cmd, env=env)
    proc.communicate()
    return_code = proc.returncode
    if slowest and not list_tests:
        print("\nSlowest Tests:\n")
        slow_proc = subprocess.Popen(['testr', 'slowest'], env=env)
        slow_proc.communicate()
    return return_code


def call_subunit_run(test_id, pretty):
    cmd = ['python', '-m', 'subunit.run', test_id]
    env = copy.deepcopy(os.environ)
    if pretty:
        ps = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
        proc = subprocess.Popen(['subunit-trace', '--no-failure-debug', '-f'],
                                env=env, stdin=ps.stdout)
        ps.stdout.close()
    else:
        proc = subprocess.Popen(cmd, env=env)
    proc.communicate()
    return_code = proc.returncode
    return return_code


def call_testtools_run(test_id):
    cmd = ['python', '-m', 'testtools.run', test_id]
    env = copy.deepcopy(os.environ)
    proc = subprocess.Popen(cmd, env=env)
    proc.communicate()
    return_code = proc.returncode
    return return_code


def main():
    opts = parse_args()
    if opts.pretty and opts.subunit:
        msg = ('Subunit output and pretty output cannot be specified at the '
               'same time')
        print(msg)
        exit(2)
    if opts.list and opts.no_discover:
        msg = ('you can not list tests when you are bypassing discovery to '
               'run a single test')
        print(msg)
        exit(3)
    exclude_regex = construct_regex(opts.blacklist_file, opts.regex)
    if not os.path.isdir('.testrepository'):
        subprocess.call('testr init')
    if not opts.no_discover and not opts.pdb:
        exit(call_testr(exclude_regex, opts.subunit, opts.pretty, opts.list,
                        opts.slowest))
    elif opts.pdb:
        exit(call_testtools_run(opts.pdb))
    else:
        exit(call_subunit_run(opts.no_discover, opts.pretty))

if __name__ == '__main__':
    main()
