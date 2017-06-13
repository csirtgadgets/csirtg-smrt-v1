import arrow
import datetime
import re
from pprint import pprint
from tzlocal import get_localzone  # pip install tzlocal


def round_time(dt=datetime.datetime.now(), round=60):
    if isinstance(round, str):
        round = int(round)
    
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds+round/2) // round * round
    return dt + datetime.timedelta(0, rounding-seconds, -dt.microsecond)


def _parse_timestamp_syslog(syslog_timestamp):
    """
    Return a timestamp with the correct year and in UTC from a syslog timestamp
    :return: string (ex: 2015-11-11T21:15:29-0000)

    Reference:
    https://github.com/logstash-plugins/logstash-filter-date/pull/4/files
    https://github.com/jsvd/logstash-filter-date/blob/cfd8949e94ed0760434e3c9a9ff3da5351b4fd59/lib/logstash/filters/date.rb#L189
    """

    local_tz = get_localzone()
    time_now = arrow.get(get_localzone())

    # get the current month
    now_month = time_now.month

    # semi normalize syslog timestamp
    syslog_timestamp_obj = arrow.get(syslog_timestamp, ['MMM  D HH:mm:ss', 'MMM D HH:mm:ss'])

    # get the month of the syslog timestamp
    event_month = syslog_timestamp_obj.month

    # calculate event year based on current month and event month
    if event_month == now_month:
        event_year = time_now.year
    elif event_month == 12 and now_month == 1:
        event_year = (time_now.year - 1)
    elif event_month == 1 and now_month == 12:
        event_year = (time_now.year + 1)
    else:
        event_year = time_now.year

    # update event year based on calculated result and local timezone
    syslog_timestamp_obj = syslog_timestamp_obj.replace(year=event_year, tzinfo=local_tz.zone)

    return syslog_timestamp_obj.to('UTC').format('YYYY-MM-DDTHH:mm:ssZ')


def parse_timestamp(ts, syslog=False):
    if syslog:
        return _parse_timestamp_syslog(ts)

    try:
        t = arrow.get(ts)
        if t.year < 1980:
            if type(ts) == datetime.datetime:
                ts = str(ts)
            if len(ts) == 8:
                ts = '{}T00:00:00Z'.format(ts)
                t = arrow.get(ts, 'YYYYMMDDTHH:mm:ss')

            if t.year < 1980:
                raise RuntimeError('invalid timestamp: %s' % ts)

        return t
    except ValueError as e:
        if len(ts) == 14:
            match = re.search('^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$', ts)
            if match:
                ts = '{}-{}-{}T{}:{}:{}Z'.format(match.group(1), match.group(2), match.group(3), match.group(4),
                                                 match.group(5), match.group(6))
                t = arrow.get(ts, 'YYYY-MM-DDTHH:mm:ss')
                return t
            else:
                raise RuntimeError('Invalid Timestamp: %s' % ts)
        else:
            raise RuntimeError('Invalid Timestamp: %s' % ts)
    else:
        raise RuntimeError('Invalid Timestamp: %s' % ts)
