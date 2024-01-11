import sys
import struct
import logging
import datetime
import binascii
import six

g_logger = logging.getLogger("BinaryParser")


def dosdate(dosdate, dostime):
    """
    `dosdate`: 2 bytes, little endian.
    `dostime`: 2 bytes, little endian.
    returns: datetime.datetime or datetime.datetime.min on error
    """
    try:
        t = ord(dosdate[1]) << 8
        t |= ord(dosdate[0])
        day = t & 0b0000000000011111
        month = (t & 0b0000000111100000) >> 5
        year = (t & 0b1111111000000000) >> 9
        year += 1980

        t = ord(dostime[1]) << 8
        t |= ord(dostime[0])
        sec = t & 0b0000000000011111
        sec *= 2
        minute = (t & 0b0000011111100000) >> 5
        hour = (t & 0b1111100000000000) >> 11

        return datetime.datetime(year, month, day, hour, minute, sec)
    except:
        return datetime.datetime.min


def align(offset, alignment):
    """
    Return the offset aligned to the nearest greater given alignment
    Arguments:
    - `offset`: An integer
    - `alignment`: An integer
    """
    if offset % alignment == 0:
        return offset
    return offset + (alignment - (offset % alignment))


class ParseException(Exception):
    """
    An exception to be thrown during parsing, such as
    when an invalid header is encountered.
    """
    def __init__(self, value):
        """
        Constructor.
        Arguments:
        - `value`: A string description.
        """
        super(ParseException, self).__init__(value)

    def __str__(self):
        return str(unicode(self))

    def __unicode__(self):
        return u"Parse Exception(%s)" % (self._value)


class OverrunBufferException(ParseException):
    """
    An exception to be thrown during parsing when something is unpack into
    or from a location beyond the boundaries of a buffer.
    """
    def __init__(self, readOffs, bufLen):
        tvalue = "read: %s, buffer length: %s" % (hex(readOffs), hex(bufLen))
        super(ParseException, self).__init__(tvalue)

    def __str__(self):
        return str(unicode(self))

    def __unicode__(self):
        return u"Tried to parse beyond the end of the file (%s)" % (self._value)


class Block(object):
    """
    Base class for structured blocks used in parsing.
    A block is associated with a offset into a byte-string.
    """
    def __init__(self, buf, offset, parent):
        """
        Constructor.
        Arguments:
        - `buf`: Byte string containing binary data.
        - `offset`: The offset into the buffer at which the block starts.
        - `parent`: The parent block, which links to this block.
        """
        self._buf = buf
        self._offset = offset
        self._parent = parent

    def __unicode__(self):
        return u"BLOCK @ %s." % (hex(self.offset()))

    def __str__(self):
        return str(unicode(self))

    def _prepare_fields(self, fields=False):
        """
        Declaratively add fields to this block.
        self._fields should contain a list of tuples ("type", "name", offset).
        This method will dynamically add corresponding offset and unpacker methods
          to this block.
        Arguments:
        - `fields`: (Optional) A list of tuples to add. Otherwise,
            self._fields is used.
        """
        for field in fields:
            def handler():
                f = getattr(self, "unpack_" + field[0])
                return f(*(field[2:]))
            setattr(self, field[1], handler)
            debug_payload = handler()
            if isinstance(debug_payload, six.text_type):
                debug_payload = debug_payload.encode('utf8')
            else:
                debug_payload = str(debug_payload)
            debug_payload = binascii.hexlify(debug_payload)
            g_logger.debug("(%s) %s\t@ %s\t: %s" % (field[0].upper(),
                                         field[1],
                                         hex(self.absolute_offset(field[2])),
                                         debug_payload))
            setattr(self, "_off_" + field[1], field[2])

    def declare_field(self, type, name, offset, length=False):
        """
        A shortcut to add a field.
        Arguments:
        - `type`: A string. Should be one of the unpack_* types.
        - `name`: A string.
        - `offset`: A number.
        - `length`: (Optional) A number.
        """
        if length:
            self._prepare_fields([(type, name, offset, length)])
        else:
            self._prepare_fields([(type, name, offset)])

    def unpack_byte(self, offset):
        """
        Returns a little-endian unsigned byte from the relative offset.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        Throws:
        - `OverrunBufferException`
        """
        o = self._offset + offset
        try:
            return struct.unpack_from("<B", self._buf, o)[0]
        except struct.error:
            raise OverrunBufferException(o, len(self._buf))

    def unpack_word(self, offset):
        """
        Returns a little-endian WORD (2 bytes) from the relative offset.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        Throws:
        - `OverrunBufferException`
        """
        o = self._offset + offset
        try:
            return struct.unpack_from("<H", self._buf, o)[0]
        except struct.error:
            raise OverrunBufferException(o, len(self._buf))

    def pack_word(self, offset, word):
        """
        Applies the little-endian WORD (2 bytes) to the relative offset.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        - `word`: The data to apply.
        """
        o = self._offset + offset
        return struct.pack_into("<H", self._buf, o, word)

    def unpack_dword(self, offset):
        """
        Returns a little-endian DWORD (4 bytes) from the relative offset.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        Throws:
        - `OverrunBufferException`
        """
        o = self._offset + offset
        try:
            return struct.unpack_from("<I", self._buf, o)[0]
        except struct.error:
            raise OverrunBufferException(o, len(self._buf))

    def unpack_int(self, offset):
        """
        Returns a little-endian signed integer (4 bytes) from the relative offset.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        Throws:
        - `OverrunBufferException`
        """
        o = self._offset + offset
        try:
            return struct.unpack_from("<i", self._buf, o)[0]
        except struct.error:
            raise OverrunBufferException(o, len(self._buf))

    def unpack_qword(self, offset):
        """
        Returns a little-endian QWORD (8 bytes) from the relative offset.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        Throws:
        - `OverrunBufferException`
        """
        o = self._offset + offset
        try:
            return struct.unpack_from("<Q", self._buf, o)[0]
        except struct.error:
            raise OverrunBufferException(o, len(self._buf))

    def unpack_string(self, offset, length=False):
        """
        Returns a string from the relative offset with the given length.
        The string does not include the final NULL character.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        - `length`: (Optional) The length of the string. If no length is provided,
                       the string runs until a NULL.
        Throws:
        - `OverrunBufferException`
        - `IndexError`
        """
        o = self._offset + offset

        if not length:
            end = self._buf.find("\x00", o)
            length = end - o

        try:
            return struct.unpack_from("<%ds" % (length), self._buf, o)[0].partition("\x00")[0]
        except struct.error:
            raise OverrunBufferException(o, len(self._buf))

    def unpack_wstring(self, offset, ilength=False):
        """
        Returns a UTF-16 decoded string from the relative offset with
        the given length, where each character is a wchar (2 bytes).
        The string does not include the final
        NULL character.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        - `length`: (Optional) The length of the string. If no length is provided,
                       the string runs until a double NULL.
        Throws:
        - `UnicodeDecodeError`
        - `IndexError`
        """

        raw_bytes = self._buf[self._offset + offset:]

        # Trim to specified length
        if ilength:
            raw_bytes = raw_bytes[:ilength]

        # Ensure raw_bytes is even-length
        if len(raw_bytes) % 2:
            raw_bytes = raw_bytes[:-1]
        try:
            index = [raw_bytes[i:i + 2] for i in range(0, len(raw_bytes), 2)].index('\x00\x00')
            raw_bytes = raw_bytes[:index * 2]
        except ValueError:
            pass
        return raw_bytes.decode("utf-16-le")

    def unpack_dosdate(self, offset):
        """
        Returns a datetime from the DOSDATE and DOSTIME starting at
        the relative offset.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        Throws:
        - `OverrunBufferException`
        """
        try:
            o = self._offset + offset
            return dosdate(self._buf[o:o + 2], self._buf[o + 2:o + 4])
        except struct.error:
            raise OverrunBufferException(o, len(self._buf))

    def unpack_guid(self, offset):
        """
        Returns a string containing a GUID starting at the relative offset.
        Arguments:
        - `offset`: The relative offset from the start of the block.
        Throws:
        - `OverrunBufferException`
        """
        o = self._offset + offset

        try:
            _bin = self._buf[o:o + 16]
        except IndexError:
            raise OverrunBufferException(o, len(self._buf))

        # Yeah, this is ugly
        h = map(ord, _bin)
        return "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x" % \
            (h[3], h[2], h[1], h[0],
             h[5], h[4],
             h[7], h[6],
             h[8], h[9],
             h[10], h[11], h[12], h[13], h[14], h[15])

    def absolute_offset(self, offset):
        """
        Get the absolute offset from an offset relative to this block
        Arguments:
        - `offset`: The relative offset into this block.
        """
        return self._offset + offset

    def parent(self):
        """
        Get the parent block. See the class documentation for what the
        parent link is.
        """
        return self._parent

    def offset(self):
        """
        Equivalent to self.absolute_offset(0x0), which is the starting
        offset of this block.
        """
        return self._offset
