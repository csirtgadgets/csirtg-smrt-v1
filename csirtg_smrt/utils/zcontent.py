import magic
import sys
from pprint import pprint
from csirtg_smrt.constants import PYVERSION


def _is_ascii(f, mime):
    if mime.startswith(('text/plain', 'ASCII text')):
        return True


def _is_rss(f, mime):
    if not _is_xml(f, mime):
        return


def _is_xml(f, mime):
    if mime == 'XML document text':
        return 'xml'

    first = f.readline()
    second = f.readline().rstrip("\n")
    last = f.readlines()[-1].rstrip("\n")

    if not first.startswith("<?xml "):
        return

    if second.startswith("<rss ") and last.endswith("</rss>"):
        return 'rss'


def _is_json(f, mime):
    if not _is_ascii(f, mime):
        return

    first = f.readline().rstrip("\n")
    last = first
    try:
        last = f.readlines()[-1].rstrip("\n")
    except Exception:
        pass

    if not first.startswith(("'[{", "'{")):
        return

    if not last.endswith(("}]'", "}'")):
        return

    return 'json'


def _is_delimited(f, mime):
    if not _is_ascii(f, mime):
        return

    m = {
        "\t": 'tsv',
        ',': 'csv',
        '|': 'pipe',
        ';': 'semicolon'
    }

    first = f.readline().rstrip("\n")
    while first.startswith('#'):
        first = f.readline().rstrip("\n")

    second = f.readline().rstrip("\n")
    for d in m:
        c = first.count(d)
        if c == 0:
            continue

        if second.count(d) == c:
            return m[d]

    return False

TESTS = [
    _is_delimited,
    _is_json,
    _is_xml,
]


def get_mimetype(f):
    try:
        ftype = magic.from_file(f, mime=True)
    except AttributeError:
        try:
            mag = magic.open(magic.MAGIC_MIME)
            mag.load()
            ftype = mag.file(f)
        except AttributeError as e:
            raise RuntimeError('unable to detect cached file type')

    if PYVERSION < 3:
        ftype = ftype.decode('utf-8')

    return ftype


def data_type(f, mime=None):
    if not mime:
        mime = get_mimetype(f)

    if isinstance(f, str):
        f = open(f)

    t = None
    for tt in TESTS:
        f.seek(0)
        t = tt(f, mime)
        if t:
            return t

f = sys.argv[1]
if __name__ == "__main__":
    with open(f) as FILE:
        mime_type = magic.from_file(f)
        print(mime_type)

        print(data_type(FILE, mime_type))
