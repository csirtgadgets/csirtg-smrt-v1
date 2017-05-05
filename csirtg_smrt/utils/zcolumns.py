import socket
from csirtg_smrt.utils.zarrow import parse_timestamp
from csirtg_indicator.utils import resolve_itype
from csirtg_indicator import Indicator
from pprint import pprint


def is_timestamp(s):
    t = False
    try:
        t = parse_timestamp(s)
        return t
    except Exception:
        pass

    return t


def is_reporttime(s):
    pass


def detect(l):
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

        if isinstance(e, str):
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
                i2.tags = e
                continue

    timestamps = sorted(timestamps, reverse=True)

    if len(timestamps) > 0:
        i2.lasttime = timestamps[0]

    if len(timestamps) > 1:
        i2.firsttime = timestamps[1]


    # TODO! double check this
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

    pprint(i2)

    # id sub-datatype
        # reporttime vs lasttime vs firsttime
        # src port, dest port
        # tag vs description

    pass

import sys
def main():
    i = ['192.168.1.1', '2015-02-28T00:00:00Z', 'scanner', '2015-02-28T01:00:00Z', 1159, 2293]
    detect(i)

if __name__ == "__main__":
    main()