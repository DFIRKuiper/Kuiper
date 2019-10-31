import datetime
import logging

from BinaryParser import Block
from BinaryParser import align
from BinaryParser import OverrunBufferException
from known_guids import known_guids


g_logger = logging.getLogger("ShellItems")


class SHITEMTYPE:
    '''
    This is like an enum...
    These are the 'supported' SHITEM types
    '''
    UNKNOWN0 = 0x00
    UNKNOWN1 = 0x01
    UNKNOWN2 = 0x2E
    FILE_ENTRY = 0x30
    FOLDER_ENTRY = 0x1F
    VOLUME_NAME = 0x20
    NETWORK_LOCATION = 0x40
    URI = 0x61
    CONTROL_PANEL = 0x71
    DELEGATE_ITEM = 0x74


class SHITEM(Block):
    def __init__(self, buf, offset, parent):
        super(SHITEM, self).__init__(buf, offset, parent)

        self.declare_field("word", "size", 0x0)
        self.declare_field("byte", "type", 0x2)
        g_logger.debug("SHITEM @ %s of type %s.", hex(offset), hex(self.type()))

    def __unicode__(self):
        return u"SHITEM @ %s." % (hex(self.offset()))

    def name(self):
        return "??"

    def m_date(self):
        return datetime.datetime.min

    def a_date(self):
        return datetime.datetime.min

    def cr_date(self):
        return datetime.datetime.min


class SHITEM_FOLDERENTRY(SHITEM):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_FOLDERENTRY @ %s.", hex(offset))
        super(SHITEM_FOLDERENTRY, self).__init__(buf, offset, parent)

        self._off_folderid = 0x3      # UINT8
        self.declare_field("guid", "guid", 0x4)

    def __unicode__(self):
        return u"SHITEM_FOLDERENTRY @ %s: %s." % \
          (hex(self.offset()), self.name())

    def folder_id(self):
        _id = self.unpack_byte(self._off_folderid)

        if _id == 0x00:
            return "INTERNET_EXPLORER"
        elif _id == 0x42:
            return "LIBRARIES"
        elif _id == 0x44:
            return "USERS"
        elif _id == 0x48:
            return "MY_DOCUMENTS"
        elif _id == 0x50:
            return "MY_COMPUTER"
        elif _id == 0x58:
            return "NETWORK"
        elif _id == 0x60:
            return "RECYCLE_BIN"
        elif _id == 0x68:
            return "INTERNET_EXPLORER"
        elif _id == 0x70:
            return "UKNOWN"
        elif _id == 0x80:
            return "MY_GAMES"
        else:
            return ""

    def name(self):
        if self.guid() in known_guids:
            return "{%s}" % known_guids[self.guid()]
        return "{%s: %s}" % (self.folder_id(), self.guid())


class SHITEM_UNKNOWNENTRY0(SHITEM):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_UNKNOWNENTRY0 @ %s.", hex(offset))
        super(SHITEM_UNKNOWNENTRY0, self).__init__(buf, offset, parent)

        self.declare_field("word", "size", 0x0)
        if self.size() == 0x20:
            self.declare_field("guid", "guid", 0xE)
        # pretty much completely unknown
        # TODO, if you have time for research

    def __unicode__(self):
        return u"SHITEM_UNKNOWNENTRY0 @ %s: %s." % \
          (hex(self.offset()), self.name())

    def name(self):
        if self.size() == 0x20:
            return "{%s}" % known_guids.get(self.guid(), self.guid())
        else:
            return "??"


class SHITEM_UNKNOWNENTRY2(SHITEM):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_UNKNOWNENTRY2 @ %s.", hex(offset))
        super(SHITEM_UNKNOWNENTRY2, self).__init__(buf, offset, parent)

        self.declare_field("byte", "flags", 0x3)
        self.declare_field("guid", "guid", 0x4)

    def __unicode__(self):
        return u"SHITEM_UNKNOWNENTRY2 @ %s: %s." % \
          (hex(self.offset()), self.name())

    def __str__(self):
        return "SHITEM_UNKNOWNENTRY2 @ %s: %s." % \
          (hex(self.offset()), self.name())

    def name(self):
        return "{%s}" % known_guids.get(self.guid(), self.guid())


class SHITEM_URIENTRY(SHITEM):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_URIENTRY @ %s.", hex(offset))
        super(SHITEM_URIENTRY, self).__init__(buf, offset, parent)

        self.declare_field("dword", "flags", 0x3)
        self.declare_field("wstring", "uri", 0x8)

    def __unicode__(self):
        return u"SHITEM_URIENTRY @ %s: %s." % \
          (hex(self.offset()), self.name())

    def name(self):
        return self.uri()


class SHITEM_CONTROLPANELENTRY(SHITEM):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_CONTROLPANELENTRY @ %s.", hex(offset))
        super(SHITEM_CONTROLPANELENTRY, self).__init__(buf, offset, parent)

        self.declare_field("byte", "flags", 0x3)
        self.declare_field("guid", "guid", 0xE)

    def __unicode__(self):
        return u"SHITEM_CONTROLPANELENTRY @ %s: %s." % \
          (hex(self.offset()), self.name())

    def name(self):
        return "{CONTROL PANEL: %s}" % known_guids.get(self.guid(), self.guid())


class SHITEM_VOLUMEENTRY(SHITEM):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_VOLUMEENTRY @ %s.", hex(offset))
        super(SHITEM_VOLUMEENTRY, self).__init__(buf, offset, parent)

        if self.type() & 0x1:
            self.declare_field("string", "name", 0x3)

    def __unicode__(self):
        return u"SHITEM_VOLUMEENTRY @ %s: %s." % \
          (hex(self.offset()), self.name())


class SHITEM_NETWORKLOCATIONENTRY(SHITEM):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_NETWORKVOLUMEENTRY @ %s.", hex(offset))
        super(SHITEM_NETWORKLOCATIONENTRY, self).__init__(buf, offset, parent)

        if self.type() & 0xF == 0xD:
            self.declare_field("guid", "guid", 0x4)
            return
        self.declare_field("byte", "flags", 0x4)
        off = 0x5
        self.declare_field("string", "location", 0x5)
        off += len(self.name()) + 1
        if self.flags() & 0x80:
            self.declare_field("string", "description", off)
            off += len(self.description()) + 1
        if self.flags() & 0x40:
            self.declare_field("string", "comments", off)
            off += len(self.comments()) + 1

    def __unicode__(self):
        return u"SHITEM_NETWORKVOLUMEENTRY @ %s: %s." % \
          (hex(self.offset()), self.name())

    def name(self):
        if hasattr(self, 'guid'):
            return "{%s}" % known_guids.get(self.guid(), self.guid())
        return self.location()


class ExtensionBlock_BEEF0004(Block):
    """
    Extension block found in Fileentry, delegate shell item
    """
    def __init__(self, buf, offset, parent):
        super(ExtensionBlock_BEEF0004, self).__init__(buf, offset, parent)
        # Initialize name functors:
        self.localized_name = lambda: u''
        self.long_name = lambda: u''
        off = 0
        self.declare_field("word", "ext_size", off); off += 2
        self.declare_field("word", "ext_version", off); off += 2

        if self.ext_version() >= 0x03:
            off += 4 # 0xbeef0004

            self.declare_field("dosdate", "cr_date", off); off += 4
            self.declare_field("dosdate", "a_date", off); off += 4

            off += 2 # unknown
        else:
            self.cr_date = lambda: datetime.datetime.min
            self.a_date = lambda: datetime.datetime.min

        if self.ext_version() >= 0x0007:
            off += 2
            off += 8 # fileref
            off += 8 # unknown

        if self.ext_version() >= 0x0003:
            self.declare_field("word", "long_name_size", off); off += 2
        if self.ext_version() >= 0x0009:
            off += 4 # Unknown
        if self.ext_version() >= 0x0008:
            off += 4 # Unknown

        if self.ext_version() >= 0x0003:
            self.declare_field("wstring", "long_name", off)
            off += 2 * len(self.long_name()) + 2
        if 0x0003 <= self.ext_version() < 0x0007 and self.long_name_size() > 0:
            self.declare_field("string", "localized_name", off)
            off += self.long_name_size() + 1
        elif self.ext_version() >= 0x0007 and self.long_name_size() > 0:
            self.declare_field("wstring", "localized_name", off)
            off += 2 * self.long_name_size() + 2


class SHITEM_WITH_EXTENSION(SHITEM):
    def __init__(self, buf, offset, parent):
        super(SHITEM_WITH_EXTENSION, self).__init__(buf, offset, parent)
        self.extension_block = None

    def __getattr__(self, item):
        if hasattr(self.extension_block, item):
            return getattr(self.extension_block, item)
        return self.__getattribute__(item)


class Fileentry(SHITEM_WITH_EXTENSION):
    """
    The Fileentry structure is used both in the BagMRU and Bags keys with
    minor differences (eg. sizeof and location of size field).
    """
    def __init__(self, buf, offset, parent, filesize_offset):
        g_logger.debug("Fileentry @ %s.", hex(offset))
        super(Fileentry, self).__init__(buf, offset, parent)

        off = filesize_offset
        self.declare_field("dword", "filesize", off); off += 4
        self.declare_field("dosdate", "m_date", off); off += 4
        self.declare_field("word", "fileattrs", off); off += 2
        self.declare_field("word", "ext_offset", self.size() - 2)
        if self.ext_offset() > self.size():
            raise OverrunBufferException(self.ext_offset(), self.size())

        if self.type() & 0x4:
            self.declare_field("wstring", "short_name", off, length=self.ext_offset() - off)
        else:
            self.declare_field("string", "short_name", off, length=self.ext_offset() - off)
        self.extension_block = ExtensionBlock_BEEF0004(buf, self.ext_offset() + offset, self)

    def __unicode__(self):
        return u"Fileentry @ %s: %s." % (hex(self.offset()), self.name())

    def name(self):
        if self.long_name():
            return self.long_name()
        return self.short_name()


class SHITEM_FILEENTRY(Fileentry):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_FILEENTRY @ %s.", hex(offset))
        super(SHITEM_FILEENTRY, self).__init__(buf, offset, parent, 0x4)

        self.declare_field("byte", "flags", 0x3)

    def __unicode__(self):
        return u"SHITEM_FILEENTRY @ %s: %s." % (hex(self.offset()),
                                                self.name())


class FILEENTRY_FRAGMENT(SHITEM):
    def __init__(self, buf, offset, parent, filesize_offset):
        g_logger.debug("FILEENTRY_FRAGMENT @ %s.", hex(offset))
        super(FILEENTRY_FRAGMENT, self).__init__(buf, offset, parent)

        off = filesize_offset
        self.declare_field("dword", "filesize", off); off += 4
        self.declare_field("dosdate", "m_date", off); off += 4
        self.declare_field("word", "fileattrs", off); off += 2
        self.declare_field("string", "short_name", off)

        off += len(self.short_name()) + 1
        off = align(off, 2)

    def name(self):
        return self.short_name()

    def __unicode__(self):
        return u"ITEMPOS_FILEENTRY @ %s: %s." % (hex(self.offset()), self.name())


class SHITEM_DELEGATE(SHITEM_WITH_EXTENSION):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEM_UNKNOWNENTRY3 @ %s.", hex(offset))
        super(SHITEM_DELEGATE, self).__init__(buf, offset, parent)
        # Unknown - Empty ( 1 byte)
        # Unknown - size? - 2 bytes
        # CFSF - 4 bytes
        # sub shell item data size - 2 bytes
        self.declare_field("dword", "signature", 0x6)  # CFSF 0x46534643

        off = 0xA
        self.sub_item = FILEENTRY_FRAGMENT(buf, offset + off, self, 0x4)
        off += self.sub_item.size()

        off += 2  # Empty extension block?

        # 5e591a74-df96-48d3-8d67-1733bcee28ba
        self.declare_field("guid", "delegate_item_identifier", off); off += 0x10
        self.declare_field("guid", "item_class_identifier", off); off += 0x10
        self.extension_block = ExtensionBlock_BEEF0004(buf, offset + off, self)

    def __unicode__(self):
        return u"SHITEM_DELEGATE @ %s: %s." % (hex(self.offset()), self.name())

    def name(self):
        if self.long_name():
            return self.long_name()
        return self.sub_item.short_name()

    def m_date(self):
        return self.sub_item.m_date()


class SHITEMLIST(Block):
    def __init__(self, buf, offset, parent):
        g_logger.debug("SHITEMLIST @ %s.", hex(offset))
        super(SHITEMLIST, self).__init__(buf, offset, parent)

    def get_item(self, off):
        # UNKNOWN1

        _type = self.unpack_byte(off + 2)
        if _type & 0x70 == SHITEMTYPE.FILE_ENTRY:
            try:
                item = SHITEM_FILEENTRY(self._buf, off, self)
            except OverrunBufferException:
                item = FILEENTRY_FRAGMENT(self._buf, off, self, 0x4)

        elif _type == SHITEMTYPE.FOLDER_ENTRY:
            item = SHITEM_FOLDERENTRY(self._buf, off, self)

        elif _type == SHITEMTYPE.UNKNOWN2:
            item = SHITEM_UNKNOWNENTRY2(self._buf, off, self)

        elif _type & 0x70 == SHITEMTYPE.VOLUME_NAME:
            item = SHITEM_VOLUMEENTRY(self._buf, off, self)

        elif _type & 0x70 == SHITEMTYPE.NETWORK_LOCATION:
            item = SHITEM_NETWORKLOCATIONENTRY(self._buf, off, self)

        elif _type == SHITEMTYPE.URI:
            item = SHITEM_URIENTRY(self._buf, off, self)

        elif _type == SHITEMTYPE.CONTROL_PANEL:
            item = SHITEM_CONTROLPANELENTRY(self._buf, off, self)

        elif _type == SHITEMTYPE.UNKNOWN0:
            item = SHITEM_UNKNOWNENTRY0(self._buf, off, self)

        elif _type == SHITEMTYPE.DELEGATE_ITEM:
            item = SHITEM_DELEGATE(self._buf, off, self)

        else:
            g_logger.debug("Unknown type: %s", hex(_type))
            item = SHITEM(self._buf, off, self)
        return item

    def items(self):
        off = self.offset()

        while True:
            size = self.unpack_word(off)

            if size == 0:
                return

            item = self.get_item(off)

            size = item.size()

            if size:
                yield item
                off += size
            else:
                break

    def __unicode__(self):
        return u"SHITEMLIST @ %s." % (hex(self.offset()))
