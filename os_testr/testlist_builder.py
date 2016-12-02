# Copyright 2016 RedHat, Inc.
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

from os_testr import regex_builder
import re


def black_reader(blacklist_file):
    black_file = open(blacklist_file, 'r')
    regex_comment_lst = []  # tupple of (regex_compild, msg, skipped_lst)
    for line in black_file:
        raw_line = line.strip()
        split_line = raw_line.split('#')
        # Before the # is the regex
        line_regex = split_line[0].strip()
        if len(split_line) > 1:
            # After the # is a comment
            comment = ''.join(split_line[1:]).strip()
        else:
            comment = 'Skipped because of regex %s:' % line_regex
        if not line_regex:
            continue
        regex_comment_lst.append((re.compile(line_regex), comment, []))
    return regex_comment_lst


def print_skips(regex, message, test_list):
    for test in test_list:
        print(test)
    # Extra whitespace to separate
    print('\n')


def construct_list(blacklist_file, whitelist_file, regex, black_regex,
                   print_exclude):
    """Filters the discovered test cases

    :retrun: iterable of strings. The strings are full
        test cases names, including tags like.:
        "project.api.TestClass.test_case[positive]"
    """

    if not regex:
        regex = ''  # handle the other false things

    if whitelist_file:
        white_re = regex_builder.get_regex_from_whitelist_file(whitelist_file)
    else:
        white_re = ''

    if not regex and white_re:
        regex = white_re
    elif regex and white_re:
        regex = '|'.join((regex, white_re))

    if blacklist_file:
        black_data = black_reader(blacklist_file)
    else:
        black_data = None

    if black_regex:
        msg = "Skipped because of regex provided as a command line argument:"
        record = (re.compile(black_regex), msg, [])
        if black_data:
            black_data.append(record)
        else:
            black_data = [record]

    search_filter = re.compile(regex)

    # NOTE(afazekas): we do not want to pass a giant re
    # to an external application due to the arg length limitatios
    list_of_test_cases = [test_case for test_case in
                          regex_builder._get_test_list('')
                          if search_filter.search(test_case)]
    set_of_test_cases = set(list_of_test_cases)

    if not black_data:
        return set_of_test_cases

    # NOTE(afazekas): We might use a faster logic when the
    # print option is not requested
    for (rex, msg, s_list) in black_data:
        for test_case in list_of_test_cases:
            if rex.search(test_case):
                # NOTE(mtreinish): In the case of overlapping regex the test
                # case might have already been removed from the set of tests
                if test_case in set_of_test_cases:
                    set_of_test_cases.remove(test_case)
                    s_list.append(test_case)

    if print_exclude:
        for (rex, msg, s_list) in black_data:
            if s_list:
                print_skips(rex, msg, s_list)
    return set_of_test_cases
