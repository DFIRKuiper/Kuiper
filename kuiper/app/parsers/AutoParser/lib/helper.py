import json
import datetime
import struct
DATETIME_FORMAT = u'{0.year:04d}-{0.month:02d}-{0.day:02d} '\
    u'{0.hour:02d}:{0.minute:02d}:{0.second:02d}'


#this function has been taken from https://github.com/forensicmatt/LogicalRegTool/blob/master/lib/JsonDecoder.py
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return DATETIME_FORMAT.format(obj)
        if isinstance(obj, bytes):
            return obj.decode('ascii', 'ignore')
        return json.JSONEncoder.default(
            self, obj
        )

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
