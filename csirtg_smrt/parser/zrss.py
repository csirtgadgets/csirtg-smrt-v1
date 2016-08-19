import copy
import re

import feedparser
from pprint import pprint
from csirtg_smrt.parser import Parser
from csirtg_indicator.utils import normalize_itype
from csirtg_indicator import Indicator
from csirtg_indicator.exceptions import InvalidIndicator
from csirtg_smrt.constants import PYVERSION
from csirtg_smrt.utils.znltk import text_to_list
from csirtg_indicator.utils import normalize_itype, _normalize_url


class Rss(Parser):

    def __init__(self, *args, **kwargs):
        super(Rss, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()

        feed = []
        for l in self.fetcher.process():
            feed.append(l)

        feed = "\n".join(feed)
        try:
            feed = feedparser.parse(feed)
        except Exception as e:
            self.logger.error('Error parsing feed: {}'.format(e))
            self.logger.error(defaults['remote'])
            raise e

        patterns = False
        nltk = False
        if self.rule.feeds[self.feed].get('pattern'):
            patterns = copy.deepcopy(self.rule.feeds[self.feed]['pattern'])
            for p in patterns:
                patterns[p]['pattern'] = re.compile(patterns[p]['pattern'])
        else:
            nltk = True

        rv = []
        for e in feed.entries:
            i = copy.deepcopy(defaults)

            if patterns:
                for k in e:
                    if k == 'summary' and patterns.get('description'):
                        try:
                            m = patterns['description']['pattern'].search(e[k]).groups()
                        except AttributeError:
                            continue
                        for idx, c in enumerate(patterns['description']['values']):
                            i[c] = m[idx]
                    elif patterns.get(k):
                        try:
                            m = patterns[k]['pattern'].search(e[k]).groups()
                        except AttributeError:
                            continue
                        for idx, c in enumerate(patterns[k]['values']):
                            i[c] = m[idx]
            else:
                from bs4 import BeautifulSoup
                import enchant
                from nltk.corpus import words
                #d = enchant.Dict('en_US')
                from nltk.tokenize import wordpunct_tokenize, regexp_span_tokenize, word_tokenize, regexp
                soup = BeautifulSoup(e['summary'], 'html.parser')
                soup = soup.get_text()
                soup = soup.split(' ')
                for w in soup:
                    if len(w) < 4:
                        print('skipping %s' % w)
                        continue

                    if w.lower() in words.words():
                        print('skipping ' + w)
                        continue

                    ww = {}
                    ww['indicator'] = w
                    try:
                        pprint(w)
                        w = _normalize_url(ww)
                        pprint(w)
                    except InvalidIndicator:
                        pass

            # if not i.get('indicator'):
            #     self.logger.error('missing indicator: {}'.format(e[k]))
            #     continue
            #
            # try:
            #     i = normalize_itype(i)
            #     pprint(i)
            #     i = Indicator(**i)
            #     self.logger.debug(i)
            #     r = self.client.indicators_create(i)
            #     rv.append(r)
            # except InvalidIndicator as e:
            #     self.logger.error(e)
            #     self.logger.info('skipping: {}'.format(i['indicator']))
        return rv

Plugin = Rss