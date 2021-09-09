#!/usr/bin/env python3
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
import io
import os
import subprocess
import sys
import warnings

import pbr.version
import six.moves

from stestr import commands
from subunit import run as subunit_run
from testtools import run as testtools_run

from os_testr import regex_builder as rb


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
                        'Effectively the black-regex is added to '
                        ' black regex list, but you do need to edit a file. '
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
                        default=0,
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


def _parse_testrconf():
    # Parse the legacy .testr.conf file.
    test_dir = None
    top_dir = None
    group_regex = None

    with open('.testr.conf', 'r') as testr_conf_file:
        config = six.moves.configparser.ConfigParser()
        config.readfp(testr_conf_file)
        test_command = config.get('DEFAULT', 'test_command')
        group_regex = None
        if config.has_option('DEFAULT', 'group_regex'):
            group_regex = config.get('DEFAULT', 'group_regex')

    for line in test_command.split('\n'):
        if 'subunit.run discover' in line:
            command_parts = line.split(' ')
            top_dir_present = '-t' in line
            for idx, val in enumerate(command_parts):
                if top_dir_present:
                    if val == '-t':
                        top_dir = command_parts[idx + 1]
                        test_dir = command_parts[idx + 2]
                else:
                    if val == 'discover':
                        test_dir = command_parts[idx + 1]
    return (test_dir, top_dir, group_regex)


def call_testr(regex, subunit, pretty, list_tests, slowest, parallel, concur,
               until_failure, color, others=None, blacklist_file=None,
               whitelist_file=None, black_regex=None, load_list=None):
    # Handle missing .stestr.conf from users from before stestr migration
    test_dir = None
    top_dir = None
    group_regex = None
    if not os.path.isfile('.stestr.conf') and os.path.isfile('.testr.conf'):
        msg = ('No .stestr.conf file found in the CWD. Please create one to '
               'replace the .testr.conf file. You can find a script to do '
               'this in the stestr git repository.')
        warnings.warn(msg)

        test_dir, top_dir, group_regex = _parse_testrconf()
    elif not os.path.isfile(
        '.testr.conf') and not os.path.isfile('.stestr.conf'):
        msg = ('No .stestr.conf found, please create one.')
        print(msg)
        sys.exit(1)

    regexes = None
    if regex:
        regexes = regex.split()
    serial = not parallel
    if list_tests:
        # TODO(mtreinish): remove init call after list command detects and
        # autocreates the repository
        if not os.path.isdir('.stestr'):
            commands.init_command()
        return commands.list_command(filters=regexes)
    return_code = commands.run_command(filters=regexes, subunit_out=subunit,
                                       concurrency=concur, test_path=test_dir,
                                       top_dir=top_dir,
                                       group_regex=group_regex,
                                       until_failure=until_failure,
                                       serial=serial, pretty_out=pretty,
                                       load_list=load_list,
                                       blacklist_file=blacklist_file,
                                       whitelist_file=whitelist_file,
                                       black_regex=black_regex)

    if slowest:
        sys.stdout.write("\nSlowest Tests:\n")
        commands.slowest_command()
    return return_code


def call_subunit_run(test_id, pretty, subunit):
    env = copy.deepcopy(os.environ)
    cmd_save_results = ['stestr', 'load', '--subunit']
    if not os.path.isdir('.stestr'):
        commands.init_command()

    if pretty:
        # Use subunit run module
        cmd = ['python', '-m', 'subunit.run', test_id]
        ps = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
        # Save subunit results via testr
        pfile = subprocess.Popen(cmd_save_results, env=env,
                                 stdin=ps.stdout, stdout=subprocess.PIPE)
        ps.stdout.close()
        # Transform output via subunit-trace
        proc = subprocess.Popen(['subunit-trace', '--no-failure-debug', '-f'],
                                env=env, stdin=pfile.stdout)
        pfile.stdout.close()
        proc.communicate()
        return proc.returncode
    elif subunit:
        sstdout = io.BytesIO()
        subunit_run.main([sys.argv[0], test_id], sstdout)
        pfile = subprocess.Popen(cmd_save_results, env=env,
                                 stdin=subprocess.PIPE)
        pfile.communicate(input=sstdout.getvalue())
    else:
        testtools_run.main([sys.argv[0], test_id], sys.stdout)


def _select_and_call_runner(opts, exclude_regex, others):
    ec = 1

    if not opts.no_discover and not opts.pdb:
        ec = call_testr(exclude_regex, opts.subunit, opts.pretty, opts.list,
                        opts.slowest, opts.parallel, opts.concurrency,
                        opts.until_failure, opts.color, others,
                        blacklist_file=opts.blacklist_file,
                        whitelist_file=opts.whitelist_file,
                        black_regex=opts.black_regex)
    else:
        if others:
            print('Unexpected arguments: ' + ' '.join(others))
            return 2
        test_to_run = opts.no_discover or opts.pdb
        if test_to_run.find('/') != -1:
            test_to_run = rb.path_to_regex(test_to_run)
        ec = call_subunit_run(test_to_run, opts.pretty, opts.subunit)
    return ec


def ostestr(args):
    msg = ('Deprecate: ostestr command is deprecated now. Use stestr '
           'command instead. For more information: '
           'https://docs.openstack.org/os-testr/latest/user/ostestr.html')
    warnings.warn(msg)
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

    return _select_and_call_runner(opts, regex, others)


def main():
    exit(ostestr(sys.argv[1:]))


if __name__ == '__main__':
    main()
