from datetime import datetime


# DevelNote: need to pass in localtz now

class WindowsTime:
    """Convert the Windows time in 100 nanosecond intervals since Jan 1, 1601 to time in seconds since Jan 1, 1970"""

    def __init__(self, low, high, localtz):
        self.low = long(low)
        self.high = long(high)

        if (low == 0) and (high == 0):
            self.dt = 0
            self.dtstr = "Not defined"
            self.unixtime = 0
            return

        # Windows NT time is specified as the number of 100 nanosecond intervals since January 1, 1601.
        # UNIX time is specified as the number of seconds since January 1, 1970.
        # There are 134,774 days (or 11,644,473,600 seconds) between these dates.
        self.unixtime = self.get_unix_time()

        try:
            if localtz:
                self.dt = datetime.fromtimestamp(self.unixtime)
            else:
                self.dt = datetime.utcfromtimestamp(self.unixtime)

            # Pass isoformat a delimiter if you don't like the default "T".
            self.dtstr = self.dt.isoformat(' ')

        except:
            self.dt = 0
            self.dtstr = "Invalid timestamp"
            self.unixtime = 0

    def get_unix_time(self):
        t = float(self.high) * 2 ** 32 + self.low

        # The '//' does a floor on the float value, where *1e-7 does not, resulting in an off by one second error
        # However, doing the floor loses the usecs....
        return t * 1e-7 - 11644473600
        # return((t//10000000)-11644473600)


def hexdump(chars, sep, width):
    while chars:
        line = chars[:width]
        chars = chars[width:]
        line = line.ljust(width, '\000')
        print "%s%s%s" % (sep.join("%02x" % ord(c) for c in line),
                          sep, quotechars(line))


def quotechars(chars):
    return ''.join(['.', c][c.isalnum()] for c in chars)
