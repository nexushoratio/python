"""Provide a reasonable set of defaults for logging.

To use the global flag, register using:
   ArgparseApp().register_global_flags(logmgr)

To turn on the global log file, execute the following early in your program:
  log_mgr.activate()
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os
import pwd
import socket
import sys
import tempfile
import typing

if typing.TYPE_CHECKING:
    from mundane import app


def mundane_global_flags(argp_app: app.ArgparseApp):
    """Register global flags."""

    class LogLevel(argparse.Action):  # pylint: disable=too-few-public-methods
        """Callback action to tweak log settings during flag parsing."""

        # The following ignore is for the 'values' paramter.
        def __call__(  # type: ignore[override]
                self,
                parser: argparse.ArgumentParser,
                namespace: argparse.Namespace,
                values: str,
                option_string: str | None = None):
            logging.getLogger().setLevel(values)

    # TODO: switch to getLevelNamesMapping() once minver = 3.11
    choices = tuple(
        name for level, name in sorted(logging._levelToName.items())  # pylint: disable=protected-access
        if level)

    argp_app.global_flags.add_argument(
        '-L',
        '--log-level',
        action=LogLevel,
        help='Minimal log level',
        default=argparse.SUPPRESS,
        choices=choices)


def activate():
    """Activate this logfile setup."""
    # argv[0] -> argv[0].$HOST.$USER.$DATETIME.$PID

    progname = os.path.basename(sys.argv[0])
    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

    short_filename = f'{progname}.log'
    long_filename = (
        f'{short_filename}.{socket.gethostname()}'
        f'.{pwd.getpwuid(os.getuid())[0]}.{now}.{os.getpid()}')

    long_pathname = os.path.join(tempfile.gettempdir(), long_filename)
    short_pathname = os.path.join(tempfile.gettempdir(), short_filename)

    log_format = (
        '%(levelname).1s%(asctime)s: %(filename)s:%(lineno)d'
        '(%(funcName)s)] {%(name)s} %(message)s')
    logging.basicConfig(format=log_format, filename=long_pathname, force=True)

    # best effort on symlink
    try:
        os.unlink(short_pathname)
    except OSError:
        pass
    os.symlink(long_pathname, short_pathname)
