.. generate_subunit:

generate-subunit
================

generate-subunit is a simple tool to, as its name implies, generate a subunit
stream. It will generate a stream with a single test result to STDOUT. The
subunit protocol lets you concatenate multiple streams together so if you want
to generate a stream with multiple just append the output of multiple executions
of generate-subunit.

Summary
-------
::

    generate-subunit timestamp secs [status] [test_id]

Usage
-----

generate-subunit has 2 mandatory arguments. These are needed to specify when
the "test" started running and how long it took. The first argument is a POSIX
timestamp (which can returned by the date util using ``date +%s``) for when it
started running. The second argument is the number of seconds it took for the
execution to finish. For example::

    $ generate-subunit $(date +%s) 42

will generate a stream with the test_id 'devstack' successfully running for 42
secs starting when the command was executed. This leads into the 2 optional
arguments. The first optional argument is for specifying the status. This must
be the 3rd argument when calling generate-subunit. Valid status options can
be found in the `testtools documentation`_. If status is not specified it will
default to success. For example::

    $ generate-subunit $(date +%s) 42 fail

will be the same as the previous example except that it marks the test as
failing.

.. _testtools documentation: http://testtools.readthedocs.io/en/latest/api.html#testtools.StreamResult.status

The other optional argument is the test_id (aka test name) and is used to
identify the "test" being run. For better or worse this defaults to *devstack*.
(which is an artifact of why this tool was originally created) Note, this must
be the 4th argument when calling generate-subunit. This means you also must
specify a status if you want to set your own test_id. For example::

    $ generate-subunit %(date +%s) 42 fail my_little_test

will generate a subunit stream as before except instead the test will be named
my_little_test.
