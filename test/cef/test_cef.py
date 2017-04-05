from csirtg_smrt.parser.cef import parse_line


def test_cef():
    file = 'test/cef/cef.log'

    events = []
    with open(file) as f:
        for l in f.read().split("\n"):
            i = parse_line(l)
            events.append(i)

    assert len(events) > 0
    assert events[0]['indicator'] == '113.195.145.52'
