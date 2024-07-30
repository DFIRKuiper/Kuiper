import os
import sys
import re
import time
import argparse
from datetime import datetime, timedelta
import ctypes
import ipaddress
import xml.etree.ElementTree as ET
from dissect import cstruct
import struct

from pkg_resources import NullProvider
import SDDL3
import io
import base64
import json
import blowfish
import zlib
import hashlib
import csv
import fileinput
from scapy.all import Ether
from scapy.utils import import_hexcap
from manuf import manuf
import traceback


if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def csv_header():

    syslog.write('"File Name","Entry Length","@timestamp","Event ID","Field4","Severity","Summary","Event_Data_Size","Event_Source","Size_(bytes)","Location","LOG:Time","LOG:Event","LOG:Category","LOG:Logger","LOG:Computer","LOG:User","LOG:Virus","LOG:File","LOG:WantedAction1","LOG:WantedAction2","LOG:RealAction","LOG:Virus_Type","LOG:Flags","LOG:Description","LOG:ScanID","LOG:New_Ext","LOG:Group_ID","LOG:Event_Data1","LOG:Event_Data2_Label","LOG:Event_Data2","LOG:Event_Data3_Label","LOG:Event_Data3","LOG:Event_Data4_Label","LOG:Event_Data4","LOG:Event_Data5_Label","LOG:Event_Data5","LOG:Event_Data6_Label","LOG:Event_Data6","LOG:Event_Data7_Label","LOG:Event_Data7","LOG:Event_Data8_Label","LOG:Event_Data8","LOG:Event_Data9_Label","LOG:Event_Data9","LOG:Event_Data10_Label","LOG:Event_Data10","LOG:Event_Data11_Label","LOG:Event_Data11","LOG:Event_Data12_Label","LOG:Event_Data12","LOG:Event_Data13_Label","LOG:Event_Data13","LOG:VBin_ID","LOG:Virus_ID","LOG:Quarantine_Forward_Status","LOG:Access","LOG:SDN_Status","LOG:Compressed","LOG:Depth","LOG:Still_Infected","LOG:Def_Info","LOG:Def_Sequence_Number","LOG:Clean_Info","LOG:Delete_Info","LOG:Backup_ID","LOG:Parent","LOG:GUID","LOG:Client_Group","LOG:Address","LOG:Domain_Name","LOG:NT_Domain","LOG:MAC_Address","LOG:Version","LOG:Remote_Machine","LOG:Remote_Machine_IP","LOG:Action_1_Status","LOG:Action_2_Status","LOG:License_Feature_Name","LOG:License_Feature_Version","LOG:License_Serial_Number","LOG:License_Fulfillment_ID","LOG:License_Start_Date","LOG:License_Expiration_Date","LOG:License_LifeCycle","LOG:License_Seats_Total","LOG:License_Seats","LOG:Error_Code","LOG:License_Seats_Delta","Log:Eraser Status","LOG:Domain_GUID","LOG:Session_GUID","LOG:VBin_Session_ID","LOG:Login_Domain","LOG:Event_Data_2_1","LOG:Event_Data_2_Company_Name","LOG:Event_Data_2_Size (bytes)","LOG:Event_Data_2_Hash_Type","LOG:Event_Data_2_Hash","LOG:Event_Data_2_Product_Version","LOG:Event_Data_2_7","LOG:Event_Data_2_8","LOG:Event_Data_2_SONAR_Engine_Version","LOG:Event_Data_2_10","LOG:Event_Data_2_11","LOG:Event_Data_2_12","LOG:Event_Data_2_Product_Name","LOG:Event_Data_2_14","LOG:Event_Data_2_15","LOG:Event_Data_2_16","LOG:Event_Data_2_17","LOG:Eraser_Category_ID","LOG:Dynamic_Categoryset_ID","LOG:Subcategoryset_ID","LOG:Display_Name_To_Use","LOG:Reputation_Disposition","LOG:Reputation_Confidence","LOG:First_Seen","LOG:Reputation_Prevalence","LOG:Downloaded_URL","LOG:Creator_For_Dropper","LOG:CIDS_State","LOG:Behavior_Risk_Level","LOG:Detection_Type","LOG:Acknowledge_Text","LOG:VSIC_State","LOG:Scan_GUID","LOG:Scan_Duration","LOG:Scan_Start_Time","LOG:TargetApp","LOG:Scan_Command_GUID","LOG:Field113","LOG:Location","LOG:Field115","LOG:Digital_Signatures_Signer","LOG:Digital_Signatures_Issuer","LOG:Digital_Signatures_Certificate_Thumbprint","LOG:Field119","LOG:Digital_Signatures_Serial_Number","LOG:Digital_Signatures_Signing_Time","LOG:Field122","LOG:Field123","LOG:Field124","LOG:Field125","LOG:Field126"\n')

    seclog.write('"File Name","Entry Length","@timestamp","Event ID","Severity","Direction","Protocol","Remote Host","Remote Port","Remote MAC","Local Host","Local Port","Local MAC","Application","Signature ID","Signature SubID","Signature Name","Intrusion URL","X Intrusion Payload","User","User Domain","Location","Occurrences","End Time","Begin Time","SHA256 Hash","Description","Hack Type","Log Data Size","Field15","Field25","Field26","Remote Host IPV6","Local Host IPV6","Field34","Symantec Version Number","Profile Serial Number","Field37","MD5 Hash","URL HID Level","URL Risk Score","URL Categories","Data","LOG:Time","LOG:Event","LOG:Category","LOG:Logger","LOG:Computer","LOG:User","LOG:Virus","LOG:File","LOG:WantedAction1","LOG:WantedAction2","LOG:RealAction","LOG:Virus_Type","LOG:Flags","LOG:Description","LOG:ScanID","LOG:New_Ext","LOG:Group_ID","LOG:Event_Data1","LOG:Event_Data2_Label","LOG:Event_Data2","LOG:Event_Data3_Label","LOG:Event_Data3","LOG:Event_Data4_Label","LOG:Event_Data4","LOG:Event_Data5_Label","LOG:Event_Data5","LOG:Event_Data6_Label","LOG:Event_Data6","LOG:Event_Data7_Label","LOG:Event_Data7","LOG:Event_Data8_Label","LOG:Event_Data8","LOG:Event_Data9_Label","LOG:Event_Data9","LOG:Event_Data10_Label","LOG:Event_Data10","LOG:Event_Data11_Label","LOG:Event_Data11","LOG:Event_Data12_Label","LOG:Event_Data12","LOG:Event_Data13_Label","LOG:Event_Data13","LOG:VBin_ID","LOG:Virus_ID","LOG:Quarantine_Forward_Status","LOG:Access","LOG:SDN_Status","LOG:Compressed","LOG:Depth","LOG:Still_Infected","LOG:Def_Info","LOG:Def_Sequence_Number","LOG:Clean_Info","LOG:Delete_Info","LOG:Backup_ID","LOG:Parent","LOG:GUID","LOG:Client_Group","LOG:Address","LOG:Domain_Name","LOG:NT_Domain","LOG:MAC_Address","LOG:Version","LOG:Remote_Machine","LOG:Remote_Machine_IP","LOG:Action_1_Status","LOG:Action_2_Status","LOG:License_Feature_Name","LOG:License_Feature_Version","LOG:License_Serial_Number","LOG:License_Fulfillment_ID","LOG:License_Start_Date","LOG:License_Expiration_Date","LOG:License_LifeCycle","LOG:License_Seats_Total","LOG:License_Seats","LOG:Error_Code","LOG:License_Seats_Delta","Log:Eraser Status","LOG:Domain_GUID","LOG:Session_GUID","LOG:VBin_Session_ID","LOG:Login_Domain","LOG:Event_Data_2_1","LOG:Event_Data_2_Company_Name","LOG:Event_Data_2_Size (bytes)","LOG:Event_Data_2_Hash_Type","LOG:Event_Data_2_Hash","LOG:Event_Data_2_Product_Version","LOG:Event_Data_2_7","LOG:Event_Data_2_8","LOG:Event_Data_2_SONAR_Engine_Version","LOG:Event_Data_2_10","LOG:Event_Data_2_11","LOG:Event_Data_2_12","LOG:Event_Data_2_Product_Name","LOG:Event_Data_2_14","LOG:Event_Data_2_15","LOG:Event_Data_2_16","LOG:Event_Data_2_17","LOG:Eraser_Category_ID","LOG:Dynamic_Categoryset_ID","LOG:Subcategoryset_ID","LOG:Display_Name_To_Use","LOG:Reputation_Disposition","LOG:Reputation_Confidence","LOG:First_Seen","LOG:Reputation_Prevalence","LOG:Downloaded_URL","LOG:Creator_For_Dropper","LOG:CIDS_State","LOG:Behavior_Risk_Level","LOG:Detection_Type","LOG:Acknowledge_Text","LOG:VSIC_State","LOG:Scan_GUID","LOG:Scan_Duration","LOG:Scan_Start_Time","LOG:TargetApp","LOG:Scan_Command_GUID","LOG:Field113","LOG:Location","LOG:Field115","LOG:Digital_Signatures_Signer","LOG:Digital_Signatures_Issuer","LOG:Digital_Signatures_Certificate_Thumbprint","LOG:Field119","LOG:Digital_Signatures_Serial_Number","LOG:Digital_Signatures_Signing_Time","LOG:Field122","LOG:Field123","LOG:Field124","LOG:Field125","LOG:Field126"\n')

    tralog.write('"File Name","Record Length","@timestamp","Action","Severity","Direction","Protocol","Remote Host","Remote MAC","Remote Port","Local Host","Local MAC","Local Port","Application","User","User Domain","Location","Occurrences","Begin Time","End Time","Rule","Field13","Rule ID","Remote Host Name","Field24","Field25","Remote Host IPV6","Local Host IPV6","Field28","Field29","Hash:MD5","Hash:SHA256","Field32","Field33","Field34"\n')

    rawlog.write('"File Name","Recode Length","@timestamp","Remote Host","Remote Port","Local Host","Local Port","Direction","Action","Application","Rule","Packet Dump","Packet Decode","Event ID","Packet Length","Field11","Remote Host Name","Field16","Field17","Remote Host IPV6","Local Host IPV6","Rule ID"\n')

    processlog.write('"File Name","Record Length","@timestamp","Severity","Action","Test Mode","Description","API","Rule Name","IPV4 Address","IPV6 Address","Caller Process ID","Caller Process","Device Instance ID","Target","File Size","User","User Domain","Location","Event ID","Field9","Begin Time","End Time","Field15","Caller Return Module Name","Field21","Field22","Field26","Field28","Field29","Extra"\n')

    timeline.write('"File Name","Record Length","Date/Time1","Date/Time2","Date/Time3","Field5","@timestamp","LOG:Event","LOG:Category","LOG:Logger","LOG:Computer","LOG:User","LOG:Virus","LOG:File","LOG:WantedAction1","LOG:WantedAction2","LOG:RealAction","LOG:Virus_Type","LOG:Flags","LOG:Description","LOG:ScanID","LOG:New_Ext","LOG:Group_ID","LOG:Event_Data1","LOG:Event_Data2_Label","LOG:Event_Data2","LOG:Event_Data3_Label","LOG:Event_Data3","LOG:Event_Data4_Label","LOG:Event_Data4","LOG:Event_Data5_Label","LOG:Event_Data5","LOG:Event_Data6_Label","LOG:Event_Data6","LOG:Event_Data7_Label","LOG:Event_Data7","LOG:Event_Data8_Label","LOG:Event_Data8","LOG:Event_Data9_Label","LOG:Event_Data9","LOG:Event_Data10_Label","LOG:Event_Data10","LOG:Event_Data11_Label","LOG:Event_Data11","LOG:Event_Data12_Label","LOG:Event_Data12","LOG:Event_Data13_Label","LOG:Event_Data13","LOG:VBin_ID","LOG:Virus_ID","LOG:Quarantine_Forward_Status","LOG:Access","LOG:SDN_Status","LOG:Compressed","LOG:Depth","LOG:Still_Infected","LOG:Def_Info","LOG:Def_Sequence_Number","LOG:Clean_Info","LOG:Delete_Info","LOG:Backup_ID","LOG:Parent","LOG:GUID","LOG:Client_Group","LOG:Address","LOG:Domain_Name","LOG:NT_Domain","LOG:MAC_Address","LOG:Version","LOG:Remote_Machine","LOG:Remote_Machine_IP","LOG:Action_1_Status","LOG:Action_2_Status","LOG:License_Feature_Name","LOG:License_Feature_Version","LOG:License_Serial_Number","LOG:License_Fulfillment_ID","LOG:License_Start_Date","LOG:License_Expiration_Date","LOG:License_LifeCycle","LOG:License_Seats_Total","LOG:License_Seats","LOG:Error_Code","LOG:License_Seats_Delta","Log:Eraser Status","LOG:Domain_GUID","LOG:Session_GUID","LOG:VBin_Session_ID","LOG:Login_Domain","LOG:Event_Data_2_1","LOG:Event_Data_2_Company_Name","LOG:Event_Data_2_Size (bytes)","LOG:Event_Data_2_Hash_Type","LOG:Event_Data_2_Hash","LOG:Event_Data_2_Product_Version","LOG:Event_Data_2_7","LOG:Event_Data_2_8","LOG:Event_Data_2_SONAR_Engine_Version","LOG:Event_Data_2_10","LOG:Event_Data_2_11","LOG:Event_Data_2_12","LOG:Event_Data_2_Product_Name","LOG:Event_Data_2_14","LOG:Event_Data_2_15","LOG:Event_Data_2_16","LOG:Event_Data_2_17","LOG:Eraser_Category_ID","LOG:Dynamic_Categoryset_ID","LOG:Subcategoryset_ID","LOG:Display_Name_To_Use","LOG:Reputation_Disposition","LOG:Reputation_Confidence","LOG:First_Seen","LOG:Reputation_Prevalence","LOG:Downloaded_URL","LOG:Creator_For_Dropper","LOG:CIDS_State","LOG:Behavior_Risk_Level","LOG:Detection_Type","LOG:Acknowledge_Text","LOG:VSIC_State","LOG:Scan_GUID","LOG:Scan_Duration","LOG:Scan_Start_Time","LOG:TargetApp","LOG:Scan_Command_GUID","LOG:Field113","LOG:Location","LOG:Field115","LOG:Digital_Signatures_Signer","LOG:Digital_Signatures_Issuer","LOG:Digital_Signatures_Certificate_Thumbprint","LOG:Field119","LOG:Digital_Signatures_Serial_Number","LOG:Digital_Signatures_Signing_Time","LOG:Field122","LOG:Field123","LOG:Field124","LOG:Field125","LOG:Field126"\n')

    tamperProtect.write('"File Name","Computer","User","Action Taken","Object Type","Event","Actor","Target","Target Process","@timestamp"\n')

    quarantine.write('"File Name","Virus","Description","Record ID","Creation Date 1 UTC","Access Date 1 UTC","Modify Date 1 UTC","VBin Time 1 UTC","Storage Name","Storage Instance ID","Storage Key","Quarantine Data Size 1","Creation Date 2 UTC","Access Date 2 UTC","Modify Date 2 UTC","VBin Time 2 UTC","Unique ID","Record Type","Quarantine Session ID","Remediation Type","Wide Description","SHA1","Actual SHA1","Actual MD5","Actual SHA256","Quarantine Data Size 2","SID","SDDL","Quarantine Data Size 3","Detection Digest","GUID","QData Length","Unknown Header","Attribute Type","Attribute Data","Extra Data","LOG:Time","LOG:Event","LOG:Category","LOG:Logger","LOG:Computer","LOG:User","LOG:Virus","LOG:File","LOG:WantedAction1","LOG:WantedAction2","LOG:RealAction","LOG:Virus_Type","LOG:Flags","LOG:Description","LOG:ScanID","LOG:New_Ext","LOG:Group_ID","LOG:Event_Data1","LOG:Event_Data2_Label","LOG:Event_Data2","LOG:Event_Data3_Label","LOG:Event_Data3","LOG:Event_Data4_Label","LOG:Event_Data4","LOG:Event_Data5_Label","LOG:Event_Data5","LOG:Event_Data6_Label","LOG:Event_Data6","LOG:Event_Data7_Label","LOG:Event_Data7","LOG:Event_Data8_Label","LOG:Event_Data8","LOG:Event_Data9_Label","LOG:Event_Data9","LOG:Event_Data10_Label","LOG:Event_Data10","LOG:Event_Data11_Label","LOG:Event_Data11","LOG:Event_Data12_Label","LOG:Event_Data12","LOG:Event_Data13_Label","LOG:Event_Data13","LOG:VBin_ID","LOG:Virus_ID","LOG:Quarantine_Forward_Status","LOG:Access","LOG:SDN_Status","LOG:Compressed","LOG:Depth","LOG:Still_Infected","LOG:Def_Info","LOG:Def_Sequence_Number","LOG:Clean_Info","LOG:Delete_Info","LOG:Backup_ID","LOG:Parent","LOG:GUID","LOG:Client_Group","LOG:Address","LOG:Domain_Name","LOG:NT_Domain","LOG:MAC_Address","LOG:Version","LOG:Remote_Machine","LOG:Remote_Machine_IP","LOG:Action_1_Status","LOG:Action_2_Status","LOG:License_Feature_Name","LOG:License_Feature_Version","LOG:License_Serial_Number","LOG:License_Fulfillment_ID","LOG:License_Start_Date","LOG:License_Expiration_Date","LOG:License_LifeCycle","LOG:License_Seats_Total","LOG:License_Seats","LOG:Error_Code","LOG:License_Seats_Delta","Log:Eraser Status","LOG:Domain_GUID","LOG:Session_GUID","LOG:VBin_Session_ID","LOG:Login_Domain","LOG:Event_Data_2_1","LOG:Event_Data_2_Company_Name","LOG:Event_Data_2_Size (bytes)","LOG:Event_Data_2_Hash_Type","LOG:Event_Data_2_Hash","LOG:Event_Data_2_Product_Version","LOG:Event_Data_2_7","LOG:Event_Data_2_8","LOG:Event_Data_2_SONAR_Engine_Version","LOG:Event_Data_2_10","LOG:Event_Data_2_11","LOG:Event_Data_2_12","LOG:Event_Data_2_Product_Name","LOG:Event_Data_2_14","LOG:Event_Data_2_15","LOG:Event_Data_2_16","LOG:Event_Data_2_17","LOG:Eraser_Category_ID","LOG:Dynamic_Categoryset_ID","LOG:Subcategoryset_ID","LOG:Display_Name_To_Use","LOG:Reputation_Disposition","LOG:Reputation_Confidence","LOG:First_Seen","LOG:Reputation_Prevalence","LOG:Downloaded_URL","LOG:Creator_For_Dropper","LOG:CIDS_State","LOG:Behavior_Risk_Level","LOG:Detection_Type","LOG:Acknowledge_Text","LOG:VSIC_State","LOG:Scan_GUID","LOG:Scan_Duration","LOG:Scan_Start_Time","LOG:TargetApp","LOG:Scan_Command_GUID","LOG:Field113","LOG:Location","LOG:Field115","LOG:Digital_Signatures_Signer","LOG:Digital_Signatures_Issuer","LOG:Digital_Signatures_Certificate_Thumbprint","LOG:Field119","LOG:Digital_Signatures_Serial_Number","LOG:Digital_Signatures_Signing_Time","LOG:Field122","LOG:Field123","LOG:Field124","LOG:Field125","LOG:Field126"\n')

    settings.write('"Log Name","Max Log Size","# of Logs","Running Total of Logs","Max Log Days","Field3","Field5","Field6"\n')


def tojson():
    csvArr=['/Symantec_Client_Management_System_Log.csv','/Symantec_Client_Management_Security_Log.csv','/Symantec_Network_and_Host_Exploit_Mitigation_Traffic_Log.csv','/Symantec_Network_and_Host_Exploit_Mitigation_Packet_Log.csv','/Symantec_Client_Management_Control_Log.csv','/Symantec_Timeline.csv','/Symantec_Client_Management_Tamper_Protect_Log.csv','/quarantine.csv','/settings.csv','/packets.txt']
    array=[]
    data = {}
    objArr=[syslog,seclog,tralog,rawlog,processlog,timeline,tamperProtect,quarantine,settings,packet]
    for i in objArr:
        i.close()
    for item in csvArr:
        csvFilePath = args.output + item
        with open(csvFilePath) as csvFile:
            csvReader = csv.DictReader(csvFile)
            for rows in csvReader:
                data = rows
                for key in list(data.keys()):  # Use a list instead of a view
                    if data[key] == '':
                        del data[key] 
                array.append(data)
        os.remove(csvFilePath)
    return array
__vis_filter = b'................................ !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[.]^_`abcdefghijklmnopqrstuvwxyz{|}~.................................................................................................................................'

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(logfile, "w")

    def write(self, message):
        self.terminal.write(message)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self.log.write(ansi_escape.sub('', message))

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass


class LogFields:
    api = ''
    dateAndTime = ''
    severity = ''
    direction = ''
    summary = ''
    type = ''
    size = ''
    time = ''
    event = ''
    category = ''
    logger = ''
    computer = ''
    user = ''
    virus = ''
    file = ''
    wantedaction1 = ''
    wantedaction2 = ''
    realaction = ''
    virustype = ''
    flags = ''
    description = ''
    scanid = ''
    newext = ''
    groupid = ''
    eventdata = ''
    vbinid = ''
    virusid = ''
    quarantineforwardstatus = ''
    access = ''
    sdnstatus = ''
    compressed = ''
    depth = ''
    stillinfected = ''
    definfo = ''
    defsequincenumber = ''
    cleaninfo = ''
    deleteinfo = ''
    backupod = ''
    parent = ''
    guid = ''
    clientgroup = ''
    address = ''
    domainname = ''
    ntdomain = ''
    macaddress = ''
    version = ''
    remotemachine = ''
    remotemachineip = ''
    action1status = ''
    action2status = ''
    licensefeaturename = ''
    licensefeatureversion = ''
    licenseserialnumber = ''
    licensefulfillmentid = ''
    licensestartdate = ''
    licenseexpirationdate = ''
    licenselifecycle = ''
    licenseseatstotal = ''
    licenseseats = ''
    errorcode = ''
    licenseseatsdelta = ''
    status = ''
    domainguid = ''
    sessionguid = ''
    vbnsessionid = ''
    logindomain = ''
    eventdata2 = ''
    erasercategoryid = ''
    dynamiccategoryset = ''
    subcategorysetid = ''
    displaynametouse = ''
    reputationdisposition = ''
    reputationconfidence = ''
    firsseen = ''
    reputationprevalence = ''
    downloadurl = ''
    categoryfordropper = ''
    cidsstate = ''
    behaviorrisklevel = ''
    detectiontype = ''
    acknowledgetext = ''
    vsicstate = ''
    scanguid = ''
    scanduration = ''
    scanstarttime = ''
    targetapptype = ''
    scancommandguid = ''
    rulename = ''
    callerprocessid = ''
    callerprocess = ''
    deviceinstanceid = ''
    target = ''
    userdomain = ''
    location = ''
    ipaddress = ''
    testmode = ''
    filesize = ''
    eventtype = ''
    signatureid = ''
    signaturesubid = ''
    signaturename = ''
    intrusionurl = ''
    xintrusionpayloadurl = ''
    hash = ''
    actor = ''
    targetprocess = ''
    packetdump = ''
    packetdecode = ''
    digitalsigner = ''
    digitalissuer = ''
    digitalthumbprint = ''
    digitalsn = ''
    digitaltime = ''
    action = ''
    objecttype = ''
    location = ''
    urlhidlevel = ''
    urlriskscore = ''
    urlcategories = ''


VBN_DEF = """

typedef struct _VBN_METADATA_V1{
    int32 QM_HEADER_Offset;
    char Description[384];
    char Log_line[984];
    int32 Flags; //if 0x2 contains dates, if 0x1 no dates
    uint32 Record_ID;
    int64 Date_Created;
    int64 Date_Accessed;
    int64 Date_Modified;
    int32 Data_Type1; //if 0x2 contains storage info, if 0x0 no storage info
    char Unknown1[484];
    char Storage_Name[48];
    int32 Storage_Instance_ID;
    char Storage_Key[384];
    int32 Data_Type2;
    int32 Unknown2;
    char Unknown3[8];
    int32 Data_Type3;
    int32 Quarantine_Data_Size;
    int32 Date_Accessed_2;
    int32 Date_Modified_2;
    int32 Date_Created_2;
    int32 VBin_Time_2;
    char Unknown4[8];
    char Unique_ID[16];
    char Unknown5[260];
    int32 Unknown6;
    int32 Record_Type;
    int32 Quarantine_Session_ID;
    int32 Remediation_Type;
    int32 Unknown7;
    int32 Unknown8;
    int32 Unknown9;
    int32 Unknown10;
    int32 Unknown11;
    int32 Unknown12;
    int32 Unknown13;
    wchar WDescription[384];
    char Unknown14[212];
} VBN_METADATA_V1;

typedef struct _VBN_METADATA_V2 {
    int32 QM_HEADER_Offset;
    char Description[384];
    char Log_line[2048];
    int32 Flags; //if 0x2 contains dates, if 0x1 no dates
    uint32 Record_ID;
    int64 Date_Created;
    int64 Date_Accessed;
    int64 Date_Modified;
    int32 Data_Type1; //if 0x2 contains storage info, if 0x0 no storage info
    char Unknown1[484];
    char Storage_Name[48];
    int32 Storage_Instance_ID;
    char Storage_Key[384];
    int32 Data_Type2;
    uint32 Unknown2;
    char Unknown3[8];
    int32 Data_Type3;
    int32 Quarantine_Data_Size;
    int32 Date_Accessed_2;
    int32 Unknown4;
    int32 Date_Modified_2;
    int32 Unknown5;
    int32 Date_Created_2;
    int32 Unknown6;
    int32 VBin_Time_2;
    int32 Unknown7;
    int32 Unknown8;
    char Unique_ID[16];
    char Unknown9[260];
    int32 Unknown10;
    int32 Record_Type;
    uint32 Quarantine_Session_ID;
    int32 Remediation_Type;
    int32 Unknown11;
    int32 Unknown12;
    int32 Unknown13;
    int32 Unknown14;
    int32 Unknown15;
    int32 Unknown16;
    int32 Unknown17;
    wchar WDescription[384];
    char Unknown18[212];
} VBN_METADATA_V2;

typedef struct _VBN_METADATA_Linux{
    int32 QM_HEADER_Offset;
    char Description[4096];
    char Log_line[1112];
    int32 Flags; //if 0x2 contains dates, if 0x1 no dates
    uint32 Record_ID;
    char Unknown1[36];
    int32 Quarantine_Data_Size;
    int32 Date_Modified;
    int32 Date_Created;
    int32 Date_Accessed;
    int32 VBin_Time;
    int32 Data_Type1; //if 0x2 contains storage info, if 0x0 no storage info
    char Unknown2[452];
    char Storage_Name[48];
    int32 Storage_Instance_ID;
    char Storage_Key[4096];
    int32 Data_Type2;
    char Unknown3[16];
    char Unknown4[36];
    int32 Quarantine_Data_Size_2;
    int32 Date_Modified_2;
    int32 Date_Created_2;
    int32 Date_Accessed_2;
    int32 VBin_Time_2;
    char Unknown5[8];
    char Unique_ID[16];
    char Unknown6[4096];
    int32 Unknown7;
    int32 Record_Type;
    int32 Quarantine_Session_ID;
    int32 Remediation_Type;
    int32 Unknown8;
    int32 Unknown9;
    int32 Unknown10;
    int32 Unknown11;
    int32 Unknown12;
    int32 Unknown13;
    int32 Unknown14;
    wchar WDescription[384];
    char Unknown15[212];
} VBN_METADATA_Linux;

typedef struct _VBN_METADATA_Linux_V2{
    int32 QM_HEADER_Offset;
    char Description[4096];
    char Log_line[1112];
    int32 Flags; //if 0x2 contains dates, if 0x1 no dates
    uint32 Record_ID;
    char Unknown1[40];
    int32 Quarantine_Data_Size;
    int32 Unknown2;
    int32 Date_Modified;
    int32 Date_Created;
    int32 Date_Accessed;
    int32 VBin_Time;
    int32 Data_Type1; //if 0x2 contains storage info, if 0x0 no storage info
    char Unknown3[444];
    char Storage_Name[48];
    int32 Storage_Instance_ID;
    char Storage_Key[4096];
    int32 Data_Type2;
    int32 Unknown4;
    char Unknown5[44];
    int32 Data_Type3;
    int32 Unknown6;
    int32 Quarantine_Data_Size_2;
    int32 Unknown7;
    int32 Date_Modified_2;
    int32 Date_Created_2;
    int32 Date_Accessed_2;
    int32 VBin_Time_2;
    char Unknown8[8];
    char Unique_ID[16];
    char Unknown9[4096];
    int32 Unknown10;
    int32 Record_Type;
    int32 Quarantine_Session_ID;
    int32 Remediation_Type;
    int32 Unknown11;
    int32 Unknown12;
    int32 Unknown13;
    int32 Unknown14;
    int32 Unknown15;
    int32 Unknown16;
    int32 Unknown17;
    wchar WDescription[384];
    char Unknown18[212];
} VBN_METADATA_Linux_V2;

typedef struct _Quarantine_Metadata_Header {
    int64 QM_Header;
    int64 QM_Header_Size;
    int64 QM_Size;
    int64 QM_Size_Header_Size;
    int64 End_of_QM_to_End_of_VBN;
} Quarantine_Metadata_Header;

typedef struct _ASN1_1 {
    BYTE Tag;
    BYTE Value;
} ASN1_1;

typedef struct _ASN1_2 {
    BYTE Tag;
    short Value;
} ASN1_2;

typedef struct _ASN1_3 {
    BYTE Tag;
    char Value[3];
} ASN1_3;

typedef struct _ASN1_4 {
    BYTE Tag;
    long Value;
} ASN1_4;

typedef struct _ASN1_8 {
    BYTE Tag;
    char Value[8];
} ASN1_8;

typedef struct _ASN1_16 {
    BYTE Tag;
    char GUID[16];
} ASN1_16;

typedef struct _ASN1_String_A {
    BYTE Tag;
    int32 Data_Length;
    char StringA[Data_Length];
} ASN1_String_A;

typedef struct _ASN1_String_W {
    BYTE Tag;
    int32 Data_Length;
    char StringW[Data_Length];
} ASN1_String_W;

typedef struct _ASN1_GUID {
    BYTE Tag;
    int32 Data_Length;
    char GUID[Data_Length];
} ASN1_GUID;

typedef struct _ASN1_BLOB {
    BYTE Tag;
    int32 Data_Length;
    char BLOB[Data_Length];
} ASN1_BLOB;

typedef struct _ASN1_Error {
    char Data[16];
} ASN1_Error;

typedef struct _Tag {
    BYTE Tag;
} Tag;

typedef struct _Quarantine_SDDL {
    BYTE Tag7;
    int32 Security_Descriptor_Size;
    char Security_Descriptor[Security_Descriptor_Size]; //need to fix for wchar
    BYTE Tag8;
    int32 Tag8_Data;
    BYTE Tag9;
    int64 Quarantine_Data_Size_3;
} Quarantine_SDDL;

typedef struct _Chunk {
    BYTE Data_Type;
    int32 Chunk_Size;
} Chunk;

typedef struct _Unknown_Header {
    int64 Unknown15;
    int32 Size;
    int64 Unknown16;
    char Unknown17[Size];
    int64 Unknown18;
    int32 Quarantine_Data_Size;
    int64 Unknown19;
} Unknown_Header;

typedef struct _Unknown_Attribute {
    int64 Data_Type;
    int64 Data_Size;
    int32 Name_Size;
    char Name[Name_Size];
    char Data[Data_Size];
} Unknown_Attribute;

typedef struct _ADS_Attribute {
    int64 Attribute_Type;
    int64 Attribute_Size;
    int32 Attribute_Name_Size;
    char ADS_Name[Attribute_Name_Size];
    char Data[Attribute_Size];
} ADS_Attribute;

typedef struct _OBJECT_ID_Attribute {
    int64 Attribute_Type;
    int64 Attribute_Size;
    int32 Attribute_Name_Size;
    char GUID_Object_Id[16];
    char GUID_Birth_Volume_Id[16];
    char GUID_Birth_Object_Id[16];
    char GUID_Domain_Id[16];
} OBJECT_ID_Attribute;

typedef struct _Extended_Attribute {
    int64 Attribute_type;
    int64 Attribute_Size;
    int32 Attribute_Name_Size;
} Extended_Attribute;

typedef struct _FILE_FULL_EA_INFORMATION {
  ULONG  NextEntryOffset;
  UCHAR  Flags;
  UCHAR  EaNameLength;
  USHORT EaValueLength;
  char   EaName[EaNameLength];
  char   EaValue[EaValueLength + 1];
} FILE_FULL_EA_INFORMATION;

typedef struct _QData_Location {
    int64 Header;
    int64 Quarantine_Data_Offset;
    int64 QData_Location_Size;
    int32 QData_Info_Size;
    char Unknown15[Quarantine_Data_Offset -28];
} QData_Location;

typedef struct _QData_Info {
    int64 QData_Info_Header;
    int64 QData_Info_Size;
    char QData[QData_Info_Size -16];
} QData_Info;

typedef struct _Quarantine_Hash {
    BYTE Tag1;
    int32 Tag1_Data;
    BYTE Tag2;
    BYTE Tag2_Data;
} Quarantine_Hash;

typedef struct _Quarantine_Hash_Continued {
    BYTE Tag3;
    int32 SHA1_Hash_Length;
    char SHA1[SHA1_Hash_Length]; //need to fix for wchar
    BYTE Tag4;
    int32 Tag4_Data;
    BYTE Tag5;
    int32 Tag5_Data;
    BYTE Tag6;
    int32 QFS_Size;
    char Quarantine_Data_Size_2[QFS_Size];
} Quarantine_Hash_Continued;

"""

vbnstruct = cstruct.cstruct()
vbnstruct.load(VBN_DEF)


def xor(msg, key):
    return ''.join(chr(key ^ j) for j in msg)


def sddl_translate(string):
    target = 'service'
    _ = string + '\n\n'
    sec = SDDL3.SDDL(string, target)

    if sec.owner_sid:
        _ += '\tOwner Name: ' + sec.owner_account + '\n'
        _ += '\tOwner SID: ' + sec.owner_sid + '\n\n'

    if sec.group_sid:
        _ += '\tGroup Name: ' + sec.group_account + '\n'
        _ += '\tGroup SID: ' + sec.group_sid + '\n\n'

    if sec.sddl_dacl:
        if sec.dacl_flags:
            _ += 'Type: ' + sec.sddl_dacl + str(sec.dacl_flags) + '\n'

        else:
            _ += 'Type: ' + sec.sddl_dacl + '\n'

        _ = acl_translate(_, sec.dacl)

    if sec.sddl_sacl:
        if sec.sacl_flags:
            _ += 'Type: ' + sec.sddl_sacl + str(sec.sacl_flags) + '\n'

        else:
            _ += 'Type: ' + sec.sddl_sacl + '\n'

        _ = acl_translate(_, sec.sacl)

    return _


def acl_translate(_, acl):
    count = 0
    for ace in acl:
        _ += '\tAce[{:02d}]'.format(count) + '\n'
        _ += '\t\tACE Type: ' + ace.ace_type + '\n'

        if ace.flags:
            _ += '\t\tAce Flags:\n'

            for flag in ace.flags:
                _ += '\t\t\t' + flag + '\n'

        _ += '\t\tAccess Mask:\n'

        for perm in ace.perms:
            _ += '\t\t\t' + perm + '\n'

        if ace.object_type:
            _ += '\t\tObject GUID: ' + ace.object_type + '\n'

        if ace.inherited_type:
            _ += '\t\tInherited Object GUID: ' + ace.inherited_type + '\n'
        _ += '\t\tTrustee: ' + ace.trustee + '\n'
        _ += '\t\tAce Sid: ' + ace.sid + '\n'
        count += 1

    return _


def sec_event_type(_):
    event_value = {
                   # Compliance events:
                   '209': 'Host Integrity failed (TSLOG_SEC_NO_AV)',
                   '210': 'Host Integrity passed (TSLOG_SEC_AV)',
                   '221': 'Host Integrity failed but it was reported as PASS',
                   '237': 'Host Integrity custom log entry',
                   # Firewall and IPS events:
                   '201': 'Invalid traffic by rule',  # SEP14.2.1
                   '202': 'Port Scan',  # SEP14.2.1
                   '203': 'Denial-of-service attack',  # SEP14.2.1
                   '204': 'Trojan horse',  # SEP14.2.1
                   '205': 'Executable file changed',  # SEP14.2.1
                   '206': 'Intrusion Prevention System (Intrusion Detected,TSLOG_SEC_INTRUSION_DETECTED)',  # SEP14.2.1
                   '207': 'Active Response',
                   '208': 'MAC Spoofing',  # SEP14.2.1
                   '211': 'Active Response Disengaged',
                   '216': 'Executable file change detected',
                   '217': 'Executable file change accepted',
                   '218': 'Executable file change denied',
                   '219': 'Active Response Canceled',  # SEP14.2.1
                   '220': 'Application Hijacking',
                   '249': 'Browser Protection event',
                   # Application and Device control:
                   '238': 'Device control disabled device',
                   '239': 'Buffer Overflow Event',
                   '240': 'Software protection has thrown an exception',
                   '241': 'Not used',   # SEP14.2.1
                   '242': 'Device control enabled the device',  # SEP14.2.1
                   # Memory Exploit Mitigation events:
                   '250': 'Memory Exploit Mitigation blocked an event',  # SEP14.2.1
                   '251': 'Memory Exploit Mitigation allowed an event'  # SEP14.2.1
                   }

    for k, v in event_value.items():
        if k == str(_):
            return v

    else:
        return _


def sec_network_protocol(_):
    network_protocol = {
                        '1': 'OTHERS',
                        '2': 'TCP',
                        '3': 'UDP',
                        '4': 'ICMP'
                        }

    for k, v in network_protocol.items():
        if k == str(_):
            return v

    else:
        return _


def sec_severity(_):
    severity_value = {
                      range(0, 4): 'Critical',
                      range(4, 8): 'Major',
                      range(8, 12): 'Minor',
                      range(12, 16): 'Information'
                     }

    for k in severity_value:
        if _ in k:
            return severity_value[k]

    else:
        return _


def url_categories(_):
    cat = {
           '1': 'Adult/Mature Content',
           '3': 'Pornography',
           '4': 'Sex Education',
           '5': 'Intimate Apparel/Swimsuit',
           '6': 'Nudity',
           '7': 'Gore/Extreme',
           '9': 'Scam/Questionable Legality',
           '11': 'Gambling',
           '14': 'Violence/Intolerance',
           '15': 'Weapons',
           '16': 'Abortion',
           '17': 'Hacking',
           '18': 'Phishing',
           '20': 'Entertainment',
           '21': 'Business/Economy',
           '22': 'Alternative Spirituality/Belief',
           '23': 'Alcohol',
           '24': 'Tobacco',
           '25': 'Controlled Substances',
           '26': 'Child Pornography',
           '27': 'Education',
           '29': 'Charitable/Non-Profit',
           '30': 'Art/Culture',
           '31': 'Finance',
           '32': 'Brokerage/Trading',
           '33': 'Games',
           '34': 'Government/Legal',
           '35': 'Military',
           '36': 'Political/Social Advocacy',
           '37': 'Health',
           '38': 'Technology/Internet',
           '40': 'Search Engines/Portals',
           '43': 'Malicious Sources/Malnets',
           '44': 'Malicious Outbound Data/Botnets',
           '45': 'Job Search/Careers',
           '46': 'News',
           '47': 'Personals/Dating',
           '49': 'Reference',
           '50': 'Mixed Content/Potentially Adult',
           '51': 'Chat (IM)/SMS',
           '52': 'Email',
           '53': 'Newsgroups/Forums',
           '54': 'Religion',
           '55': 'Social Networking',
           '56': 'File Storage/Sharing',
           '57': 'Remote Access',
           '58': 'Shopping',
           '59': 'Auctions',
           '60': 'Real Estate',
           '61': 'Society/Daily Living',
           '63': 'Personal Sites',
           '64': 'Restaurants/Food',
           '65': 'Sports/Recreation',
           '66': 'Travel',
           '67': 'Vehicles',
           '68': 'Humor/Jokes',
           '71': 'Software Downloads',
           '83': 'Peer-to-Peer (P2P)',
           '84': 'Audio/Video Clips',
           '85': 'Office/Business Applications',
           '86': 'Proxy Avoidance',
           '87': 'For Kids',
           '88': 'Web Ads/Analytics',
           '89': 'Web Hosting',
           '90': 'Uncategorized',
           '92': 'Suspicious',
           '93': 'Sexual Expression',
           '95': 'Translation',
           '96': 'Web Infrastructure',
           '97': 'Content Delivery Networks',
           '98': 'Placeholders',
           '101': 'Spam',
           '102': 'Potentially Unwanted Software',
           '103': 'Dynamic DNS Host',
           '104': 'URL Shorteners',
           '105': 'Email Marketing',
           '106': 'E-Card/Invitations',
           '107': 'Informational',
           '108': 'Computer/Information Security',
           '109': 'Internet Connected Devices',
           '110': 'Internet Telephony',
           '111': 'Online Meetings',
           '112': 'Media Sharing',
           '113': 'Radio/Audio Streams',
           '114': 'TV/Video Streams',
           '116': 'Cloud Infrastructure',
           '117': 'Cryptocurrency',
           '118': 'Piracy/Copyright Concerns',
           '121': 'Marijuana',
           '124': 'Compromised Sites'
          }

    result = ''

    for a in _:
        if a.rstrip() in cat:
            result += cat[a.rstrip()] + ','

        else:
            result += a.rstrip() + ','

    return result[:-1]


def sys_severity(_):
    severity_value = {
                      '0': 'Information',
                      '1': 'Warning',
                      '2': 'Error',
                      '3': 'Fatal'
                     }

    for k, v in severity_value.items():
        if k == str(_):
            return v

    else:
        return _


def log_severity(_):
    severity_value = {
                      '0': 'Information',
                      '15': 'Information',
                      '1': 'Warning',
                      '2': 'Error',
                      '3': 'Critical',
                      '7': 'Major'
                     }

    for k, v in severity_value.items():
        if k == str(_):
            return v

    else:
        return _


def log_direction(_):
    direction = {
                 '0': 'Unknown',
                 '1': 'Incoming',
                 '2': 'Outgoing'
                }

    for k, v in direction.items():
        if k == str(_):
            return v

    else:
        return _


def log_description(data):
    try:
        if data[3] == '2' and data[64] == '1':
            return 'AP realtime defferd scanning'

    except:
        pass

    return data[13].strip('"')


def log_event(_):
    event = {
             '1': 'IS_ALERT',
             '2': 'SCAN_STOP',
             '3': 'SCAN_START',
             '4': 'PATTERN_UPDATE',
             '5': 'INFECTION',
             '6': 'FILE_NOTOPEN',
             '7': 'LOAD_PATTERN',
             '8': 'MESSAGE_INFO',
             '9': 'MESSAGE_ERROR',
             '10': 'CHECKSUM',
             '11': 'TRAP',
             '12': 'CONFIG_CHANGE',
             '13': 'SHUTDOWN',
             '14': 'STARTUP',
             '16': 'PATTERN_DOWNLOAD',
             '17': 'TOO_MANY_VIRUSES',
             '18': 'FWD_TO_QSERVER',
             '19': 'SCANDLVR',
             '20': 'BACKUP',
             '21': 'SCAN_ABORT',
             '22': 'RTS_LOAD_ERROR',
             '23': 'RTS_LOAD',
             '24': 'RTS_UNLOAD',
             '25': 'REMOVE_CLIENT',
             '26': 'SCAN_DELAYED',
             '27': 'SCAN_RESTART',
             '28': 'ADD_SAVROAMCLIENT_TOSERVER',
             '29': 'REMOVE_SAVROAMCLIENT_FROMSERVER',
             '30': 'LICENSE_WARNING',
             '31': 'LICENSE_ERROR',
             '32': 'LICENSE_GRACE',
             '33': 'UNAUTHORIZED_COMM',
             '34': 'LOG:FWD_THRD_ERR',
             '35': 'LICENSE_INSTALLED',
             '36': 'LICENSE_ALLOCATED',
             '37': 'LICENSE_OK',
             '38': 'LICENSE_DEALLOCATED',
             '39': 'BAD_DEFS_ROLLBACK',
             '40': 'BAD_DEFS_UNPROTECTED',
             '41': 'SAV_PROVIDER_PARSING_ERROR',
             '42': 'RTS_ERROR',
             '43': 'COMPLIANCE_FAIL',
             '44': 'COMPLIANCE_SUCCESS',
             '45': 'SECURITY_SYMPROTECT_POLICYVIOLATION',
             '46': 'ANOMALY_START',
             '47': 'DETECTION_ACTION_TAKEN',
             '48': 'REMEDIATION_ACTION_PENDING',
             '49': 'REMEDIATION_ACTION_FAILED',
             '50': 'REMEDIATION_ACTION_SUCCESSFUL',
             '51': 'ANOMALY_FINISH',
             '52': 'COMMS_LOGIN_FAILED',
             '53': 'COMMS_LOGIN_SUCCESS',
             '54': 'COMMS_UNAUTHORIZED_COMM',
             '55': 'CLIENT_INSTALL_AV',
             '56': 'CLIENT_INSTALL_FW',
             '57': 'CLIENT_UNINSTALL',
             '58': 'CLIENT_UNINSTALL_ROLLBACK',
             '59': 'COMMS_SERVER_GROUP_ROOT_CERT_ISSUE',
             '60': 'COMMS_SERVER_CERT_ISSUE',
             '61': 'COMMS_TRUSTED_ROOT_CHANGE',
             '62': 'COMMS_SERVER_CERT_STARTUP_FAILED',
             '63': 'CLIENT_CHECKIN',
             '64': 'CLIENT_NO_CHECKIN',
             '65': 'SCAN_SUSPENDED',
             '66': 'SCAN_RESUMED',
             '67': 'SCAN_DURATION_INSUFFICIENT',
             '68': 'CLIENT_MOVE',
             '69': 'SCAN_FAILED_ENHANCED',
             '70': 'COMPLIANCE_FAILEDAUDIT',
             '71': 'HEUR_THREAT_NOW_WHITELISTED',
             '72': 'INTERESTING_PROCESS_DETECTED_START',
             '73': 'LOAD_ERROR_BASH',
             '74': 'LOAD_ERROR_BASH_DEFINITIONS',
             '75': 'INTERESTING_PROCESS_DETECTED_FINISH',
             '76': 'BASH_NOT_SUPPORTED_FOR_OS',
             '77': 'HEUR_THREAT_NOW_KNOWN',
             '78': 'DISABLE_BASH',
             '79': 'ENABLE_BASH',
             '80': 'DEFS_LOAD_FAILED',
             '81': 'LOCALREP_CACHE_SERVER_ERROR',
             '82': 'REPUTATION_CHECK_TIMEOUT',
             '83': 'SYMEPSECFILTER_DRIVER_ERROR',
             '84': 'VSIC_COMMUNICATION_WARNING',
             '85': 'VSIC_COMMUNICATION_RESTORED',
             '86': 'ELAM_LOAD_FAILED',
             '87': 'ELAM_INVALID_OS',
             '88': 'ELAM_ENABLE',
             '89': 'ELAM_DISABLE',
             '90': 'ELAM_BAD',
             '91': 'ELAM_BAD_REPORTED_AS_UNKNOWN',
             '92': 'DISABLE_SYMPROTECT',
             '93': 'ENABLE_SYMPROTECT',
             '94': 'NETSEC_EOC_PARSE_FAILED'
            }

    for k, v in event.items():
        if k == _:
            return v

    else:
        return _


def log_category(_):
    category = {
                '1': 'Infection',
                '2': 'Summary',
                '3': 'Pattern',
                '4': 'Security'
               }

    for k, v in category.items():
        if k == _:
            return v

    else:
        return _


def log_logger(_):
    logger = {
              '0': 'Scheduled',
              '1': 'Manual',
              '2': 'Real_Time',
              '3': 'Integrity_Shield',
              '6': 'Console',
              '7': 'VPDOWN',
              '8': 'System',
              '9': 'Startup',
              '10': 'Idle',
              '11': 'DefWatch',
              '12': 'Licensing',
              '13': 'Manual_Quarantine',
              '14': 'SymProtect',
              '15': 'Reboot_Processing',
              '16': 'Bash',
              '17': 'SymElam',
              '18': 'PowerEraser',
              '19': 'EOCScan',
              '100': 'LOCAL_END',
              '101': 'Client',
              '102': 'Forewarded',
              '256': 'Transport_Client'
             }

    for k, v in logger.items():
        if k == _:
            return v

    else:
        return _


def log_action(_):
    action = {
              '4294967295': 'Invalid',
              '1': 'Quarantine',
              '2': 'Rename',
              '3': 'Delete',
              '4': 'Leave Alone',
              '5': 'Clean',
              '6': 'Remove Macros',
              '7': 'Save file as...',
              '8': 'Send to backend',
              '9': 'Restore from Quarantine',
              '10': 'Rename Back (unused)',
              '11': 'Undo Action',
              '12': 'Error',
              '13': 'Backup to quarantine (backup view)',
              '14': 'Pending Analysis',
              '15': 'Partial Analysis',
              '16': 'Terminate Process Required',
              '17': 'Exclude from Scanning',
              '18': 'Reboot Processing',
              '19': 'Clean by Deletion',
              '20': 'Access Denied',
              '21': 'TERMINATE PROCESS ONLY',
              '22': 'NO REPAIR',
              '23': 'FAIL',
              '24': 'RUN POWERTOOL',
              '25': 'NO REPAIR POWERTOOL',
              '98': 'Suspicious',
              '99': 'Details Pending',
              '100': 'IDS Block',
              '101': 'Firewall violation',
              '102': 'Allowed by User',
              '110': 'INTERESTING PROCESS CAL',
              '111': 'INTERESTING PROCESS DETECTED',
              '200': 'Attachment Stripped',
              '500': 'Not Applicable',
              '1000': 'INTERESTING PROCESS HASHED DETECTED',
              '1001': 'DNS HOST FILE EXCEPTOION'
             }

    for k, v in action.items():
        if k == _:
            return v

    else:
        return _


def log_c_action(_):
    action = {
              '0': 'Allow',
              '1': 'Block',
              '2': 'Ask',
              '3': 'Continue',
              '4': 'Terminate'
             }

    for k, v in action.items():
        if k == str(_):
            return v

    else:
        return _


def log_virus_type(_):
    virus = {
             '48': 'Heuristic',
             '64': 'Reputation',
             '80': 'Hack Tools',
             '96': 'Spyware',
             '112': 'Trackware',
             '128': 'Dialers',
             '144': 'Remote Access',
             '160': 'Adware',
             '176': 'Joke Programs',
             '224': 'Heuristic Application',
            }

    for k, v in virus.items():
        if k == _:
            return v

    else:
        return _


def log_quarantine_forward_status(_):
    status = {
              '0': 'None',
              '1': 'Failed',
              '2': 'OK'
             }

    for k, v in status.items():
        if k == _:
            return v

    else:
        return _


def log_yn(_):
    yn = {
          '0': 'No',
          '1': 'Yes'
         }

    for k, v in yn.items():
        if k == _:
            return v

    else:
        return _


def log_clean_info(_):
    clean = {
             '0': 'Cleanable',
             '1': 'No Clean Pattern',
             '2': 'Not Cleanable'
            }

    for k, v in clean.items():
        if k == _:
            return v

    else:
        return _


def log_delete_info(_):
    delete = {
              '4': 'Deletable',
              '5': 'Not Deletable'
             }

    for k, v in delete.items():
        if k == _:
            return v

    else:
        return _


def log_eraser_status(_):
    status = {
              '0': 'Success',
              '1': 'Reboot Required',
              '2': 'Nothing To Do',
              '3': 'Repaired',
              '4': 'Deleted',
              '5': 'False',
              '6': 'Abort',
              '7': 'Continue',
              '8': 'Service Not Stopped',
              '9': 'Application Heuristic Scan Failure',
              '10': 'Cannot Remediate',
              '11': 'Whitelist Failure',
              '12': 'Driver Failure',
              '13': 'Reserved01',
              '13': 'Commercial Application List Failure',
              '13': 'Application Heuristic Scan Invalid OS',
              '13': 'Content Manager Data Error',
              '999': 'Leave Alone',
              '1000': 'Generic Failure',
              '1001': 'Out Of Memory',
              '1002': 'Not Initialized',
              '1003': 'Invalid Argument',
              '1004': 'Insufficient Buffer',
              '1005': 'Decryption Error',
              '1006': 'File Not Found',
              '1007': 'Out Of Range',
              '1008': 'COM Error',
              '1009': 'Partial Failure',
              '1010': 'Bad Definitions',
              '1011': 'Invalid Command',
              '1012': 'No Interface',
              '1013': 'RSA Error',
              '1014': 'Path Not Empty',
              '1015': 'Invalid Path',
              '1016': 'Path Not Empty',
              '1017': 'File Still Present',
              '1018': 'Invalid OS',
              '1019': 'Not Implemented',
              '1020': 'Access Denied',
              '1021': 'Directory Still Present',
              '1022': 'Inconsistent State',
              '1023': 'Timeout',
              '1024': 'Action Pending',
              '1025': 'Volume Write Protected',
              '1026': 'Not Reparse Point',
              '1027': 'File Exists',
              '1028': 'Target Protected',
              '1029': 'Disk Full',
              '1030': 'Shutdown In Progress',
              '1031': 'Media Error',
              '1032': 'Network Defs Error'
              }

    for k, v in status.items():
        if k == _:
            return v

    else:
        return _


def log_eraser_category_id(_):
    eraser = {
              '1': 'HeuristicTrojanWorm',
              '2': 'HeuristicKeyLogger',
              '100': 'CommercialRemoteControl',
              '101': 'CommercialKeyLogger',
              '200': 'Cookie',
              '300': 'Shields'
             }

    for k, v in eraser.items():
        if k == _:
            return v

    else:
        return _


def log_dynamic_categoryset_id(_):
    id = {
          '1': 'MALWARE',
          '2': 'SECURITY_RISK',
          '3': 'POTENTIALLY_UNWANTED_APPLICATIONS',
          '4': 'EXPERIMENTAL_HEURISTIC',
          '5': 'LEGACY_VIRAL',
          '6': 'LEGACY_NON_VIRAL',
          '7': 'VATEGORY_CRIMEWARE',
          '8': 'ADVANCED_HEURISTICS',
          '9': 'REPUTATION_BACKED_ADVANCED_HEURISTICS',
          '10': 'PREVALENCE_BACKED_ADVANCED_HEURISTICS'
         }

    for k, v in id.items():
        if k == _:
            return v

    else:
        return _


def log_display_name_to_use(_):
    display = {
               '0': 'Application Name',
               '1': 'VID Virus Name'
              }

    for k, v in display.items():
        if k == _.rstrip():
            return v

    else:
        return _


def log_reputation_disposition(_):
    rep = {
           '0': 'Good',
           '1': 'Bad',
           '127': 'Unknown'
          }

    for k, v in rep.items():
        if k == _:
            return v

    else:
        return _


def log_reputation_confidence(_):
    _ = int(_) if _ else ''
    conf = {
            range(0, 10): 'Unknown',
            range(10, 25): 'Low',
            range(25, 65): 'Medium',
            range(65, 100): 'High',
            range(100, 200): 'Extremely High'
           }

    for k in conf:
        if _ in k:
            return conf[k]

    else:
        return _


def log_reputation_prevalence(_):
    _ = int(_) if _ else ''
    prev = {
            range(0, 1): 'Unknown',
            range(1, 51): 'Very Low',
            range(51, 101): 'Low',
            range(101, 151): 'Moderate',
            range(151, 201): 'High',
            range(201, 256): 'Very High',
            range(256, 356): 'Extremely High'
           }

    for k in prev:
        if _ in k:
            return prev[k]

    else:
        return _


def log_detection_type(_):
    dtype = {
             '0': 'Traditional',
             '1': 'Heuristic'
            }

    for k, v in dtype.items():
        if k == _:
            return v

    else:
        return _


def log_vsic_state(_):
    state = {
             '0': 'Off',
             '1': 'On',
             '': 'Failed'
            }

    for k, v in state.items():
        if k == _:
            return v

    else:
        return _


def log_target_app_type(_):
    target = {
              '0': 'Normal',
              '1': 'Metro'
             }

    for k, v in target.items():
        if k == _:
            return v

    else:
        return _


def cids_state(_):
    status = {
              '0': 'Disabled',
              '1': 'On',
              '2': 'Not Installed',
              '3': 'Disabled By Policy',
              '4': 'Malfunctioning',
              '5': 'Disabled As Unlicensed',
              '127': 'Status Not Reported'
             }

    for k, v in status.items():
        if k == _:
            return v

    else:
        return _


def log_flags(_):

    flagStr = ''
    if _ & 0x400000:
        flagStr = flagStr + "EB_ACCESS_DENIED "

    if _ & 0x800000:
        flagStr = flagStr + "EB_NO_VDIALOG "

    if _ & 0x1000000:
        flagStr = flagStr + "EB_LOG "

    if _ & 0x2000000:
        flagStr = flagStr + "EB_REAL_CLIENT "

    if _ & 0x4000000:
        flagStr = flagStr + "EB_ENDUSER_BLOCKED "

    if _ & 0x8000000:
        flagStr = flagStr + "EB_AP_FILE_WIPED "

    if _ & 0x10000000:
        flagStr = flagStr + "EB_PROCESS_KILLED "

    if _ & 0x20000000:
        flagStr = flagStr + "EB_FROM_CLIENT "

    if _ & 0x40000000:
        flagStr = flagStr + "EB_EXTRN_EVENT "

    if _ & 0x1FF:

        if _ & 0x1:
            flagStr = flagStr + "FA_SCANNING_MEMORY "

        if _ & 0x2:
            flagStr = flagStr + "FA_SCANNING_BOOT_SECTOR "

        if _ & 0x4:
            flagStr = flagStr + "FA_SCANNING_FILE "

        if _ & 0x8:
            flagStr = flagStr + "FA_SCANNING_BEHAVIOR "

        if _ & 0x10:
            flagStr = flagStr + "FA_SCANNING_CHECKSUM "

        if _ & 0x20:
            flagStr = flagStr + "FA_WALKSCAN "

        if _ & 0x40:
            flagStr = flagStr + "FA_RTSSCAN "

        if _ & 0x80:
            flagStr = flagStr + "FA_CHECK_SCAN "

        if _ & 0x100:
            flagStr = flagStr + "FA_CLEAN_SCAN "

    if _ & 0x803FFE00:
        flagStr = flagStr + "EB_N_OVERLAYS("

        if _ & 0x200:
            flagStr = flagStr + "N_OFFLINE "

        if _ & 0x400:
            flagStr = flagStr + "N_INFECTED "

        if _ & 0x800:
            flagStr = flagStr + "N_REPSEED_SCAN "

        if _ & 0x1000:
            flagStr = flagStr + "N_RTSNODE "

        if _ & 0x2000:
            flagStr = flagStr + "N_MAILNODE "

        if _ & 0x4000:
            flagStr = flagStr + "N_FILENODE "

        if _ & 0x8000:
            flagStr = flagStr + "N_COMPRESSED "

        if _ & 0x10000:
            flagStr = flagStr + "N_PASSTHROUGH "

        if _ & 0x40000:
            flagStr = flagStr + "N_DIRNODE "

        if _ & 0x80000:
            flagStr = flagStr + "N_ENDNODE "

        if _ & 0x100000:
            flagStr = flagStr + "N_MEMNODE "

        if _ & 0x200000:
            flagStr = flagStr + "N_ADMIN_REQUEST_REMEDIATION "

        flagStr = flagStr[:-1] + ")"

    return flagStr


def remediation_type_desc(_):
    remType = {
               '0': '',
               '2000': 'Registry',
               '2001': 'File',
               '2002': 'Process',
               '2003': 'Batch File',
               '2004': 'INI File',
               '2005': 'Service',
               '2006': 'Infected File',
               '2007': 'COM Object',
               '2008': 'Host File Entry',
               '2009': 'Directory',
               '2010': 'Layered Service Provider',
               '2011': 'Internet Browser Cache'
              }

    for k, v in remType.items():
        if k == str(_):
            return v

    return _


def hash_type(_):

    hashType = {
                '0': 'MD5',
                '1': 'SHA-1',
                '2': 'SHA-256'
               }

    for k, v in hashType.items():
        if k == _:
            return v

    return _


def log_tp_event(eventType, _):

    if eventType == '301':
        event = {
                 '1': 'File","Create',
                 '2': 'File","Delete',
                 '3': 'File","Open',
                 '6': 'Directory","Create',
                 '7': 'Directory","Delete',
                 '14': 'Registry Key","Create',
                 '15': 'Registry Key","Delete',
                 '16': 'Registry Value","Delete',
                 '17': 'Registry Value","Set',
                 '18': 'Registry Key","Rename',
                 '19': 'Registry Key","Set Security',
                 '45': 'File","Set Security',
                 '46': 'Directory","Set Security',
                 '55': 'Process","Open',
                 '56': 'Process","Duplicate',
                 '58': 'Thread","Duplicate'
                }

        for k, v in event.items():
            if k == _:
                return v

    return str('","'+_)


def idsxp_protocol(_):
    protocol = {
                0: 'HOPOPT',
                1: 'ICMP',
                2: 'IGMP',
                3: 'GGP',
                4: 'IPv4',
                5: 'ST',
                6: 'TCP',
                7: 'CBT',
                8: 'EGP',
                9: 'IGP',
                10: 'BBN-RCC-MON',
                11: 'NVP-II',
                12: 'PUP',
                13: 'ARGUS (deprecated)',
                14: 'EMCON',
                15: 'XNET',
                16: 'CHAOS',
                17: 'UDP',
                18: 'MUX',
                19: 'DCN-MEAS',
                20: 'HMP',
                21: 'PRM',
                22: 'XNS-IDP',
                23: 'TRUNK-1',
                24: 'TRUNK-2',
                25: 'LEAF-1',
                26: 'LEAF-2',
                27: 'RDP',
                28: 'IRTP',
                29: 'ISO-TP4',
                30: 'NETBLT',
                31: 'MFE-NSP',
                32: 'MERIT-INP',
                33: 'DCCP',
                34: '3PC',
                35: 'IDPR',
                36: 'XTP',
                37: 'DDP',
                38: 'IDPR-CMTP',
                39: 'TP++',
                40: 'IL',
                41: 'IPv6',
                42: 'SDRP',
                43: 'IPv6-Route',
                44: 'IPv6-Frag',
                45: 'IDRP',
                46: 'RSVP',
                47: 'GRE',
                48: 'DSR',
                49: 'BNA',
                50: 'ESP',
                51: 'AH',
                52: 'I-NLSP',
                53: 'SWIPE (deprecated)',
                54: 'NARP',
                55: 'MOBILE',
                56: 'TLSP',
                57: 'SKIP',
                58: 'IPv6-ICMP',
                59: 'IPv6-NoNxt',
                60: 'IPv6-Opts',
                61: 'Any Host Internal Protocol',
                62: 'CFTP',
                63: 'Any Local Network',
                64: 'SAT-EXPAK',
                65: 'KRYPTOLAN',
                66: 'RVD',
                67: 'IPPC',
                68: 'Any Distributed File System',
                69: 'SAT-MON',
                70: 'VISA',
                71: 'IPCV',
                72: 'CPNX',
                73: 'CPHB',
                74: 'WSN',
                75: 'PVP',
                76: 'BR-SAT-MON',
                77: 'SUN-ND',
                78: 'WB-MON',
                79: 'WB-EXPAK',
                80: 'ISO-IP',
                81: 'VMTP',
                82: 'SECURE-VMTP',
                83: 'VINES',
                84: 'TTP/IPTM',
                85: 'NSFNET-IGP',
                86: 'DGP',
                87: 'TCF',
                88: 'EIGRP',
                89: 'OSPFIGP',
                90: 'Sprite-RPC',
                91: 'LARP',
                92: 'MTP',
                93: 'AX.25',
                94: 'IPIP',
                95: 'MICP (deprecated)',
                96: 'SCC-SP',
                97: 'ETHERIP',
                98: 'ENCAP',
                99: 'Any Private Encryption Scheme',
                100: 'GMTP',
                101: 'IFMP',
                102: 'PNNI',
                103: 'PIM',
                104: 'ARIS',
                105: 'SCPS',
                106: 'QNX',
                107: 'A/N',
                108: 'IPComp',
                109: 'SNP',
                110: 'Compaq-Peer',
                111: 'IPX-in-IP',
                112: 'VRRP',
                113: 'PGM',
                114: 'Any 0-hop Protocol',
                115: 'L2TP',
                116: 'DDX',
                117: 'IATP',
                118: 'STP',
                119: 'SRP',
                120: 'UTI',
                121: 'SMP',
                122: 'SM (deprecated)',
                123: 'PTP',
                124: 'ISIS over IPv4',
                125: 'FIRE',
                126: 'CRTP',
                127: 'CRUDP',
                128: 'SSCOPMCE',
                129: 'IPLT',
                130: 'SPS',
                131: 'PIPE',
                132: 'SCTP',
                133: 'FC',
                134: 'RSVP-E2E-IGNORE',
                135: 'Mobility Header',
                136: 'UDPLite',
                137: 'MPLS-in-IP',
                138: 'manet',
                139: 'HIP',
                140: 'Shim6',
                141: 'WESP',
                142: 'ROHC',
                143: 'Ethernet',
                range(144, 252): 'Unassigned	',
                253: 'Experementation/Testing',
                254: 'Experementation/Testing',
                255: 'Reserved'
               }

    for k, v in protocol.items():
        if k == _:
            return v

    else:
        return str(_)


def protocol(_):
    protocol = {
                '301': 'TCP initiated',
                '302': 'UDP datagram',
                '303': 'Ping request',
                '304': 'TCP completed',
                '305': 'Traffic (other)',
                '306': 'ICMPv4 packet',
                '307': 'Ethernet packet',
                '308': 'IP packet',
                '309': 'ICMPv6 packet'
               }

    for k, v in protocol.items():
        if k == str(_):
            return v

    else:
        return _


def eth_type(_):
    type = {
            range(257, 512): 'Experimental',
            512: 'XEROX PUP (see 0A00)',
            513: 'PUP Addr Trans (see 0A01)',
            1024: 'Nixdorf',
            1536: 'XEROX NS IDP',
            1632: 'DLOG',
            1633: 'DLOG',
            2048: 'Internet Protocol version 4 (IPv4)',
            2049: 'X.75 Internet',
            2050: 'NBS Internet',
            2051: 'ECMA Internet',
            2052: 'Chaosnet',
            2053: 'X.25 Level 3',
            2054: 'Address Resolution Protocol (ARP)',
            2055: 'XNS Compatability',
            2056: 'Frame Relay ARP',
            2076: 'Symbolics Private',
            range(2184, 2187): 'Xyplex',
            2304: 'Ungermann-Bass net debugr',
            2560: 'Xerox IEEE802.3 PUP',
            2561: 'PUP Addr Trans',
            2989: 'Banyan VINES',
            2990: 'VINES Loopback',
            2991: 'VINES Echo',
            4096: 'Berkeley Trailer nego',
            range(4097, 4112): 'Berkeley Trailer encap/IP',
            5632: 'Valid Systems',
            8947: 'TRILL',
            8948: 'L2-IS-IS',
            16962: 'PCS Basic Block Protocol',
            21000: 'BBN Simnet',
            24576: 'DEC Unassigned (Exp.)',
            24577: 'DEC MOP Dump/Load',
            24578: 'DEC MOP Remote Console',
            24579: 'DEC DECNET Phase IV Route',
            24580: 'DEC LAT',
            24581: 'DEC Diagnostic Protocol',
            24582: 'DEC Customer Protocol',
            24583: 'DEC LAVC; SCA',
            range(24584, 24586): 'DEC Unassigned',
            range(24592, 24597): '3Com Corporation',
            25944: 'Trans Ether Bridging',
            25945: 'Raw Frame Relay',
            28672: 'Ungermann-Bass download',
            28674: 'Ungermann-Bass dia/loop',
            range(28704, 28714): 'LRT',
            28720: 'Proteon',
            28724: 'Cabletron',
            32771: 'Cronus VLN',
            32772: 'Cronus Direct',
            32773: 'HP Probe',
            32774: 'Nestar',
            32776: 'AT&T',
            32784: 'Excelan',
            32787: 'SGI diagnostics',
            32788: 'SGI network games',
            32789: 'SGI reserved',
            32790: 'SGI bounce server',
            32793: 'Apollo Domain',
            32814: 'Tymshare',
            32815: 'Tigan; Inc.',
            32821: 'Reverse Address Resolution Protocol (RARP)',
            32822: 'Aeonic Systems',
            32824: 'DEC LANBridge',
            range(32825, 32829): 'DEC Unassigned',
            32829: 'DEC Ethernet Encryption',
            32830: 'DEC Unassigned',
            32831: 'DEC LAN Traffic Monitor',
            range(32832, 32835): 'DEC Unassigned',
            32836: 'Planning Research Corp.',
            32838: 'AT&T',
            32839: 'AT&T',
            32841: 'ExperData',
            32859: 'Stanford V Kernel exp.',
            32860: 'Stanford V Kernel prod.',
            32861: 'Evans & Sutherland',
            32864: 'Little Machines',
            32866: 'Counterpoint Computers',
            32869: 'Univ. of Mass. @ Amherst',
            32870: 'Univ. of Mass. @ Amherst',
            32871: 'Veeco Integrated Auto.',
            32872: 'General Dynamics',
            32873: 'AT&T',
            32874: 'Autophon',
            32876: 'ComDesign',
            32877: 'Computgraphic Corp.',
            range(32878, 32888): 'Landmark Graphics Corp.',
            32890: 'Matra',
            32891: 'Dansk Data Elektronik',
            32892: 'Merit Internodal',
            range(32893, 32896): 'Vitalink Communications',
            32896: 'Vitalink TransLAN III',
            range(32897, 32900): 'Counterpoint Computers',
            32923: 'Appletalk',
            range(32924, 32927): 'Datability',
            32927: 'Spider Systems Ltd.',
            32931: 'Nixdorf Computers',
            range(32932, 32948): 'Siemens Gammasonics Inc.',
            range(32960, 32964): 'DCA Data Exchange Cluster',
            32964: 'Banyan Systems',
            32965: 'Banyan Systems',
            32966: 'Pacer Software',
            32967: 'Applitek Corporation',
            range(32968, 32973): 'Intergraph Corporation',
            range(32973, 32975): 'Harris Corporation',
            range(32975, 32979): 'Taylor Instrument',
            range(32979, 32981): 'Rosemount Corporation',
            32981: 'IBM SNA Service on Ether',
            32989: 'Varian Associates',
            range(32990, 32992): 'Integrated Solutions TRFS',
            range(128, 524289): 'Allen-Bradley',
            range(8388608, 33009): 'Datability',
            33010: 'Retix',
            33011: 'AppleTalk AARP (Kinetics)',
            range(33012, 33014): 'Kinetics',
            33015: 'Apollo Computer',
            33023: 'Wellfleet Communications',
            33024: 'Customer VLAN Tag Type (C-Tag; formerly called the Q-Tag) (initially Wellfleet)',
            range(33025, 33028): 'Wellfleet Communications',
            range(33031, 33034): 'Symbolics Private',
            33072: 'Hayes Microcomputers',
            33073: 'VG Laboratory Systems',
            range(33074, 33079): 'Bridge Communications',
            range(33079, 33081): 'Novell; Inc.',
            range(33081, 33086): 'KTI',
            33096: 'Logicraft',
            33097: 'Network Computing Devices',
            33098: 'Alpha Micro',
            33100: 'SNMP',
            33101: 'BIIN',
            33102: 'BIIN',
            33103: 'Technically Elite Concept',
            33104: 'Rational Corp',
            range(33105, 33108): 'Qualcomm',
            range(33116, 33119): 'Computer Protocol Pty Ltd',
            range(33124, 33127): 'Charles River Data System',
            33149: 'XTP',
            33150: 'SGI/Time Warner prop.',
            33152: 'HIPPI-FP encapsulation',
            33153: 'STP; HIPPI-ST',
            33154: 'Reserved for HIPPI-6400',
            33155: 'Reserved for HIPPI-6400',
            range(33156, 33165): 'Silicon Graphics prop.',
            33165: 'Motorola Computer',
            range(33178, 33188): 'Qualcomm',
            33188: 'ARAI Bunkichi',
            range(33189, 33199): 'RAD Network Devices',
            range(33207, 33210): 'Xyplex',
            range(33228, 33238): 'Apricot Computers',
            range(33238, 33246): 'Artisoft',
            range(33254, 33264): 'Polygon',
            range(33264, 33267): 'Comsat Labs',
            range(33267, 33270): 'SAIC',
            range(33270, 33273): 'VG Analytical',
            range(33283, 33286): 'Quantum Software',
            range(33313, 33315): 'Ascom Banking Systems',
            range(33342, 33345): 'Advanced Encryption Syste',
            range(33407, 33411): 'Athena Programming',
            range(33379, 33387): 'Charles River Data System',
            range(33434, 33436): 'Inst Ind Info Tech',
            range(33436, 33452): 'Taurus Controls',
            range(33452, 34452): 'Walker Richer & Quinn',
            range(34452, 34462): 'Idea Courier',
            range(34462, 34466): 'Computer Network Tech',
            range(34467, 34477): 'Gateway Communications',
            34523: 'SECTRA',
            34526: 'Delta Controls',
            34525: 'Internet Protocol version 6 (IPv6)',
            34527: 'ATOMIC',
            range(34528, 34544): 'Landis & Gyr Powers',
            range(34560, 34577): 'Motorola',
            34667: 'TCP/IP Compression',
            34668: 'IP Autonomous Systems',
            34669: 'Secure Data',
            34824: 'IEEE Std 802.3 - Ethernet Passive Optical Network (EPON)',
            34827: 'Point-to-Point Protocol (PPP)',
            34828: 'General Switch Management Protocol (GSMP)',
            34887: 'MPLS',
            34888: 'MPLS with upstream-assigned label',
            34913: 'Multicast Channel Allocation Protocol (MCAP)',
            34915: 'PPP over Ethernet (PPPoE) Discovery Stage',
            34916: 'PPP over Ethernet (PPPoE) Session Stage',
            34958: 'IEEE Std 802.1X - Port-based network access control',
            34984: 'IEEE Std 802.1Q - Service VLAN tag identifier (S-Tag)',
            range(35478, 35480): 'Invisible Software',
            34997: 'IEEE Std 802 - Local Experimental Ethertype',
            34998: 'IEEE Std 802 - Local Experimental Ethertype',
            34999: 'IEEE Std 802 - OUI Extended Ethertype',
            35015: 'IEEE Std 802.11 - Pre-Authentication (802.11i)',
            35020: 'IEEE Std 802.1AB - Link Layer Discovery Protocol (LLDP)',
            35045: 'IEEE Std 802.1AE - Media Access Control Security',
            35047: 'Provider Backbone Bridging Instance tag',
            35061: 'IEEE Std 802.1Q  - Multiple VLAN Registration Protocol (MVRP)',
            35062: 'IEEE Std 802.1Q - Multiple Multicast Registration Protocol (MMRP)',
            35085: 'IEEE Std 802.11 - Fast Roaming Remote Request (802.11r)',
            35095: 'IEEE Std 802.21 - Media Independent Handover Protocol',
            35113: 'IEEE Std 802.1Qbe - Multiple I-SID Registration Protocol',
            35131: 'TRILL Fine Grained Labeling (FGL)',
            35136: 'IEEE Std 802.1Qbg - ECP Protocol (also used in 802.1BR)',
            35142: 'TRILL RBridge Channel',
            35143: 'GeoNetworking as defined in ETSI EN 302 636-4-1',
            35151: 'NSH (Network Service Header)',
            36864: 'Loopback',
            36865: '3Com(Bridge) XNS Sys Mgmt',
            36866: '3Com(Bridge) TCP-IP Sys',
            36867: '3Com(Bridge) loop detect',
            39458: 'Multi-Topology',
            41197: 'LoWPAN encapsulation',
            47082: 'The Ethertype will be used to identify a Channel in which control messages are encapsulated as payload of GRE packets. When a GRE packet tagged with the Ethertype is received; the payload will be handed to the network processor for processing.',
            65280: 'BBN VITAL-LanBridge cache',
            range(65280, 65296): 'ISC Bunker Ramo',
            65535: 'Reserved'
           }

    for k, v in type.items():
        if k == _:
            return v

    return _


def icmp_type_code(type, code):
    typeName = ''
    codeDescription = ''
    types = {
             0: {
                 'type': 'Echo Reply',
                 0: 'No Code'
                },
             1: {
                 'type': 'Unassigned'
                },
             2: {
                 'type': 'Unassigned'
                },
             3: {
                 'type': 'Destination Unreachable',
                 0: 'Net Unreachable',
                 1: 'Host Unreachable',
                 2: 'Protocol Unreachable',
                 3: 'Port Unreachable',
                 4: 'Fragmentation Needed and Do not Fragment was Set',
                 5: 'Source Route Failed',
                 6: 'Destination Network Unknown',
                 7: 'Destination Host Unknown',
                 8: 'Source Host Isolated',
                 9: 'Communication with Destination Network is Administratively Prohibited',
                 10: 'Communication with Destination Host is Administratively Prohibited',
                 11: 'Destination Network Unreachable for Type of Service',
                 12: 'Destination Host Unreachable for Type of Service',
                 13: 'Communication Administratively Prohibited',
                 14: 'Host Precedence Violation',
                 15: 'Precedence cutoff in effect'
                },
             4: {
                 'type': 'Source Quench (Deprecated)',
                 0: 'No Code'
                },
             5: {
                 'type': 'Redirect',
                 0: 'Redirect Datagram for the Network (or subnet)',
                 1: 'Redirect Datagram for the Host',
                 2: 'Redirect Datagram for the Type of Service and Network',
                 3: 'Redirect Datagram for the Type of Service and Host'
                },
             6: {
                 'type': 'Alternate Host Address (Deprecated)',
                 0: 'Alternate Address for Host'
                },
             7: {
                 'type': 'Unassigned'
                },
             8: {
                 'type': 'Echo',
                 0: 'No Code'
                },
             9: {
                 'type': 'Router Advertisement',
                 0: 'Normal router advertisement',
                 16: 'Does not route common traffic'
                },
             10: {
                 'type': 'Router Solicitation',
                 0: 'No Code'
                },
             11: {
                 'type': 'Time Exceeded',
                 0: 'Time to Live exceeded in Transit',
                 1: 'Fragment Reassembly Time Exceeded'
                },
             12: {
                 'type': 'Parameter Problem',
                 0: 'Pointer indicates the error',
                 1: 'Missing a Required Option',
                 2: 'Bad Length'
                },
             13: {
                 'type': 'Timestamp',
                 0: 'No Code'
                },
             14: {
                 'type': 'Timestamp Reply',
                 0: 'No Code'
                },
             15: {
                 'type': 'Information Request (Deprecated)',
                 0: 'No Code'
                },
             16: {
                 'type': 'Information Reply (Deprecated)',
                 0: 'No Code'
                },
             17: {
                 'type': 'Address Mask Request (Deprecated)',
                 0: 'No Code'
                },
             18: {
                 'type': 'Address Mask Reply (Deprecated)',
                 0: 'No Code'
                },
             19: {
                 'type': 'Reserved (for Security)'
                },
             range(20, 30): {
                 'type': 'Reserved (for Robustness Experiment)'
                },
             30: {
                 'type': 'Traceroute (Deprecated)'
                },
             31: {
                 'type': 'Datagram Conversion Error (Deprecated)'
                },
             32: {
                 'type': 'Mobile Host Redirect (Deprecated)'
                },
             33: {
                 'type': 'IPv6 Where-Are-You (Deprecated)'
                },
             34: {
                 'type': 'IPv6 I-Am-Here (Deprecated)'
                },
             35: {
                 'type': 'Mobile Registration Request (Deprecated)'
                },
             36: {
                 'type': 'Mobile Registration Reply (Deprecated)'
                },
             37: {
                 'type': 'Domain Name Request (Deprecated)'
                },
             38: {
                 'type': 'Domain Name Reply (Deprecated))'
                },
             39: {
                 'type': 'SKIP (Deprecated)'
                },
             40: {
                 'type': 'Photuris',
                 0: 'Bad SPI',
                 1: 'Authentication Failed',
                 2: 'Decompression Failed',
                 3: 'Decryption Failed',
                 4: 'Need Authentication',
                 5: 'Need Authorization'
                },
             41: {
                 'type': 'ICMP messages utilized by experimental mobility protocols such as Seamoby'
                },
             42: {
                 'type': 'Extended Echo Request',
                 0: 'No Error',
                 range(1, 256): 'Unassigned'
                },
             43: {
                 'type': 'Extended Echo Reply',
                 0: 'No Error',
                 1: 'Malformed Query',
                 2: 'No Such Interface',
                 3: 'No Such Table Entry',
                 4: 'Multiple Interfaces Satisfy Query',
                 range(5, 256): 'Unassigned'
                },
             range(44, 253): {
                 'type': 'Unassigned'
                },
             253: {
                 'type': 'RFC3692-style Experiment 1'
                },
             254: {
                 'type': 'RFC3692-style Experiment 2'
                },
             255: {
                 'type': 'Reserved'
                }
            }

    for k, v in types.items():
        if k == type:
            typeName = types[type]['type']

    for k, v in types[type].items():
        if k == code:
            codeDescription = types[type][code]

    return typeName, codeDescription


def test_mode(_):
    testMode = {
                '0': 'Production',
                '1': 'Yes'
               }

    for k, v in testMode.items():
        if k == str(_):
            return v

    return _


def sec_event_id(_):
    eventid = {
               # Installation events Possible values are:
               '12070001': 'Internal error',
               '12070101': 'Install complete',
               '12070102': 'Restart recommended',
               '12070103': 'Restart required',
               '12070104': 'Installation failed',
               '12070105': 'Uninstallation complete',
               '12070106': 'Uninstallation failed',
               '12071037': 'Symantec Endpoint Protection installed',
               '12071038': 'Symantec Firewall installed',
               '12071039': 'Uninstall',
               '1207103A': 'Uninstall rolled-back',
               # Service events Possible values are:
               '12070201': 'Service starting',
               '12070202': 'Service started',
               '12070203': 'Service start failure',
               '12070204': 'Service stopped',
               '12070205': 'Service stop failure',
               '1207021A': 'Attempt to stop service',
               # Configuration events Possible values are:
               '12070206': 'Config import complete',
               '12070207': 'Config import error',
               '12070208': 'Config export complete',
               '12070209': 'Config export error',
               # Host Integrity events Possible values are:
               '12070210': 'Host Integrity disabled',
               '12070211': 'Host Integrity enabled',
               '12070220': 'NAP integration enabled',
               # Import events Possible values are:
               '12070214': 'Successfully imported advanced rule',
               '12070215': 'Failed to import advanced rule',
               '12070216': 'Successfully exported advanced rule',
               '12070217': 'Failed to export advanced rule',
               '1207021B': 'Imported sylink',
               # Client events Possible values are:
               '12070218': 'Client Engine enabled',
               '12070219': 'Client Engine disabled',
               '12071046': 'Proactive Threat Scanning is not supported on this platform',
               '12071047': 'Proactive Threat Scanning load error',
               '12071048': 'SONAR content load error',
               '12071049': 'Allow application',
               # Server events Possible values are:
               '12070301': 'Server connected',
               '12070302': 'No server response',
               '12070303': 'Server connection failed',
               '12070304': 'Server disconnected',
               '120B0001': 'Cannot reach server',
               '120B0002': 'Reconnected to the server',
               '120b0003': 'Automatic upgrade complete',
               # Policy events Possible values are:
               '12070306': 'New policy received',
               '12070307': 'New policy applied',
               '12070308': 'New policy failed',
               '12070309': 'Cannot download policy',
               '120B0005': 'Cannot download policy',
               '1207030A': 'Have latest policy',
               '120B0004': 'Have latest policy',
               # Antivirus engine events Possible values are:
               '12071006': 'Scan omission',
               '12071007': 'Definition file loaded',
               '1207100B': 'Virus behavior detected',
               '1207100C': 'Configuration changed',
               '12071010': 'Definition file download',
               '12071012': 'Sent to quarantine server',
               '12071013': 'Delivered to Symantec',
               '12071014': 'Security Response backup',
               '12071015': 'Scan aborted',
               '12071016': 'Symantec Endpoint Protection Auto-Protect Load error',
               '12071017': 'Symantec Endpoint Protection Auto-Protect enabled',
               '12071018': 'Symantec Endpoint Protection Auto-Protect disabled',
               '1207101A': 'Scan delayed',
               '1207101B': 'Scan restarted',
               '12071027': 'Symantec Endpoint Protection is using old virus definitions',
               '12071041': 'Scan suspended',
               '12071042': 'Scan resumed',
               '12071043': 'Scan duration too short',
               '12071045': 'Scan enhancements failed',
               # Licensing events Possible values are:
               '1207101E': 'License warning',
               '1207101F': 'License error',
               '12071020': 'License in grace period',
               '12071023': 'License installed',
               '12071025': 'License up-to-date',
               # Security events Possible values are:
               '1207102B': 'Computer not compliant with security policy',
               '1207102C': 'Computer compliant with security policy',
               '1207102D': 'Tamper attempt',
               '12071034': 'Login failed',
               '12071035': 'Login succeeded',
               # Submission events Possible values are:
               '12120001': 'System message from centralized reputation',
               '12120002': 'Authentication token failure',
               '12120003': 'Reputation failure',
               '12120004': 'Reputation network failure',
               '12130001': 'System message from Submissions',
               '12130002': 'Submissions failure',
               '12130003': 'Intrusion prevention submission',
               '12130004': 'Antivirus detection submission',
               '12130005': 'Antivirus advanced heuristic detection submission',
               '12130006': 'Manual user submission',
               '12130007': 'SONAR heuristic submission',
               '12130008': 'SONAR detection submission',
               '12130009': 'File Reputation submission',
               '1213000A': 'Client authentication token request',
               '1213000B': 'LiveUpdate error submission',
               '1213000C': 'Process data submission',
               '1213000D': 'Configuration data submission',
               '1213000E': 'Network data submission',
               # Other events Possible values are:
               '1207020A': 'Email post OK',
               '1207020B': 'Email post failure',
               '1207020C': 'Update complete',
               '1207020D': 'Update failure',
               '1207020E': 'Manual location change',
               '1207020F': 'Location changed',
               '12070212': 'Old rasdll version detected',
               '12070213': 'Auto-update postponed',
               '12070305': 'Mode changed',
               '1207030B': 'Cannot apply HI script',
               '1207030C': 'Content Update Server',
               '1207030D': 'Content Update Packet',
               '12070500': 'System message from device control',
               '12070600': 'System message from anti-buffer overflow driver',
               '12070700': 'System message from network access component',
               '12070800': 'System message from LiveUpdate',
               '12070900': 'System message from GUP',
               '12072000': 'System message from Memory Exploit Mitigation',
               '12072009': 'Intensive Protection disabled',
               '1207200A': 'Intensive Protection enabled',
               '12071021': 'Access denied warning',
               '12071022': 'Log forwarding error',
               '12071044': 'Client moved',
               '12071036': 'Access denied warning',
               '12071000': 'Message from Intrusion Prevention',
               '12071050': 'SONAR disabled',
               '12071051': 'SONAR enabled'
              }

    for k, v in eventid.items():

        if k == _.upper():
            return v

    return _


def raw_event_id(_):

    eventid = {
               '401': 'Raw Ethernet'
              }

    for k, v in eventid.items():

        if k == str(_):
            return v


def process_event_id(_):

    eventid = {
               '501': 'Application Control Driver',
               '502': 'Application Control Rules',
               '999': 'Tamper Protection'
              }

    for k, v in eventid.items():

        if k == str(_):
            return v


def attrib_type(_):

    attid = {
             2: '$EA',
             4: '$DATA',
             7: '$OBJECT_ID'
            }

    for k, v in attid.items():

        if k == _:
            return v


def read_unpack_hex(f, loc, count):

    # jump to the specified location
    f.seek(loc)

    raw = f.read(count)
    result = int(raw, 16)

    return result


def read_log_entry(f, loc, count):

    # jump to the specified location
    f.seek(loc)

    return f.read(count)

def read_ndca(_):
    _ = io.BytesIO(_)
    _.seek(20)
    bodylength = int(flip(_.read(4).hex()), 16)
    _.seek(4, 1)
    total = int(flip(_.read(4).hex()), 16)
    _.seek(9, 1)
    n = 0
    msg = []

    while n != total:
        header = int(_.read(7)[3:-3].hex(), 16)
        datalength = int(flip(_.read(2).hex()), 16)
        entrylength = int(flip(_.read(2).hex()), 16)
        entry = _.read(entrylength).decode("utf-8", "ignore")

        if header == 6:
            data = _.read(datalength).decode("utf-8", "ignore")

        else:
            data = int(flip(_.read(datalength).hex()), 16)

        msg.append(f'{entry}  {data}')
        _.seek(1, 1)
        n += 1

    _.seek(-1, 1)
    msg.append(_.read(bodylength).decode("utf-8", "ignore").translate(__vis_filter))

    return '\n'.join(msg)


def read_log_data(data, tz):
    entry = LogFields()
    data = re.split(',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', data.decode("utf-8", "ignore"))
    field113 = ''
    field115 = ''
    field119 = ''
    field122 = ''
    field123 = ''
    field124 = ''
    field125 = ''
    field126 = ''
    entry.time = from_symantec_time(data[0], tz)
    entry.event = log_event(data[1])
    entry.category = log_category(data[2])
    entry.logger = log_logger(data[3])
    entry.computer = data[4]
    entry.user = data[5]
    entry.virus = data[6]
    entry.file = data[7]
    entry.wantedaction1 = log_action(data[8])
    entry.wantedaction2 = log_action(data[9])
    entry.realaction = log_action(data[10])
    entry.virustype = log_virus_type(data[11])
    entry.flags = log_flags(int(data[12]))
    entry.description = log_description(data)
    entry.scanid = data[14]
    entry.newext = data[15]
    entry.groupid = data[16]
    entry.eventdata = event_data1(data[17])
    entry.vbinid = data[18]
    entry.virusid = data[19]
    entry.quarantineforwardstatus = log_quarantine_forward_status(data[20])
    entry.access = data[21]
    entry.sdnstatus = data[22]
    entry.compressed = log_yn(data[23])
    entry.depth = data[24]
    entry.stillinfected = log_yn(data[25])
    entry.definfo = data[26]
    entry.defsequincenumber = data[27]
    entry.cleaninfo = log_clean_info(data[28])
    entry.deleteinfo = log_delete_info(data[29])
    entry.backupod = data[30]
    entry.parent = data[31]
    entry.guid = data[32]
    entry.clientgroup = data[33]
    entry.address = data[34]
    entry.domainname = data[35]
    entry.ntdomain = data[36]
    entry.macaddress = data[37]
    entry.version = data[38]
    entry.remotemachine = data[39]
    entry.remotemachineip = data[40]
    entry.action1status = data[41]
    entry.action2status = data[42]
    entry.licensefeaturename = data[43]
    entry.licensefeatureversion = data[44]
    entry.licenseserialnumber = data[45]
    entry.licensefulfillmentid = data[46]
    entry.licensestartdate = data[47]
    entry.licenseexpirationdate = data[48]
    entry.licenselifecycle = data[49]
    entry.licenseseatstotal = data[50]
    entry.licenseseats = data[51]
    entry.errorcode = data[52]
    entry.licenseseatsdelta = data[53]
    entry.status = log_eraser_status(data[54])
    entry.domainguid = data[55]
    entry.sessionguid = data[56]
    entry.vbnsessionid = data[57]
    entry.logindomain = data[58]

    try:
        entry.eventdata2 = event_data2(data[59])
        entry.erasercategoryid = log_eraser_category_id(data[60])
        entry.dynamiccategoryset = log_dynamic_categoryset_id(data[61])
        entry.subcategorysetid = data[62]
        entry.displaynametouse = log_display_name_to_use(data[63])
        entry.reputationdisposition = log_reputation_disposition(data[64])
        entry.reputationconfidence = log_reputation_confidence(data[65])
        entry.firsseen = data[66]
        entry.reputationprevalence = log_reputation_prevalence(data[67])
        entry.downloadurl = data[68]
        entry.categoryfordropper = data[69]
        entry.cidsstate = cids_state(data[70])
        entry.behaviorrisklevel = data[71]
        entry.detectiontype = log_detection_type(data[72])
        entry.acknowledgetext = data[73]
        entry.vsicstate = log_vsic_state(data[74])
        entry.scanguid = data[75]
        entry.scanduration = data[76]
        entry.scanstarttime = from_symantec_time(data[77], tz)
        entry.targetapptype = log_target_app_type(data[78])
        entry.scancommandguid = data[79]

    except:
        pass

    try:
        field113 = data[80]
        entry.location = data[81]
        field115 = data[82]
        entry.digitalsigner = data[83].replace('"', '')
        entry.digitalissuer = data[84]
        entry.digitalthumbprint = data[85]
        field119 = data[86]
        entry.digitalsn = data[87]
        entry.digitaltime = from_unix_sec(data[88])
        field122 = data[89]
        field123 = data[90]
        if re.match('^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?', data[91]):
            try:
                parsed = json.loads(base64.b64decode(data[91]))
                field124 = json.dumps(parsed, indent=4, sort_keys=True)
                field124 = field124.replace('"', '""')

            except:
                field124 = data[91]

        else:
            field124 = data[91]

        field125 = data[92]
        field126 = data[93]

    except:
        pass

    return f'"{entry.time}","{entry.event}","{entry.category}","{entry.logger}","{entry.computer}","{entry.user}","{entry.virus}","{entry.file}","{entry.wantedaction1}","{entry.wantedaction2}","{entry.realaction}","{entry.virustype}","{entry.flags}","{entry.description}","{entry.scanid}","{entry.newext}","{entry.groupid}","{entry.eventdata}","{entry.vbinid}","{entry.virusid}","{entry.quarantineforwardstatus}","{entry.access}","{entry.sdnstatus}","{entry.compressed}","{entry.depth}","{entry.stillinfected}","{entry.definfo}","{entry.defsequincenumber}","{entry.cleaninfo}","{entry.deleteinfo}","{entry.backupod}","{entry.parent}","{entry.guid}","{entry.clientgroup}","{entry.address}","{entry.domainname}","{entry.ntdomain}","{entry.macaddress}","{entry.version}","{entry.remotemachine}","{entry.remotemachineip}","{entry.action1status}","{entry.action2status}","{entry.licensefeaturename}","{entry.licensefeatureversion}","{entry.licenseserialnumber}","{entry.licensefulfillmentid}","{entry.licensestartdate}","{entry.licenseexpirationdate}","{entry.licenselifecycle}","{entry.licenseseatstotal}","{entry.licenseseats}","{entry.errorcode}","{entry.licenseseatsdelta}","{entry.status}","{entry.domainguid}","{entry.sessionguid}","{entry.vbnsessionid}","{entry.logindomain}","{entry.eventdata2}","{entry.erasercategoryid}","{entry.dynamiccategoryset}","{entry.subcategorysetid}","{entry.displaynametouse}","{entry.reputationdisposition}","{entry.reputationconfidence}","{entry.firsseen}","{entry.reputationprevalence}","{entry.downloadurl}","{entry.categoryfordropper}","{entry.cidsstate}","{entry.behaviorrisklevel}","{entry.detectiontype}","{entry.acknowledgetext}","{entry.vsicstate}","{entry.scanguid}","{entry.scanduration}","{entry.scanstarttime}","{entry.targetapptype}","{entry.scancommandguid}","{field113}","{entry.location}","{field115}","{entry.digitalsigner}","{entry.digitalissuer}","{entry.digitalthumbprint}","{field119}","{entry.digitalsn}","{entry.digitaltime}","{field122}","{field123}","{field124}","{field125}","{field126}"'


def read_sep_tag(_, fname, sub=False, vbn=False):
    total = len(_)
    _ = io.BytesIO(_)
    blob = False
    match = []
    dd = ''
    sddl = ''
    sid = ''
    guid = ''
    dec = ''
    dbguid = None
    lastguid = ''
    lasttoken = 0
    lastvalue = 0
    hit = None
    virus = ''
    results = ''
    binary = []
    count = 0
    verify = struct.unpack("B", _.read(1))[0]
    _.seek(-1, 1)
    tagtime = time.time()

    while True:
        i = _.tell()

        if vbn is True and (time.time() - tagtime) > 1 and not args.hex_dump:
            progress(i, total, status='Parsing Quarantine Metadata')

        if sub and verify != 6:
            break

        try:
            code = struct.unpack("B", _.read(1))[0]

        except:
            break

        dec += '{:02x}\n'.format(code)

        if code == 0:
            break

        if code == 1 or code == 10:
            _.seek(-1, 1)
            tag = vbnstruct.ASN1_1(_.read(2))
            dec += hexdump(tag.dumps()[1:])
            lastvalue = tag.dumps()[1:]

        elif code == 2:
            _.seek(-1, 1)
            tag = vbnstruct.ASN1_2(_.read(3))
            dec += hexdump(tag.dumps()[1:])

        elif code == 3 or code == 6:
            _.seek(-1, 1)
            tag = vbnstruct.ASN1_4(_.read(5))
            dec += hexdump(tag.dumps()[1:])

        elif code == 4:
            _.seek(-1, 1)
            tag = vbnstruct.ASN1_8(_.read(9))
            dec += hexdump(tag.dumps()[1:])

        elif code == 7:
            size = struct.unpack("<I", _.read(4))[0]
            _.seek(-5, 1)
            tag = vbnstruct.ASN1_String_A(_.read(5 + size))
            dec += hexdump(tag.dumps()[1:5])
            string = tag.dumps()[5:].decode('latin-1').replace("\x00", "")
            dec += hexdump(tag.dumps()[5:]) + f'### STRING-A\n      {string}\n'

            if hit == 'virus':
                virus = tag.StringA.decode('latin-1').replace("\x00", "")
                hit = None

            else:
                match.append(tag.StringA.decode('latin-1').replace("\x00", ""))

        elif code == 8:
            size = struct.unpack("<I", _.read(4))[0]
            _.seek(-5, 1)
            tag = vbnstruct.ASN1_String_W(_.read(5 + size))
            dec += hexdump(tag.dumps()[1:5])
            string = tag.dumps()[5:].decode('latin-1').replace("\x00", "").replace("\r\n", "\r\n\t  ")

            if lastguid == '00000000000000000000000000000000':
                rstring = string.replace("\r\n\t  ", "\n")

                results += f'{rstring}\n'

            dec += hexdump(tag.dumps()[5:]) + f'### STRING-W\n      {string}\n\n'

            if hit == 'virus':
                virus = tag.StringW.decode('latin-1').replace("\x00", "")
                hit = None

            else:
                match.append(tag.StringW.decode('latin-1').replace("\x00", ""))

        elif code == 9:
            size = struct.unpack("<I", _.read(4))[0]
            _.seek(-5, 1)

            if size == 16:
                tag = vbnstruct.ASN1_GUID(_.read(5 + size))
                dec += hexdump(tag.dumps()[1:5])
                dec += f'### GUID\n{hexdump(tag.dumps()[5:])}'
                if tag.dumps()[5:] == b'\xbb\x81\x1a:\x8f\xc1\xbeH\x82,\x8bbc\xa5 M':
                    blob = True
                else:
                    blob = False

                if re.match(b'\xb9\x1f\x8a\\\\\xb75\\\D\x98\x03%\xfc\xa1W\^q', tag.GUID):
                    hit = 'virus'

            elif blob is True or lastvalue == b'\x0f':
                if lasttoken == 8:
                    tag = vbnstruct.ASN1_4(_.read(5))
                    dec += hexdump(tag.dumps()[1:])
                    blob = True

                else:
                    tag = vbnstruct.ASN1_BLOB(_.read(5 + size))
                    dec += hexdump(tag.dumps()[1:5])
                    dec += f'### BLOB\n{hexdump(tag.dumps()[5:])}'

                    if b'\x00x\xda' in tag.dumps()[5:15]:
                        if tag.dumps()[5:].startswith(b'CMPR'):
                            dec += f'### BLOB Decompressed\n{hexdump(zlib.decompress(tag.dumps()[13:]))}'
                            binary.append(zlib.decompress(tag.dumps()[13:]))

                        else:
                            data = read_sep_tag(zlib.decompress(tag.dumps()[9:]), fname)
                            dec += f'### BLOB Decompressed\n{data[6]}### BLOB Decompressed End\n\n'

                            if os.path.exists(args.output+'/ccSubSDK/BHSvcPlg.csv'):
                                with fileinput.input(files=(args.output+'/ccSubSDK/BHSvcPlg.csv'), inplace=True, mode='r') as fn:
                                    reader = csv.DictReader(fn)
                                    header = '","'.join(reader.fieldnames)
                                    print(f'"{header}"')

                                    for row in reader:
                                        if fname in row['ccSubSDK File GUID']:
                                            row['SONAR'] = data[3] + '\n' + '\n'.join(data[0]) + '\n'

                                        val = '","'.join(str(x).replace('"', '""') for x in row.values())
                                        print(f'"{val}"')

                    else:
                        binary.append(tag.dumps()[5:])

                    blob = False

            else:
                tag = vbnstruct.ASN1_4(_.read(5))
                dec += hexdump(tag.dumps()[1:])
                blob = True

        elif code == 15:
            _.seek(-1, 1)
            tag = vbnstruct.ASN1_16(_.read(17))
            count += 1

            if count == 1:
                dbguid = '{' + '-'.join([flip(tag.dumps()[1:5].hex()), flip(tag.dumps()[5:7].hex()), flip(tag.dumps()[7:9].hex()), tag.dumps()[9:11].hex(), tag.dumps()[11:17].hex()]).upper() + '}'

            lastguid = tag.dumps()[1:].hex()
            dec += f'\n### GUID\n{hexdump(tag.dumps()[1:])}'

        elif code == 16:
            _.seek(-1, 1)
            tag = vbnstruct.ASN1_16(_.read(17))
            dec += hexdump(tag.dumps()[1:])

        else:
            if lasttoken != 9:
                if lasttoken == 1:
                    _.seek(-1, 1)
                    dec = dec[:-3]
                    tag = vbnstruct.ASN1_Error(_.read(16))
                    dec += f'### Error\n{hexdump(tag.dumps())}'

                else:
                    dec = ''
                    break

        lasttoken = code

        if args.hex_dump:
            cstruct.dumpstruct(tag)

    if vbn is True and (time.time() - tagtime) > 1 and not args.hex_dump:
        print('\n')

    for a in match:
        if 'Detection Digest:' in a:
            match.remove(a)
            dd = '\r\n'.join(a.split('\r\n')[1:]).replace('"', '""')

        try:
            sddl = sddl_translate(a)
            match.remove(a)

        except:
            pass

        rsid = re.match('^S-\d-(\d+-){1,14}\d+$', a)

        if rsid:
            sid = a
            match.remove(a)

        rguid = re.match('^(\{{0,1}([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}\}{0,1})$', a)

        if rguid:
            guid = a
            match.remove(a)

    if virus == '' and (len(match) >= 6 and vbn is True):
        virus = match[0]
        del match[0]

    return match, dd, sddl, sid, virus, guid, dec, dbguid, results, binary


def write_report(_, fname):
    for m in re.finditer('(?P<XML><Report Type="(?P<Report>.*?)".*Report>)', _):
        reportname = args.output+'/ccSubSDK/'+m.group('Report')+'.csv'
        header = []
        data = ['']

        if os.path.isfile(reportname):
            data = open(reportname).readlines()
            header = data[0][1:-2].split('","')
            header.remove('File Name')

        reporttype = open(reportname, 'w', encoding='utf-8')
        tree = ET.fromstring(m.group('XML').translate(__vis_filter))
        rows = ''

        for node in tree.iter():
            value = []

            for k, v in node.attrib.items():
                if k == 'Type' or k == 'Count':
                    continue

                else:
                    if k not in header:
                        header.append(k)

                    if len(header) > len(value):
                        diff = len(header) - len(value)
                        value += ' ' * diff

                    pos = header.index(k)

                    if k == 'Infection_Timestamp' or k == 'Discovery_Timestamp' or k == 'Active_timestamp':
                        value[pos] = from_unix_sec(v)

                    else:
                        value[pos] = v

            if len(value) != 0:
                value = '","'.join(value)
                rows += f'"{fname}","{value}"\n'

        header = '","'.join(header)
        data[0] = f'"File Name","{header}"\n'
        reporttype.writelines(data)
        reporttype.write(rows)
        reporttype.close()


def event_data1(_):
    pos = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    _ = _.replace('"', '').split('\t')

    if len(_) < 13:
        diff = 13 - len(_)
        b = [''] * diff
        _.extend(b)

    if ':' in _[0]:
        var = _[0]
        _ = _[0].split(':')
        _.insert(0, var)
        b = [''] * 7
        _.extend(b)

    labels = event_data1_labels(_[0])

    if _[0] == '101':
        _[9] = remediation_type_desc(_[9])

    assert(len(labels) == len(pos))
    acc = 0

    for i in range(len(labels)):
        _.insert(pos[i]+acc, labels[i])
        acc += 1

    _ = '","'.join(_)

    return _


def event_data1_labels(_):
    labels = []

    if _ == '101':
        labels = ["GUID", "Unknown", "Num Side Effects Repaired", "Anonaly Action Type", "Anomaly Action Operation", "Unknown", "Anomaly Name", "Anomaly Categories", "Anomaly Action Type ID", "Anomaly Action OperationID", "Previous Log GUID", "Unknown"]

    elif _ == '201':
        labels = ["Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown"]

    elif _ == '301':
        labels = ["Actor PID", "Actor", "Event", "Target PID", "Target", "Target Process", "Unknown", "Unknown", "N/A", "N/A", "N/A", "N/A"]

    elif len(_) > 3:
        labels = ["Scan Status", "Risks", "Scanned", "Files/Folders/Drives Omitted", "Trusted Files Skipped", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]

    else:
        labels = [''] * 12

    return labels


def event_data2(_):
    _ = _.replace('"', '').split('\t')
    if len(_) < 17:
        diff = 17 - len(_)
        b = [''] * diff
        _.extend(b)

    _[3] = hash_type(_[3])
    _ = '","'.join(_)

    return _


def entry_check(f, startEntry, nextEntry):
    startEntry = startEntry + nextEntry
    f.seek(startEntry)
    check = f.read(1)

    while check != b'0':
        startEntry += 1
        f.seek(startEntry)
        check = f.read(1)

        if len(check) == 0:
            break

        if check == b'0':
            f.seek(startEntry)

    if len(check) == 0:
        return startEntry, False

    return startEntry, True


def from_unix_sec(_):
    try:
        return datetime.utcfromtimestamp(int(_)).strftime('%Y-%m-%d %H:%M:%S')

    except:
        return datetime.utcfromtimestamp(0).strftime('%Y-%m-%d %H:%M:%S')


def from_win_64_hex(dateAndTime):
    """Convert a Windows 64 Hex Big-Endian value to a date"""
    base10_microseconds = int(dateAndTime, 16) / 10

    try:
        dateAndTime = datetime(1601, 1, 1) + timedelta(microseconds=base10_microseconds)

    except:
        dateAndTime = datetime(1601, 1, 1)

    return dateAndTime.strftime('%Y-%m-%d %H:%M:%S.%f')


def from_symantec_time(timestamp, tz):

    year, month, day_of_month, hours, minutes, seconds = (
        int(hexdigit[0] + hexdigit[1], 16) for hexdigit in zip(
            timestamp[::2], timestamp[1::2]))

    timestamp = datetime(year + 1970, month + 1, day_of_month, hours, minutes, seconds) + timedelta(hours=tz)

    return timestamp.strftime('%Y-%m-%d %H:%M:%S')


def from_filetime(_):

    if _ == 0:
        _ = datetime(1601, 1, 1).strftime('%Y-%m-%d %H:%M:%S')

    else:
        _ = datetime.utcfromtimestamp(float(_ - 116444736000000000) / 10000000).strftime('%Y-%m-%d %H:%M:%S.%f')
        
    return _


def from_hex_ip(ipHex):
    ipHex = ipHex.decode("utf-8", "ignore")

    if ipHex == '0':
        return '0.0.0.0'

    if len(ipHex) != 8:
        ipHex = '0' + ipHex

    try:
        ipv4 = (
            int(hexdigit[0] + hexdigit[1], 16) for hexdigit in zip(
                ipHex[::2], ipHex[1::2]))

        return '.'.join(map(str, reversed(list(ipv4))))

    except:
        return '0.0.0.0'


def from_hex_ipv6(ipHex):
    ipHex = ipHex.decode("utf-8", "ignore")
    chunks = [ipHex[i:i+2] for i in range(0, len(ipHex), 2)]

    try:
        ipv6 = (
            x[0] + x[1] for x in zip(
                chunks[1::2], chunks[::2]))

        return ipaddress.ip_address(':'.join(ipv6)).compressed

    except:
        return '::'


def from_hex_mac(macHex):
    mac = (
        hexdigit[0] + hexdigit[1] for hexdigit in zip(
            macHex[::2], macHex[1::2]))

    return '-'.join(map(str, mac))[0:17]


def hexdump(buf, pcap=False):
    """Return a hexdump output string of the given buffer."""
    total = len(buf)
    file = io.BytesIO(buf)
    res = []
    hextime = time.time()

    for length in range(0, len(buf), 16):
        i = file.tell()

        if (time.time() - hextime) > 1 and not args.hex_dump:
            progress(i, total, status='Dumping Hex')

        data = file.read(16)
        hexa = ' '.join(['{:02x}'.format(i) for i in data])
        line = ''.join([31 < i < 127 and chr(i) or '.' for i in data])
        res.append('  {:08x}  {:47}  {}'.format(length, hexa, line))

    if (time.time() - hextime) > 1 and not args.hex_dump:
        print('\n')

    if pcap:
        packet.write('\n'.join(res))
        packet.write('\n\n')

        return '\n'.join(res)

    else:
        return '\n'.join(res)+'\n\n'


def flip(_):
    _ = (hexdigit[0] + hexdigit[1] for hexdigit in zip(
        _[::2], _[1::2]))
    _ = ''.join(map(str, reversed(list(_))))

    return _


def splitCount(s, count):
    return ':'.join(s[i:i+count] for i in range(0, len(s), count))


def parse_header(f):

    headersize = len(f.readline())

    if headersize == 0:
        print(f'\033[1;33mSkipping {f.name}. Unknown File Type. \033[1;0m\n')
        return 11, 0, 0, 1, 0, 0, 0, 0

    f.seek(0)
    sheader = f.read(16).hex()

    if sheader[0:16] == '3216144c01000000':
        return 9, 0, 0, 1, 0, 0, 0, 0

    if re.search('\{[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}$', f.name, re.IGNORECASE):
        return 10, 0, 0, 1, 0, 0, 0, 0

    f.seek(0)

    if headersize == 55:
        logType = 5
        maxSize = read_unpack_hex(f, 0, 8)
        field3 = read_unpack_hex(f, 9, 8)
        cLogEntries = read_unpack_hex(f, 18, 8)
        field5 = read_unpack_hex(f, 27, 8)
        field6 = read_unpack_hex(f, 36, 8)
        tLogEntries = 'N\A'
        maxDays = read_unpack_hex(f, 45, 8)

        return logType, maxSize, field3, cLogEntries, field5, field6, tLogEntries, maxDays

    if headersize == 72:
        logType = read_unpack_hex(f, 0, 8)
        maxSize = read_unpack_hex(f, 9, 8)
        field3 = read_unpack_hex(f, 18, 8)
        cLogEntries = read_unpack_hex(f, 27, 8)
        field5 = read_unpack_hex(f, 36, 8)
        field6 = 'N\A'
        tLogEntries = read_unpack_hex(f, 45, 16)
        maxDays = read_unpack_hex(f, 62, 8)

        return logType, maxSize, field3, cLogEntries, field5, field6, tLogEntries, maxDays

    try:
        from_symantec_time(f.readline().split(b',')[0].decode("utf-8", "ignore"), 0)
        return 6, 0, 0, 1, 0, 0, 0, 0

    except:
        pass

    try:
        f.seek(388, 0)
        from_symantec_time(f.read(2048).split(b',')[0].decode("utf-8", "ignore"), 0)
        return 7, 0, 0, 1, 0, 0, 0, 0

    except:
        pass

    try:
        f.seek(4100, 0)
        from_symantec_time(f.read(2048).split(b',')[0].decode("utf-8", "ignore"), 0)
        return 8, 0, 0, 1, 0, 0, 0, 0

    except:
        print(f'\033[1;33mSkipping {f.name}. Unknown File Type. \033[1;0m\n')
        return 11, 0, 0, 1, 0, 0, 0, 0
        return 11, 0, 0, 1, 0, 0, 0, 0
        return 11, 0, 0, 1, 0, 0, 0, 0


def parse_syslog(f, logEntries):
    startEntry = 72
    nextEntry = read_unpack_hex(f, startEntry, 8)
    entry = LogFields()
    systime = time.time()
    count = 0

    while True:
        if (time.time() - systime) > 1:
            progress(count, logEntries, status='Parsing log entries')

        data = '""'
        entry.size = ''
        logEntry = read_log_entry(f, startEntry, nextEntry).split(b'\t')
        entry.dateAndTime = from_win_64_hex(logEntry[1])
        entry.severity = sys_severity(int(logEntry[4], 16))
        eds = int(logEntry[5].decode("utf-8", "ignore"), 16)
        entry.summary = logEntry[6].decode("utf-8", "ignore").replace('"', '""')
        entry.type = logEntry[7].decode("utf-8", "ignore")

        if eds == 11:
            entry.size = int(logEntry[8][2:10], 16)

        if eds > 11:
            data = read_log_data(logEntry[8], 0)

        try:
            entry.location = logEntry[9].decode("utf-8", "ignore")
        except:
            entry.location = ''

        syslog.write(f'"{os.path.basename(f.name)}","{int(logEntry[0].decode("utf-8", "ignore"), 16)}","{entry.dateAndTime}","{sec_event_id(logEntry[2].decode("utf-8", "ignore"))}","{logEntry[3].decode("utf-8", "ignore")}","{entry.severity}","{entry.summary}","{eds}","{entry.type}","{entry.size}","{entry.location}",{data}\n')

        if len(data) > 2:
            timeline.write(f'"{f.name}","","","","","",{data}\n')

        count += 1

        if count == logEntries:
            break

        startEntry, moreData = entry_check(f, startEntry, nextEntry)

        if moreData is False:
            print(f'\033[1;31mEntry mismatch: {count} entries found. Should be {logEntries}.\033[1;0m\n')
            break

        nextEntry = read_unpack_hex(f, startEntry, 8)


def parse_seclog(f, logEntries):
    startEntry = 72
    nextEntry = read_unpack_hex(f, startEntry, 8)
    entry = LogFields()
    sectime = time.time()
    count = 0

    while True:
        if (time.time() - sectime) > 1:
            progress(count, logEntries, status='Parsing log entries')

        logEntry = read_log_entry(f, startEntry, nextEntry).split(b'\t', 16)
        logData = []
        data = ''

        if int(logEntry[12], 16) == 0:
            logData = ['']

        else:
            if re.match(b'^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$', logEntry[16][:int(logEntry[12], 16)]):
                logData = ['']
                parsed = json.loads(base64.b64decode(logEntry[16][:int(logEntry[12], 16)]).decode("utf-8", "ignore"))
                data = json.dumps(parsed, indent=4, sort_keys=True)
                data = data.replace('"', '""')

            else:
                logData = read_log_data(logEntry[16][:int(logEntry[12], 16)], 0).split(",")

        entry.dateAndTime = from_win_64_hex(logEntry[1])
        entry.eventtype = sec_event_type(int(logEntry[2], 16))
        entry.severity = sec_severity(int(logEntry[3], 16))
        entry.localhost = from_hex_ip(logEntry[4])
        entry.remotehost = from_hex_ip(logEntry[5])
        entry.protocol = sec_network_protocol(int(logEntry[6], 16))
        entry.direction = log_direction(int(logEntry[8], 16))
        entry.begintime = from_win_64_hex(logEntry[9])
        entry.endtime = from_win_64_hex(logEntry[10])
        entry.occurrences = int(logEntry[11], 16)
        entry.description = logEntry[13].decode("utf-8", "ignore")
        entry.application = logEntry[15].decode("utf-8", "ignore")
        logEntry2 = logEntry[16][int(logEntry[12], 16):].split(b'\t')
        entry.localmac = logEntry2[1].hex()

        if len(entry.localmac) < 32:
            while True:
                logEntry2[1] = logEntry2[1] + b'\t'
                logEntry2[1:3] = [b''.join(logEntry2[1:3])]
                entry.localmac = logEntry2[1].hex()

                if len(entry.localmac) == 32:
                    entry.localmac = from_hex_mac(logEntry2[1].hex())
                    break

        else:
            entry.localmac = from_hex_mac(logEntry2[1].hex())

        entry.remotemac = logEntry2[2].hex()

        if len(entry.remotemac) < 32:
            while True:
                logEntry2[2] = logEntry2[2] + b'\t'
                logEntry2[2:4] = [b''.join(logEntry2[2:4])]
                entry.remotemac = logEntry2[2].hex()

                if len(entry.remotemac) == 32:
                    entry.remotemac = from_hex_mac(logEntry2[2].hex())
                    break

        else:
            entry.remotemac = from_hex_mac(logEntry2[2].hex())

        entry.location = logEntry2[3].decode("utf-8", "ignore")
        entry.user = logEntry2[4].decode("utf-8", "ignore")
        entry.userdomain = logEntry2[5].decode("utf-8", "ignore")
        entry.signatureid = int(logEntry2[6], 16)
        entry.signaturesubid = int(logEntry2[7], 16)
        entry.remoteport = int(logEntry2[10], 16)
        entry.localport = int(logEntry2[11], 16)
        REMOTE_HOST_IPV6 = from_hex_ipv6(logEntry2[12])
        LOCAL_HOST_IPV6 = from_hex_ipv6(logEntry2[13])
        entry.signaturename = logEntry2[14].decode("utf-8", "ignore")
        entry.xintrusionpayloadurl = logEntry2[15].decode("utf-8", "ignore")
        entry.intrusionurl = logEntry2[16].decode("utf-8", "ignore")

        try:
            entry.hash = logEntry2[22].decode("utf-8", "ignore").strip('\r')
            # SEP14.3.0.1
            entry.urlhidlevel = logEntry2[23].decode("utf-8", "ignore")
            entry.urlriskscore = logEntry2[24].decode("utf-8", "ignore")
            entry.urlcategories = url_categories(logEntry2[25].decode("utf-8", "ignore").split(","))

        except:
            pass

        seclog.write(f'"{os.path.basename(f.name)}","{int(logEntry[0].decode("utf-8", "ignore"), 16)}","{entry.dateAndTime}","{entry.eventtype}","{entry.severity}","{entry.direction}","{entry.protocol}","{entry.remotehost}","{entry.remoteport}","{entry.remotemac}","{entry.localhost}","{entry.localport}","{entry.localmac}","{entry.application}","{entry.signatureid}","{entry.signaturesubid}","{entry.signaturename}","{entry.intrusionurl}","{entry.xintrusionpayloadurl}","{entry.user}","{entry.userdomain}","{entry.location}","{entry.occurrences}","{entry.endtime}","{entry.begintime}","{entry.hash}","{entry.description}","{logEntry[7].decode("utf-8", "ignore")}","{int(logEntry[12], 16)}","{logEntry[14].decode("utf-8", "ignore")}","{logEntry2[8].decode("utf-8", "ignore")}","{logEntry2[9].decode("utf-8", "ignore")}","{REMOTE_HOST_IPV6}","{LOCAL_HOST_IPV6}","{logEntry2[17].decode("utf-8", "ignore")}","{logEntry2[18].decode("utf-8", "ignore")}","{logEntry2[19].decode("utf-8", "ignore")}","{logEntry2[20].decode("utf-8", "ignore")}","{logEntry2[21].decode("utf-8", "ignore")}","{entry.urlhidlevel}","{entry.urlriskscore}","{entry.urlcategories}","{data}",{",".join(logData)}\n')

        if len(logData) > 1:
            timeline.write(f'"{f.name}","{int(logEntry[12], 16)}","","","","",{",".join(logData)}\n')

        count += 1

        if count == logEntries:
            break

        startEntry, moreData = entry_check(f, startEntry, nextEntry)

        if moreData is False:
            print(f'\033[1;31mEntry mismatch: {count} entries found. Should be {logEntries}.\033[1;0m\n')
            break

        nextEntry = read_unpack_hex(f, startEntry, 8)


def parse_tralog(f, logEntries):
    startEntry = 72
    nextEntry = read_unpack_hex(f, startEntry, 8)
    entry = LogFields()
    tratime = time.time()
    count = 0

    while True:
        if (time.time() - tratime) > 1:
            progress(count, logEntries, status='Parsing log entries')

        logEntry = read_log_entry(f, startEntry, nextEntry).split(b'\t')
        entry.dateAndTime = from_win_64_hex(logEntry[1])
        entry.protocol = protocol(int(logEntry[2].decode("utf-8", "ignore"), 16))
        entry.localhost = from_hex_ip(logEntry[3])
        entry.remotehost = from_hex_ip(logEntry[4])
        entry.localport = int(logEntry[5], 16)
        entry.remoteport = int(logEntry[6], 16)

        if entry.protocol == "ICMPv4 packet":
            typeName, codeDescription = icmp_type_code(entry.localport, entry.remoteport)
            entry.protocol = f'{entry.protocol} [type={entry.localport}, code={entry.remoteport}]\r\nName:{typeName}\r\nDescription:{codeDescription}'
            entry.localport = ''
            entry.remoteport = ''

        if entry.protocol == "Ethernet packet":
            entry.protocol = f'{entry.protocol} [type={hex(entry.localport)}]\r\nDescription: {eth_type(entry.localport)}'
            entry.localport = ''
            entry.remoteport = ''
        entry.direction = log_direction(int(logEntry[7], 16))
        entry.endtime = from_win_64_hex(logEntry[8])
        entry.begintime = from_win_64_hex(logEntry[9])
        entry.occurrences = int(logEntry[10], 16)
        entry.action = log_c_action(int(logEntry[11], 16))
        entry.severity = sec_severity(int(logEntry[13], 16))
        entry.rule = logEntry[16].decode("utf-8", "ignore")
        entry.application = logEntry[17].decode("utf-8", "ignore")
        entry.localmac = logEntry[18].hex()

        if len(entry.localmac) < 32:
            while True:
                logEntry[18] = logEntry[18] + b'\t'
                logEntry[18:20] = [b''.join(logEntry[18:20])]
                entry.localmac = logEntry[18].hex()

                if len(entry.localmac) == 32:
                    entry.localmac = from_hex_mac(logEntry[18].hex())
                    break

        else:
            entry.localmac = from_hex_mac(logEntry[18].hex())

        entry.remotemac = logEntry[19].hex()

        if len(entry.remotemac) < 32:
            while True:
                logEntry[19] = logEntry[19] + b'\t'
                logEntry[19:21] = [b''.join(logEntry[19:21])]
                entry.remotemac = logEntry[19].hex()

                if len(entry.remotemac) == 32:
                    entry.remotemac = from_hex_mac(logEntry[19].hex())
                    break

        else:
            entry.remotemac = from_hex_mac(logEntry[19].hex())

        entry.location = logEntry[20].decode("utf-8", "ignore")
        entry.user = logEntry[21].decode("utf-8", "ignore")
        entry.userdomain = logEntry[22].decode("utf-8", "ignore")

        try:
            field33 = logEntry[32].decode("utf-8", "ignore")
            field34 = logEntry[33].decode("utf-8", "ignore")

        except:
            field33 = ''
            field34 = ''

        tralog.write(f'"{os.path.basename(f.name)}","{int(logEntry[0].decode("utf-8", "ignore"), 16)}","{entry.dateAndTime}","{entry.action}","{entry.severity}","{entry.direction}","{entry.protocol}","{entry.remotehost}","{entry.remotemac}","{entry.remoteport}","{entry.localhost}","{entry.localmac}","{entry.localport}","{entry.application}","{entry.user}","{entry.userdomain}","{entry.location}","{entry.occurrences}","{entry.begintime}","{entry.endtime}","{entry.rule}","{logEntry[12].decode("utf-8", "ignore")}","{logEntry[14].decode("utf-8", "ignore")}","{logEntry[15].decode("utf-8", "ignore")}","{logEntry[23].decode("utf-8", "ignore")}","{logEntry[24].decode("utf-8", "ignore")}","{from_hex_ipv6(logEntry[25])}","{from_hex_ipv6(logEntry[26])}","{logEntry[27].decode("utf-8", "ignore")}","{logEntry[28].decode("utf-8", "ignore")}","{logEntry[29].decode("utf-8", "ignore")}","{logEntry[30].decode("utf-8", "ignore")}","{logEntry[31].decode("utf-8", "ignore")}","{field33}","{field34}"\n')
        count += 1

        if count == logEntries:
            break

        startEntry = startEntry + nextEntry
        f.seek(startEntry)
        check = f.read(1)

        while check != b'0':
            startEntry += 1
            f.seek(startEntry)
            check = f.read(1)

            if len(check) == 0:
                break

            if check == b'0':
                f.seek(startEntry)

        if len(check) == 0:
            print(f'\033[1;31mEntry mismatch: {count} entries found. Should be {logEntries}.\033[1;0m\n')
            break

        nextEntry = read_unpack_hex(f, startEntry, 8)


def parse_raw(f, logEntries):
    startEntry = 72
    nextEntry = read_unpack_hex(f, startEntry, 8)
    entry = LogFields()
    rawtime = time.time()
    count = 0

    while True:
        if (time.time() - rawtime) > 1:
            progress(count, logEntries, status='Parsing log entries')

        logEntry = read_log_entry(f, startEntry, nextEntry).split(b'\t')

        if len(logEntry) > 20:
            while True:
                logEntry[13] = logEntry[13] + b'\t'
                logEntry[13:15] = [b''.join(logEntry[13:15])]

                if len(logEntry) == 20:
                    break

        entry.dateAndTime = from_win_64_hex(logEntry[1])
        eventId = raw_event_id(int(logEntry[2].decode("utf-8", "ignore"), 16))
        entry.localhost = from_hex_ip(logEntry[3])
        entry.remotehost = from_hex_ip(logEntry[4])
        entry.localport = int(logEntry[5], 16)
        entry.remoteport = int(logEntry[6], 16)
        plength = int(logEntry[7], 16)
        entry.direction = log_direction(int(logEntry[8], 16))
        entry.action = log_c_action(int(logEntry[9], 16))
        entry.application = logEntry[12].decode("utf-8", "ignore")
        entry.packetdecode = hexdump(logEntry[13], pcap=True).replace('"', '""')
        entry.rule = logEntry[14].decode("utf-8", "ignore")
        entry.packetdump = Ether(import_hexcap(hexdump(logEntry[13], pcap=True))).show(dump=True)

        rawlog.write(f'"{os.path.basename(f.name)}","{int(logEntry[0].decode("utf-8", "ignore"), 16)}","{entry.dateAndTime}","{entry.remotehost}","{entry.remoteport}","{entry.localhost}","{entry.localport}","{entry.direction}","{entry.action}","{entry.application}","{entry.rule}","{entry.packetdump}","{entry.packetdecode}","{eventId}","{plength}","{logEntry[10].decode("utf-8", "ignore")}","{logEntry[11].decode("utf-8", "ignore")}","{logEntry[15].decode("utf-8", "ignore")}","{logEntry[16].decode("utf-8", "ignore")}","{logEntry[17].decode("utf-8", "ignore")}","{logEntry[18].decode("utf-8", "ignore")}","{logEntry[19].decode("utf-8", "ignore")}"\n')
        count += 1

        if count == logEntries:
            break

        startEntry = startEntry + nextEntry
        f.seek(startEntry)
        check = f.read(1)

        while check != b'0':
            startEntry += 1
            f.seek(startEntry)
            check = f.read(1)

            if len(check) == 0:
                break

            if check == b'0':
                f.seek(startEntry)

        if len(check) == 0:
            print(f'\033[1;31mEntry mismatch: {count} entries found. Should be {logEntries}.\033[1;0m\n')
            break

        nextEntry = read_unpack_hex(f, startEntry, 8)


def parse_processlog(f, logEntries):
    startEntry = 72
    nextEntry = read_unpack_hex(f, startEntry, 3)
    entry = LogFields()
    processtime = time.time()
    count = 0

    while True:
        if (time.time() - processtime) > 1:
            progress(count, logEntries, status='Parsing log entries')
        null = None
        field28 = null
        field29 = ''
        extra = null
        logEntry = read_log_entry(f, startEntry, nextEntry).split(b'\t')
        entry.dateAndTime = from_win_64_hex(logEntry[1])
        entry.severity = int(logEntry[3], 16)
        entry.action = log_c_action(int(logEntry[4], 16))
        entry.testmode = test_mode(logEntry[5].decode("utf-8", "ignore"))
        entry.description = logEntry[6].decode("utf-8", "ignore")
        entry.api = logEntry[7].decode("utf-8", "ignore")
        entry.rulename = logEntry[11].decode("utf-8", "ignore")
        entry.callerprocessid = int(logEntry[12], 16)
        entry.callerprocess = logEntry[13].decode("utf-8", "ignore")
        entry.target = logEntry[16].decode("utf-8", "ignore")
        entry.location = logEntry[17].decode("utf-8", "ignore")
        entry.user = logEntry[18].decode("utf-8", "ignore")
        entry.userdomain = logEntry[19].decode("utf-8", "ignore")
        entry.ipaddress = from_hex_ip(logEntry[22])
        entry.deviceinstanceid = logEntry[23].decode("utf-8", "ignore")
        entry.filesize = int(logEntry[24], 16)
        ipv6 = from_hex_ipv6(logEntry[26].split(b'\r\n')[0])

        try:
            extra = logEntry[26].split(b'\r\n')[1]

        except:
            field28 = logEntry[27].decode("utf-8", "ignore")
            field29 = logEntry[28].split(b'\r\n')[0].decode("utf-8", "ignore")
            extra = logEntry[28].split(b'\r\n')[1]

        processlog.write(f'"{os.path.basename(f.name)}","{int(logEntry[0].decode("utf-8", "ignore"), 16)}","{entry.dateAndTime}","{entry.severity}","{entry.action}","{entry.testmode}","{entry.description}","{entry.api}","{entry.rulename}","{entry.ipaddress}","{ipv6}","{entry.callerprocessid}","{entry.callerprocess}","{entry.deviceinstanceid}","{entry.target}","{entry.filesize}","{entry.user}","{entry.userdomain}","{entry.location}","{process_event_id(int(logEntry[2].decode("utf-8", "ignore"), 16))}","{logEntry[8].decode("utf-8", "ignore")}","{from_win_64_hex(logEntry[9])}","{from_win_64_hex(logEntry[10])}","{logEntry[14].decode("utf-8", "ignore")}","{logEntry[15].decode("utf-8", "ignore")}","{logEntry[20].decode("utf-8", "ignore")}","{logEntry[21].decode("utf-8", "ignore")}","{logEntry[25].decode("utf-8", "ignore")}","{field28}","{field29}","{extra}"\n')
        count += 1

        if count == logEntries:
            break

        startEntry = startEntry + nextEntry
        f.seek(startEntry)
        check = f.read(1)

        if len(check) == 0:
            print(f'\033[1;31mEntry mismatch: {count} entries found. Should be {logEntries}.\033[1;0m\n')
            break

        nextEntry = read_unpack_hex(f, startEntry, 3)


def parse_avman(f, logEntries):
    startEntry = 55
    nextEntry = read_unpack_hex(f, startEntry, 8)
    avtime = time.time()
    count = 0

    while True:
        if (time.time() - avtime) > 1:
            progress(count, logEntries, status='Parsing log entries')

        logEntry = read_log_entry(f, startEntry, nextEntry).split(b'\t', 5)
        logData = read_log_data(logEntry[5], 0)

        if logData.split('","')[1] == 'SECURITY_SYMPROTECT_POLICYVIOLATION':
            parse_tamper_protect(logData.split('","'), logEntry, f.name)

        timeline.write(f'"{os.path.basename(f.name)}","{int(logEntry[0].decode("utf-8", "ignore"), 16)}","{from_win_64_hex(logEntry[1])}","{from_win_64_hex(logEntry[2])}","{from_win_64_hex(logEntry[3])}","{logEntry[4].decode("utf-8", "ignore")}",{logData}\n')

        count += 1

        if count == logEntries:
            break

        startEntry, moreData = entry_check(f, startEntry, nextEntry)

        if moreData is False:
            print(f'\033[1;31mEntry mismatch: {count} entries found. Should be {logEntries}.\033[1;0m\n')
            break

        nextEntry = read_unpack_hex(f, startEntry, 8)


def parse_tamper_protect(logData, logEntry, fname):
    # need action
    entry = LogFields()

    entry.time = logData[0]
    entry.computer = logData[4]
    entry.user = logData[5]
    entry.event = log_tp_event(logData[17], logData[23])
    entry.actor = f'{logData[21]} (PID {logData[19]})'
    entry.targetprocess = f'{logData[29]} (PID {logData[25]})'
    entry.target = logData[27]

    tamperProtect.write(f'"{os.path.basename(fname)}","{entry.computer}","{entry.user}","{entry.action}","{entry.event}","{entry.actor}","{entry.target}","{entry.targetprocess}","{entry.time}\n')


def parse_daily_av(f, logType, tz):
    if logType == 6:
        f.seek(0)
        logEntry = f.readline()

    if logType == 7:
        f.seek(388, 0)
        logEntry = f.read(2048).split(b'\x00\x00')[0]

    if logType == 8:
        f.seek(4100, 0)
        logEntry = f.read(1112).split(b'\x00\x00')[0]

    while logEntry:
        logEntry = read_log_data(logEntry, tz)

        if logEntry.split('","')[1] == 'SECURITY_SYMPROTECT_POLICYVIOLATION':
            parse_tamper_protect(logEntry.split('","'), logEntry, f.name)

        timeline.write(f'"{f.name}","","","","","",{logEntry}\n')

        if logType == 7 or logType == 8:
            break

        logEntry = f.readline()


def parse_vbn(f, logType, tz):
    vbin = ''  # linux
    qfile = ''
    sddl = ''
    sha1 = ''
    qds2 = ''
    qds3 = ''
    attribType = ''
    dd = ''
    tags = []
    sid = ''
    virus = ''
    guid = ''
    attribData = ''
    qfile_actual_md5 = ''
    qfile_actual_sha1 = ''
    qfile_actual_sha256 = ''
    qfs = 0
    extraData = None
    header = 0
    footer = 0
    qdl = False
    f.seek(0, 0)
    qm_offset = struct.unpack('i', f.read(4))[0]
    f.seek(0, 0)

    if logType == 7:
        f.seek(388, 0)
        logEntry = f.read(2048).split(b'\x00\x00')[0]

    if logType == 8:
        f.seek(4100, 0)
        logEntry = f.read(1112).split(b'\x00\x00')[0]

    logEntry = read_log_data(logEntry, tz)
    f.seek(0, 0)

    if qm_offset == 3676:
        vbnmeta = vbnstruct.VBN_METADATA_V1(f)

    if qm_offset == 4752:
        vbnmeta = vbnstruct.VBN_METADATA_V2(f)

    if qm_offset == 15100:
        vbnmeta = vbnstruct.VBN_METADATA_Linux(f)

    if qm_offset == 15108:
        vbnmeta = vbnstruct.VBN_METADATA_Linux_V2(f)

    wDescription = vbnmeta.WDescription.rstrip('\0')
    description = vbnmeta.Description.rstrip(b'\x00').decode("utf-8", "ignore")
    storageName = vbnmeta.Storage_Name.rstrip(b'\x00').decode("utf-8", "ignore")
    storageKey = vbnmeta.Storage_Key.rstrip(b'\x00').decode("utf-8", "ignore")
    uniqueId = '{' + '-'.join([flip(vbnmeta.Unique_ID.hex()[:8]), flip(vbnmeta.Unique_ID.hex()[8:12]), flip(vbnmeta.Unique_ID.hex()[12:16]), vbnmeta.Unique_ID.hex()[16:20], vbnmeta.Unique_ID.hex()[20:32]]).upper() + '}'

    if args.hex_dump:
        cstruct.dumpstruct(vbnmeta)

    if vbnmeta.Record_Type == 0:
        try:
            qds2 = vbnmeta.Quarantine_Data_Size_2

        except:
            pass

        qdl = xor(f.read(8), 0x5A).encode('latin-1').hex()

        if qdl == 'ce20aaaa06000000':
            if args.hex_dump:
                print('\n           #######################################################')
                print('           #######################################################')
                print('           ##                                                   ##')
                print('           ## The following data structures are xored with 0x5A ##')
                print('           ##                                                   ##')
                print('           #######################################################')
                print('           #######################################################\n')
            qdata_location_size = xor(f.read(4), 0x5A).encode('latin-1')
            qdata_location_size = struct.unpack('i', qdata_location_size)[0]
            f.seek(-12, 1)
            qdata_location = vbnstruct.QData_Location(xor(f.read(qdata_location_size), 0x5A).encode('latin-1'))

            if args.hex_dump:
                cstruct.dumpstruct(qdata_location)

            pos = vbnmeta.QM_HEADER_Offset + qdata_location.Quarantine_Data_Offset
            file_size = qdata_location.QData_Location_Size - qdata_location.Quarantine_Data_Offset
            f.seek(pos)

            if args.extract:
                print('\n           #######################################################')
                print('           #######################################################')
                print('           ##                                                   ##')
                print('           ##    Extracting quarantine file. Please wait....    ##')
                print('           ##                                                   ##')
                print('           #######################################################')
                print('           #######################################################\n')

            if args.extract or args.quarantine_dump or args.hash_file:
                qfile = xor(f.read(file_size), 0x5A)

            f.seek(pos + file_size)
            # need to properly parse
            qdata_info = vbnstruct.QData_Info(xor(f.read(), 0x5A).encode('latin-1'))

            if args.hex_dump:
                cstruct.dumpstruct(qdata_info)

        else:
            f.seek(-8, 1)

            if args.extract or args.quarantine_dump or args.hash_file:
                qfile = xor(f.read(), 0x5A)

    if vbnmeta.Record_Type == 1:
        if args.hex_dump:
            print('\n           #######################################################')
            print('           #######################################################')
            print('           ##                                                   ##')
            print('           ##            Quarantine Metadata (ASN.1)            ##')
            print('           ##                                                   ##')
            print('           #######################################################')
            print('           #######################################################\n')

        tags, dd, sddl, sid, virus, guid, dec, dbguid, results, binary = read_sep_tag(f.read(), f.name, vbn=True)

        if args.extract or args.quarantine_dump:
            print(f'\033[1;31mRecord type 1 does not contain quarantine data.\033[1;0m\n')

    if vbnmeta.Record_Type == 2:
        f.seek(vbnmeta.QM_HEADER_Offset, 0)
        f.seek(8, 1)
        qm_size = xor(f.read(8), 0x5A).encode('latin-1')
        qm_size = struct.unpack('q', qm_size)[0]
        f.seek(-16, 1)
        qmh = vbnstruct.Quarantine_Metadata_Header(xor(f.read(qm_size), 0x5A).encode('latin-1'))

        if args.hex_dump:
            print('\n           #######################################################')
            print('           #######################################################')
            print('           ##                                                   ##')
            print('           ## The following data structures are xored with 0x5A ##')
            print('           ##                                                   ##')
            print('           #######################################################')
            print('           #######################################################\n')

            cstruct.dumpstruct(qmh)

            print('\n           #######################################################')
            print('           #######################################################')
            print('           ##                                                   ##')
            print('           ##            Quarantine Metadata (ASN.1)            ##')
            print('           ##                                                   ##')
            print('           #######################################################')
            print('           #######################################################\n')

        tags, dd, sddl, sid, virus, guid, dec, dbguid, results, bianry = read_sep_tag(xor(f.read(qmh.QM_Size), 0x5A).encode('latin-1'), f.name, vbn=True)

        pos = qmh.QM_Size_Header_Size + vbnmeta.QM_HEADER_Offset
        f.seek(pos)
        dataType = int.from_bytes(xor(f.read(1), 0x5A).encode('latin-1'), 'little')
        f.seek(pos)

        if dataType == 3:
            qi = vbnstruct.Quarantine_Hash(xor(f.read(7), 0x5A).encode('latin-1'))

            if args.hex_dump:
                cstruct.dumpstruct(qi)

            if qi.Tag2_Data == 1:
                qhc = vbnstruct.Quarantine_Hash_Continued(xor(f.read(110), 0x5A).encode('latin-1'))
                sha1 = qhc.SHA1.decode('latin-1').replace("\x00", "")
                qds2 = int.from_bytes(qhc.Quarantine_Data_Size_2, 'little')

                if args.hex_dump:
                    cstruct.dumpstruct(qhc)

            try:
                dataType = int.from_bytes(xor(f.read(1), 0x5A).encode('latin-1'), 'little')

                if dataType == 8:
                    pos += 35 + qhc.SHA1_Hash_Length
                    f.seek(pos)
                    qsddl_size = struct.unpack('i', xor(f.read(4), 0x5A).encode('latin-1'))[0] + 18
                    f.seek(-4, 1)
                    qsddl = vbnstruct.Quarantine_SDDL(xor(f.read(qsddl_size), 0x5A).encode('latin-1'))

                    sddl = sddl_translate(qsddl.Security_Descriptor.decode('latin-1').replace("\x00", ""))
                    qds3 = qsddl.Quarantine_Data_Size_3

                    if args.hex_dump:
                        cstruct.dumpstruct(qsddl)

                    pos += 19 + qsddl.Security_Descriptor_Size
                    f.seek(pos)

                if dataType == 9:
                    extraData = qds2 - vbnmeta.Quarantine_Data_Size
                    pos += 35 + qhc.SHA1_Hash_Length
                    f.seek(pos)

                chunk = vbnstruct.Chunk(xor(f.read(5), 0x5A).encode('latin-1'))
                pos += 5
                f.seek(pos)

                if extraData is not None:
                    uh = vbnstruct.Unknown_Header(xor(f.read(1000), 0xA5).encode('latin-1'))
                    header = uh.Size + 40
                    footer = extraData - header

                    if args.hex_dump:
                        cstruct.dumpstruct(uh)

                    f.seek(pos)

                if args.hex_dump or args.extract or args.quarantine_dump or args.hash_file:
                    while True:
                        if chunk.Data_Type == 9:

                            if args.hex_dump:
                                cstruct.dumpstruct(chunk)

                            qfile += xor(f.read(chunk.Chunk_Size), 0xA5)

                            try:
                                pos += chunk.Chunk_Size
                                chunk = vbnstruct.Chunk(xor(f.read(5), 0x5A).encode('latin-1'))
                                pos += 5
                                f.seek(pos)

                            except:
                                break

                        else:
                            break

                if extraData is not None:
                    qfs = qds2 - footer
                    f.seek(-footer, 2)

                    try:
                        attribType = attrib_type(int.from_bytes(xor(f.read(1), 0xA5).encode('latin-1'), 'little'))

                        if f.read(1) == b'':
                            attribType = ''

                        f.seek(-2, 1)

                        if attribType == '$EA':
                            ea1 = vbnstruct.Extended_Attribute(xor(f.read(20), 0xA5).encode('latin-1'))

                            if args.hex_dump:
                                cstruct.dumpstruct(ea1)

                            while True:
                                neo = int.from_bytes(xor(f.read(4), 0xA5).encode("latin-1"), "little")
                                f.seek(1, 1)
                                nl = int.from_bytes(xor(f.read(1), 0xA5).encode("latin-1"), "little")
                                vl = int.from_bytes(xor(f.read(2), 0xA5).encode("latin-1"), "little")
                                f.seek(-8, 1)
                                neo2 = nl + vl + 8
                                neo3 = neo - neo2 - 1
                                ea = vbnstruct.FILE_FULL_EA_INFORMATION(xor(f.read(neo2 + 1), 0xA5).encode('latin-1'))

                                eaname = ea.EaName.decode('latin-1')
                                eavalue = ea.EaValue.hex()[(56 - nl) * 2:]

                                if eaname == "$KERNEL.PURGE.APPID.VERSIONINFO":
                                    eavalue = bytes.fromhex(eavalue).decode('latin-1')[::2]
                                attribData += (f'{eaname}\n{eavalue}\n\n')

                                if args.hex_dump:
                                    cstruct.dumpstruct(ea)

                                if ea.NextEntryOffset == 0:
                                    break

                                f.seek(neo3, 1)

                        elif attribType == '$DATA':
                            ads = vbnstruct.ADS_Attribute(xor(f.read(footer), 0xA5).encode('latin-1'))

                            adsname = ads.ADS_Name.replace(b'\x00', b'').decode('latin-1')
                            adsdata = ads.Data.replace(b'\x00', b'').decode('latin-1')
                            attribData = (f'{adsname}\n\n{adsdata}')

                            if args.hex_dump:
                                cstruct.dumpstruct(ads)

                        elif attribType == '$OBJECT_ID':
                            oi = vbnstruct.OBJECT_ID_Attribute(xor(f.read(footer), 0xA5).encode('latin-1'))

                            guid1 = '-'.join([flip(oi.GUID_Object_Id.hex()[0:8]), flip(oi.GUID_Object_Id.hex()[8:12]), flip(oi.GUID_Object_Id.hex()[12:16]), oi.GUID_Object_Id.hex()[16:20], oi.GUID_Object_Id.hex()[20:32]])

                            guid2 = '-'.join([flip(oi.GUID_Birth_Volume_Id.hex()[0:8]), flip(oi.GUID_Birth_Volume_Id.hex()[8:12]), flip(oi.GUID_Birth_Volume_Id.hex()[12:16]), oi.GUID_Birth_Volume_Id.hex()[16:20], oi.GUID_Birth_Volume_Id.hex()[20:32]])

                            guid3 = '-'.join([flip(oi.GUID_Birth_Object_Id.hex()[0:8]), flip(oi.GUID_Birth_Object_Id.hex()[8:12]), flip(oi.GUID_Birth_Object_Id.hex()[12:16]), oi.GUID_Birth_Object_Id.hex()[16:20], oi.GUID_Birth_Object_Id.hex()[20:32]])

                            guid4 = '-'.join([flip(oi.GUID_Domain_Id.hex()[0:8]), flip(oi.GUID_Domain_Id.hex()[8:12]), flip(oi.GUID_Domain_Id.hex()[12:16]), oi.GUID_Domain_Id.hex()[16:20], oi.GUID_Domain_Id.hex()[20:32]])

                            uuid = int(''.join([flip(oi.GUID_Birth_Object_Id.hex()[12:16]), flip(oi.GUID_Birth_Object_Id.hex()[8:12]), flip(oi.GUID_Birth_Object_Id.hex()[0:8])])[1:], 16)
                            guidtime = datetime.utcfromtimestamp((uuid - 0x01b21dd213814000)*100/1e9)

                            guidmac = splitCount(oi.GUID_Birth_Object_Id.hex()[20:32], 2)
                            p = manuf.MacParser()
                            macvendor = p.get_manuf_long(guidmac)

                            if macvendor is None:
                                macvendor = "(Unknown vendor)"

                            attribData = (f'MAC Address: {guidmac}\nMAC Vendor: {macvendor}\nCreation: {guidtime}\n\nObject ID: {guid1}\nBirth Volume ID: {guid2}\nBirth Object ID: {guid3}\nDomain ID: {guid4}')

                            if args.hex_dump:
                                cstruct.dumpstruct(oi)

                        else:
                            unknown = vbnstruct.Unknown_Attribute(xor(f.read(footer), 0xA5).encode('latin-1'))

                            if args.hex_dump:
                                cstruct.dumpstruct(unknown)

                    except:
                        pass

            except:
                if args.extract:
                    print(f'\033[1;31mDoes not contain quarantine data. Clean by Deletion.\033[1;0m\n')
                    print(f'\033[1;32mFinished parsing {f.name} \033[1;0m\n')

                pass

        if dataType == 6:
            if args.hex_dump:
                print(hexdump(xor(f.read(), 0x5A).encode('latin-1')))

    if len(qfile) > 0 and args.hash_file:
        if (header or qfs) == 0:
            qfile_actual_md5 = hashlib.md5(qfile.encode('latin-1')).hexdigest()
            qfile_actual_sha1 = hashlib.sha1(qfile.encode('latin-1')).hexdigest()
            qfile_actual_sha256 = hashlib.sha256(qfile.encode('latin-1')).hexdigest()
        else:
            qfile_actual_md5 = hashlib.md5(qfile[header:qfs].encode('latin-1')).hexdigest()
            qfile_actual_sha1 = hashlib.sha1(qfile[header:qfs].encode('latin-1')).hexdigest()
            qfile_actual_sha256 = hashlib.sha256(qfile[header:qfs].encode('latin-1')).hexdigest()

        if vbnmeta.Record_Type == 0:
            print(f'\033[1;37mSHA1({qfile_actual_sha1}) of the quarantined data.\033[1;0m\n')

        elif sha1.lower() != qfile_actual_sha1.lower():
            print(f'\033[1;37mActual SHA1({qfile_actual_sha1}) of the quarantined data does not match stated SHA1({sha1})!\033[1;0m\n')

        else:
            print(f'\033[1;37mQuarantine data hash verified.\033[1;0m\n')

    if args.quarantine_dump and len(qfile) > 0:
        if (header or qfs) == 0:
            print(hexdump(qfile.encode('latin-1')))

        else:
            print(hexdump(qfile[header:qfs].encode('latin-1')))

    if args.extract and len(qfile) > 0:
        output = open(args.output + '/' + os.path.basename(description) + '.vbn', 'wb+')

        if (header or qfs) == 0:
            output.write(bytes(qfile, encoding='latin-1'))

        else:
            output.write(bytes(qfile[header:qfs], encoding='latin-1'))
        print(output.name)
    if not (args.extract or args.hex_dump):
        try:
            modify = from_filetime(vbnmeta.Date_Modified)
            create = from_filetime(vbnmeta.Date_Created)
            access = from_filetime(vbnmeta.Date_Accessed)
            vbin = 'Linux Only'

        except:
            modify = from_unix_sec(vbnmeta.Date_Modified)
            create = from_unix_sec(vbnmeta.Date_Created)
            access = from_unix_sec(vbnmeta.Date_Accessed)
            vbin = from_unix_sec(vbnmeta.VBin_Time)

        attribData = attribData.replace('"', '""')

        quarantine.write(f'"{f.name}","{virus}","{description}","{vbnmeta.Record_ID}","{create}","{access}","{modify}","{vbin}","{storageName}","{vbnmeta.Storage_Instance_ID}","{storageKey}","{vbnmeta.Quarantine_Data_Size}","{from_unix_sec(vbnmeta.Date_Created_2)}","{from_unix_sec(vbnmeta.Date_Accessed_2)}","{from_unix_sec(vbnmeta.Date_Modified_2)}","{from_unix_sec(vbnmeta.VBin_Time_2)}","{uniqueId}","{vbnmeta.Record_Type}","{hex(vbnmeta.Quarantine_Session_ID)[2:].upper()}","{remediation_type_desc(vbnmeta.Remediation_Type)}","{wDescription}","{sha1.upper()}","{qfile_actual_sha1.upper()}","{qfile_actual_md5.upper()}","{qfile_actual_sha256.upper()}","{qds2}","{sid}","{sddl}","{qds3}","{dd}","{guid}","{"Yes" if qdl == "ce20aaaa06000000" else "No"}","{"Yes" if header > 0 else "No"}","{attribType}","{attribData}","{tags}",{logEntry}\n')


def extract_sym_submissionsidx(f):
    f.seek(48)
    cnt = 0

    while f.read(4) == b'@\x99\xc6\x89':
        f.seek(20, 1)
        len1 = struct.unpack('i', f.read(4))[0]
        len2 = struct.unpack('i', f.read(4))[0]
        print(f'\033[1;35m\tSubmission {cnt} len1={len1} len2={len2}\033[1;0m\n')
        f.seek(8, 1)

        if not os.path.exists(args.output + '/ccSubSDK/submissions'):
            os.makedirs(args.output + '/ccSubSDK/submissions')

        newfilename = open(args.output + '/ccSubSDK/submissions/submissions.idx_Symantec_submission_['+str(cnt)+']_idx.out', 'wb')

        key = f.read(16)
        data = f.read(len1 - 16)
        dec = blowfishit(data, key)
        newfilename.write(dec.encode('latin-1'))
        dec = read_sep_tag(dec.encode('latin-1'), f.name, sub=True)

        if dec[6] == '':
            newfilename.close()
            os.remove(newfilename.name)
            f.seek(-len1 - 40, 1)
            data = f.read(len1 + 40)
            extract_sym_submissionsidx_sub(data, cnt, len1)
            cnt += 1
            continue

        newfilename = open(args.output + '/ccSubSDK/submissions/submissions.idx_Symantec_submission_['+str(cnt)+']_idx.met', 'wb')

        newfilename.write(dec[6].encode('latin-1'))
        if dec[7]:
            read_submission(dec[8], dec[7], cnt)

        print(f'\033[1;32m\tFinished parsing Submission {cnt}\033[1;0m\n')

        cnt += 1


def extract_sym_submissionsidx_sub(f, cnt, len1):
    print(f'\033[1;32m\t\tParsing sub-entries for Submission {cnt}\033[1;0m\n')
    print(f'\033[1;35m\t\tSubmission {cnt}-0\033[1;0m\n')

    newfilename = open(args.output + '/ccSubSDK/submissions/submissions.idx_Symantec_submission_['+str(cnt)+'-0]_idx.out', 'wb')

    subcnt = 1
    f = io.BytesIO(f)

    try:
        pos = [(m.start(0)) for m in re.finditer(b'@\x99\xc6\x89', f.read())][1]
        print(f'\033[1;35m\t\tSubmission {cnt}-0 len1={pos} len2=0\033[1;0m\n')

    except:
        f.seek(0)
        print(f'\033[1;35m\t\tSubmission {cnt}-0 len1={len1} len2=0\033[1;0m\n')
        newfilename.write(f.read())
        print(f'\033[1;32m\t\tFinished parsing Submission {cnt}-0\033[1;0m\n')
        return

    f.seek(0)
    newfilename.write(f.read(pos))
    print(f'\033[1;32m\t\tFinished parsing Submission {cnt}-0\033[1;0m\n')

    while f.read(4) == b'@\x99\xc6\x89':
        f.seek(20, 1)
        len1 = struct.unpack('i', f.read(4))[0]
        len2 = struct.unpack('i', f.read(4))[0]
        print(f'\033[1;35m\t\tSubmission {cnt}-{subcnt} len1={len1} len2={len2}\033[1;0m\n')
        f.seek(8, 1)

        newfilename = open(args.output + '/ccSubSDK/submissions/submissions.idx_Symantec_submission_['+str(cnt)+'-'+str(subcnt)+']_idx.out', 'wb')

        key = f.read(16)
        data = f.read(len1 - 16)
        dec = blowfishit(data, key)
        newfilename.write(dec.encode('latin-1'))
        dec = read_sep_tag(dec.encode('latin-1'), None, sub=True)

        newfilename = open(args.output + '/ccSubSDK/submissions/submissions.idx_Symantec_submission_['+str(cnt)+'-'+str(subcnt)+']_idx.met', 'wb')

        newfilename.write(dec[6].encode('latin-1'))
        if dec[7]:
            read_submission(dec[8], dec[7], str(cnt)+'-'+str(subcnt))
        print(f'\033[1;32m\t\tFinished parsing Submission {cnt}-{subcnt}\033[1;0m\n')
        subcnt += 1


def read_submission(_, fname, index):
    test = {}
    column = 0
    for x in _.split('\n'):
        x = re.split('(?<!.{48}):(?!\\\)|(?<!.{48})=', x, maxsplit=1)

        if x[0] == 'Detection Digest':
            y = x
            column = 2

        if column == 2:
            if len(x[0]) == 0:
                x = y
                x[1] = x[1].replace('"', '""')
                column = 0

            if len(x) == 1:
                y[1] = y[1] + x[0] + '\n'
                continue

        if len(x[0]) == 0:
            continue

        if len(x) == 1:
            if re.match('[a-fA-F\d]{32}', x[0]):
                x.insert(0, 'MD5')

            elif re.match('Detection of', x[0]):
                x.insert(0, 'Detection')

            elif re.search('Submission of', x[0]):
                x.insert(0, 'Submission')

            elif re.match('BASH-', x[0]):
                x.insert(0, 'BASH Plugin')
                column = 1

            elif column == 1:
                x.insert(0, 'ImagePath')
                column = 0

            else:
                x.insert(0, 'Unknown')

        test[x[0]] = x[1]

    if 'Submission' in test:
        subtype = args.output+'/ccSubSDK/SubmissionsEim.csv'

    elif 'BASH Plugin' in test:
        subtype = args.output+'/ccSubSDK/BHSvcPlg.csv'

    elif ('Signature Set Version' in test or 'Signature ID' in test):
        subtype = args.output+'/ccSubSDK/IDSxp.csv'

    elif 'File Reputation' in test.values():
        subtype = args.output+'/ccSubSDK/AtpiEim_ReportSubmission.csv'

    elif 'Client Authentication Token Request' in test.values():
        subtype = args.output+'/ccSubSDK/RepMgtTim.csv'

    else:
        subtype = args.output+'/ccSubSDK/Reports.csv'
#        print(test)
#        input('paused')


def extract_sym_ccSubSDK(f):
    guid = {
            '2B5CA624B61E3F408B994BF679001DC2': 'BHSvcPlg',
            '334FC1F5F2DA574E9BE8A16049417506': 'SubmissionsEim',  # CLSID_SAVAVSAMPLESUBMISSION
            '38ACED4CA8B2134D83ED4D35F94338BD': 'SubmissionsEim',  # CLSID_SAVAVPINGSUBMISSION
            '5E6E81A4A77338449805BB2B7AB12FB4': 'AtpiEim_ReportSubmission',  # OID_REPORTSUBMISSION
            '6AB68FC93C09E744B828A598179EFC83': 'IDSxpx86',
            '95AAE6FD76558D439889B9D02BE0B850': 'IDSxpx86',
            '6A007A980A5B0A48BDFC4D887AEACAB0': 'IDSxpx86',
            'D40650BD02FDE745889CB15F0693C770': 'IDSxpx86',
            '3DC1B6DEBAE889458213D8B252C465FC': 'IDSxpx86',
            '8EF95B94E971E842BAC952B02E79FB74': 'AVModule',
            'A72BBCC1E52A39418B8BB591BDD9AE76': 'RepMgtTim',  # OID_CATSUBMISSION
            'F2ECB3F7D763AE4DB49322CF763FC270': 'ccSubEng'
           }

    f.seek(0)
    GUID = f.read(16).hex()

    for k, v in guid.items():
        if k == GUID.upper():
            GUID = v + '/' + GUID

    if not os.path.exists(args.output + '/ccSubSDK/' + GUID + '/' + os.path.basename(f.name)):
        os.makedirs(args.output + '/ccSubSDK/' + GUID + '/' + os.path.basename(f.name))

    newfilename = open(args.output + '/ccSubSDK/' + GUID + '/' + os.path.basename(f.name) + '/Symantec_ccSubSDK.out', 'wb')

    key = f.read(16)
    data = f.read()
    dec = blowfishit(data, key)

    newfilename.write(dec.encode('latin-1'))
    newfilename.close()
    dec = read_sep_tag(dec.encode('latin-1'), os.path.basename(f.name))

    write_report(dec[6], os.path.basename(f.name))

    newfilename = open(args.output + '/ccSubSDK/' + GUID + '/' + os.path.basename(f.name) + '/Symantec_ccSubSDK.met', 'wb')

    newfilename.write(dec[6].encode('latin-1'))
    newfilename.close()

    if dec[9] and args.extract_blob:
        cnt = 0

        for i in dec[9]:
            binary = open(args.output + '/ccSubSDK/' + GUID + '/' + os.path.basename(f.name) + '/' + str(cnt) + '.blob', 'wb')
            binary.write(i)
            binary.close()
            cnt += 1


def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stderr.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stderr.flush()


def blowfishit(data, key):
    dec = ''
    total = len(data)
    cipher = blowfish.Cipher(key, byte_order="little")
    data = io.BytesIO(data)

    while data:
        dec += str(cipher.decrypt_block(data.read(8)).decode('latin-1'))
        i = data.tell()

        if total > 1000000:
            progress(i, total, status='Decrypting file')

        check = data.read(1)

        if len(check) == 0:
            break

        data.seek(-1, 1)

    if total > 1000000:
        print('\n')

    return dec


def utc_offset(_):
    tree = ET.parse(_)
    root = tree.getroot()

    for SSAUTC in root.iter('SSAUTC'):
        utc = SSAUTC.get('Bias')

    return int(utc)


# banner = '''
# \033[1;93m____________\033[1;0m
# \033[1;93m|   |  |   |\033[1;0m
# \033[1;93m|   |  |   |\033[1;97m   ____  _____ ____
# \033[1;93m|   |  |   |\033[1;97m  / ___|| ____|  _ \ _ __   __ _ _ __ ___  ___ _ __
# \033[1;93m|   |  |\033[1;92m___\033[1;93m|\033[1;97m  \___ \|  _| | |_) | '_ \ / _` | '__/ __|/ _ \ '__|
# \033[1;93m \  |  \033[1;92m/ _ \ \033[1;97m  ___) | |___|  __/| |_) | (_| | |  \__ \  __/ |
# \033[1;93m  \ | \033[1;92m| (_) |\033[1;97m |____/|_____|_|   | .__/ \__,_|_|  |___/\___|_| v{}
# \033[1;93m    \  \033[1;92m\___/\033[1;97m                    |_|
# \033[1;93m     \/\033[1;0m      by @bmmaloney97
# '''.format(__version__)


def main():
    x()
    for filename in filenames:
        # print(f'\033[1;35mStarted parsing {filename} \033[1;0m\n')

        try:
            with open(filename, 'rb') as f:
                logType, maxSize, field3, cLogEntries, field5, field6, tLogEntries, maxDays = parse_header(f)

                try:
                    if logType <= 5:
                        settings.write(f'"{filename}","{maxSize}","{cLogEntries}","{tLogEntries}","{maxDays}","{field3}","{field5}","{field6}"\n')

                    if cLogEntries == 0:
                        print(f'\033[1;33mSkipping {filename}. Log is empty. \033[1;0m\n')
                        continue

                    if logType == 0:
                        parse_syslog(f, cLogEntries)

                    if logType == 1:
                        parse_seclog(f, cLogEntries)

                    if logType == 2:
                        parse_tralog(f, cLogEntries)

                    if logType == 3:
                        parse_raw(f, cLogEntries)

                    if logType == 4:
                        # can have more fields after ipv6
                        parse_processlog(f, cLogEntries)

                    if logType == 5:
                        parse_avman(f, cLogEntries)

                    if logType == 6:
                        parse_daily_av(f, logType, args.timezone)

                    if logType == 7:
                        parse_vbn(f, logType, args.timezone)

                        if not (args.extract or args.hex_dump):
                            parse_daily_av(f, logType, args.timezone)

                    if logType == 8:
                        parse_vbn(f, logType, args.timezone)

                        if not (args.extract or args.hex_dump):
                            parse_daily_av(f, logType, args.timezone)

                    if logType == 9:
                        extract_sym_submissionsidx(f)

                    if logType == 10:
                        extract_sym_ccSubSDK(f)

                    if logType == 11:
                        continue

                    # print(f'\033[1;32mFinished parsing {filename} \033[1;0m\n')

                except Exception as e:
                    print(f'\033[1;31mProblem parsing {filename}: {e} \033[1;0m\n')
                    if args.verbose:
                        traceback.print_exc()
                    continue

        except Exception as e:
            print(f'\033[1;33mSkipping {filename}. \033[1;31m{e}\033[1;0m\n')

    # print(f'\033[1;37mProcessed {len(filenames)} file(s) in {format((time.time() - start), ".4f")} seconds \033[1;0m')
    return tojson()
    # sys.exit()


# print(banner)
def x():
    global syslog,seclog,tralog,rawlog,processlog,timeline,packet,tamperProtect,quarantine,settings,filenames,args,start,logfile
    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="File to be parsed")
    parser.add_argument("-d", "--dir", help="Directory to be parsed")
    parser.add_argument("-e", "--extract", help="Extract quarantine file from VBN if present.", action="store_true")
    parser.add_argument("-eb", "--extract-blob", help="Extract potential binary blobs from ccSubSDK", action="store_true")
    parser.add_argument("-hd", "--hex-dump", help="Dump hex output of VBN to screen.", action="store_true")
    parser.add_argument("-qd", "--quarantine-dump", help="Dump hex output of quarantine to screen.", action="store_true")
    parser.add_argument("-hf", "--hash-file", help="Hash quarantine data to see if it matches recorded hash.", action="store_true")
    parser.add_argument("-o", "--output", help="Directory to output files to. Default is current directory.", default=".")
    parser.add_argument("-a", "--append", help="Append to output files.", action="store_true")
    parser.add_argument("-r", "--registrationInfo", help="Path to registrationInfo.xml")
    parser.add_argument("-tz", "--timezone", type=int, help="UTC offset")
    parser.add_argument("-k", "--kape", help="Kape mode", action="store_true")
    parser.add_argument("-l", "--log", help="Save console output to log", action="store_true")
    parser.add_argument("-v", "--verbose", help="More verbose errors", action="store_true")

    if len(sys.argv) == 1:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    logfile = args.output + "/" + datetime.now().strftime("%Y-%m-%dT%H%M%S_console.log")

    if args.log:
        sys.stdout = Logger()

    regex = re.compile(r'\\Symantec Endpoint Protection\\(Logs|.*\\Data\\Logs|.*\\Data\\Quarantine|.*\\Data\\CmnClnt\\ccSubSDK)')
    filenames = []

    if args.hex_dump and not args.file:
        print("\n\033[1;31m-e, --extract and/or -hd, --hexdump can only be used with -f, --file.\033[1;0m\n")
        sys.exit()

    if args.registrationInfo:
        try:
            print('\033[1;36mAttempting to apply timezone offset.\n \033[1;0m')
            args.timezone = utc_offset(args.registrationInfo)
            print(f'\033[1;32mTimezone offset of {args.timezone} applied successfully. \033[1;0m\n')

        except Exception as e:
            print(f'\033[1;31mUnable to apply offset. Timestamps will not be adjusted. {e}\033[1;0m\n')
            pass

    if (args.kape or args.dir) and not args.file:
        print('\nSearching for Symantec logs.\n')
        rootDir = '/'

        if args.dir:
            rootDir = args.dir

        for path, subdirs, files in os.walk(rootDir):
            if args.kape:
                if 'registrationInfo.xml' in files:
                    pass

                elif not regex.findall(path):
                    continue

            for name in files:
                if args.timezone is None and (args.registrationInfo or name == 'registrationInfo.xml'):
                    reginfo = os.path.join(path, name)

                    if args.registrationInfo:
                        reginfo = args.registrationInfo

                    try:
                        print(f'\033[1;36m{reginfo} found. Attempting to apply timezone offset.\n \033[1;0m')
                        args.timezone = utc_offset(reginfo)
                        print(f'\033[1;32mTimezone offset of {args.timezone} applied successfully. \033[1;0m\n')

                    except Exception as e:
                        print(f'\033[1;31mUnable to apply offset. Timestamps will not be adjusted. {e}\033[1;0m\n')

                filenames.append(os.path.join(path, name))

        if not filenames:
            print('No Symantec logs found.')
            sys.exit()

    if args.file:
        filenames = [args.file]

    if args.timezone is None:
        args.timezone = 0

    if args.output and not (args.extract or args.hex_dump):

        if not args.append:
            syslog = open(args.output + '/Symantec_Client_Management_System_Log.csv', 'w', encoding='utf-8')
            seclog = open(args.output + '/Symantec_Client_Management_Security_Log.csv', 'w', encoding='utf-8')
            tralog = open(args.output + '/Symantec_Network_and_Host_Exploit_Mitigation_Traffic_Log.csv', 'w', encoding='utf-8')
            rawlog = open(args.output + '/Symantec_Network_and_Host_Exploit_Mitigation_Packet_Log.csv', 'w', encoding='utf-8')
            processlog = open(args.output + '/Symantec_Client_Management_Control_Log.csv', 'w', encoding='utf-8')
            timeline = open(args.output + '/Symantec_Timeline.csv', 'w', encoding='utf-8')
            packet = open(args.output + '/packets.txt', 'w', encoding='utf-8')
            tamperProtect = open(args.output + '/Symantec_Client_Management_Tamper_Protect_Log.csv', 'w', encoding='utf-8')
            quarantine = open(args.output + '/quarantine.csv', 'w', encoding='utf-8')
            settings = open(args.output + '/settings.csv', 'w', encoding='utf-8')

        else:
            syslog = open(args.output + '/Symantec_Client_Management_System_Log.csv', 'a', encoding='utf-8')
            seclog = open(args.output + '/Symantec_Client_Management_Security_Log.csv', 'a', encoding='utf-8')
            tralog = open(args.output + '/Symantec_Network_and_Host_Exploit_Mitigation_Traffic_Log.csv', 'a', encoding='utf-8')
            rawlog = open(args.output + '/Symantec_Network_and_Host_Exploit_Mitigation_Packet_Log.csv', 'a', encoding='utf-8')
            processlog = open(args.output + '/Symantec_Client_Management_Control_Log.csv', 'a', encoding='utf-8')
            timeline = open(args.output + '/Symantec_Timeline.csv', 'a', encoding='utf-8')
            packet = open(args.output + '/packets.txt', 'a', encoding='utf-8')
            tamperProtect = open(args.output + '/Symantec_Client_Management_Tamper_Protect_Log.csv', 'a', encoding='utf-8')
            quarantine = open(args.output + '/quarantine.csv', 'a', encoding='utf-8')
            settings = open(args.output + '/settings.csv', 'a', encoding='utf-8')

        if os.stat(timeline.name).st_size == 0:
            csv_header()

if __name__ == "__main__":
    print (json.dumps(main()))
