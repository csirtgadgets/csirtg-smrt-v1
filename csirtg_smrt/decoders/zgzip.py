import gzip


def get_lines(file, split="\n"):

    with gzip.open(file, 'rb') as f:
        for l in f:
            yield l
