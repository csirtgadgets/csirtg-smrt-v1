from csirtg_smrt.utils.zcontent import get_type
import os.path

T = {
    'test.csv': 'csv',
    'test.rss': 'rss',
    'test.json': 'json',
    'test.tsv': 'tsv',
    'test.xml': 'xml',
}


def test_smrt_utils():
    for t in T:
        p = ['test', 'utils', t]
        p = os.path.join(*p)
        assert T[t] == get_type(p)
