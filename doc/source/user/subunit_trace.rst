.. _subunit_trace:

subunit-trace
=============

subunit-trace is an output filter for subunit streams. It is often used in
conjunction with test runners that emit subunit to enable a consistent and
useful realtime output from a test run.

Summary
-------
::

   subunit-trace [--fails|-f] [--failonly] [--perc-diff|-d] [--no-summary]
                 [--diff-threshold|-t <threshold>] [--color]

Options
-------

--no-failure-debug, -n
                      Disable printing failure debug information in realtime
--fails, -f
                      Print failure debug information after the stream is
                      processed
--failonly
                      Don't print success items
--perc-diff, -d
                      Print percent change in run time on each test
--diff-threshold THRESHOLD, -t THRESHOLD
                      Threshold to use for displaying percent change from the
                      avg run time. If one is not specified the percent
                      change will always be displayed.
--no-summary
                      Don't print the summary of the test run after completes
--color
                      Print result with colors

Usage
-----
subunit-trace will take a subunit stream in via STDIN. This is the only input
into the tool. It will then print on STDOUT the formatted test result output
for the test run information contained in the stream.

A subunit v2 stream must be passed into subunit-trace. If only a subunit v1
stream is available you must use the subunit-1to2 utility to convert it before
passing the stream into subunit-trace. For example this can be done by chaining
pipes::

    $ cat subunit_v1 | subunit-1to2 | subunit-trace

Adjusting per test output
^^^^^^^^^^^^^^^^^^^^^^^^^

subunit-trace provides several options to customize it's output. This allows
users to customize the output from subunit-trace to suit their needs. The output
from subunit-trace basically comes in 2 parts, the per test output, and the
summary at the end. By default subunit-trace will print failure messages during
the per test output, meaning when a test fails it will also print the message
and any traceback and other attachments at that time. However this can be
disabled by using --no-failure-debug, -n. For example::

    $ testr run --subunit | subunit-trace --no-failure-debug

Here is also the option to print all failures together at the end of the test
run before the summary view. This is done using the --fails/-f option. For
example::

    $ testr run --subunit | subunit-trace --fails

Often the --fails and --no-failure-debug options are used in conjunction to
only print failures at the end of a test run. This is useful for large test
suites where an error message might be lost in the noise. To do this ::

    $ testr run --subunit | subunit-trace --fails --no-failure-debug

By default subunit-trace will print a line for each test after it completes with
the test status. However, if you only want to see the run time output for
failures and not any other test status you can use the --failonly option. For
example::

     $ testr run --subunit | subunit-trace --failonly

The last output option provided by subunit-trace is to disable the summary view
of the test run which is normally displayed at the end of a run. You can do
this using the --no-summary option. For example::

    $ testr run --subunit | subunit-trace --no-summary


Show per test run time percent change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

subunit-trace provides an option to display the percent change in run time
from the previous run. To do this subunit-trace leverages the testr internals
a bit. It uses the times.dbm database which, the file repository type in
testrepository will create, to get the previous run time for a test. If testr
hasn't ever been used before or for whatever reason subunit-trace is unable to
find the times.dbm file from testr no percentages will be displayed even if it's
enabled. Additionally, if a test is run which does not have an entry in the
times.dbm file will not have a percentage printed for it.

To enable this feature you use --perc-diff/-d, for example::

    $ testr run --subunit | subunit-trace --perc-diff

There is also the option to set a threshold value for this option. If used it
acts as an absolute value and only percentage changes that exceed it will be
printed. Use the --diff-threshold/-t option to set a threshold, for example::

    $ testr run --subunit | subunit-trace --perc-diff --threshold 45

This will only display percent differences when the change in run time is either
>=45% faster or <=45% slower.
