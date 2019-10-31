#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: mftsession.py
#
# Copyright (c) 2010 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0
#
# Date: May 2013
#

VERSION = "v2.0.18"
import datetime
import dateutil.parser as parser
import csv
import json
import os
import sys
from optparse import OptionParser

import mft


SIAttributeSizeXP = 72
SIAttributeSizeNT = 48


class MftSession:
    """Class to describe an entire MFT processing session"""

    @staticmethod
    def fmt_excel(date_str):
        return '="{}"'.format(date_str)

    @staticmethod
    def fmt_norm(date_str):
        return date_str


    def __init__(self,filenamex,outputfilex):
        self.mft = {}
        self.fullmft = {}
        self.folders = {}
        self.debug = False
        self.mftsize = 0
        self.outpufilex = outputfilex
        self.filenamex = filenamex

    def mft_options(self):

        parser = OptionParser()
        parser.set_defaults(inmemory=False, debug=False, UseLocalTimezone=False, UseGUI=False)

        parser.add_option("-v", "--version", action="store_true", dest="version",
                          help="report version and exit")

        parser.add_option("-f", "--file", dest="filename",
                          help="read MFT from FILE", metavar="FILE")

        parser.add_option("-j", "--json",
                          dest="json",
                          help="File paths should use the windows path separator instead of linux")

        parser.add_option("-o", "--output", dest="output",
                          help="write results to FILE", metavar="FILE")

        parser.add_option("-a", "--anomaly",
                          action="store_true", dest="anomaly",
                          help="turn on anomaly detection")

        parser.add_option("-e", "--excel",
                          action="store_true", dest="excel",
                          help="print date/time in Excel friendly format")

        parser.add_option("-b", "--bodyfile", dest="bodyfile",
                          help="write MAC information to bodyfile", metavar="FILE")

        parser.add_option("--bodystd", action="store_true", dest="bodystd",
                          help="Use STD_INFO timestamps for body file rather than FN timestamps")

        parser.add_option("--bodyfull", action="store_true", dest="bodyfull",
                          help="Use full path name + filename rather than just filename")

        parser.add_option("-c", "--csvtimefile", dest="csvtimefile",
                          help="write CSV format timeline file", metavar="FILE")

        parser.add_option("-l", "--localtz",
                          action="store_true", dest="localtz",
                          help="report times using local timezone")

        parser.add_option("-d", "--debug",
                          action="store_true", dest="debug",
                          help="turn on debugging output")

        parser.add_option("-s", "--saveinmemory",
                          action="store_true", dest="inmemory",
                          help="Save a copy of the decoded MFT in memory. Do not use for very large MFTs")

        parser.add_option("-p", "--progress",
                          action="store_true", dest="progress",
                          help="Show systematic progress reports.")

        parser.add_option("-w", "--windows-path",
                          action="store_true", dest="winpath",
                          help="File paths should use the windows path separator instead of linux")


        (self.options, args) = parser.parse_args()
        for path in dir(self.options):
            if not path.startswith('__') and not callable(getattr(self.options, path)):
                if path != 'cat' :

                    if path == "filename":
                        setattr(self.options, path,self.filenamex)
                    if path == 'output':
                        setattr(self.options, path,self.outpufilex)
                    # if path =='csvtimefile':
                    #     setattr(self.options, path,True)
        #print self.options
        self.path_sep = '\\' if self.options.winpath else '/'

        if self.options.excel:
            self.options.date_formatter = MftSession.fmt_excel
        else:
            self.options.date_formatter = MftSession.fmt_norm

    def open_files(self):


        if self.options.version:
            print("Version is: %s" % VERSION)
            sys.exit()

        if self.options.filename is None:
            print "-f <filename> required."
            sys.exit()

        # if self.options.output == None and self.options.bodyfile == None and self.options.csvtimefile == None:
        #     print "-o <filename> or -b <filename> or -c <filename> required."
        #     sys.exit()

        try:
            self.file_mft = open(self.options.filename, 'rb')
        except:
            print "Unable to open file: %s" % self.options.filename
            sys.exit()

        if self.options.output is not None:
            try:
                self.file_csv = csv.writer(open(self.options.output, 'wb'), dialect=csv.excel, quoting=1)
            except (IOError, TypeError):
                print "Unable to open file: %s" % self.options.output
                sys.exit()

        if self.options.bodyfile is not None:
            try:
                self.file_body = open(self.options.bodyfile, 'w')
            except:
                print "Unable to open file: %s" % self.options.bodyfile
                sys.exit()

        if self.options.csvtimefile is not None:
            try:
                self.file_csv_time = open(self.options.csvtimefile, 'w')
            except (IOError, TypeError):
                print "Unable to open file: %s" % self.options.csvtimefile
                sys.exit()

    # Provides a very rudimentary check to see if it's possible to store the entire MFT in memory
    # Not foolproof by any means, but could stop you from wasting time on a doomed to failure run.
    def sizecheck(self):

        # The number of records in the MFT is the size of the MFT / 1024
        self.mftsize = long(os.path.getsize(self.options.filename)) / 1024

        if self.options.debug:
            print 'There are %d records in the MFT' % self.mftsize

        if not self.options.inmemory:
            return

        # The size of the full MFT is approximately the number of records * the avg record size
        # Avg record size was determined empirically using some test data
        sizeinbytes = self.mftsize * 4500

        if self.options.debug:
            print 'Need %d bytes of memory to save into memory' % sizeinbytes

        try:
            arr = []
            for i in range(0, sizeinbytes / 10):
                arr.append(1)

        except MemoryError:
            print 'Error: Not enough memory to store MFT in memory. Try running again without -s option'
            sys.exit()

    def process_mft_file(self):
        all_record = []
        self.sizecheck()

        self.build_filepaths()

        # reset the file reading
        self.num_records = 0
        self.file_mft.seek(0)
        raw_record = self.file_mft.read(1024)

        if self.options.output is not None:
            self.file_csv.writerow(mft.mft_to_csv(None, True, self.options))

        while raw_record != "":
            record = mft.parse_record(raw_record, self.options)
            if self.options.debug:
                print record

            record['filename'] = self.mft[self.num_records]['filename']

            rtn_record = self.do_output(record)
            all_record.append(rtn_record)

            self.num_records += 1

            if record['ads'] > 0:
                for i in range(0, record['ads']):
                    #                         print "ADS: %s" % (record['data_name', i])
                    record_ads = record.copy()
                    record_ads['filename'] = record['filename'] + ':' + record['data_name', i]
                    rtn_record = self.do_output(record_ads)
                    all_record.append(rtn_record)

            raw_record = self.file_mft.read(1024)
        return all_record

    def do_output(self, record):


        if self.options.inmemory:
            self.fullmft[self.num_records] = record

        if self.options.output is not None:
            all_record = []
            recordx= mft.mft_to_csv(record, False, self.options)
            if 'Corrupt' in recordx:
                pass
            elif recordx[8] == 'NoSIRecord':
                pass
            else:
                app = {}
                app['RecordNumber']= recordx[0]
                app['Good']= recordx[1]
                app['Active']= recordx[2]
                app['Recordtype']= recordx[3]
                app['SequenceNumber']= recordx[4]
                app['ParentFileRec.#']= recordx[5]
                app['ParentFileRec.Seq.#']= recordx[6]
                app['Filename#1']= recordx[7]
                app['StdInfoCreationdate']= recordx[8]
                try:
                    date = parser.parse(recordx[8]).isoformat()
                except:
                    date = '1700-1-1 00:00:00'
                    date = parser.parse(date)
                    date =date.isoformat()
                app['@timestamp'] = date
                app['@timestamp']= date
                app['StdInfoModificationdate']= recordx[9]
                app['StdInfoAccessdate']= recordx[10]
                app['StdInfoEntrydate']= recordx[11]
                app['FNInfoCreationdate']= recordx[12]
                app['FNInfoModificationdate']= recordx[13]
                app['FNInfoAccessdate']= recordx[14]
                app['FNInfoEntrydate']= recordx[15]
                app['BirthVolumeID']= recordx[16]
                app['BirthObjectID']= recordx[17]
                app['BirthDomainID']= recordx[18]
                app['Filename#2']= recordx[19]
                app['FNInfoCreationdate']= recordx[20]
                app['FNInfoModifydate']= recordx[21]
                app['FNInfoAccessdate']= recordx[22]
                app['FNInfoEntrydate']= recordx[23]
                app['Filename#3']= recordx[24]
                app['FNInfoCreationdate']= recordx[25]
                app['FNInfoModifydate']= recordx[26]
                app['FNInfoAccessdate']= recordx[27]
                app['FNInfoEntrydate']= recordx[28]
                app['Filename#4']= recordx[29]
                app['FNInfoCreationdate']= recordx[30]
                app['FNInfoModifydate']= recordx[31]
                app['FNInfoAccessdate']= recordx[32]
                app['FNInfoEntrydate']= recordx[33]
                app['StandardInformation']= recordx[34]
                app['AttributeList']= recordx[35]
                app['Filename']= recordx[36]
                app['ObjectID']= recordx[37]
                app['VolumeName']= recordx[38]
                app['VolumeInfo']= recordx[39]
                app['Data']= recordx[40]
                app['IndexRoot']= recordx[41]
                app['IndexAllocation']= recordx[42]
                app['Bitmap']= recordx[43]
                app['ReparsePoint']= recordx[44]
                app['EAInformation']= recordx[45]
                app['EA']= recordx[46]
                app['PropertySet']= recordx[47]
                app['LoggedUtilityStream']= recordx[48]
                app['Log/Notes']= recordx[49]
                app['STFFNShift']= recordx[50]
                app['uSecZero']= recordx[51]
                app['ADS']= recordx[52]
                app['PossibleCopy']= recordx[53]
                app['PossibleVolumeMove']= recordx[54]
                all_record.append(app)
                return app
            # self.file_csv.writerow(mft.mft_to_csv(record, False, self.options))

        if self.options.json is not None:
            #print record
            #print "\n"
            with open(self.options.json, 'a') as outfile:
                json.dump(mft.mft_to_json(record), outfile)
                outfile.write('\n')


        if self.options.csvtimefile is not None:
            self.file_csv_time.write(mft.mft_to_l2t(record))

        if self.options.bodyfile is not None:
            self.file_body.write(mft.mft_to_body(record, self.options.bodyfull, self.options.bodystd))

        if self.options.progress:
            if self.num_records % (self.mftsize / 5) == 0 and self.num_records > 0:
                print 'Building MFT: {0:.0f}'.format(100.0 * self.num_records / self.mftsize) + '%'

    def plaso_process_mft_file(self):

        # TODO - Add ADS support ....

        self.build_filepaths()

        # reset the file reading
        self.num_records = 0
        self.file_mft.seek(0)
        raw_record = self.file_mft.read(1024)

        while raw_record != "":
            record = mft.parse_record(raw_record, self.options)
            if self.options.debug:
                print record

            record['filename'] = self.mft[self.num_records]['filename']

            self.fullmft[self.num_records] = record

            self.num_records += 1

            raw_record = self.file_mft.read(1024)

    def build_filepaths(self):
        # reset the file reading
        self.file_mft.seek(0)

        self.num_records = 0

        # 1024 is valid for current version of Windows but should really get this value from somewhere
        raw_record = self.file_mft.read(1024)
        while raw_record != "":
            minirec = {}
            record = mft.parse_record(raw_record, self.options)
            if self.options.debug:
                print record

            minirec['filename'] = record['filename']
            minirec['fncnt'] = record['fncnt']
            if record['fncnt'] == 1:
                minirec['par_ref'] = record['fn', 0]['par_ref']
                minirec['name'] = record['fn', 0]['name']
            if record['fncnt'] > 1:
                minirec['par_ref'] = record['fn', 0]['par_ref']
                for i in (0, record['fncnt'] - 1):
                    # print record['fn',i]
                    if record['fn', i]['nspace'] == 0x1 or record['fn', i]['nspace'] == 0x3:
                        minirec['name'] = record['fn', i]['name']
                if minirec.get('name') is None:
                    minirec['name'] = record['fn', record['fncnt'] - 1]['name']

            self.mft[self.num_records] = minirec

            if self.options.progress:
                if self.num_records % (self.mftsize / 5) == 0 and self.num_records > 0:
                    print 'Building Filepaths: {0:.0f}'.format(100.0 * self.num_records / self.mftsize) + '%'

            self.num_records += 1

            raw_record = self.file_mft.read(1024)

        self.gen_filepaths()

    def get_folder_path(self, seqnum):
        if self.debug:
            print "Building Folder For Record Number (%d)" % seqnum

        if seqnum not in self.mft:
            return 'Orphan'

        # If we've already figured out the path name, just return it
        if (self.mft[seqnum]['filename']) != '':
            return self.mft[seqnum]['filename']

        try:
            # if (self.mft[seqnum]['fn',0]['par_ref'] == 0) or
            # (self.mft[seqnum]['fn',0]['par_ref'] == 5):  # There should be no seq
            # number 0, not sure why I had that check in place.
            if self.mft[seqnum]['par_ref'] == 5:  # Seq number 5 is "/", root of the directory
                self.mft[seqnum]['filename'] = self.path_sep + self.mft[seqnum]['name']
                return self.mft[seqnum]['filename']
        except:  # If there was an error getting the parent's sequence number, then there is no FN record
            self.mft[seqnum]['filename'] = 'NoFNRecord'
            return self.mft[seqnum]['filename']

        # Self referential parent sequence number. The filename becomes a NoFNRecord note
        if (self.mft[seqnum]['par_ref']) == seqnum:
            if self.debug:
                print "Error, self-referential, while trying to determine path for seqnum %s" % seqnum
            self.mft[seqnum]['filename'] = 'ORPHAN' + self.path_sep + self.mft[seqnum]['name']
            return self.mft[seqnum]['filename']

        # We're not at the top of the tree and we've not hit an error
        parentpath = self.get_folder_path((self.mft[seqnum]['par_ref']))
        self.mft[seqnum]['filename'] = parentpath + self.path_sep + self.mft[seqnum]['name']

        return self.mft[seqnum]['filename']

    def gen_filepaths(self):

        for i in self.mft:

            #            if filename starts with / or ORPHAN, we're done.
            #            else get filename of parent, add it to ours, and we're done.

            # If we've not already calculated the full path ....
            if (self.mft[i]['filename']) == '':

                if self.mft[i]['fncnt'] > 0:
                    self.get_folder_path(i)
                    # self.mft[i]['filename'] = self.mft[i]['filename'] + '/' +
                    #   self.mft[i]['fn',self.mft[i]['fncnt']-1]['name']
                    # self.mft[i]['filename'] = self.mft[i]['filename'].replace('//','/')
                    if self.debug:
                        print "Filename (with path): %s" % self.mft[i]['filename']
                else:
                    self.mft[i]['filename'] = 'NoFNRecord'
