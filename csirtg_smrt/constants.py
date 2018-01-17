import os.path
import tempfile
import sys

from ._version import get_versions
VERSION = get_versions()['version']
del get_versions

TEMP_DIR = os.path.join(tempfile.gettempdir())
RUNTIME_PATH = os.environ.get('CSIRTG_SMRT_RUNTIME_PATH', TEMP_DIR)
RUNTIME_PATH = os.path.join(RUNTIME_PATH)

SMRT_CACHE = os.path.join(RUNTIME_PATH, 'smrt')
SMRT_CACHE = os.environ.get('CSIRTG_SMRT_CACHE_PATH', SMRT_CACHE)
CACHE_PATH = SMRT_CACHE

SMRT_RULES_PATH = os.path.join(RUNTIME_PATH, 'smrt', 'rules')
SMRT_RULES_PATH = os.environ.get('CSIRTG_SMRT_RULES_PATH', SMRT_RULES_PATH)

# Logging stuff
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'

LOGLEVEL = 'ERROR'
LOGLEVEL = os.environ.get('CSIRTG_LOGLEVEL', LOGLEVEL).upper()

REMOTE_ADDR = 'http://localhost:5000'
REMOTE_ADDR = os.environ.get('CSIRTG_REMOTE_ADDR', REMOTE_ADDR)

CONFIG_PATH = os.environ.get('CSIRTG_SMRT_CONFIG_PATH', os.path.join(os.getcwd(), 'csirtg-smrt.yml'))
if not os.path.isfile(CONFIG_PATH):
    CONFIG_PATH = os.path.join(os.path.expanduser('~'), 'csirtg-smrt.yml')

PYVERSION = 2
if sys.version_info > (3,):
    PYVERSION = 3


FIREBALL_SIZE = os.getenv('CSIRTG_SMRT_FIREBALL_SIZE', 100)
if FIREBALL_SIZE == '':
    FIREBALL_SIZE = 100

ROUTER_ADDR = "ipc://{}".format(os.path.join(RUNTIME_PATH, 'router.ipc'))
ROUTER_ADDR = os.environ.get('CIF_ROUTER_ADDR', ROUTER_ADDR)


PORT_APPLICATION_MAP = {
    '21': 'ftp',
    '22': 'ssh',
    '23': 'telnet',
    '80': 'http',
    '443': 'https',
    '3306': 'mysql',
    '5900': 'vnc',
    '3389': 'rdp'
}
