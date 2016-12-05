try:
    import sqlalchemy
except ImportError:
    raise ImportError('Requires sqlalchemy')

import logging
import os
import arrow
from sqlalchemy import Column, Integer, create_engine, DateTime, UnicodeText, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, load_only
from csirtg_smrt.constants import PYVERSION, RUNTIME_PATH
from sqlalchemy.sql.expression import func
from pprint import pprint

DB_FILE = os.path.join(RUNTIME_PATH, 'smrt.db')
Base = declarative_base()

if PYVERSION > 2:
    basestring = (str, bytes)

logger = logging.getLogger(__name__)


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True)
    indicator = Column(UnicodeText, index=True)
    group = Column(Text)
    provider = Column(Text)
    firsttime = Column(DateTime)
    lasttime = Column(DateTime)
    tags = Column(Text)
    created_at = Column(DateTime, default=func.now())

    def __init__(self, indicator=None, group='everyone', provider=None, firsttime=None, lasttime=None, tags=None):

        self.indicator = indicator
        self.group = group
        self.provider = provider
        self.firsttime = firsttime
        self.lasttime = lasttime
        self.tags = tags

        if isinstance(self.tags, list):
            self.tags.sort()
            self.tags = ','.join(self.tags)

        if self.lasttime and isinstance(self.lasttime, basestring):
            self.lasttime = arrow.get(self.lasttime).datetime

        if self.firsttime and isinstance(self.firsttime, basestring):
            self.firsttime = arrow.get(self.firsttime).datetime


# http://www.pythoncentral.io/sqlalchemy-orm-examples/
class Archiver(object):
    def __init__(self, dbfile=DB_FILE, autocommit=False, dictrows=True, **kwargs):

        self.dbfile = dbfile
        self.autocommit = autocommit
        self.dictrows = dictrows
        self.path = "sqlite:///{0}".format(self.dbfile)

        echo = False

        #if logger.getEffectiveLevel() == logging.DEBUG:
        #   echo = True

        # http://docs.sqlalchemy.org/en/latest/orm/contextual.html
        self.engine = create_engine(self.path, echo=echo)
        self.handle = sessionmaker(bind=self.engine)
        self.handle = scoped_session(self.handle)
        self._session = None

        Base.metadata.create_all(self.engine)

        logger.debug('database path: {}'.format(self.path))

        self.clear_memcache()

    def begin(self):
        if self._session:
            self._session.begin(subtransactions=True)
            return self._session

        self._session = self.handle()
        return self._session

    def commit(self):
        self._session.commit()
        self.session = None
        self.clear_memcache()

    def clear_memcache(self):
        self.memcache = {}
        self.memcached_provider = None

    def cache_provider(self, provider):
        if self.memcached_provider == provider:
            return

        self.memcached_provider = provider
        logger.info("Caching archived indicators for provider {}".format(provider))
        q = self.handle().query(Indicator).filter_by(provider=provider)
        q = q.options(load_only("indicator", "group", "tags", "firsttime", "lasttime"))
        q = q.yield_per(1000)
        for i in q:
            self.memcache[i.indicator] = (i.group, i.tags, i.firsttime, i.lasttime)
        logger.info("Cached provider {} in memory, {} objects".format(provider, len(self.memcache)))

    def search(self, indicator):
        tags = indicator.tags
        if isinstance(tags, list):
            tags.sort()
            tags = ','.join(tags)

        self.cache_provider(indicator.provider)

        if indicator.indicator not in self.memcache:
            return False

        existing = self.memcache[indicator.indicator]
        existing_compare = [existing[0], existing[1]]  # group and tags
        
        new_compare = [indicator.group, tags]
        if indicator.firsttime:
            existing_compare.append(existing[2])
            new_compare.append(indicator.firsttime.replace(tzinfo=None))

        if indicator.lasttime:
            existing_compare.append(existing[3])
            new_compare.append(indicator.lasttime.replace(tzinfo=None))

        return existing_compare == new_compare

    def create(self, indicator):
        tags = indicator.tags
        if isinstance(indicator.tags, list):
            indicator.tags.sort()
            tags = ','.join(indicator.tags)

        i = Indicator(indicator=indicator.indicator, provider=indicator.provider, group=indicator.group,
                      lasttime=indicator.lasttime, tags=tags, firsttime=indicator.firsttime)

        s = self.begin()
        s.add(i)
        s.commit()
        if self.memcache:
            self.memcache[indicator] = (indicator.group, tags, indicator.firsttime, indicator.lasttime)

        return i.id

    def cleanup(self, days=180):
        date = arrow.utcnow()
        date = date.replace(days=-days)

        s = self.handle()
        count = s.query(Indicator).filter(Indicator.created_at < date.datetime).delete()
        s.commit()

        return count
