
import json
import struct
import uuid
import datetime
import os
import re
import argparse
import olefile
import string

"""
references:
https://cyberforensicator.com/wp-content/uploads/2017/01/1-s2.0-S1742287616300202-main.2-14.pdf
https://github.com/libyal/liblnk/blob/master/documentation/Windows%20Shortcut%20File%20(LNK)%20format.asciidoc
https://community.malforensics.com/t/list-of-jump-list-ids/158
"""

logo ="""
                    _:*///:_
                _+*///////////+_
    ____----*////////////////////**----____
   *//////////////////////////////////********
   */////////////////       ////**************
   *////////////////          /***************
   *///////////////   /////   ****************
   *//////////////   /////**   ***************
   *//////////////   ////***   ***************
   *//////////////   ///****   ***************
   *////////////                 *************
   *////////////    Saleh Bin    *************
   *////////////     Muhaysin    *************
   *////////////                 *************
    *////////********************************
     */////  github.com/salehmuhaysin  *****
      *///*********************************
======================================================
"""

appid_path = os.path.dirname(os.path.abspath(__file__)) + '/JLParser_AppID.csv'


class JL:


    quiet     = True # If true then show the print details, if false only show the result in screen
    pretty     = False

    codecs = ["ascii","cp1256"]


    def __init__(self , args , appid_path):
        if not args.quiet:
            self.quiet = False

        self.print_msg(logo)

        if args.input_file is None and args.input_dir is None:
            self.print_msg("[-] Error: You need to provide either file or directory (-f or -d)")
            return None
        elif args.input_file is not None and args.input_dir is not None:
            self.print_msg("[-] Error: You need to provide either file or directory (-f or -d) not both")
            return None


        self.output_format     = args.output_format if args.output_format is not None and args.output_format in ['json' , 'csv'] else 'json'
        self.delimiter        = args.delimiter if args.delimiter is not None else ','
        self.output_file     = args.output_file if args.output_file is not None else None
        if args.pretty:
            self.pretty = True

        # set the AppIDs
        appid_path = appid_path if args.appids_file is None else args.appids_file
        appid_path = os.path.abspath(appid_path)
        if os.path.exists(appid_path):

            AppIDs = self.read_AppId(appid_path)
        else:
            self.print_msg("[-] Error: File " + appid_path + " not found")
            return None

        # get the list of files to be parsed
        files = []

        if args.input_file is not None:
            files = [args.input_file]
        else:
            if os.path.isdir(args.input_dir):
                for file in self.dir_walk(args.input_dir):
                    filename = os.path.basename(file)
                    if filename.endswith('.automaticDestinations-ms') or filename.endswith('.customDestinations-ms') or filename.endswith('.lnk'):
                        files.append(file)
            else:
                self.print_msg("[-] Error: Path " + str(args.input_dir) + " is not directory or not found")
                return None

        output = []
        for file in files:
            self.print_msg("[+] Parse File: " + file)
            if os.path.isfile(file):
                output += self.automaticDest(file , AppIDs) # parse JumpList
            else:
                self.print_msg("[-] Error: Path " + str(file) + " is not file or not found")
                return None

        # handle all the output results
        self.handle_output(output)



    # if results True then print the msg even if quiet arguments enabled
    # used to print the parsed data
    def print_msg(self, msg , results=False):
        if not self.quiet and results:
            print(msg)



    # return json in a beautifier
    def json_beautifier(self, js):
        return json.dumps(js, sort_keys=True, indent=4)

    def dir_walk(self, path):
        files = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            for f in filenames:
                files.append( os.path.join(dirpath , f)  )
        return files

    # this will read the AppID file and return json of all appids
    def read_AppId(self, path):
        with open(path, 'r') as f:
            lines = f.readlines()
            appid = {}
            for l in lines:
                fields = l.rstrip().split(',')
                appid[fields[1]] = (fields[0] , fields[2])

            return appid
        return {}

    # File attribute flags
    def get_network_provider_types(self, provider_bytes):
        flags = {
            0x00010000: 'WNNC_NET_MSNET',
            0x00020000: 'WNNC_NET_SMB',
            0x00020000: 'WNNC_NET_LANMAN',
            0x00030000: 'WNNC_NET_NETWARE',
            0x00040000: 'WNNC_NET_VINES',
            0x00050000: 'WNNC_NET_10NET',
            0x00060000: 'WNNC_NET_LOCUS',
            0x00070000: 'WNNC_NET_SUN_PC_NFS',
            0x00080000: 'WNNC_NET_LANSTEP',
            0x00090000: 'WNNC_NET_9TILES',
            0x000A0000: 'WNNC_NET_LANTASTIC',
            0x000B0000: 'WNNC_NET_AS400',
            0x000C0000: 'WNNC_NET_FTP_NFS',
            0x000D0000: 'WNNC_NET_PATHWORKS',
            0x000E0000: 'WNNC_NET_LIFENET',
            0x000F0000: 'WNNC_NET_POWERLAN',
            0x00100000: 'WNNC_NET_BWNFS',
            0x00110000: 'WNNC_NET_COGENT',
            0x00120000: 'WNNC_NET_FARALLON',
            0x00130000: 'WNNC_NET_APPLETALK',
            0x00140000: 'WNNC_NET_INTERGRAPH',
            0x00150000: 'WNNC_NET_SYMFONET',
            0x00160000: 'WNNC_NET_CLEARCASE',
            0x00170000: 'WNNC_NET_FRONTIER',
            0x00180000: 'WNNC_NET_BMC',
            0x00190000: 'WNNC_NET_DCE',
            0x001A0000: 'WNNC_NET_AVID',
            0x001B0000: 'WNNC_NET_DOCUSPACE',
            0x001C0000: 'WNNC_NET_MANGOSOFT',
            0x001D0000: 'WNNC_NET_SERNET',
            0x001E0000: 'WNNC_NET_RIVERFRONT1',
            0x001F0000: 'WNNC_NET_RIVERFRONT2',
            0x00200000: 'WNNC_NET_DECORB',
            0x00210000: 'WNNC_NET_PROTSTOR',
            0x00220000: 'WNNC_NET_FJ_REDIR',
            0x00230000: 'WNNC_NET_DISTINCT',
            0x00240000: 'WNNC_NET_TWINS',
            0x00250000: 'WNNC_NET_RDR2SAMPLE',
            0x00260000: 'WNNC_NET_CSC',
            0x00270000: 'WNNC_NET_3IN1',
            0x00290000: 'WNNC_NET_EXTENDNET',
            0x002A0000: 'WNNC_NET_STAC',
            0x002B0000: 'WNNC_NET_FOXBAT',
            0x002C0000: 'WNNC_NET_YAHOO',
            0x002D0000: 'WNNC_NET_EXIFS',
            0x002E0000: 'WNNC_NET_DAV',
            0x002F0000: 'WNNC_NET_KNOWARE',
            0x00300000: 'WNNC_NET_OBJECT_DIRE',
            0x00310000: 'WNNC_NET_MASFAX',
            0x00320000: 'WNNC_NET_HOB_NFS',
            0x00330000: 'WNNC_NET_SHIVA',
            0x00340000: 'WNNC_NET_IBMAL',
            0x00350000: 'WNNC_NET_LOCK',
            0x00360000: 'WNNC_NET_TERMSRV',
            0x00370000: 'WNNC_NET_SRT',
            0x00380000: 'WNNC_NET_QUINCY',
            0x00390000: 'WNNC_NET_OPENAFS',
            0x003A0000: 'WNNC_NET_AVID1',
            0x003B0000: 'WNNC_NET_DFS',
            0x003C0000: 'WNNC_NET_KWNP',
            0x003D0000: 'WNNC_NET_ZENWORKS',
            0x003E0000: 'WNNC_NET_DRIVEONWEB',
            0x003F0000: 'WNNC_NET_VMWARE',
            0x00400000: 'WNNC_NET_RSFX',
            0x00410000: 'WNNC_NET_MFILES',
            0x00420000: 'WNNC_NET_MS_NFS',
            0x00430000: 'WNNC_NET_GOOGLE',
            0x00440000: 'WNNC_NET_NDFS',
        }

        setFlags = []
        for f in flags.keys():
            if f & provider_bytes == f:
                setFlags.append(flags[f])

        return ','.join(setFlags)




    # Get network share flags
    def get_network_share_flags(self, network_flag):
        flags = {
            0x0001:    'ValidDevice',
            0x0002:    'ValidNetType'
        }

        setFlags = []
        for f in flags.keys():
            if f & network_flag == f:
                setFlags.append(flags[f])

        return ','.join(setFlags)


    # Get drive type
    def get_drive_type(self, drive_type):
        ids = {
            0:    'DRIVE_UNKNOWN',
            1:    'DRIVE_NO_ROOT_DIR',
            2:    'DRIVE_REMOVABLE',
            3:    'DRIVE_FIXED',
            4:    'DRIVE_REMOTE',
            5:    'DRIVE_CDROM',
            6:    'DRIVE_RAMDISK'
        }
        try:
            return ids[drive_type]
        except Exception as e:
            return 'Unknown'


    # get the Location Flags
    def get_location_flags(self, data_bytes):
        flags = {
            0x0001:    'VolumeIDAndLocalBasePath',
            0x0002:    'CommonNetworkRelativeLinkAndPathSuffix'
        }

        setFlags = []
        for f in flags.keys():
            if f & data_bytes == f:
                setFlags.append(flags[f])

        return ','.join(setFlags)

    # Show Window definitions
    def get_show_window_id(self, data_sw_bytes):
        ids = {
            0:    'SW_HIDE',
            1:    'SW_NORMAL',
            2:    'SW_SHOWMINIMIZED',
            3:    'SW_MAXIMIZE',
            4:    'SW_SHOWNOACTIVATE',
            5:    'SW_SHOW',
            6:    'SW_MINIMIZE',
            7:    'SW_SHOWMINNOACTIVE',
            8:    'SW_SHOWNA',
            9:    'SW_RESTORE',
            10:    'SW_SHOWDEFAULT',
            11:    'SW_FORCEMINIMIZE'
        }

        return ids[data_sw_bytes]

    # File attribute flags
    def get_file_attr_flags(self, data_flag_bytes):
        flags = {
            0x00000001:    'FILE_ATTRIBUTE_READONLY',
            0x00000002:    'FILE_ATTRIBUTE_HIDDEN',
            0x00000004:    'FILE_ATTRIBUTE_SYSTEM',
            0x00000008:    'Unknown',
            0x00000010:    'FILE_ATTRIBUTE_DIRECTORY',
            0x00000020:    'FILE_ATTRIBUTE_ARCHIVE',
            0x00000040:    'FILE_ATTRIBUTE_DEVICE',
            0x00000080:    'FILE_ATTRIBUTE_NORMAL',
            0x00000100:    'FILE_ATTRIBUTE_TEMPORARY',
            0x00000200:    'FILE_ATTRIBUTE_SPARSE_FILE',
            0x00000400:    'FILE_ATTRIBUTE_REPARSE_POINT',
            0x00000800:    'FILE_ATTRIBUTE_COMPRESSED',
            0x00001000:    'FILE_ATTRIBUTE_OFFLINE',
            0x00002000:    'FILE_ATTRIBUTE_NOT_CONTENT_INDEXED',
            0x00004000:    'FILE_ATTRIBUTE_ENCRYPTED',
            0x00008000:    'Unknown',
            0x00010000:    'FILE_ATTRIBUTE_VIRTUAL'
        }

        setFlags = []
        for f in flags.keys():
            if f & data_flag_bytes == f:
                setFlags.append(flags[f])

        return ','.join(setFlags)


    # Data Flags mapping
    def get_data_flags(self, data_flag_bytes):
        flags = {
            0x00000001:    'HasTargetIDList',
            0x00000002:    'HasLinkInfo',
            0x00000004:    'HasName',
            0x00000008:    'HasRelativePath',
            0x00000010:    'HasWorkingDir',
            0x00000020:    'HasArguments',
            0x00000040:    'HasIconLocation',
            0x00000080:    'IsUnicode',
            0x00000100:    'ForceNoLinkInfo',
            0x00000200:    'HasExpString',
            0x00000400:    'RunInSeparateProcess',
            0x00000800:    'Unknown',
            0x00001000:    'HasDarwinID',
            0x00002000:    'RunAsUser',
            0x00004000:    'HasExpIcon',
            0x00008000:    'NoPidlAlias',
            0x00010000:    'Unknown',
            0x00020000:    'RunWithShimLayer',
            0x00040000:    'ForceNoLinkTrack',
            0x00080000:    'EnableTargetMetadata',
            0x00100000:    'DisableLinkPathTracking',
            0x00200000:    'DisableKnownFolderTracking',
            0x00400000:    'DisableKnownFolderAlias',
            0x00800000:    'AllowLinkToLink',
            0x01000000:    'UnaliasOnSave',
            0x02000000:    'PreferEnvironmentPath',
            0x04000000:    'KeepLocalIDListForUNCTarget'
        }
        setFlags = []
        for f in flags.keys():
            if f & data_flag_bytes == f:
                setFlags.append(flags[f])

        return ','.join(setFlags)




    # FILETIME to ISO time format
    def ad_timestamp(self, timestamp , isObject=False):
        timestamp = self.unpack_int_l(timestamp) - (self.unpack_int_l(timestamp) & 0xf000000000000000)

        # if the timestamp extracted from object ID, you need to subtract 5748192000000000 from it
        if isObject:
            timestamp -= 5748192000000000

        if timestamp > 0:
            dt = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=timestamp/10)
            return dt.isoformat()
        else:
            return "1700-01-01T00:00:00"



    # unpack the struct of the provided data
    def unpack_int_l(self, data , type='int'):
        if len(data)==1 and type=='int':
            return struct.unpack('<B' , data)[0]
        elif len(data)==2 and type=='int':
            return struct.unpack('<H' , data)[0]
        elif len(data)==4 and type=='int':
            return struct.unpack('<I' , data)[0]
        elif len(data)==4 and type=='singed_int':
            return struct.unpack('<i' , data)[0]
        elif len(data) == 8 and type=='int':
            return struct.unpack('<Q' , data)[0]
        elif len(data)==4 and type=='float':
            return struct.unpack('<f' , data)[0]
        elif len(data)==8 and type=='float':
            return struct.unpack('<d' , data)[0]
        elif len(data)==6 and type=='mac':
            return "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("BBBBBB",data)
        elif type=='uni':
            return data.decode('UTF-16-LE')
        elif type=='printable':
            for codec in self.codecs:
                try:
                    return data.decode(codec,errors='strict')
                except Exception as e:
                    pass
            return self.unpack_int_l(data , 'ascii')

        elif type=='ascii':
            count       = 0
            date_ascii  = ""
            while count < len(data) and chr(data[count]) in string.printable:
                date_ascii += chr(data[count])
                count +=1
            return date_ascii
        elif len(data)==16 and type=='uuid':
            return str(uuid.UUID(bytes_le=data))
        else:
            return -1;


    def parse_DestList(self, data):

        # ===== parse the DestList Header
        DestList_header = {
            'Version_Number'            : self.unpack_int_l(data[:4]),
            'Total_Current_Entries'     : self.unpack_int_l(data[4:8]),
            'Total_Pinned_Entries'      : self.unpack_int_l(data[8:12]),
            'Last_Issued_ID_Num'        : self.unpack_int_l(data[16:24]),
            'Number_of_Actions'         : self.unpack_int_l(data[24:32])
        }


        # specify the OS version based on the Version_Number
        Version_Number = {
            1: "Win7/8",
            3: "Win10 build 1511",
            4: 'Win10 build 1607'
        }

        DestList_header['OS_Version'] = Version_Number[DestList_header['Version_Number']] if DestList_header['Version_Number'] in Version_Number.keys() else "Unknown"


        # ====== Parse each entry in the DiskList Payload
        DestList_Entries = []
        start_DestList_Entries = 32
        for entry in range(0 , DestList_header['Total_Current_Entries']):
            entry_data = data[start_DestList_Entries:]
            DestList_Entry = {
                'Checksum'                     : hex(self.unpack_int_l(entry_data[0:8])),
                'New_Volume_ID'             : self.unpack_int_l(entry_data[8:24] , 'uuid'),
                'New_Object_ID'             : self.unpack_int_l(entry_data[24:40] , 'uuid'),
                'New_Object_ID_Timestamp'    : self.ad_timestamp(entry_data[24:32] , isObject=True),
                'New_Object_ID_MFT_Seq'        : self.unpack_int_l(entry_data[32:34]),
                'New_Object_ID_MAC_Addr'    : self.unpack_int_l(entry_data[34:40] , 'mac'),
                'Birth_Volume_ID'             : self.unpack_int_l(entry_data[40:56] , 'uuid'),
                'Birth_Object_ID'             : self.unpack_int_l(entry_data[56:72] , 'uuid'),
                'Birth_Object_ID_Timestamp'    : self.ad_timestamp( entry_data[24:32] , isObject=True ),
                'Birth_Object_ID_MFT_Seq'    : self.unpack_int_l(entry_data[64:66]),
                'Birth_Object_ID_MAC_Addr'    : self.unpack_int_l(entry_data[66:72] , 'mac'),
                'NetBIOS'                     : self.unpack_int_l(entry_data[72:88] , 'printable'),
                'Last_Recorded_Access'        : self.ad_timestamp(entry_data[100:108]),
                'Pin_Status_Counter'        : 'unpinned' if self.unpack_int_l(entry_data[108:112]) == 0xFFFFFFFF else str(self.unpack_int_l(entry_data[108:112])),
            }

            # this means it is Windows10 machine not Windows 7/8
            if DestList_header['Version_Number'] == 3 or DestList_header['Version_Number'] == 4:
                DestList_Entry['Entry_ID_Number'] = self.unpack_int_l(entry_data[88:92])
                DestList_Entry['Access_Counter']  = self.unpack_int_l(entry_data[116:120])

                data_len = self.unpack_int_l(entry_data[128:130])*2

                DestList_Entry['Data'] = self.unpack_int_l(entry_data[130:130+data_len] , 'uni')
                start_DestList_Entries += 130 + data_len + 4

            else:
                DestList_Entry['Entry_ID_Number'] = self.unpack_int_l(entry_data[88:96])
                DestList_Entry['Access_Counter']  = int(self.unpack_int_l(entry_data[96:100] , 'float'))

                data_len = self.unpack_int_l(entry_data[112:114])*2
                DestList_Entry['Data'] = self.unpack_int_l(entry_data[114:114+data_len] , 'uni')
                start_DestList_Entries += 114 + data_len

            DestList_Entries.append(DestList_Entry)



        # merge DestList_Entries and DestList_header
        for e in range(0 , len(DestList_Entries)):
            for d in DestList_header.keys():
                DestList_Entries[e][d] = DestList_header[d]
        return DestList_Entries



    def parse_Lnk(self, stream):


        # ========== Lnk Stream Header
        header_size     = self.unpack_int_l(stream[:4])
        stream_header     = stream[:header_size]
        LnkStreamHeader = {
            'LNK_Class_ID'         : "{" + self.unpack_int_l(stream_header[4:20] , 'uuid') + "}",
            'Data_Flags'        : self.get_data_flags(self.unpack_int_l(stream_header[20:24])),
            'File_Attrbutes'    : self.get_file_attr_flags(self.unpack_int_l(stream_header[24:28])),
            'Time_Creation'        : self.ad_timestamp(stream_header[28:36]),
            '@timestamp'            :self.ad_timestamp(stream_header[28:36]),
            'Time_Access'        : self.ad_timestamp(stream_header[36:44]),
            'Time_Modification'    : self.ad_timestamp(stream_header[44:52]),
            'FileSize'            : self.unpack_int_l(stream_header[52:56]),
            'IconIndex'            : self.unpack_int_l(stream_header[56:60] , type='singed_int'),
            'ShowWindow'        : self.get_show_window_id(self.unpack_int_l(stream_header[60:64])),
        }


        # ========== Lnk Target ID
        # if the lnk has a target id list
        if "HasTargetIDList" in LnkStreamHeader['Data_Flags']:
            Lnk_Target_ID_Size = self.unpack_int_l(stream[header_size:header_size+2])

            # handle the target id list

            Lnk_Target_ID_Size += 2 # add the first field of link target id (2 bytes defined target id list size)

        else:
            Lnk_Target_ID_Size = 0

        # ========= Location information
        Location_Info_Details = {}
        if "HasLinkInfo" in LnkStreamHeader['Data_Flags']:

            Location_Info_Size             = self.unpack_int_l(stream[header_size+Lnk_Target_ID_Size:header_size+Lnk_Target_ID_Size+4])
            Location_Info_Offset         = header_size+Lnk_Target_ID_Size
            Location_Info_Stream         = stream[Location_Info_Offset:Location_Info_Offset+Location_Info_Size]

            Location_Info_Details['Header_Size']         = self.unpack_int_l(Location_Info_Stream[4:8])
            Location_Info_Details['Location_Flags']     = self.get_location_flags(self.unpack_int_l(Location_Info_Stream[8:12]))


            # ==== get volume information
            volume_information_offset     = self.unpack_int_l(Location_Info_Stream[12:16]) + Location_Info_Offset
            volume_info_size             = self.unpack_int_l( stream[volume_information_offset:volume_information_offset+4] )
            volume_info                 = stream[volume_information_offset:volume_information_offset+volume_info_size]

            Location_Info_Details['Drive_Type'] = self.get_drive_type(self.unpack_int_l(volume_info[4:8]))
            Location_Info_Details['Drive_SN'] = hex(self.unpack_int_l(volume_info[8:12])).lstrip("0x").upper()

            # get volume label
            if self.unpack_int_l(volume_info[12:16]) <= 16:
                volume_label_offset                 = self.unpack_int_l(volume_info[12:16]) + volume_information_offset
                volume_label                         = stream[volume_label_offset:volume_label_offset+stream[volume_label_offset:].find(b'\0')]

                Location_Info_Details['Volume_Label'] = self.unpack_int_l(volume_label , 'printable')
            else:
                volume_label_offset                 = self.unpack_int_l(volume_info[16:20]) + volume_information_offset
                volume_label                         = stream[volume_label_offset:volume_label_offset+stream[volume_label_offset:].find(b'\0\0')]
                Location_Info_Details['Volume_Label'] = self.unpack_int_l(volume_label , 'uni')

            # ==== local path
            local_path_offset = self.unpack_int_l(Location_Info_Stream[16:20]) + Location_Info_Offset
            Location_Info_Details['Local_Path'] = self.unpack_int_l(stream[local_path_offset:local_path_offset+stream[local_path_offset:].find(b'\0')], 'printable')
            if Location_Info_Details['Header_Size'] > 28:
                local_path_uni_offset = self.unpack_int_l(Location_Info_Stream[28:32]) + Location_Info_Offset



            # ==== network share information
            network_share_offset= self.unpack_int_l(Location_Info_Stream[20:24]) + Location_Info_Offset
            network_share_size     = self.unpack_int_l(stream[network_share_offset:network_share_offset+4])
            network_share_stream= stream[network_share_offset:network_share_offset+network_share_size]

            Location_Info_Details['Network_Share_Flags']     = self.get_network_share_flags(self.unpack_int_l(network_share_stream[4:8]))

            if self.unpack_int_l(network_share_stream[8:12]) > 20:
                Network_Share_Name_offset     = network_share_offset+self.unpack_int_l(network_share_stream[20:24])
            else:
                Network_Share_Name_offset     = network_share_offset+self.unpack_int_l(network_share_stream[8:12])
                Location_Info_Details['Network_Share_Name']     = self.unpack_int_l(stream[Network_Share_Name_offset:Network_Share_Name_offset+stream[Network_Share_Name_offset:].find(b'\0')] , 'printable')

            # device name
            if 'ValidDevice' in Location_Info_Details['Network_Share_Flags'] and self.unpack_int_l(network_share_stream[12:16]) != 0:
                Network_Device_Name_offset     = network_share_offset+self.unpack_int_l(network_share_stream[12:16])
                Location_Info_Details['Network_Device_Name'] = self.unpack_int_l(stream[Network_Device_Name_offset:Network_Device_Name_offset+stream[Network_Device_Name_offset:].find(b'\0')] , 'printable')

            # network provider type
            if 'ValidNetType' in Location_Info_Details['Network_Share_Flags'] and self.unpack_int_l(network_share_stream[16:20]) != 0:
                Location_Info_Details['Network_Providers'] = self.get_network_provider_types(self.unpack_int_l(network_share_stream[16:20]))


            # get the information unicode if exists
            if self.unpack_int_l(network_share_stream[8:12]) > 20:
                unicode_network_share_name_offset = self.unpack_int_l(network_share_stream[20:24]) + network_share_offset
                Location_Info_Details['Network_Share_Name_uni'] = self.unpack_int_l(stream[unicode_network_share_name_offset:unicode_network_share_name_offset+stream[unicode_network_share_name_offset:].find(b'\0\0')] , 'uni'),

                if self.unpack_int_l(network_share_stream[24:28]) != 0:
                    unicode_network_decide_name_offset = self.unpack_int_l(network_share_stream[24:28]) + network_share_offset
                    Location_Info_Details['Network_Share_Name_uni'] = self.unpack_int_l(stream[unicode_network_decide_name_offset:unicode_network_decide_name_offset+stream[unicode_network_decide_name_offset:].find(b'\0\0')] , 'uni'),


            # ==== Common Path
            common_path_offset                    = self.unpack_int_l(Location_Info_Stream[24:28]) + Location_Info_Offset
            Location_Info_Details['Common_Path']= self.unpack_int_l(stream[common_path_offset:common_path_offset+stream[common_path_offset:].find(b'\0')] , 'printable')


            # ==== combine all dictionaries
        lnk_details = {}
        for lsh in LnkStreamHeader.keys():
            lnk_details[lsh] = LnkStreamHeader[lsh]
        for lid in Location_Info_Details.keys():
            lnk_details[lid] = Location_Info_Details[lid]

        return lnk_details





    def automaticDest(self, path , AppIDs):


        # check file to get the AppID
        filename = os.path.basename(path)
        AppID     = "Unknown"
        AppType = "Unknown"
        AppDesc = "Unknown"
        if re.search(r'[0-9A-F]{16}.(AUTOMATICDESTINATIONS-MS|AUTOMATICDESTINATIONS-MS)', filename.upper(), flags = 0):
            AppID = filename.split('.')[0]
            if AppID in AppIDs.keys():
                AppType = AppIDs[AppID][0]
                AppDesc = AppIDs[AppID][1]

        clean_entry = {
                    'LNK_Class_ID'             : '',
                    'Data_Flags'             : '',
                    'File_Attrbutes'         : '',
                    'Time_Creation'         : '',
                    '@timestamp'            :'',
                    'Time_Access'             : '',
                    'Time_Modification'     : '',
                    'FileSize'                 : '',
                    'IconIndex'             : '',
                    'ShowWindow'             : '',
                    'Header_Size'             : '',
                    'Location_Flags'         : '',
                    'Drive_Type'             : '',
                    'Drive_SN'                 : '',
                    'Volume_Label'             : '',
                    'Local_Path'             : '',
                    'Network_Share_Flags'     : '',
                    'Network_Share_Name'     : '',
                    'Network_Device_Name'     : '',
                    'Network_Providers'     : '',
                    'Network_Share_Name_uni': '',
                    'Common_Path'             : '',
                    'entry_number'             : '',
                    'AppID'                 : AppID,
                    'AppType'                 : AppType,
                    'AppDesc'                 : AppDesc,
                    'Source_Name'             : filename,
                    'Source_Path'             : path
                }

        # if the file is automaticDestinations (Ole Format) then extract the data
        if olefile.isOleFile(path):

            ole= olefile.OleFileIO(path)

            DestList = {}
            JumpList = []
            for oleDir in ole.listdir():

                oleDir             = oleDir[0]
                stream             = ole.openstream(oleDir)
                stream_data     = stream.read()
                stream_header     = self.unpack_int_l(stream_data[:4])

                if stream_header != 76:
                    DestList = self.parse_DestList(stream_data[:ole.get_size(oleDir)])
                else:
                    entry_details = self.parse_Lnk(stream_data[:ole.get_size(oleDir)])
                    entry_details['entry_number'] = oleDir
                    JumpList.append( entry_details )



            for jl in range(0 , len(JumpList)):
                # combine the details of entry from DestList with the details of entry from JumpList
                for dl in range(0 , len(DestList)):
                    if JumpList[jl]['entry_number'] == DestList[dl]['Entry_ID_Number']:
                        for dl_entry in DestList[dl].keys():
                            JumpList[jl][dl_entry] = DestList[dl][dl_entry]

                # fill empty fields
                for i in clean_entry.keys():
                    if i not in JumpList[jl].keys():
                        JumpList[jl][i] = clean_entry[i]

                JumpList[jl]['Artifact'] = 'JumpList'

            return JumpList


        else:
            # check if the magic header of the file is 4c000000 (LNK) header
            lnk_f = open(path , 'rb')
            lnk_content = lnk_f.read()
            if self.unpack_int_l(lnk_content[:4]) == 76:

                Lnk_Entries = []

                entry_details = self.parse_Lnk(lnk_content)
                # fill empty fields
                for i in clean_entry.keys():
                    if i not in entry_details.keys():
                        entry_details[i] = clean_entry[i]

                entry_details['Artifact'] = 'LNK_File'

                Lnk_Entries.append( entry_details )


                return Lnk_Entries



            else:
                self.print_msg("[-] File " + path + " not a OleFile or LNK file")
            lnk_f.close()
        return []

    # print the output of parsed artifacts
    def handle_output(self, output):

        output_text = ""
        # json
        if self.output_format.lower() == 'json':
            output_text = self.json_beautifier( output ) if self.pretty else json.dumps( output )

        # text
        elif self.output_format.lower() == 'csv':
            output_csv = []

            columns = output[0].keys()
            output_csv.append('"' + str('"' + self.delimiter + '"').join(columns) + '"')

            for o in output:
                temp_output = []
                for c in columns:
                    temp_output.append(str(o[c]))
                output_csv.append('"' + str('"' + self.delimiter + '"').join(temp_output) + '"')

            output_text = '\n'.join(output_csv)


        # print the output if output file not specified, otherwise write the output to the output file
        if self.output_file is None:
            self.print_msg(output_text , results=True)
        else:
            f = open(self.output_file , 'w')
            f.write(output_text)
            f.close()




def main():


    # ================== arguments
    a_parser = argparse.ArgumentParser('Python script parser JumpList and Lnk Files (automaticDestinations-ms, customDestinations-ms, and .lnk)')

    requiredargs = a_parser.add_mutually_exclusive_group(required=True)
    requiredargs.add_argument('-f', dest='input_file', help='Path to the JumpList or Lnk file')
    requiredargs.add_argument('-d', dest='input_dir', help='Path to the JumpList and Lnk directories (recursively), it will parse all files (automaticDestinations-ms, customDestinations-ms, and .lnk)')

    optionalargs = a_parser.add_argument_group('Optional Arguments')
    optionalargs.add_argument('-of' , dest='output_format' , help='Output format (csv, json), (default: json)')
    optionalargs.add_argument('-o' , dest='output_file' , help='Output file to write the results to')
    optionalargs.add_argument('-a' , dest='appids_file' , help='AppIDs configuration file (default: '+appid_path+')')
    optionalargs.add_argument('-dl' , dest='delimiter' , help='CSV file delimiter (default ",") only if "-o csv" used')
    optionalargs.add_argument('-p' , dest='pretty', action='store_true' , help='Save the output of json in pretty format (default: not pretty), only if "-o json" used')
    optionalargs.add_argument('-q' , dest='quiet', action='store_true' , help="Don't show the information messages, only the results")

    args = a_parser.parse_args()
    jumplist = JL(args , appid_path)



main()
