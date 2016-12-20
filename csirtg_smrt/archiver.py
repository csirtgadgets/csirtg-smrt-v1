try:
    import sqlalchemy
except ImportError:
    raise ImportError('Requires sqlalchemy')

import logging
import os
import arrow
from sqlalchemy import Column, Integer, create_engine, DateTime, UnicodeText, Text, desc, asc
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

    def clear_memcache(self):
        self.memcache = {}
        self.memcached_provider = None

    def cache_provider(self, provider):
        if self.memcached_provider == provider:
            return

        self.memcached_provider = provider
        self.memcache = {}
        logger.info("Caching archived indicators for provider {}".format(provider))
        q = self.handle().query(Indicator) \
            .filter_by(provider=provider) \
            .order_by(asc(Indicator.lasttime), asc(Indicator.firsttime), asc(Indicator.created_at))

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

        # Is there any cached record?
        if indicator.indicator not in self.memcache:
            return False

        (ex_group, ex_tags, ex_ft, ex_lt) = self.memcache[indicator.indicator]
        
        # Is the indicator or tags different?
        if (ex_group, ex_tags) != (indicator.group, tags):
            return False

        timestamp_comparisons = (
            (ex_ft, indicator.firsttime),
            (ex_lt, indicator.lasttime),
        )

        for existing_ts, indicator_ts in timestamp_comparisons:
            # If the new indicator does not have this ts, ignore it
            if indicator_ts is None:
                continue
            # Cache has no old ts, but there is a new one, so we are out of date
            if existing_ts is None:
                return False
            # otherwise, compare timestamps to see if we are out of date
            if indicator_ts.replace(tzinfo=None) > existing_ts.replace(tzinfo=None):
                return False

        # If we made it here, the cached indicator is >= to the one in the feed.
        return True

    def create(self, indicator):
        tags = indicator.tags
        if isinstance(indicator.tags, list):
            indicator.tags.sort()
            tags = ','.join(indicator.tags)

        i = indicator.indicator
        if PYVERSION == 2:
            if isinstance(i, str):
                i = unicode(i)

        i = Indicator(indicator=i, provider=indicator.provider, group=indicator.group,
                      lasttime=indicator.lasttime, tags=tags, firsttime=indicator.firsttime)

        s = self.begin()
        s.add(i)
        s.commit()

        firsttime = None
        if indicator.firsttime:
            firsttime = indicator.firsttime.replace(tzinfo=None)

        lasttime = None
        if indicator.lasttime:
            lasttime = indicator.lasttime.replace(tzinfo=None)

        self.memcache[indicator.indicator] = (
            indicator.group,
            tags,
            firsttime,
            lasttime
        )

        return i.id

    def cleanup(self, days=180):
        date = arrow.utcnow()
        date = date.replace(days=-days)

        s = self.handle()
        count = s.query(Indicator).filter(Indicator.created_at < date.datetime).delete()
        s.commit()

        return count
