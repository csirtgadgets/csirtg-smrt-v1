import logging
import os

import arrow
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine, DateTime, UnicodeText, \
    Text, Boolean, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref, class_mapper, scoped_session

from cifsdk.constants import RUNTIME_PATH
from cif.store.plugin import Store
import json
from cifsdk.exceptions import AuthError
from cifsdk.constants import PYVERSION
from pprint import pprint

DB_FILE = os.path.join(RUNTIME_PATH, 'cif.sqlite')
Base = declarative_base()

from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.sql.expression import func

if PYVERSION > 2:
    basestring = (str, bytes)

logger = logging.getLogger(__name__)


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True)
    indicator = Column(UnicodeText)
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

        Base.metadata.create_all(self.engine)

        logger.debug('database path: {}'.format(self.path))

    def search(self, indicator, provider, group, tags, firsttime=None, lasttime=None):
        if isinstance(tags, list):
            tags.sort()
            tags = ','.join(tags)

        rv = self.handle().query(Indicator).filter_by(indicator=indicator, provider=provider, group=group, tags=tags)

        if firsttime:
            rv = rv.filter_by(firsttime=firsttime)

        if lasttime:
            rv = rv.filter_by(lasttime=lasttime)

        return rv.count()

    def create(self, indicator, provider, group, tags, firsttime=None, lasttime=None):
        if isinstance(tags, list):
            tags.sort()
            tags = ','.join(tags)

        i = Indicator(indicator=indicator, provider=provider, group=group, lasttime=lasttime, tags=tags,
                      firsttime=firsttime)

        s = self.handle()
        s.add(i)
        s.commit()

        logger.debug(i)

        return i.id

    def cleanup(self, days=180):
        date = arrow.utcnow()
        date = date.replace(days=-days)

        s = self.handle()

        count = 0
        rv = s.query(Indicator).filter(Indicator.created_at < date.datetime)
        if rv.count():
            count = rv.count()
            rv.delete()
            s.commit()

        return count
