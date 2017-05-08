from csirtg_smrt.parser.delim import Delim
import re


class Tsv(Delim):

    def __init__(self, *args, **kwargs):
        super(Tsv, self).__init__(*args, **kwargs)

        self.pattern = re.compile("\t+")

Plugin = Tsv
