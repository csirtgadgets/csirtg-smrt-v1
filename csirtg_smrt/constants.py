import os.path
import tempfile

from ._version import get_versions
VERSION = get_versions()['version']
del get_versions

TEMP_DIR = os.path.join(tempfile.gettempdir())
RUNTIME_PATH = os.environ.get('CSIRTG_RUNTIME_PATH', TEMP_DIR)
RUNTIME_PATH = os.path.join(RUNTIME_PATH)

SMRT_CACHE = os.path.join(RUNTIME_PATH, 'smrt')
SMRT_CACHE = os.environ.get('CSIRTG_SMRT_CACHE', SMRT_CACHE)

SMRT_RULES_PATH = os.path.join(RUNTIME_PATH, 'smrt', 'rules')
SMRT_RULES_PATH = os.environ.get('CSIRTG_SMRT_RULES_PATH', SMRT_RULES_PATH)

# Logging stuff
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'

LOGLEVEL = 'INFO'
LOGLEVEL = os.environ.get('CSIRTG_LOGLEVEL', LOGLEVEL).upper()

REMOTE_ADDR = 'http://localhost:5000'
REMOTE_ADDR = os.environ.get('CSIRTG_REMOTE_ADDR', REMOTE_ADDR)
