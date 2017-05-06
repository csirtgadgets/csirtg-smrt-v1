import socket
from csirtg_smrt.utils.zarrow import parse_timestamp
from csirtg_indicator.utils import resolve_itype
from csirtg_indicator import Indicator
from pprint import pprint
from csirtg_smrt.constants import PYVERSION

if PYVERSION >= 3:
    basestring = (str, bytes)


def is_timestamp(s):
    try:
        t = parse_timestamp(s)
        return t
    except Exception:
        pass


def get_indicator(l):
    i = {}

    # step 1, detect datatypes
    for e in l:
        if isinstance(e, int):
            i[e] = 'int'
            continue

        t = None
        try:
            t = resolve_itype(e)
            if t:
                i[e] = 'indicator'
                continue
        except Exception:
            pass

        if is_timestamp(e):
            i[e] = 'timestamp'
            continue

        if isinstance(e, basestring):
            i[e] = 'string'

    i2 = Indicator()
    timestamps = []
    ports = []

    for e in i:
        if i[e] == 'indicator':
            i2.indicator = e
            continue

        if i[e] == 'timestamp':
            timestamps.append(e)
            continue

        if i[e] == 'int':
            ports.append(e)
            continue

        if i[e] == 'string':
            if ' ' in e:
                i2.description = e
                continue

            if len(e) < 10:
                i2.tags = [e]
                continue

    timestamps = sorted(timestamps, reverse=True)

    if len(timestamps) > 0:
        i2.lasttime = timestamps[0]

    if len(timestamps) > 1:
        i2.firsttime = timestamps[1]

    if len(ports) > 0:
        if len(ports) == 1:
            i2.portlist = ports[0]
        else:
            if ports[0] > ports[1]:
                i2.portlist = ports[0]
                i2.dest_portlist = ports[1]
            else:
                i2.portlist = ports[1]
                i2.dest_portlist = ports[0]

    return i2


def main():
    i = ['192.168.1.1', '2015-02-28T00:00:00Z', 'scanner', '2015-02-28T01:00:00Z', 1159, 2293]
    i2 = get_indicator(i)
    print(i2)

if __name__ == "__main__":
    main()