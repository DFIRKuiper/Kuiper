#!/usr/bin/env python
#
# CCM_RUA_Finder.py
# Version 1.2 #StatusUpdate
#   Thanks to Chakib (@Tecko921) for the status update feature request, testing, and feedback!
#
# Author:
#   David Pany - Mandiant (FireEye) - 2017
#   Twitter: @DavidPany
#   Please send  comments, bug reports, and questions to @DavidPany
#       or push changes directly to GitHub
#
# Editor:
#   Fred House - Madiant (FireEye) - 2016
#   Twitter: @0xF2EDCA5A 
#
# Usage:
#   CCM_RUA_Finder.py -i path\to\OBJECTS.DATA -o path\to\output.xls
#
#   The output file will be TSV formatted. Excel will automatically parse
#   TSV files with .xls extensions.
#
# Description:
#   CCM_RUA_finder.py extracts SCCM software metering RecentlyUsedApplication
#   logs from:
#      	C:\WINDOWS\system32\wbem\Repository\OBJECTS.DATA
#       C:\WINDOWS\system32\wbem\Repository\FS\OBJECTS.DATA
#       or the extracted contents of C:\Windows\CCM\InventoryStore.sdf
#
# Record Structure:
#   All WMI class definitions share a similar structure that at a high-level 
#   consists of a header section, a property section, and a data section. 
#   The header section contains a unique GUID that allows us to quickly 
#   identify class instances in the raw data, and the property and data 
#   sections contain the values we are interested in carving. Most importantly, 
#   the order of the values in the property and data sections is static, 
#   meaning we can reliably carve fields using a combination of offsets and 
#   regular expressions.
#
#   A complete analysis of WMI class and class instance structures is covered 
#   in the FLARE team's "Windows Management Instrumentation (WMI) Offense, 
#   Defense, and Forensics" white paper. 
#
#   https://www.fireeye.com/content/dam/fireeye-www/global/en/current-threats/pdfs/wp-windows-management-instrumentation.pdf
#
#   The data can be stored in a well defined format _usually_ delimited by
#   two null bytes or the data can even be found in an XML structure:
#       Null Delimited Format:
#           Potentially overwritten header:
#               string GUID Header in utf16;
#                   7C261551B264D35E30A7FA29C75283DAE04BBA71DBE8F5E553F7AD381B406DD8
#                   or
#                   6FA62F462BEF740F820D72D9250D743C
#               uint32 Timestamp1
#               uint32 Timestamp2
#               136bits unknown
#               uint16 FileSize
#               80bits unknown
#               uint16 LaunchCount
#           Two Null Byte (usually) Delimited Values
#               string "CCM_RecentlyUsedApps"
#               string AdditionalProductCodes
#               string CompanyName
#               string ExplorerFileName
#               string FileDescription
#               string FilePropertiesHash
#               string FileVersion
#               string FolderPath
#               string LastUsedTime
#               string LastUserName
#               string msiDisplayName
#               string msiPublisher
#               string msiVersion
#               string OriginalFileName
#               string ProductLanguage
#               string ProductName
#               string ProductVersion
#               string SoftwarePropertiesHash
#
#       XML Format:
#            <CCM_RecentlyUsedApps>
#            <AdditionalProductCodes>.*</AdditionalProductCodes>
#            <CompanyName>.*</CompanyName>
#            <ExplorerFileName>.*</ExplorerFileName>
#            <FileDescription>.*</FileDescription><
#            FilePropertiesHash>.*</FilePropertiesHash>
#            <FileSize>.*</FileSize>
#            <FileVersion>.*</FileVersion>
#            <FolderPath>.*</FolderPath>
#            <LastUsedTime>.*</LastUsedTime>
#            <LastUserName>.*</LastUserName>
#            <msiDisplayName>.*</msiDisplayName>
#            <msiPublisher>.*</msiPublisher>
#            <msiVersion>.*</msiVersion>
#            <OriginalFileName>.*</OriginalFileName>
#            <ProductCode>.*</ProductCode>
#            <ProductLanguage>.*</ProductLanguage>
#            <ProductName>.*</ProductName>
#            <ProductVersion>.*</ProductVersion>
#            <SoftwarePropertiesHash>.*</SoftwarePropertiesHash>
#            </CCM_RecentlyUsedApps>
#
# License:
#
#  Copyright (c) 2017 David Pany
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy 
#  of this software and associated documentation files (the "Software"), to deal 
#  in the Software without restriction, including without limitation the rights 
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
#  copies of the Software, and to permit persons to whom the Software is 
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in 
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
#  SOFTWARE.
#



from __future__ import print_function
import os
import re
import struct
import argparse
import json
from datetime import datetime, timedelta
from unidecode import unidecode
#import logging
import sys
import dateutil.parser as parser

import string

# Set up logging - default level WARN
#logging.basicConfig(level=logging.WARN)
reload(sys)
sys.setdefaultencoding('utf-8')
# WMI GUIDs for CCM RUA class instances
CCM_RUA_GUID_VISTA_UTF16 = (
    "7C261551B264D35E30A7FA29C75283DAE04BBA71DBE8F5E553F7AD381B406DD8"
    .encode('utf-16le'))
CCM_RUA_GUID_XP_UTF16 = ("6FA62F462BEF740F820D72D9250D743C"
                         .encode('utf-16le'))
# Constants:
SEEK_REWIND_SIZE = 300 # Rewind 300 bytes to search for next record
DEFAULT_READ_SIZE = 50 # Read 50 byte chunks to look for CCM_RUA headers
BLOCK_READ_SIZE = 2100 # Read 2100 bytes to capture entire CCM_RUA record
MATCH_PARTIAL_FAST_FORWARD = 31 # Advance 31 to look for next header
MISS_PARTIAL_REWIND = 19 # Rewind 19 to catch partial string headers

def update_status(current_progress, full_progress):
    """This function manages command line status updates"""
#This will not be used by us
    #Clear StdOut
    sys.stdout.write("\b" * (40))
    sys.stdout.write("{}".format(" " * 50))
    sys.stdout.write("\b" * (50))
    sys.stdout.flush()

    # update StdOut with new info
    sys.stdout.write("\t\t{}% complete...".format(((current_progress * 100) / full_progress)))
    sys.stdout.flush()


def find_ccm_rua_data(od_path):
    """This function returns 2100 byte chuncks of data that contain
    CCM_RUA entries"""

    max_seek_size = os.path.getsize(od_path) #don't seek past file size
    od_file = open(od_path, "rb")
    current_seek = 0 #Start seeking the file at 0 bytes

    # Set to hold data that may contain CCM_RUA data for further processing
    data_blocks = set()

#    logging.info("Reading File")

    #create loopcount to throttle status updates
    loop_count = 0

    while current_seek <= max_seek_size:
        #print status update
        if loop_count % 1000000 == 0:
#            update_status(current_seek, max_seek_size)
            pass

        # Read 50 bytes at a time to look for CCM_RUA string
        current_buffer = od_file.read(DEFAULT_READ_SIZE)
        current_seek += DEFAULT_READ_SIZE

        # Check for CCM_RUA string
        if "CCM_RecentlyUsedApps" in current_buffer:
            old_seek = current_seek

            # Rewind 300 (or less) bytes to capture the entire header
            if current_buffer < SEEK_REWIND_SIZE:
                current_seek = 0
            else:
                current_seek = current_seek - SEEK_REWIND_SIZE
            od_file.seek(current_seek)

            # Read enough data to capture the all CCM_RUA data
            rua_buffer = od_file.read(BLOCK_READ_SIZE)

            # Add this buffer to data_blocks for further processing
            data_blocks.add(rua_buffer)

            # Advance slightly in case this was a carved partial hit so the
            # next potential record cannot missed if it is split between
            # two 50 byte chunks
            current_seek = old_seek + MATCH_PARTIAL_FAST_FORWARD

        else:
            # Rewind slighly in case a CCM_RUA string hit is split between
            # two 50 byte chunks
            old_seek = current_seek
            current_seek = old_seek - MISS_PARTIAL_REWIND
        od_file.seek(current_seek)

        loop_count += 1

    # Display status update for 100% completion
#    update_status(max_seek_size, max_seek_size)
#    logging.info("Completed Reading File")

    return data_blocks

def main(filepath):
    """The main function will search all data chunks containing CCM RUA data
    to parse information from them"""

    all_ccm_data_set = find_ccm_rua_data(filepath)

    ccm_xml_mo = re.compile(
        "<CCM_RecentlyUsedApps><AdditionalProductCodes>"
        "(?P<additional_product_codes>.*?)</AdditionalProductCodes>"
        "<CompanyName>(?P<company_name>.*?)</CompanyName><ExplorerFileName>"
        "(?P<explorer_file_name>.*?)</ExplorerFileName><FileDescription>"
        "(?P<file_description>.*?)</FileDescription><FilePropertiesHash>"
        "(?P<file_properties_hash>.*?)</FilePropertiesHash><FileSize>"
        "(?P<file_size>.*?)</FileSize><FileVersion>(?P<file_version>.*?)"
        "</FileVersion><FolderPath>(?P<folder_path>.*?)</FolderPath>"
        "<LastUsedTime>(?P<last_used_time>.*?)</LastUsedTime><LastUserName>"
        "(?P<last_user_name>.*?)</LastUserName><msiDisplayName>"
        "(?P<msi_display_name>.*?)</msiDisplayName><msiPublisher>"
        "(?P<msi_publisher>.*?)</msiPublisher><msiVersion>"
        "(?P<msi_version>.*?)</msiVersion><OriginalFileName>"
        "(?P<original_file_name>.*?)</OriginalFileName><ProductCode>"
        "(?P<product_code>.*?)</ProductCode><ProductLanguage>"
        "(?P<product_language>.*?)</ProductLanguage><ProductName>"
        "(?P<product_name>.*?)</ProductName><ProductVersion>"
        "(?P<product_version>.*?)</ProductVersion><SoftwarePropertiesHash>"
        "(?P<software_properties_hash>.*?)</SoftwarePropertiesHash>"
        "</CCM_RecentlyUsedApps>")

    # MO to match CCM_RUA data from string header to end
    ccm_nulldel_carve_mo = re.compile(
        "CCM_RecentlyUsedApps\x00\x00"
        "(?P<additional_product_codes>[^\x00]*)\x00\x00"
        "(?P<company_name>[^\x00]*)\x00\x00"
        "(?P<explorer_file_name>[^\x00]*)\x00\x00"
        "(?P<file_description>[^\x00]*)\x00\x00"
        "(?P<file_properties_hash>[^\x00]*)\x00\x00"
        "(?P<file_version>[^\x00]*)\x00\x00"
        "(?P<folder_path>[^\x00]*)\x00\x00"
        "(?P<last_used_time>[^\x00]*)\x00\x00"
        "(?P<last_user_name>[^\x00]*)\x00\x00"
        "(?P<msi_display_name>[^\x00]*)\x00\x00"
        "(?P<msi_publisher>[^\x00]*)\x00\x00"
        "(?P<msi_version>[^\x00]*)\x00\x00"
        "(?P<original_file_name>[^\x00]*)\x00\x00"
        "(?P<product_language>[^\x00]*)\x00\x00"
        "(?P<product_name>[^\x00]*)\x00\x00"
        "(?P<product_version>[^\x00]*)\x00\x00"
        "(?P<software_properties_hash>[^\x00]*)")

    # MO to match CCM_RUA data from GUID header to end
    ccm_nulldel_full_mo = re.compile(
        "(?P<GUID>{}|{})".format(CCM_RUA_GUID_VISTA_UTF16, CCM_RUA_GUID_XP_UTF16)
        + "(?P<rua_header>[.\x00-\xFF]{20,250})CCM_RecentlyUsedApps\x00\x00"
        "(?P<additional_product_codes>[^\x00]*)\x00\x00"
        "(?P<company_name>[^\x00]*)\x00\x00"
        "(?P<explorer_file_name>[^\x00]*)\x00\x00"
        "(?P<file_description>[^\x00]*)\x00\x00"
        "(?P<file_properties_hash>[^\x00]*)\x00\x00"
        "(?P<file_version>[^\x00]*)\x00\x00"
        "(?P<folder_path>[^\x00]*)\x00\x00"
        "(?P<last_used_time>[^\x00]*)\x00\x00"
        "(?P<last_user_name>[^\x00]*)\x00\x00"
        "(?P<msi_display_name>[^\x00]*)\x00\x00"
        "(?P<msi_publisher>[^\x00]*)\x00\x00"
        "(?P<msi_version>[^\x00]*)\x00\x00"
        "(?P<original_file_name>[^\x00]*)\x00\x00"
        "(?P<product_language>[^\x00]*)\x00\x00"
        "(?P<product_name>[^\x00]*)\x00\x00"
        "(?P<product_version>[^\x00]*)\x00\x00"
        "(?P<software_properties_hash>[^\x00]*)")



    # For each line that may contain a CCM_RUA record, determine the type of
    # record and parse appropriately
    lst =[]
    for ccm_data in all_ccm_data_set:

        #Determine what type of match we have: null full, null carve, or XML
        ccm_nulldel_full_match = re.search(ccm_nulldel_full_mo, ccm_data)
        ccm_nulldel_carve_match = re.search(ccm_nulldel_carve_mo, ccm_data)
        ccm_xml_match = re.search(ccm_xml_mo, ccm_data)

        # Parse the matched data depending on the identified format
        if ccm_nulldel_full_match:
            lst.append(parse_null_delimited_record(ccm_nulldel_full_match, True))

        elif ccm_nulldel_carve_match:
            lst.append(parse_null_delimited_record(ccm_nulldel_carve_match, False))

        elif ccm_xml_match:
            lst.append(parse_xml_record(ccm_xml_match))

        else:
            # Ignore instances of the CCM RUA tag that are not usually followed
            # by actual records
            if (
                    "CCM_RecentlyUsedApps\x00\x00AdditionalProductCode" in ccm_data or
                    "CCM_RecentlyUsedApps\x00\x00\\\\.\\root\\" in ccm_data or
                    "CCM_RecentlyUsedApps\x00\x00AAInstProv" in ccm_data or
                    "class CCM_RecentlyUsedApps" in ccm_data or
                    "instance of InventoryDataItem" in ccm_data or
                    "</CCM_RecentlyUsedApps>" in ccm_data or
                    '"CCM_RecentlyUsedApps"' in ccm_data or
                    ("CCM_RecentlyUsedApps>" in ccm_data and
                     "</CCM_RecentlyUsedApps>" not in ccm_data)):
                pass
            else:
#                logging.warn("Potentially missed line:\n")
#                logging.warn("{}\n\n".format(ccm_data).replace("\\x00", " "))
                pass
    return lst

def parse_null_delimited_record(ccm_nulldel_match, full_tf):
    """Parse records delimited by \x00\x00"""
    dic ={}
    # If this a full record (not carved), we will try to parse the headers
    if full_tf:
        header_data = "{}{}".format(
            ccm_nulldel_match.group("GUID"),
            ccm_nulldel_match.group("rua_header"))

        #if a standard GUID header is in the begininning of the header
        if (
                CCM_RUA_GUID_VISTA_UTF16 in header_data or
                CCM_RUA_GUID_XP_UTF16 in header_data):

            #Determine the type of record based on the header
            if CCM_RUA_GUID_VISTA_UTF16 in header_data:
                dic['record_type'] = "Vista+_Full_NullDelim"
            elif CCM_RUA_GUID_XP_UTF16 in header_data:
                dic['record_type'] = "XP_Full_NullDelim"

            # Find timestamps, file size, and launch count in the header
            # header == data from GUID header to "CCM_RecentlyUsedApps"
            header_data_mo = re.compile(
                "(?P<GUID>{}|{})".format(CCM_RUA_GUID_VISTA_UTF16, CCM_RUA_GUID_XP_UTF16)
                + "(?P<timestamp_1>[\x00-\xFF]{8})(?P<timestamp_2>[\x00-\xFF]{8})"
                "(?P<unused>[\x00-\xFF]{34})(?P<file_size>[\x00-\xFF]{4})"
                "(?P<unused2>[\x00-\xFF]{20})(?P<launch_count>[\x00-\xFF]{4})")

            header_data_match = re.search(header_data_mo, header_data)

            # Parse timestamps from header and convert to human readable format
            timestamp_1_bin = header_data_match.group("timestamp_1")
            timestamp_2_bin = header_data_match.group("timestamp_2")

            timestamp_1_nano = struct.unpack("<Q", timestamp_1_bin)[0]
            timestamp_2_nano = struct.unpack("<Q", timestamp_2_bin)[0]

            dic['Timestamp1'] = convert_nano_to_human_time(timestamp_1_nano)
            dic['Timestamp2'] = convert_nano_to_human_time(timestamp_2_nano)

            # Parse file size and launch count from header
            dic['FileSize'] = str( struct.unpack("<L", header_data_match.group("file_size"))[0] )
            dic['LaunchCount'] = str( struct.unpack("<L", header_data_match.group("launch_count"))[0])
            timestamps_exist = True

        # If the header doesn't exist, this is a carved record without
        # timestamps, file size, and launch count
        else:
            timestamps_exist = False
            record_type = "Carved_NullDelim"

    # If we don't have a header, regex matches will be different
    else:
        timestamps_exist = False
        record_type = "Carved_NullDelim"

    # If there is no header, we need to add null data here
    if not timestamps_exist:
        dic['Timestamp1'] = "1700-01-01T00:00:00"
        dic['Timestamp2'] = "1700-01-01T00:00:00"
        dic['FileSize'] = " "
        dic['LaunchCount'] = " "

    # Find each field of the data format as defined in script header
    dic['AdditionalProductCodes'] = ccm_nulldel_match.group("additional_product_codes")
    dic['CompanyName'] = ccm_nulldel_match.group("company_name")
    dic['ExplorerFileName'] = ccm_nulldel_match.group("explorer_file_name")
    dic['FileDescription'] = ccm_nulldel_match.group("file_description")
    dic['FilePropertiesHash'] = ccm_nulldel_match.group("file_properties_hash")
    dic['FileVersion'] = ccm_nulldel_match.group("file_version")
    dic['FolderPath'] = ccm_nulldel_match.group("folder_path")

    raw_time = ccm_nulldel_match.group("last_used_time")
    year = raw_time[:4]
    month = raw_time[4:6]
    day = raw_time[6:8]
    hour = raw_time[8:10]
    minute = raw_time[10:12]
    second = raw_time[12:14]
    lastdate = "{}-{}-{}T{}:{}:{}".format(
        year, month, day, hour, minute, second)
    dic['LastUsedTime'] =lastdate
    dic['@timestamp'] = lastdate
    time_zone_offset = raw_time[-4:]

    dic['LastUserName'] = ccm_nulldel_match.group("last_user_name")
    dic['MsiDisplayName'] = ccm_nulldel_match.group("msi_display_name")
    dic['MsiPublisher'] = ccm_nulldel_match.group("msi_publisher")
    dic['MsiVersion'] = ccm_nulldel_match.group("msi_version")
    dic['OriginalFileName'] = ccm_nulldel_match.group("original_file_name")
    dic['ProductLanguage'] = ccm_nulldel_match.group("product_language")
    dic['ProductName'] = ccm_nulldel_match.group("product_name")
    dic['ProductVersion'] = ccm_nulldel_match.group("product_version")
    dic['SoftwarePropertiesHash'] = ccm_nulldel_match.group("software_properties_hash")

    #This value doesn't seem to exist in the Null Delimited format
    dic['ProductCode'] = " "

    for i in dic.keys():
        r = ""
        for c in range( 0 , len(dic[i]) ):
            if dic[i][c] in string.printable:
                r +=  dic[i][c]
        dic[i] = r
        
    app = dict((k,str(v)) for k,v in dic.iteritems())

    return json.loads(json.dumps(app))


def parse_xml_record(ccm_xml_match):
    """Parse XML formatted records"""
    dic = {}
    # Find each field of the data format as defined in script header
    dic['AdditionalProductCodes'] = ccm_xml_match.group("additional_product_codes")
    dic['CompanyName'] = ccm_xml_match.group("company_name")
    dic['ExplorerFileName'] = ccm_xml_match.group("explorer_file_name")
    dic['FileDescription'] = ccm_xml_match.group("file_description")
    dic['FilePropertiesHash'] = ccm_xml_match.group("file_properties_hash")
    dic['FileSize'] = ccm_xml_match.group("file_size")
    dic['FileVersion'] = ccm_xml_match.group("file_version")
    dic['FolderPath'] = ccm_xml_match.group("folder_path").replace("\\\\", "\\")

    raw_time = ccm_xml_match.group("last_used_time")
    year = raw_time[:4]
    month = raw_time[4:6]
    day = raw_time[6:8]
    hour = raw_time[8:10]
    minute = raw_time[10:12]
    second = raw_time[12:14]
    dateused= "{}-{}-{}T{}:{}:{}".format(
        year, month, day, hour, minute, second)
    time_zone_offset = raw_time[-4:]
    dic['LastUsedTime'] =dateused
    dic['@timestamp']  = dateused

    dic['LastUserName'] = ccm_xml_match.group("last_user_name").replace("\\\\", "\\")
    dic['MsiDisplayName'] = ccm_xml_match.group("msi_display_name")
    dic['Msi_Publisher'] = ccm_xml_match.group("msi_publisher")
    dic['MsiVersion'] = ccm_xml_match.group("msi_version")
    dic['OriginalFileName'] = ccm_xml_match.group("original_file_name")
    dic['ProductCode'] = ccm_xml_match.group("product_code")
    dic['ProductLanguage'] = ccm_xml_match.group("product_language")
    dic['ProductName'] = ccm_xml_match.group("product_name")
    dic['ProductVersion'] = ccm_xml_match.group("product_version")
    dic['SoftwarePropertiesHash'] = ccm_xml_match.group("software_properties_hash")
    dic['Timestamp1'] = ""
    dic['Timestamp2'] = ""
    dic['LaunchCount'] = ""

    # Build output string

    # Send sanitized parsed data to output file or stdout appropriately
    return json.loads(json.dumps(dic, encoding="ISO-8859-1"))

def sanitize_string(input_string):
    """Remove non-friendly characters from output strings"""

    return (input_string.replace("\\\\\\\\x0020", " ")
            .replace("\\\\\\\\\\\\\\\\", "\\").replace("\\\\x0020", " ")
            .replace("\\\\\\\\", "\\").replace("&#174;", "(R)")
            .replace("\\x0020", " "))

def convert_nano_to_human_time(epoch_time):
    """This funcction converts a nanosecond epoch time to human readable format"""
    date =  datetime(1601, 1, 1) + timedelta(microseconds=(epoch_time)/10)
    #date = parser.parse(date).isoformat()
    date =date.isoformat()

    return date

# if __name__ == "__main__":
#     main()
