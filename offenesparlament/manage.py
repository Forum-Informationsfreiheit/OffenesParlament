#!/usr/bin/env python
import os
import sys

try:
    import local_manage
    print 'local_manage.py exists, quitting!'
    sys.exit(-1)
except ImportError, e:
    pass

def run():
    from configurations.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "offenesparlament.settings")
    os.environ.setdefault('DJANGO_CONFIGURATION', 'Dev')

    run()
