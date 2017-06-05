.. _subunit2html:

subunit2html
============

subunit2html is a tool that takes in a subunit stream file and will output an
html page

Summary
-------
::

    subunit2html subunit_stream [output]

Usage
-----

subunit2html takes in 1 mandatory argument. This is used to specify the location
of the subunit stream file. For example::

    $ subunit2html subunit_stream

By default subunit2html will store the generated html results file at
results.html file in the current working directory.

An optional second argument can be provided to set the output path of the html
results file that is generated. If it is provided this will be the output path
for saving the generated file, otherwise results.html in the current working
directory will be used. For example::

    $ subunit2html subunit_stream test_results.html

will write the generated html results file to test_results.html in the current
working directory
