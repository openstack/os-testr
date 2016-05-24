# Copyright 2016 Hewlett-Packard Development Company, L.P.
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
    lines = []
    for line in open(file_path).read().splitlines():
        split_line = line.strip().split('#')
        # Before the # is the regex
        line_regex = split_line[0].strip()
        if line_regex:
            lines.append(line_regex)
    return '|'.join(lines)


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
                if exclude_regex:
                    exclude_regex = '|'.join([line_regex, exclude_regex])
                else:
                    exclude_regex = line_regex
        if exclude_regex:
            exclude_regex = "^((?!" + exclude_regex + ").)*$"
    if regex:
        exclude_regex += regex
    if whitelist_file:
        exclude_regex += '%s' % get_regex_from_whitelist_file(whitelist_file)
    return exclude_regex
