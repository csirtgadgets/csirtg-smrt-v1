from csirtg_smrt.parser.delim import Delim
import re


class Semicolon(Delim):

    def __init__(self, *args, **kwargs):
        super(Semicolon, self).__init__(*args, **kwargs)

        self.pattern = re.compile('[\s+]?;[\s+]?')


Plugin = Semicolon
