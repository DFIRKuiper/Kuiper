import json
import datetime
import struct
DATETIME_FORMAT = u'{0.year:04d}-{0.month:02d}-{0.day:02d} '\
    u'{0.hour:02d}:{0.minute:02d}:{0.second:02d}'


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return DATETIME_FORMAT.format(obj)
        if isinstance(obj, bytes):
            return obj.decode('ascii', 'ignore')
        return json.JSONEncoder.default(
            self, obj
        )

def convert_datetime(date_value):
    if type(date_value) == bytes:
        date_value = struct.unpack("Q", date_value)[0]
    if date_value < 0:
        return None

    micro_secs, _ = divmod(date_value, 10)
    time_delta = datetime.timedelta(
        microseconds=micro_secs
    )

    orig_datetime = datetime.datetime(1601, 1, 1)
    new_datetime = orig_datetime + time_delta
    return new_datetime.isoformat()

def from_fat(fat):
    """Convert an MS-DOS wFatDate wFatTime timestamp to a date"""
    try:
        byte_swap = [fat[i:i+2] for i in range(0, len(fat), 2)]
        to_le = byte_swap[1]+byte_swap[0]+byte_swap[3]+byte_swap[2]
        binary_conv = int(to_le, 16)
        binary = '{0:032b}'.format(binary_conv)
        stamp = [binary[:7], binary[7:11], binary[11:16], binary[16:21], binary[21:27], binary[27:32]]
        for binary in stamp[:]:
            dec = int(binary, 2)
            stamp.remove(binary)
            stamp.append(dec)
        stamp[0] = stamp[0] + 1980
        stamp[5] = stamp[5] * 2
        dt_obj = datetime.datetime(stamp[0], stamp[1], stamp[2], stamp[3], stamp[4], stamp[5])
        return dt_obj.strftime('%Y-%m-%dT%H:%M:%S.%f')
    except Exception as e:
        return None
    

def strip_control_characters(input):
    if input:
        import re
        # unicode invalid characters
        RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                         u'|' + \
                         u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                          (chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff),
                           chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff),
                           chr(0xd800),chr(0xdbff),chr(0xdc00),chr(0xdfff),
                           )
        input = re.sub(RE_XML_ILLEGAL, "", input)
        # ascii control characters
        input = re.sub(r"[\x01-\x1F\x7F]", "", input)
    return input
