import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint
import tempfile
from csirtg_smrt.archiver import Archiver
import logging

#logging.basicConfig(level=logging.DEBUG)


def test_smrt_archiver_lasttime():
    tmpfile = tempfile.mktemp()
    archiver = Archiver(dbfile=tmpfile)
    rule = 'test/smrt/rules/archiver.yml'
    feed = 'lasttime'

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) > 0

            f = {i.indicator: i.__dict__() for i in x}
            assert f['216.243.31.2']['lasttime'] == '2016-03-23T20:22:27.000000Z'

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) == 0


def test_smrt_archiver_firsttime():
    tmpfile = tempfile.mktemp()
    archiver = Archiver(dbfile=tmpfile)
    rule = 'test/smrt/rules/archiver.yml'
    feed = 'firsttime'

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) > 0

            f = {i.indicator: i.__dict__() for i in x}
            assert f['216.243.31.2']['lasttime'] == '2016-03-23T20:22:27.000000Z'

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) == 0


def test_smrt_archiver_both():
    tmpfile = tempfile.mktemp()
    archiver = Archiver(dbfile=tmpfile)
    rule = 'test/smrt/rules/archiver.yml'
    feed = 'both'

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) > 0

            f = {i.indicator: i.__dict__() for i in x}
            assert f['216.243.31.2']['lasttime'] == '2016-03-23T20:22:27.000000Z'

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) == 0


def test_smrt_archiver_neither():
    tmpfile = tempfile.mktemp()
    archiver = Archiver(dbfile=tmpfile)
    rule = 'test/smrt/rules/archiver.yml'
    feed = 'neither'

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) > 0

            f = {i.indicator: i.__dict__() for i in x}
            
            assert f['216.243.31.2'].get('lasttime') is None

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) == 0


def test_smrt_archiver_lasttime_clear():
    tmpfile = tempfile.mktemp()
    archiver = Archiver(dbfile=tmpfile)
    rule = 'test/smrt/rules/archiver.yml'
    feed = 'lasttime'

    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) > 0

            f = {i.indicator: i.__dict__() for i in x}
            assert f['216.243.31.2']['lasttime'] == '2016-03-23T20:22:27.000000Z'

    archiver.clear_memcache()
    with Smrt(REMOTE_ADDR, 1234, client='stdout', archiver=archiver) as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds(rule, feed=feed):
            x = list(s.process(r, f))
            assert len(x) == 0