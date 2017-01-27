from zipfile import ZipFile
from csirtg_smrt.constants import PYVERSION


def get_lines(file, split="\n"):
    with ZipFile(file) as f:
        for m in f.infolist():
            if PYVERSION == 2:
                for l in f.read(m.filename).split(split):
                    yield l
            else:
                with f.open(m.filename) as zip:
                    for l in zip.readlines():
                        yield l
