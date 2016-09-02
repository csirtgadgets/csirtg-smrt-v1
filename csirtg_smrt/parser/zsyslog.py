from csirtg_smrt.parser.pattern import Pattern
import re

RE_SYSLOG = '\s|\t'


class _Syslog(Pattern):
    # todo - syslog receiver
    # https://gist.github.com/pklaus/c4c37152e261a9e9331f
    # https://gist.github.com/marcelom/4218010

    def __init__(self, *args, **kwargs):
        super(_Syslog, self).__init__(*args, **kwargs)

        self.pattern = RE_SYSLOG
        self.split = '='


Plugin = _Syslog
