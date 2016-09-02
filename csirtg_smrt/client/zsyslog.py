from csirtg_indicator import Indicator
from csirtg_smrt.client.plugin import Client
import logging
import logging.handlers


class _Syslog(Client):

    __name__ = 'syslog'

    def __init__(self, remote='localhost:514', *args, **kwargs):
        super(_Syslog, self).__init__(remote)

        self.port = 514
        if ':' in self.remote:
            self.remote, self.port = self.remote.split(':')

        self.port = int(self.port)

        self.logger = logging.getLogger('csirtg-smrt')
        self.logger.setLevel(logging.INFO)
        handler = logging.handlers.SysLogHandler(address=(self.remote, self.port))
        self.logger.addHandler(handler)

    def indicators_create(self, data, **kwargs):
        if isinstance(data, dict):
            data = Indicator(**data)

        if isinstance(data, Indicator):
            data = [data]

        for i in data:
            firsttime = i.firsttime
            if firsttime:
                firsttime = firsttime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            lasttime = i.lasttime
            if lasttime:
                lasttime = lasttime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            reporttime = i.reporttime
            if reporttime:
                reporttime = reporttime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            line = "provider={} indicator={} tlp={} firsttime={} lasttime={} reporttime={}".format(
                i.provider,
                i.indicator,
                i.tlp,
                firsttime,
                lasttime,
                reporttime,
            )
            self.logger.info(line)

Plugin = _Syslog
