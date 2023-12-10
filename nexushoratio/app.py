"""Give an app reasonable startup defaults.

To use this module, simply define a 'main' function with a single
'app_parser' argument and add the following to the end of your main
module:

if __name__ == '__main__':
    sys.exit(app.run(main))


The main function is expected to take an argparse.ArgumentParser object
and use that as a parents= parameter to another instance.
"""

import argparse
import datetime
import logging
import os
import pwd
import socket
import resource
import sys
import tempfile

import humanize


class LogAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """Callback action to tweak log settings during flag parsing."""

    def __call__(self, parser, namespace, values, option_string=None):
        numeric_level = getattr(logging, values.upper())
        logging.getLogger().setLevel(numeric_level)


def run(func):
    """Main entry point for application.

    Args:
        func: callback function - Signature should be
            typing.Callable[[argparse.ArgumentParser], int].

    Returns:
        Return value of func.
    """
    parser = argparse.ArgumentParser(add_help=False)
    group = parser.add_argument_group('Global flags')
    group.add_argument('-h', '--help', action='help')
    group.add_argument(
        '-L',
        '--loglevel',
        action=LogAction,
        help='Log level',
        default=argparse.SUPPRESS,
        choices=('debug', 'info', 'warning', 'error'))

    # argv[0] -> argv[0].$HOST.$USER.$DATETIME.$PID

    progname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
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
    logging.basicConfig(
        level=logging.INFO, format=log_format, filename=long_pathname)
    logging.info('Started.')
    # best effort on symlink
    try:
        os.unlink(short_pathname)
    except OSError:
        pass
    os.symlink(long_pathname, short_pathname)
    ret = func(parser)
    logging.info(
        'Max memory used: %s',
        humanize.naturalsize(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    logging.info('Finished. (%d)', ret or 0)
    return ret
