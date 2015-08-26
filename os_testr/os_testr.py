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

import argparse
import copy
import os
import subprocess
import sys

from subunit import run as subunit_run
from testtools import run as testtools_run


def get_parser(args):
    parser = argparse.ArgumentParser(
        description='Tool to run openstack tests')
    list_files = parser.add_mutually_exclusive_group()
    list_files.add_argument('--blacklist_file', '-b',
                            help='Path to a blacklist file, this file '
                                 'contains a separate regex exclude on each '
                                 'newline')
    list_files.add_argument('--whitelist_file', '-w',
                            help='Path to a whitelist file, this file '
                                 'contains a separate regex on each newline.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--regex', '-r',
                       help='A normal testr selection regex. If a blacklist '
                            'file is specified, the regex will be appended '
                            'to the end of the generated regex from that '
                            'file.')
    group.add_argument('--path', metavar='FILE_OR_DIRECTORY',
                       help='A file name or directory of tests to run.')
    group.add_argument('--no-discover', '-n', metavar='TEST_ID',
                       help="Takes in a single test to bypasses test "
                            "discover and just excute the test specified. "
                            "A file name may be used in place of a test "
                            "name.")
    pretty = parser.add_mutually_exclusive_group()
    pretty.add_argument('--pretty', '-p', dest='pretty', action='store_true',
                        help='Print pretty output from subunit-trace. This is '
                             'mutually exclusive with --subunit')
    pretty.add_argument('--no-pretty', dest='pretty', action='store_false',
                        help='Disable the pretty output with subunit-trace')
    parser.add_argument('--subunit', '-s', action='store_true',
                        help='output the raw subunit v2 from the test run '
                             'this is mutually exclusive with --pretty')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all the tests which will be run.')
    slowest = parser.add_mutually_exclusive_group()
    slowest.add_argument('--slowest', dest='slowest', action='store_true',
                         help="after the test run print the slowest tests")
    slowest.add_argument('--no-slowest', dest='slowest', action='store_false',
                         help="after the test run don't print the slowest "
                              "tests")
    parser.add_argument('--pdb', metavar='TEST_ID',
                        help='Run a single test that has pdb traces added')
    parallel = parser.add_mutually_exclusive_group()
    parallel.add_argument('--parallel', dest='parallel', action='store_true',
                          help='Run tests in parallel (this is the default)')
    parallel.add_argument('--serial', dest='parallel', action='store_false',
                          help='Run tests serially')
    parser.add_argument('--concurrency', '-c', type=int, metavar='WORKERS',
                        help='The number of workers to use when running in '
                             'parallel. By default this is the number of cpus')
    parser.add_argument('--until-failure', action='store_true',
                        help='Run the tests in a loop until a failure is '
                             'encountered. Running with subunit or pretty'
                             'output enable will force the loop to run tests'
                             'serially')
    parser.add_argument('--print-exclude', action='store_true',
                        help='If an exclude file is used this option will '
                             'prints the comment from the same line and all '
                             'skipped tests before the test run')
    parser.set_defaults(pretty=True, slowest=True, parallel=True)
    return parser.parse_args(args)


def _get_test_list(regex, env=None):
    env = env or copy.deepcopy(os.environ)
    proc = subprocess.Popen(['testr', 'list-tests', regex], env=env,
                            stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    raw_test_list = out.split('\n')
    bad = False
    test_list = []
    exclude_list = ['OS_', 'CAPTURE', 'TEST_TIMEOUT', 'PYTHON',
                    'subunit.run discover']
    for line in raw_test_list:
        for exclude in exclude_list:
            if exclude in line:
                bad = True
                break
            elif not line:
                bad = True
                break
        if not bad:
            test_list.append(line)
        bad = False
    return test_list


def print_skips(regex, message):
    test_list = _get_test_list(regex)
    if test_list:
        if message:
            print(message)
        else:
            print('Skipped because of regex %s:' % regex)
        for test in test_list:
            print(test)
        # Extra whitespace to separate
        print('\n')


def path_to_regex(path):
    root, _ = os.path.splitext(path)
    return root.replace('/', '.')


def get_regex_from_whitelist_file(file_path):
    return '|'.join(open(file_path).read().splitlines())


def construct_regex(blacklist_file, whitelist_file, regex, print_exclude):
    if not blacklist_file:
        exclude_regex = ''
    else:
        black_file = open(blacklist_file, 'r')
        exclude_regex = ''
        for line in black_file:
            raw_line = line.strip()
            split_line = raw_line.split('#')
            # Before the # is the regex
            line_regex = split_line[0].strip()
            if len(split_line) > 1:
                # After the # is a comment
                comment = split_line[1].strip()
            else:
                comment = ''
            if line_regex:
                if print_exclude:
                    print_skips(line_regex, comment)
                exclude_regex = '|'.join([line_regex, exclude_regex])
        if exclude_regex:
            exclude_regex = "(?!.*" + exclude_regex + ")"
    if regex:
        exclude_regex += regex
    if whitelist_file:
        exclude_regex += '%s' % get_regex_from_whitelist_file(whitelist_file)
    return exclude_regex


def call_testr(regex, subunit, pretty, list_tests, slowest, parallel, concur,
               until_failure):
    if parallel:
        cmd = ['testr', 'run', '--parallel']
        if concur:
            cmd.append('--concurrency=%s' % concur)
    else:
        cmd = ['testr', 'run']
    if list_tests:
        cmd = ['testr', 'list-tests']
    elif (subunit or pretty) and not until_failure:
        cmd.append('--subunit')
    elif not (subunit or pretty) and until_failure:
        cmd.append('--until-failure')
    cmd.append(regex)
    env = copy.deepcopy(os.environ)
    # This workaround is necessary because of lp bug 1411804 it's super hacky
    # and makes tons of unfounded assumptions, but it works for the most part
    if (subunit or pretty) and until_failure:
        test_list = _get_test_list(regex, env)
        count = 0
        failed = False
        if not test_list:
            print("No tests to run")
            exit(1)
        # If pretty or subunit output is desired manually loop forever over
        # test individually and generate the desired output in a linear series
        # this avoids 1411804 while retaining most of the desired behavior
        while True:
            for test in test_list:
                if pretty:
                    cmd = ['python', '-m', 'subunit.run', test]
                    ps = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
                    proc = subprocess.Popen(['subunit-trace',
                                             '--no-failure-debug', '-f',
                                             '--no-summary'], env=env,
                                            stdin=ps.stdout)
                    ps.stdout.close()
                    proc.communicate()
                    if proc.returncode > 0:
                        failed = True
                        break
                else:
                    try:
                        subunit_run.main([sys.argv[0], test], sys.stdout)
                    except SystemExit as e:
                        if e > 0:
                            print("Ran %s tests without failure" % count)
                            exit(1)
                        else:
                            raise
                count = count + 1
            if failed:
                print("Ran %s tests without failure" % count)
                exit(0)
    # If not until-failure special case call testr like normal
    elif pretty and not list_tests:
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


def call_subunit_run(test_id, pretty, subunit):
    if pretty:
        env = copy.deepcopy(os.environ)
        cmd = ['python', '-m', 'subunit.run', test_id]
        ps = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
        proc = subprocess.Popen(['subunit-trace', '--no-failure-debug', '-f'],
                                env=env, stdin=ps.stdout)
        ps.stdout.close()
        proc.communicate()
        return proc.returncode
    elif subunit:
        subunit_run.main([sys.argv[0], test_id], sys.stdout)
    else:
        testtools_run.main([sys.argv[0], test_id], sys.stdout)


def _select_and_call_runner(opts, exclude_regex):
    ec = 1
    if not os.path.isdir('.testrepository'):
        subprocess.call(['testr', 'init'])

    if not opts.no_discover and not opts.pdb:
        ec = call_testr(exclude_regex, opts.subunit, opts.pretty, opts.list,
                        opts.slowest, opts.parallel, opts.concurrency,
                        opts.until_failure)
    else:
        test_to_run = opts.no_discover or opts.pdb
        if test_to_run.find('/') != -1:
            test_to_run = path_to_regex(test_to_run)
        ec = call_subunit_run(test_to_run, opts.pretty, opts.subunit)
    return ec


def main():
    opts = get_parser(sys.argv[1:])
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
    if not opts.parallel and opts.concurrency:
        msg = "You can't specify a concurrency to use when running serially"
        print(msg)
        exit(4)
    if (opts.pdb or opts.no_discover) and opts.until_failure:
        msg = "You can not use until_failure mode with pdb or no-discover"
        print(msg)
        exit(5)
    if opts.path:
        regex = path_to_regex(opts.path)
    else:
        regex = opts.regex
    exclude_regex = construct_regex(opts.blacklist_file,
                                    opts.whitelist_file,
                                    regex,
                                    opts.print_exclude)
    exit(_select_and_call_runner(opts, exclude_regex))

if __name__ == '__main__':
    main()
