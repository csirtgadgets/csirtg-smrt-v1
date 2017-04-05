from csirtg_smrt.parser.ufw import parse_line


def test_ufw():
    file = 'test/ufw/ufw.log'

    events = []
    with open(file) as f:
        for l in f.read().split("\n"):
            i = parse_line(l)

            events.append(i)

    assert len(events) > 0
    assert events[0]['indicator'] == '114.33.197.193'


def test_ufw_ubuntu16():
    file = 'test/ufw/ufw_ubuntu16.log'

    events = []
    with open(file) as f:
        for l in f.read().split("\n"):
            i = parse_line(l)

            events.append(i)

    assert len(events) > 0
    assert events[0]['indicator'] == '10.0.2.2'
    assert events[1]['indicator'] == '61.7.190.140'
