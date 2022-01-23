#!/usr/bin/env python

'''
Initially Developed January 30, 2021

Updates
2021-06-24 - Added Python3 support
2021-04-26 - Added two new GUIDs to lookup table
2021-02-23 - Built in logic to identify multi-year entries (abnormal, but it can happen)
2021-02-13 - Processed DNS table (if available) and correlates hostname(s) to IPv4 addresses

DISCLAIMER: 

Copyright (c) 2021, BriMor Labs
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the BriMor Labs nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL BRIMOR LABS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Many thanks to:
- Patrick Bennett
- Kevin Stokes
- Mark McKinnon and Mark Baggett (for their work on SRUM parsing scripts which helped with ESE database/field structure
- Microsoft reference material on this artifact: https://docs.microsoft.com/en-us/windows-server/administration/user-access-logging/manage-user-access-logging
'''


import pyesedb
import sys
import os
import re
import math
import uuid
import binascii
import struct
import socket
import textwrap
from datetime import timedelta
from datetime import datetime
from binascii import unhexlify
from struct import unpack
import time
import json  

# Declared variables
kstrikeversionnumber = "20210624" # KStrike Version number
StartTime=time.time() # Recording the start time
insertdatefourofyear = [] # We will use this later
insertdateyyyymmdd = [] # We will use this later
lastaccessfourofyear = [] # We will use this later
lastaccessyyyymmdd = [] # We will use this later
insertdatehour = [] # We will use this later
insertdateday = [] # We will use this later
clienttablenumber = [] # We will use this later
dnstablenumber = [] # We will use this later
totalcountofaccesses = [] # We will use this later
badyeardetector = [] # We will use this later as a check
correlatedtwoaccessmismatchyear = "No" # We will use this later as a check


# Setup dictionary for column types
Column_Dict = {0:'NULL', 1:'Text', 2:'Integer', 3:'Integer', 4:'Integer', 5:'Integer', 6:'Real', 7:'Real', 8:'Text', 9:'Blob', \
              10:'Text', 11:'Blob', 12:'Text', 13:'Integer', 14:'Integer', 15:'Integer', 16:'Text', 17:'Integer'} #Column Type dictionary. Add to it as needed
Table_Dict = {'MSysObjects':'MSysObjects', 'MSysObjectsShadow':'MSysObjectsShadow', 'MSysObjids':'MSysObjids', 'MSysLocales':'MSysLocales', \
           'CLIENTS':'CLIENTS','ROLE_ACCESS':'ROLE_ACCESS','VIRTUALMACHINES':'VIRTUALMACHINES','MSysObjids':'MSysObjids','DNS':'DNS'} #Table Dictionary. Add to it as needed
GUID_Dict = {'{10A9226F-50EE-49D8-A393-9A501D47CE04}':'File Server', '{4116A14D-3840-4F42-A67F-F2F9FF46EB4C}':'Windows Deployment Services', '{48EED6B2-9CDC-4358-B5A5-8DEA3B2F3F6A}':'DHCP Server', \
            '{7CC4B071-292C-4732-97A1-CF9A7301195D}':'FAX Server', '{7FB09BD3-7FE6-435E-8348-7D8AEFB6CEA3}':'Print and Document Services', '{910CBAF9-B612-4782-A21F-F7C75105434A}':'BranchCache', \
            '{952285D9-EDB7-4B6B-9D85-0C09E3DA0BBD}':'Remote Access', '{B4CDD739-089C-417E-878D-855F90081BE7}':'Active Directory Rights Management Service', '{BBD85B29-9DCC-4FD9-865D-3846DCBA75C7}':'Network Policy and Access Services', \
            '{C23F1C6A-30A8-41B6-BBF7-F266563DFCD6}':'FTP Server', '{C50FCC83-BC8D-4DF5-8A3D-89D7F80F074B}':'Active Directory Certificate Services', '{D6256CF7-98FB-4EB4-AA18-303F1DA1F770}':'Web Server', \
            '{D8DC1C8E-EA13-49CE-9A68-C9DCA8DB8B33}':'Windows Server Update Services','{AD495FC3-0EAA-413D-BA7D-8B13FA7EC598}':'Active Directory Domain Services','{BD7F7C0D-7C36-4721-AFA8-0BA700E26D9E}':'SQL Server Database Engine',\
            '{DDE30B98-449E-4B93-84A6-EA86AF0B19FE}':'MSMQ','{1479A8C1-9808-411E-9739-2D3C5923E86A}':'Windows Server 2016 DatacenterRemote Desktop Gateway','{90E64AFA-70DB-4FEF-878B-7EB8C868F091}':'Windows ServerRemote Desktop Services',\
            '{2414BC1B-1572-4CD9-9CA5-65166D8DEF3D}':'SQL Server Analysis Services','{8CC0AC85-40F7-4886-9DAB-021519800418}':'Reporting Services'} #This is our GUID dictionary lookup. Add to it as needed
DNS_Dict = {}

class output: 
   data = []
   headers = []
   buffer = ""
   tmp_stdout = None
   def write(self, line):
      line = line.rstrip("").lstrip("")
      if line == "":
         return
      if line.endswith("||"):
         value = self.buffer + line
         for v in value.rstrip("||").split("||"):
            self.data.append(v)
         self.buffer = ""
      else: 
         self.buffer += line
   def __init__(self): 
      pass

   def set_header(self, headers , output_file=None):
      self.headers = headers 
      if output_file is not None and not output_file.endswith(".json") :

         with open(output_file , "w") as f:
            try:
                f.write('||'.join(headers) + "\n")
            except Exception as e: 
               f.write("ERR ["+str(e)+"]: "+ str(headers) + "\n")


   def print(self , output_file=None):
      if output_file is None:
         j = {'@timestamp':''}
         for i in range(len(self.headers)): 
            j[self.headers[i]] = self.data[i]
         timestamp = j['LastAccess'].replace(" ","T")
         j['@timestamp']= timestamp
         # self.data.append()
         self.tmp_stdout.write(json.dumps(j) + "\n")
      
      self.data = []
   def flush(self):
      pass
output = output()
output.tmp_stdout = sys.stdout 
sys.stdout = output

def win_date_bin_to_datetime(win_date_bin): #This converts the datetime field of the CLIENTS table specificaly, it is Windows FILETIME
    decimaldate = int(struct.unpack("<Q",win_date_bin)[0]) #Seems odd, but you must unpack it this way
    try:
        windowsdt = datetime(1601,1,1,0,0,0) + timedelta(microseconds=decimaldate/10) #Yay math!
    except:
        windowsdt = "UNRECOGNIZED TIMESTAMP"
    sys.stdout.write(str(windowsdt)+"||")
    fourofyear=str(windowsdt)[0:4] #Pulling the four of the year
    fullyyyymmdd=str(windowsdt)[0:10] # Pulling the full yyyy-mm-dd
    twoofhour=str(windowsdt)[11:13] #Pulling the two of hour
    twoofdate=str(windowsdt)[8:10] #Pulling the two of date
    if ((len(fourofyear) == 4) and Column_Name == "InsertDate"):
        global insertdatefourofyear #This will be used for our date formatting later on
        global insertdatehour #This will be used for our check to ensure proper date formatting later on
        global insertdateday #This will be used for our check to ensure proper date formatting later on
        global insertdateyyyymmdd #This will be used for our insertdateyyyymmdd possible string later on
        insertdatefourofyear = fourofyear #Grabbing the year from the windowsdt string
        insertdateyyyymmdd = fullyyyymmdd # Grabbing the yyyy-mm-dd from the windowsdt string
        insertdatehour = twoofhour #Grabbing the hour from the windowsdt string
        insertdateday = twoofdate #Grabbing the day from the windowsdt string
    elif ((len(fourofyear) == 4) and Column_Name == "LastAccess"):
        global lastaccessfourofyear # This will be used for our date formatting discount double check later on
        global lastaccessyyyymmdd #This will be used for our lastaccessyyyymmdd possible string later on
        lastaccessfourofyear = fourofyear #Grabbing the year
        lastaccessyyyymmdd = fullyyyymmdd # Grabbing the yyyy-mm-dd from the windowsdt string


def Check_Column_Type(Table_Record, Column_Type, Column_Number, Record_List): #Add field clarity as needed, but most likely not needed
    if (Column_Type == 0):   # Null
       return 0,"NULL"
    elif (Column_Type == 1): #Boolean
       if (Table_Record.get_value_data(Column_Number) == None):
          return 0,Record_List.append('NULL')
       else:
          return 0,Record_List.append(str(Table_Record.get_value_data(Column_Number).decode('utf-16', 'ignore')))   
    elif (Column_Type == 2): #INTEGER_8BIT_UNSIGNED
       return 0,Record_List.append(Table_Record.get_value_data_as_integer(Column_Number))
    elif (Column_Type == 3): #INTEGER_16BIT_SIGNED
       return 0,Record_List.append(Table_Record.get_value_data_as_integer(Column_Number))   
    elif (Column_Type == 4): #INTEGER_32BIT_SIGNED 
       return 0,Record_List.append(Table_Record.get_value_data_as_integer(Column_Number))
    elif (Column_Type == 5): #CURRENCY
       return 0,Record_List.append(Table_Record.get_value_data_as_integer(Column_Number))   
    elif (Column_Type == 6): #INTEGER_8BIT_UNSIGNED
       return 0,Record_List.append(Table_Record.get_value_data_as_floating_point(Column_Number))
    elif (Column_Type == 7): #DOUBLE_64BIT
       return 0,Record_List.append(Table_Record.get_value_data_as_floating_point(Column_Number))  
    elif (Column_Type == 8): #DATETIME 
       #return Record_List.append(Table_Record.get_value_data_as_integer(Column_Number))  
       if (Table_Record.get_value_data(Column_Number) == None):
          return 0,Record_List.append('')
       elif (Table_name == "DNS" ): #Pulling out IP address from DNS table
          return 0,Record_List.append('')
       else:
          return 0,Record_List.append(win_date_bin_to_datetime(Table_Record.get_value_data(Column_Number)))
    elif (Column_Type == 9): #BINARY_DATA_TO_HEX
       if (Table_Record.get_value_data(Column_Number) == None):
          sys.stdout.write("NO BINARY_DATA_TO_HEX||NO BINARY_DATA_TO_HEX||") #Writing data out if the loop doesn't work. Including the statement, just to make sure
          return 1,"NO BINARY_DATA_TO_HEX||NO BINARY_DATA_TO_HEX||"
       else:
          hexdb=binascii.hexlify(Table_Record.get_value_data(Column_Number)) #Turning the binary data to hex
          macaddress=hexdb.decode('utf-8', 'ignore') 
          if ((len(hexdb) <= 8) and Column_Name == "Address"): #Checking to see what the hex length is, and doing the needed conversion to IP addresses here 
              if (len(hexdb)< 8):  #A check to help ensure length is right
                  hexdb = ''.join(('0',hexdb)) #Adding zeros to make sure everything is correct
              ipaddr = "%i.%i.%i.%i" % (int(hexdb[0:2],16),int(hexdb[2:4],16),int(hexdb[4:6],16),int(hexdb[6:8],16)) #Proper formatting
              raw_ipaddr_correlations = DNS_Dict.get(ipaddr, "No Match for IP address found") #Looking up value-key in DNS_Dict dictionary file above
              ipaddr_correlations = str(raw_ipaddr_correlations).strip("[]") #Removing brackets
              sys.stdout.write(str(macaddress).upper()+"||"+str(ipaddr)+" ("+str(ipaddr_correlations)+")||") #Writing raw address and converted address to stdout
              return 1,str(macaddress).upper()+"||"+str(ipaddr)+" ("+str(ipaddr_correlations)+")||"
          elif (((macaddress[:4] == "fe80") or (macaddress[:4] == "2001")) and (Column_Name == "Address") and (len(hexdb) == 32)): # A couple of checks for the IPV6 address formatting. So far have only seen fe80 and 2001, there may be more
              colonaddedtohexdb = ':'.join(macaddress[i:i + 4] for i in range(0, len(macaddress), 4)) #Adding colons to the IPV6 address
              ipv6Parts = colonaddedtohexdb.split(":") #Splitting for future ease
              macParts = [] #Parts, to be used in the futre
              for ipv6Part in ipv6Parts[-4:]: #Looping, so we can build the ipv6 address
                  while len(ipv6Part) < 4:
                      ipv6Part = "0" + ipv6Part
                  macParts.append(ipv6Part[:2])
                  macParts.append(ipv6Part[-2:])
              # modify parts to match MAC value
              macParts[0] = "%02x" % (int(macParts[0], 16) ^ 2) #Formatting
              del macParts[4] #Nope
              del macParts[3] #Nope again
              rawmacparts = ":".join(macParts) #More formatting
              finalmac=str(rawmacparts).upper() #Upper case  
              sys.stdout.write(str(macaddress).upper()+"||"+str(colonaddedtohexdb)+" IPv6 MAC: "+str(finalmac)+"||") #Writing raw address and converted address to stdout
              return 1,str(macaddress).upper()+"||"+str(colonaddedtohexdb)+" IPv6 MAC: "+str(finalmac)+"||"
          elif ( (str(macaddress) == "00000000000000000000000000000001") and (Column_Name == "Address") and (len(hexdb) == 32)): # A couple of checks for the IPV6 local host address formatting
              sys.stdout.write(str(macaddress).upper()+"||Local Host ::1||") #Writing the data out if the address is local host IPv6
              return 1,str(macaddress).upper()+"||Local Host ::1||"
          else:
              sys.stdout.write(str(macaddress).upper()+"||Unable to convert data||") #Writing data out if the loop doesn't work. Including the statement, just to make sure
              return 1,str(macaddress).upper()+"||Unable to convert data||"
    elif (Column_Type == 10): #TEXT 
       if (Table_Record.get_value_data(Column_Number) == None):
          return 0,Record_List.append('')
       else:
          return 0,Record_List.append(Table_Record.get_value_data(Column_Number).decode('utf-16', 'ignore'))
    elif (Column_Type == 11): #LARGE_BINARY_DATA
       if (Table_Record.get_value_data(Column_Number) == None):
          return 0,Record_List.append('')
       else:
          return 0,Record_List.append(Table_Record.get_value_data(Column_Number))
    elif (Column_Type == 12): #LARGE_TEXT 
       if ((Table_Record.get_value_data(Column_Number) == None) and (Column_Name == "ClientName")):
          return 0,Record_List.append('') #Returning Nothing for ClientName
       elif ((Table_Record.get_value_data(Column_Number) == None) and (Column_Name == "AuthenticatedUserName")):
          sys.stdout.write("<BLANK>||") #Printing the large text data
          return 1,"<BLANK>||"
       elif ((Table_Record.get_value_data(Column_Number) == "\x00\x00") and (Column_Name == "AuthenticatedUserName")):
          sys.stdout.write("<BLANK>||") #Printing the large text data
          return 1,"<BLANK>||"
       elif ((Table_Record.get_value_data(Column_Number) == "") and (Column_Name == "AuthenticatedUserName")):
          sys.stdout.write("<BLANK>||") #Printing the large text data
          return 1,"<BLANK>||"
       elif ((Column_Name == "Address") and (Table_name == "DNS" )): #Pulling out IP address from DNS table
          global ip_address_from_dns #Declaring the global variable
          ip_address_from_dns = Table_Record.get_value_data(Column_Number).decode('utf-16', 'ignore').replace('\x00', '') #Assigning the IP address to the variable
       elif ((Column_Name == "HostName") and (Table_name == "DNS" )): #Pulling out Hostname from DNS table
          hostname_from_dns = Table_Record.get_value_data(Column_Number).decode('utf-16', 'ignore').replace('\x00', '') #Assigning the Hostname to the variable
          #sys.stdout.write("DNS IP Address is "+ip_address_from_dns+" hostname is "+str(hostname_from_dns)+"\r\n")
          if ip_address_from_dns in DNS_Dict: #Populating DNS_Dict dictionary varaiable
              DNS_Dict[str(ip_address_from_dns)].append(str(hostname_from_dns)) #Append if value is seen
          else:
              DNS_Dict[str(ip_address_from_dns)] = [str(hostname_from_dns)] #Create new pair if value is not seen
       else:
          large_text = Table_Record.get_value_data(Column_Number).decode('utf-16', 'ignore')
          lengthoflarge_text=len(large_text) #Computing the length, as another check
          if ((lengthoflarge_text > 1) and (pythonversion == 2) ):
            sys.stdout.write(large_text.encode('utf-8')+"||") #Printing the large text data if value is greater than 1
            return 1,large_text.encode('utf-8')+"||"
          elif ((lengthoflarge_text > 1) and (pythonversion > 2) ):
            sys.stdout.write(large_text+"||") #Printing the large text data if value is greater than 1
            return 1,large_text+"||"
          else:
            sys.stdout.write("<BLANK>||") #Printing the large text data if value is not greater than 1
            return 1,"<BLANK>||"
    elif (Column_Type == 13): #SUPER_LARGE_VALUE
       return 0,Record_List.append(Table_Record.get_value_data_as_integer(Column_Number))   
    elif (Column_Type == 14): #INTEGER_32BIT_UNSIGNED 
       int32bitunsigned=str(Table_Record.get_value_data_as_integer(Column_Number))
       if (Column_Name == "TotalAccesses"): #Ensuring total accesses column name is correct
           global totalcountofaccesses #Calling the global variable
           totalcountofaccesses=int32bitunsigned #Setting the global variable for a check later on
           sys.stdout.write(int32bitunsigned+"||") #Printing the number of Accesses
           return 1,int32bitunsigned+"||"
       else:
           sys.stdout.write(int32bitunsigned+"||") #Printing the number
           return 1,int32bitunsigned+"||"
    elif (Column_Type == 15): #INTEGER_64BIT_SIGNED
       return 0,Record_List.append(Table_Record.get_value_data_as_integer(Column_Number))   
    elif (Column_Type == 16): #GUID 
       if (Table_Record.get_value_data(Column_Number) == None):
           sys.stdout.write("NO GUID DATA||") #Printing the string
           return 1,"NO GUID DATA||"
       else:
          uuid_Bytes = Table_Record.get_value_data(Column_Number)
          orgguid = uuid.UUID(bytes_le=uuid_Bytes) #Turning the data into a GUID
          urnguid=orgguid.urn #Making the GUID easier to work with
          rawguid = urnguid[9:] #Stripping out unneeded formatting 
          ucrawguid=str(rawguid).upper() #Making it all upper case
          fullguid='{'+ucrawguid+'}' #Building the GUID for the table lookup
          if (Column_Name == "RoleGuid"): #Ensuring Column Name is correct
              GUID_conversion = GUID_Dict.get(fullguid, "No Match for GUID found") #Looking up value-key in GUID_Dict dictionary file above
              sys.stdout.write(fullguid+" ("+GUID_conversion+")||") #Writing the string     
              return 1,fullguid+" ("+GUID_conversion+")||"     
          else:
              sys.stdout.write(fullguid+"||") #If it doesn't work, writing the string
              return 1,fullguid+"||"
    elif (Column_Type == 17): #INTEGER_16BIT_UNSIGNED
       value=Table_Record.get_value_data_as_integer(Column_Number)
       if ( (value > 0) and ( "Day" in str(Column_Name)) ): #Checking to see if Day is in the field. If so, we will do some converting
           juliandate= str(Column_Name)[3:] #Pulling out Julian Date
           #sys.stdout.write(str(juliandate)+" is Julian Date\r\n")
           global insertdatefourofyear #Pulling the insert date four of year
           global lastaccessfourofyear #Pulling the last access four of year
           global lastaccessyyyymmdd #Pulling the last access yyyymmdd
           global insertdateyyyymmdd #Pulling the insert date yyyymmdd
           global badyeardetector #Calling the global variable of badyeardetector
           global correlatedtwoaccessmismatchyear #Calling on the global variable of correlatedtwoaccessmismatchyear
           res = ""
           if ( (int(insertdatefourofyear)) != (int(lastaccessfourofyear)) and (Column_Name != "Day1") and (totalcountofaccesses == "2") ) : #We enter this loop if the years don't match, the day isn't Day1, and the count of accesses is two (because we can deduce what is what)
               if (correlatedtwoaccessmismatchyear != "Yes"): #A nested loop, because we need to do this
                   sys.stdout.write(str(insertdateyyyymmdd)+":1, "+str(lastaccessyyyymmdd)+":1") #Writing the string here
                   correlatedtwoaccessmismatchyear="Yes" #Setting the variable to yes
                   res += str(insertdateyyyymmdd)+":1, "+str(lastaccessyyyymmdd)+":1"
           else:
               if ( (int(insertdatefourofyear)) != (int(lastaccessfourofyear)) and (Column_Name != "Day1") and (totalcountofaccesses > "2") and (badyeardetector != "Yes") ) : #We enter this loop if the years don't match, the day isn't Day1, and the count of accesses is greater than two. Because who knows what is going on with this database here?
                   sys.stdout.write("**** WARNING: Multiple years detected, correlated \"DatesAndAccesses\" may not be accurate **** ") #Writing the WARNING string here
                   badyeardetector="Yes" #Setting the value to Yes
               import datetime #Yes, this has to happen here too
               #Checking to see if the hour is 23 and day is 31. The day should be 1, however, time skew can happen, and we are accounting for that here
               if ((Column_Name == "Day1") and (int(insertdatehour) == 23) and (int(insertdateday) == 31) ): 
                   properinsertdatefourofyear = (int(insertdatefourofyear) + 1) #Adding one to the year to make it right, and avoiding adding a variable to itself, because reasons
                   insertdatefourofyear = properinsertdatefourofyear #Setting the global variable to the proper value of +1
               testingd = datetime.datetime.strptime('{} {}'.format(juliandate, insertdatefourofyear),'%j %Y') #Formatting the day to datetime
               fullconvjd = testingd.strftime("%Y-%m-%d") #Another formatting
               sys.stdout.write(str(fullconvjd)+": "+str(value)+", ") #Printing the string
               return 1,res + str(fullconvjd)+": "+str(value)+", "
       elif ( value > 0):
           sys.stdout.write(str(Column_Name)+" "+str(value)+",") #Printing the string
       else:
           sys.stdout.write("") #Printing the string


if len(sys.argv) == 1:
   #  sys.stderr.write("\r\n88      a8P   ad88888ba                      88  88\r\n88    ,88'   d8\"     \"8b  ,d                 \"\"  88\r\n88  ,88\"     Y8,          88                     88\r\n88,d88'      `Y8aaaaa,  MM88MMM  8b,dPPYba,  88  88   ,d8   ,adPPYba,\r\n8888\"88,       `\"\"\"\"\"8b,  88     88P'   \"Y8  88  88 ,a8\"   a8P_____88\r\n88P   Y8b            `8b  88     88          88  8888[     8PP\"\"\"\"\"\"\"\r\n88     \"88,  Y8a     a8P  88,    88          88  88`\"Yba,  \"8b,   ,aa\r\n88       Y8b  \"Y88888P\"   \"Y888  88          88  88   `Y8a  `\"Ybbd8\"'\r\n\r\n") #Writing ASCII art to STDERr
   #  sys.stderr.write("Version "+str(kstrikeversionnumber)+"\r\n") #Writing version to STDERR
   #  sys.stderr.write("\r\nThis script will parse on-disk User Access Logging found on Windows Server 2012\r\nand later systems under the path \"\Windows\System32\LogFiles\SUM\"\r\nThe output is double pipe || delimited\r\n\r\n\r\nExample Usage: KStrike.py Current.mdb > SYSNAME_Current.txt\r\n\r\n") #Writing info to SDTERR
    sys.exit() #A nice clean exit
#First, we figure the version of python we are running
if sys.version_info[0] < 3:
    pythonversion=2
else:
    pythonversion=3
# sys.stderr.write("\r\nPython Version" +str(pythonversion)+" detected\r\n\r\n") #Writing info to SDTERR

output_file = None
try:
   output_file = sys.argv[2]
except:
   pass

file_object = open(sys.argv[1], "rb") #Opening file
esedb_file = pyesedb.file() #ESE db needed things
esedb_file.open_file_object(file_object) #ESE db needed things
Num_Of_tables = esedb_file.get_number_of_tables() #ESE db needed things
# sys.stderr.write ("The number of tables is "+str(Num_Of_tables)+"\r\n") #A nice message to STDERR
for i in range (0, Num_Of_tables): #Loop through the table names
    Table = esedb_file.get_table(i)
    Table_name = Table_Dict[Table.get_name()]
    Table_name.encode("utf-8")
    if (Table_name == "DNS"): #CLIENTS is the maing one we are interested in
       dnstablenumber=i #Saving this for later
    elif (Table_name == "CLIENTS"): #CLIENTS is the maing one we are interested in
       clienttablenumber=i #Saving this for later
   #  sys.stderr.write("Table "+str(i)+" Name is: "+str(Table_name)+"\r\n") #Writing data to SDTERR
#Now we parse out the DNS table
DNSTable = esedb_file.get_table(int(dnstablenumber)) #Table six is the DNS table. But checking just to be sure
Table_name = Table_Dict[DNSTable.get_name()] #Dictionary lookup
Template_Name = DNSTable. get_template_name() #Grabbing name
Table_Num_Columns = DNSTable.get_number_of_columns() #Grabbing Columns
Table_Num_Records = DNSTable.get_number_of_records() #Grabbing Records
if (Table_Num_Records > 0 and Table_name == "DNS"): #Another check to ensure we process the right table
    for t in range(0,Table_Num_Records): #Looping through the data
       progresscounter=(t + 1) #Since count starts at zero, we need to add one
      #  sys.stderr.write("Parsing "+str(progresscounter)+" of "+str(Table_Num_Records)+" DNS table records\r\n") #Needed for debugging
       for x in range(0, Table_Num_Columns): #Stepping through the data
         Data_Value=[] #To be used later
         Table_Record = DNSTable.get_record(t) #Getting record
         Column_Name = Table_Record.get_column_name(x) #Getting name
         Column_Type = Table_Record.get_column_type(x) #Getting type
         Check_Column_Type(Table_Record, Column_Type, x, Data_Value) #Arguments to pass to subroutine
else:
   #  sys.stderr.write("The table \"DNS\" has zero records\r\n")
    progresscounter="0"

if (Table_name == "CLIENTS"): #CLIENTS is the maing one we are interested in
    clienttablenumber=i #Saving this for later
#Now we parse out the CLIENTS table
ClientsTable = esedb_file.get_table(int(clienttablenumber)) #Table five is the CLIENTS table. But checking just to be sure
Table_name = Table_Dict[ClientsTable.get_name()] #Dictionary lookup
Template_Name = ClientsTable. get_template_name() #Grabbing name
Table_Num_Columns = ClientsTable.get_number_of_columns() #Grabbing Columns
Table_Num_Records = ClientsTable.get_number_of_records() #Grabbing Records
if (Table_Num_Records > 0 and Table_name == "CLIENTS"): #Another check to ensure we process the right table
    sys.stdout.set_header( ["RoleGuidRoleName","TenantId","TotalAccesses","InsertDate","LastAccess","RawAddress","ConvertedAddress_Correlated_HostName","AuthenticatedUserName","DatesAndAccesses"] , output_file)

    for t in range(0,Table_Num_Records): #Looping through the data
       progresscounter=(t + 1) #Since count starts at zero, we need to add one
      #  sys.stderr.write("Parsing "+str(progresscounter)+" of "+str(Table_Num_Records)+" CLIENTS table records\r\n") #Needed for debugging
       for x in range(0, Table_Num_Columns): #Stepping through the data
         Data_Value=[] #To be used later
         Table_Record = ClientsTable.get_record(t) #Getting record
         Column_Name = Table_Record.get_column_name(x) #Getting name
         Column_Type = Table_Record.get_column_type(x) #Getting type

         Check_Column_Type(Table_Record, Column_Type, x, Data_Value) #Arguments to pass to subroutine
         

       sys.stdout.write("||") #Last bit of formatting to string
       badyeardetector="No" #Changing it back to No
       correlatedtwoaccessmismatchyear="No" #Changing it back to No

       sys.stdout.print(output_file)
else:
   #  sys.stderr.write("The table \"CLIENTS\" has zero records\r\n")
    progresscounter="0"
esedb_file.close() #Close db

scriptruntime=(time.time() - StartTime) #Calculating the run time
formattedscriptruntime=int(scriptruntime) #Making an integer for the result
#If it is less than 60, we print seconds. Otherwise, we format it H:MM:SS format
if (formattedscriptruntime > 60):
    import datetime #Yes, we need this here (again)
    totalruntime=str(datetime.timedelta(seconds=int(formattedscriptruntime))) #Making the string
   #  sys.stderr.write("\r\nKStrike processed "+str(progresscounter)+" records in "+totalruntime+" (H:MM:SS)\r\n\r\n") #Writing the output
else:
   #  sys.stderr.write("\r\nKStrike processed "+str(progresscounter)+" records in "+str(formattedscriptruntime)+" seconds\r\n\r\n") #Just seconds here
   sys.exit() #A nice clean exit