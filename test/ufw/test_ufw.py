from csirtg_smrt.ufw import process_events


def test_ufw():
    file = 'test/ufw/ufw.log'

    events = []
    with open(file) as f:
        for l in f.read().split("\n"):
            i = process_events([l])
            events.append(i[0])

    assert len(events) > 0
    assert events[0].indicator == '114.33.197.193'
