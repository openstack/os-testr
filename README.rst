========
os-testr
========

.. image:: https://img.shields.io/pypi/v/os-testr.svg
    :target: https://pypi.org/project/os-testr/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/os-testr.svg
    :target: https://pypi.org/project/os-testr/
    :alt: Downloads

A testr wrapper to provide functionality for OpenStack projects.

* Free software: Apache license
* Documentation: https://docs.openstack.org/os-testr/
* Source: https://opendev.org/openstack/os-testr
* Bugs: https://bugs.launchpad.net/os-testr

Features
--------

.. warning::
   ``ostestr`` command is deprecated. Use `stestr`_ command instead like
   following

   0. Install `stestr`_ (This step is already done if you're using ostestr.)
   1. You can use ``stestr run ...`` instead of ``ostestr ...``
   2. You can use ``stestr list ...`` instead of ``ostestr --list ...``

   For more sub commands and options, please refer to `stestr help` or the
   `stestr`_ document.

* ``ostestr``: a testr wrapper that uses subunit-trace for output and builds
  some helpful extra functionality around testr
* ``subunit-trace``: an output filter for a subunit stream which provides
  useful information about the run
* ``subunit2html``: generates a test results html page from a subunit stream
* ``generate-subunit``: generate a subunit stream for a single test

.. _stestr: https://stestr.readthedocs.io/
