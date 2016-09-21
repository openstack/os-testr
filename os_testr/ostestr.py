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
import atexit
import copy
import os
import subprocess
import sys
import tempfile

import pbr.version
from subunit import run as subunit_run
from testtools import run as testtools_run

from os_testr import regex_builder as rb
from os_testr import testlist_builder as tlb


__version__ = pbr.version.VersionInfo('os_testr').version_string()


def get_parser(args):
    parser = argparse.ArgumentParser(
        description='Tool to run openstack tests')
    parser.add_argument('--version', action='version',
                        version='%s' % __version__)
    parser.add_argument('--blacklist-file', '-b', '--blacklist_file',
                        help='Path to a blacklist file, this file '
                             'contains a separate regex exclude on each '
                             'newline')
    parser.add_argument('--whitelist-file', '-w', '--whitelist_file',
                        help='Path to a whitelist file, this file '
                             'contains a separate regex on each newline.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--regex', '-r',
                       help='A normal testr selection regex.')
    group.add_argument('--path', metavar='FILE_OR_DIRECTORY',
                       help='A file name or directory of tests to run.')
    group.add_argument('--no-discover', '-n', metavar='TEST_ID',
                       help="Takes in a single test to bypasses test "
                            "discover and just execute the test specified. "
                            "A file name may be used in place of a test "
                            "name.")
    parser.add_argument('--black-regex', '-B',
                        help='Test rejection regex. If a test cases name '
                        'matches on re.search() operation , '
                        'it will be removed from the final test list. '
                        'Effectively the black-regexp is added to '
                        ' black regexp list, but you do need to edit a file. '
                        'The black filtering happens after the initial '
                        ' white selection, which by default is everything.')
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
    parser.add_argument('--color', action='store_true',
                        help='Use color in the pretty output')
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
    return parser.parse_known_args(args)


def call_testr(regex, subunit, pretty, list_tests, slowest, parallel, concur,
               until_failure, color, list_of_tests=None, others=None):
    others = others or []
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
    if list_of_tests:
        test_fd, test_file_name = tempfile.mkstemp()
        atexit.register(os.remove, test_file_name)
        test_file = os.fdopen(test_fd, 'w')
        test_file.write('\n'.join(list_of_tests) + '\n')
        test_file.close()
        cmd.extend(('--load-list', test_file_name))
    elif regex:
        cmd.append(regex)

    env = copy.deepcopy(os.environ)

    if pretty:
        subunit_trace_cmd = ['subunit-trace', '--no-failure-debug', '-f']
        if color:
            subunit_trace_cmd.append('--color')

    # This workaround is necessary because of lp bug 1411804 it's super hacky
    # and makes tons of unfounded assumptions, but it works for the most part
    if (subunit or pretty) and until_failure:
        test_list = rb._get_test_list(regex, env)
        count = 0
        failed = False
        if not test_list:
            print("No tests to run")
            return 1
        # If pretty or subunit output is desired manually loop forever over
        # test individually and generate the desired output in a linear series
        # this avoids 1411804 while retaining most of the desired behavior
        while True:
            for test in test_list:
                if pretty:
                    cmd = ['python', '-m', 'subunit.run', test]
                    ps = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
                    subunit_trace_cmd.append('--no-summary')
                    proc = subprocess.Popen(subunit_trace_cmd,
                                            env=env,
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
                            return 1
                        else:
                            raise
                count = count + 1
            if failed:
                print("Ran %s tests without failure" % count)
                return 0
    # If not until-failure special case call testr like normal
    elif pretty and not list_tests:
        cmd.extend(others)
        ps = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
        proc = subprocess.Popen(subunit_trace_cmd,
                                env=env, stdin=ps.stdout)
        ps.stdout.close()
    else:
        cmd.extend(others)
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


def _ensure_testr():
    if not os.path.isdir('.testrepository'):
        subprocess.call(['testr', 'init'])


def _select_and_call_runner(opts, exclude_regex, others):
    ec = 1
    _ensure_testr()

    if not opts.no_discover and not opts.pdb:
        ec = call_testr(exclude_regex, opts.subunit, opts.pretty, opts.list,
                        opts.slowest, opts.parallel, opts.concurrency,
                        opts.until_failure, opts.color, None, others)
    else:
        if others:
            print('Unexpected arguments: ' + ' '.join(others))
            return 2
        test_to_run = opts.no_discover or opts.pdb
        if test_to_run.find('/') != -1:
            test_to_run = rb.path_to_regex(test_to_run)
        ec = call_subunit_run(test_to_run, opts.pretty, opts.subunit)
    return ec


def _call_testr_with_list(opts, test_list, others):
    ec = 1
    _ensure_testr()

    if opts.list:
        print("\n".join(test_list))
        return 0

    ec = call_testr(None, opts.subunit, opts.pretty, opts.list,
                    opts.slowest, opts.parallel, opts.concurrency,
                    opts.until_failure, opts.color, test_list, others)
    return ec


def ostestr(args):
    opts, others = get_parser(args)
    if opts.pretty and opts.subunit:
        msg = ('Subunit output and pretty output cannot be specified at the '
               'same time')
        print(msg)
        return 2
    if opts.list and opts.no_discover:
        msg = ('you can not list tests when you are bypassing discovery to '
               'run a single test')
        print(msg)
        return 3
    if not opts.parallel and opts.concurrency:
        msg = "You can't specify a concurrency to use when running serially"
        print(msg)
        return 4
    if (opts.pdb or opts.no_discover) and opts.until_failure:
        msg = "You can not use until_failure mode with pdb or no-discover"
        print(msg)
        return 5
    if ((opts.pdb or opts.no_discover) and
            (opts.blacklist_file or opts.whitelist_file)):
        msg = "You can not use blacklist or whitelist with pdb or no-discover"
        print(msg)
        return 6
    if ((opts.pdb or opts.no_discover) and (opts.black_regex)):
        msg = "You can not use black-regex with pdb or no-discover"
        print(msg)
        return 7

    if opts.path:
        regex = rb.path_to_regex(opts.path)
    else:
        regex = opts.regex

    if opts.blacklist_file or opts.whitelist_file or opts.black_regex:
        list_of_tests = tlb.construct_list(opts.blacklist_file,
                                           opts.whitelist_file,
                                           regex,
                                           opts.black_regex,
                                           opts.print_exclude)
        return (_call_testr_with_list(opts, list_of_tests, others))
    else:
        return (_select_and_call_runner(opts, regex, others))


def main():
    exit(ostestr(sys.argv[1:]))

if __name__ == '__main__':
    main()
