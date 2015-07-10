.. _ostestr:

ostestr
=======

The ostestr command provides a wrapper around the testr command included in
the testrepository package. It's designed to build on the functionality
included in testr and workaround several UI bugs in the short term. By default
it also has output that is much more useful for OpenStack's test suites which
are lengthy in both runtime and number of tests. Please note that the CLI
semantics are still a work in progress as the project is quite young, so
default behavior might change in future version.

Summary
-------
    ostestr [-b|--blacklist_file <blacklist_file>] [-r|--regex REGEX]
            [-p|--pretty] [--no-pretty] [-s|--subunit] [-l|--list]
            [-n|--no-discover <test_id>] [--slowest] [--no-slowest]
            [--pdb <test_id>] [--parallel] [--serial]
            [-c|--concurrency <workers>] [--until-failure] [--print-exclude]

Options
-------

  --blacklist_file BLACKLIST_FILE, -b BLACKLIST_FILE
                        Path to a blacklist file, this file contains a
                        separate regex exclude on each newline
  --regex REGEX, -r REGEX
                        A normal testr selection regex. If a blacklist file is
                        specified, the regex will be appended to the end of
                        the generated regex from that file
  --pretty, -p
                        Print pretty output from subunit-trace. This is
                        mutually exclusive with --subunit
  --no-pretty
                        Disable the pretty output with subunit-trace
  --subunit, -s
                        output the raw subunit v2 from the test run this is
                        mutuall exclusive with --pretty
  --list, -l
                        List all the tests which will be run.
  --no-discover TEST_ID, -n TEST_ID
                        Takes in a single test to bypasses test discover and
                        just excute the test specified
  --slowest
                        After the test run print the slowest tests
  --no-slowest
                        After the test run don't print the slowest tests
  --pdb TEST_ID
                        Run a single test that has pdb traces added
  --parallel
                        Run tests in parallel (this is the default)
  --serial
                        Run tests serially
  --concurrency WORKERS, -c WORKERS
                        The number of workers to use when running in parallel.
                        By default this is the number of cpus
  --until-failure
                        Run the tests in a loop until a failure is
                        encountered. Running with subunit or prettyoutput
                        enable will force the loop to run testsserially
  --print-exclude
                        If an exclude file is used this option will prints the
                        comment from the same line and all skipped tests
                        before the test run

Running Tests
-------------

os-testr is primarily for running tests at it's basic level you just invoke
ostestr to run a test suite for a project. (assuming it's setup to run tests
using testr already) For example::

    $ ostestr

This will run tests in parallel (with the number of workers matching the number
of CPUs) and with subunit-trace output. If you need to run tests in serial you
can use the serial option::

    $ ostestr --serial

Or if you need to adjust the concurrency but still run in parallel you can use
-c/--concurrency::

    $ ostestr --concurrency 2

If you only want to run an individual test module or more specific (a single
class, or test) and parallel execution doesn't matter, you can use the
-n/--no-discover to skip test discovery and just directly calls subunit.run on
the tests under the covers. Bypassing discovery is desirable when running a
small subset of tests in a larger test suite because the discovery time can
often far exceed the total run time of the tests.

For example::

    $ ostestr --no-discover test.test_thing.TestThing.test_thing_method

Additionally, if you need to run a single test module, class, or single test
with pdb enabled you can use --pdb to directly call testtools.run under the
covers which works with pdb. For example::

    $ ostestr --pdb tests.test_thing.TestThing.test_thing_method


Test Selection
--------------

ostestr is designed to build on top of the test selection in testr. testr only
exposed a regex option to select tests. This equivalent is functionality is
exposed via the --regex option. For example::

    $ ostestr --regex 'magic\.regex'

This will do a straight passthrough of the provided regex to testr.
Additionally, ostestr allows you to specify a a blacklist file to define a set
of regexes to exclude. You can specify a blacklist file with the
--blacklist-file/-b option, for example::

    $ ostestr --blacklist_file $path_to_file

The format for the file is line separated regex, with '#' used to signify the
start of a comment on a line. For example::

    # Blacklist File
    ^regex1 # Excludes these tests
    .*regex2 # exclude those tests

Will generate a regex to pass to testr which will exclude both any tests
matching '^regex1' and '.*regex2'. If a blacklist file is used in conjunction
with the --regex option the regex specified with --regex will be appended to
the generated output from the --blacklist_file. Also it's worth noting that the
regex test selection options can not be used in conjunction with the
--no-discover or --pdb options described in the previous section. This is
because the regex selection requires using testr under the covers to actually
do the filtering, and those 2 options do not use testr.

It's also worth noting that you can use the test list option to dry run any
selection arguments you are using. You just need to use --list/-l with your
selection options to do this, for example::

    $ ostestr --regex 'regex3.*' --blacklist_file blacklist.txt --list

This will list all the tests which will be run by ostestr using that combination
of arguments.

Please not that all of this selection functionality will be expanded on in the
future and a default grammar for selecting multiple tests will be chosen in a
future release. However as of right now all current arguments (which have
guarantees on always remaining in place) are still required to perform any
selection logic while this functionality is still under development.


Output Options
--------------

By default ostestr will use subunit-trace as the output filter on the test
run. It will also print the slowest tests from the run after the run is
concluded. You can disable the printing the slowest tests with the --no-slowest
flag, for example::

    $ ostestr --no-slowest

If you'd like to disable the subunit-trace output you can do this using
--no-pretty::

    $ ostestr --no-pretty

ostestr also provides the option to just output the raw subunit stream on
STDOUT with --subunit/-s. Note if you want to use this you also have to
specify --no-pretty as the subunit-trace output and the raw subunit output
are mutually exclusive. For example, to get raw subunit output the arguments
would be::

    $ ostestr --no-pretty --subunit

An additional option on top of the blacklist file is --print-exclude option.
When this option is specified when using a blacklist file before the tests are
run ostestr will print all the tests it will be excluding from the blacklist
file. If a line in the blacklist file has a comment that will be printed before
listing the tests which will be excluded by that line's regex. If no comment is
present on a line the regex from that line will be used instead. For example,
if you were using the example blacklist file from the previous section the
output before the regular test run output would be::

    $ ostestr -b blacklist-file blacklist.txt --print-exclude
    Excludes these tests
    regex1_match
    regex1_exclude

    exclude those tests
    regex2_match
    regex2_exclude

    ...

Notes for running with tox
--------------------------

If you use `tox`_ for running your tests and call ostestr as the test command
.. _tox: https://tox.readthedocs.org/en/latest/
it's recommended that you set a posargs following ostestr on the commands
 stanza. For example::

    [testenv]
    commands = ostestr {posargs}

this will enable end users to pass args to configure the output, use the
selection logic, or any other options directly from the tox cli. This will let
tox take care of the venv management and the environment separation but enable
direct access to all of the ostestr options to easily customize your test run.
For example, assuming the above posargs usage you would be to do::

    $ tox -epy34 -- --regex ^regex1

or to skip discovery::

    $ tox -epy34 -- -n test.test_thing.TestThing.test_thing_method
