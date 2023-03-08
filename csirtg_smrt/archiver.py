try:
    import sqlalchemy
except ImportError:
    raise ImportError('Requires sqlalchemy')

import logging
import os
import arrow
from sqlalchemy import Column, Integer, create_engine, DateTime, UnicodeText, Text, desc, asc, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, load_only
from sqlalchemy import event
from sqlalchemy.engine import Engine
from csirtg_smrt.constants import PYVERSION, CACHE_PATH
from sqlalchemy.sql.expression import func
from contextlib import contextmanager
from pprint import pprint

TRACE = os.environ.get('CSIRTG_SMRT_SQLITE_TRACE')
CLEANUP_DAYS = os.getenv('CSIRTG_SMRT_ARCHIVER_CLEANUP_DAYS', 60)

DB_FILE = os.path.join(CACHE_PATH, 'smrt.db')
Base = declarative_base()

if PYVERSION > 2:
    basestring = (str, bytes)

logger = logging.getLogger(__name__)

if not TRACE:
    logger.setLevel(logging.ERROR)

# http://stackoverflow.com/q/9671490/7205341
SYNC = os.environ.get('SMRT_SQLITE_SYNC', 'NORMAL')

# https://www.sqlite.org/pragma.html#pragma_cache_size
CACHE_SIZE = os.environ.get('SMRT_SQLITE_CACHE_SIZE', 512000000)  # 512MB

AUTO_VACUUM = True
if os.getenv('SMRT_SQLITE_AUTO_VACUUM', '1') == '0':
    AUTO_VACUUM = False

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout = 5000")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA wal_autocheckpoint = 0")
    cursor.execute("PRAGMA synchronous = {}".format(SYNC))
    cursor.execute("PRAGMA temp_store = MEMORY")
    cursor.execute("PRAGMA cache_size = {}".format(CACHE_SIZE))

    if AUTO_VACUUM:
        cursor.execute("PRAGMA auto_vacuum = INCREMENTAL")

    cursor.close()

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

        if isinstance(group, list):
            self.group = group[0]

        if isinstance(self.tags, list):
            self.tags.sort()
            self.tags = ','.join(self.tags)

        if self.lasttime and isinstance(self.lasttime, basestring):
            self.lasttime = arrow.get(self.lasttime).datetime

        if self.firsttime and isinstance(self.firsttime, basestring):
            self.firsttime = arrow.get(self.firsttime).datetime

SELECTED_FIELDS = {"indicator", "group", "tags", "firsttime", "lasttime"}
SELECTED_FIELDS = [getattr(Indicator, f) for f in SELECTED_FIELDS]

# http://www.pythoncentral.io/sqlalchemy-orm-examples/
class Archiver(object):
    def __init__(self, dbfile=DB_FILE, autocommit=False, dictrows=True, **kwargs):

        self.dbfile = dbfile
        self.autocommit = autocommit
        self.dictrows = dictrows
        self.path = "sqlite:///{0}".format(self.dbfile)

        echo = False
        if TRACE:
            echo = True

        try:
            if self.engine is not None:
                self.engine.dispose()
        except AttributeError:
            pass

        # http://docs.sqlalchemy.org/en/latest/orm/contextual.html
        self.engine = create_engine(self.path, echo=echo)
        self.get_session = scoped_session(sessionmaker(bind=self.engine))
        self._session = None
        self._tx_count = 0

        Base.metadata.create_all(self.engine)

        logger.debug('database path: {}'.format(self.path))

        self.clear_memcache()

    @contextmanager
    def session_scope(self, *, session=None):
        """Provide a transactional scope around a series of operations."""
        if session is None:
            raise RuntimeError('Session required')

        try:
            yield session
            session.commit()
        except Exception as err:  # pylint: disable=broad-except
            logger.error("Error executing query: {}".format(err))
            session.rollback()
            raise
        finally:
            session.close()
    
    def begin(self):
        self._tx_count += 1
        if self._session:
            return self._session

        self._session = self.get_session()
        return self._session

    def commit(self):
        if self._tx_count == 0:
            raise Exception("commit outside of transaction")
        self._tx_count -= 1
        if self._tx_count == 0:
            self._session.commit()
            self._session = None

    def clear_memcache(self):
        self.memcache = {}
        self.memcached_provider = None

    def _cache_provider(self, provider):
        if self.memcached_provider == provider:
            return

        self.memcached_provider = provider
        self.memcache = {}
        logger.info("Caching archived indicators for provider {}".format(provider))
        with self.session_scope(session=self.get_session()) as session:
            q = session.query(Indicator) \
                .filter_by(provider=provider) \
                .order_by(Indicator.lasttime.desc(), Indicator.firsttime.desc(), Indicator.created_at.desc())

            q = q.options(load_only(*SELECTED_FIELDS))
            q = q.yield_per(1000)
            for i in q:
                if i.indicator not in self.memcache:
                    self.memcache[i.indicator] = (i.group, i.tags, i.firsttime, i.lasttime)

            logger.info("Cached provider {} in memory, {} objects".format(provider, len(self.memcache)))

    def search(self, indicator):
        tags = indicator.tags
        if isinstance(tags, list):
            tags.sort()
            tags = ','.join(tags)

        self._cache_provider(indicator.provider)

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

        with self.session_scope(session=self.get_session()) as session:
            session.add(i)
            session.flush()
            session.expunge(i)

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

    def cleanup(self, days=CLEANUP_DAYS):
        days = int(days)
        date = arrow.utcnow()
        indicator_date = date.shift(days=-days)
        count = 0

        with self.session_scope(session=self.get_session()) as session:
            count = session.query(Indicator) \
                .filter(Indicator.created_at < indicator_date.datetime).delete()

        if AUTO_VACUUM:
            logger.info('running database vacuum')
            with self.engine.connect() as conn:
                conn.execute(text('PRAGMA incremental_vacuum'))
                conn.execute(text('VACUUM'))

        with self.engine.connect() as conn:
            conn.execute(text('PRAGMA optimize'))

        self.engine.dispose()
        self.engine = None
        self.get_session = None

        return count

class NOOPArchiver:
    def __init__(self, *args, **kwargs):
        pass

    def begin(self):
        pass

    def commit(self):
        pass

    def clear_memcache(self):
        pass

    def search(self, indicator):
        return False

    def create(self, indicator):
        pass

    def cleanup(self, days=180):
        return 0
    def session_scope(self, *, session=None):
        pass
