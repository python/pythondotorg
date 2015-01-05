#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # Add argument needed (and easily forgotten) when using Vagrant.
    if 'runserver' in sys.argv and len(sys.argv) == 2:
        sys.argv.append('0.0.0.0:8000')

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pydotorg.settings.local")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
