Work Items for os-testr
=======================

Short Term
----------
 * Expose all subunit-trace options through ostestr
 * Add --html option to ostestr to run testr with subunit2html output
 * Add unit tests
   * For ostestr test selection api
   * Response code validation on more argument permutations
Long Term
---------
 * Lock down test selection CLI
   * When this is done it will become release 1.0.0
 * Add subunit-trace functional tests
   ** Sample subunit streams and test output from subunit-trace
 * Add testing for subunit2html
