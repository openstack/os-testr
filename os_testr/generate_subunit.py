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


import datetime
import sys

import pbr.version
import subunit
from subunit import iso8601


__version__ = pbr.version.VersionInfo('os_testr').version_string()


def main():
    if '--version' in sys.argv:
        print(__version__)
        exit(0)

    start_time = datetime.datetime.fromtimestamp(float(sys.argv[1])).replace(
        tzinfo=iso8601.UTC)
    elapsed_time = datetime.timedelta(seconds=int(sys.argv[2]))
    stop_time = start_time + elapsed_time

    if len(sys.argv) > 3:
        status = sys.argv[3]
    else:
        status = 'success'

    if len(sys.argv) > 4:
        test_id = sys.argv[4]
    else:
        test_id = 'devstack'

    # Write the subunit test
    output = subunit.v2.StreamResultToBytes(sys.stdout)
    output.startTestRun()
    output.status(timestamp=start_time, test_id=test_id)
    # Write the end of the test
    output.status(test_status=status, timestamp=stop_time, test_id=test_id)
    output.stopTestRun()


if __name__ == '__main__':
    main()
