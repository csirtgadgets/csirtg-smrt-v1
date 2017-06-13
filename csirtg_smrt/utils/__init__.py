import pkgutil
import logging
from csirtg_smrt.constants import LOG_FORMAT, RUNTIME_PATH, LOGLEVEL, VERSION
from argparse import ArgumentParser
import signal
import yaml
import os


def read_config(args):
    options = {}
    if os.path.isfile(args.config):
        with open(args.config) as f:
            config = yaml.load(f)

        if not config:
            return options

        if config.get('client'):
            config = config['client']
        f.close()
        if not config:
            return options
        for k in config:
            if not options.get(k):
                options[k] = config[k]
    else:
        return options

    return options


def get_argument_parser():
    BasicArgs = ArgumentParser(add_help=False)
    BasicArgs.add_argument('-d', '--debug', dest='debug', action="store_true")
    BasicArgs.add_argument('-V', '--version', action='version', version=VERSION)
    BasicArgs.add_argument(
        "--runtime-path", help="specify the runtime path [default %(default)s]", default=RUNTIME_PATH
    )
    return ArgumentParser(parents=[BasicArgs], add_help=False)


def load_plugin(path, plugin):
    p = None
    for loader, modname, is_pkg in pkgutil.iter_modules([path]):
        if modname == plugin or modname == 'z{}'.format(plugin):
            p = loader.find_module(modname).load_module(modname)
            p = p.Plugin

    return p


def setup_logging(args):
    loglevel = logging.getLevelName(LOGLEVEL)

    if args.debug:
        loglevel = logging.DEBUG

    console = logging.StreamHandler()
    logging.getLogger('').setLevel(loglevel)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger('').addHandler(console)


def setup_signals(name):
    logger = logging.getLogger(__name__)

    def sigterm_handler(_signo, _stack_frame):
        logger.info('SIGTERM Caught for {}, shutting down...'.format(name))
        raise SystemExit

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)


def setup_runtime_path(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def chunk(it, slice=50):
    """Generate sublists from an iterator
    >>> list(chunk(iter(range(10)),11))
    [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
    >>> list(chunk(iter(range(10)),9))
    [[0, 1, 2, 3, 4, 5, 6, 7, 8], [9]]
    >>> list(chunk(iter(range(10)),5))
    [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]
    >>> list(chunk(iter(range(10)),3))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    >>> list(chunk(iter(range(10)),1))
    [[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]]
    """

    assert(slice > 0)
    a=[]

    for x in it:
        if len(a) >= slice :
            yield a
            a=[]
        a.append(x)

    if a:
        yield a
