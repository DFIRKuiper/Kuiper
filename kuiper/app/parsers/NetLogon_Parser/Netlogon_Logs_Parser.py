import sys, argparse
import re
import json
import pytz
from datetime import datetime




#Define Regexs
META_DATA = re.compile('.*\[LOGON\].*\[[0-9]+\]') #Only parsing the LOGON module logs
AUTH_ENTRY =re.compile('.*SamLogon: Transitive Network logon of.*')
AUTH_ENTRY_TYPE1 = re.compile(".*\) Entered\s*")
AUTH_ENTRY_TYPE2 =re.compile('Returns 0x[0-9A-Fa-f]+') 
DOMAIN_USER = re.compile(' .*\\\\.* from')
COMPUTERS = re.compile('from.*\(via.*\)')

#Define Constants 
MODE_1='Singular'
MODE_2='Consolidated'
RECORDS_TYPES=['Authentication Request','Authentication Response','Request and Response Authentication']

#Define Global Variables Refrence -> https://stackoverflow.com/questions/16156597/how-can-i-convert-windows-timezones-to-timezones-pytz-understands
TIMEZONE_ADJUST = "Asia/Riyadh"



#Define Response Code Messages according to https://mandie.net/2013/04/23/netlogon-log-part-1/
RESPONSE_CODES= {"0x0": "Successful login",
"0xC0000064": "The specified user does not exist",
"0xC000006A":  "The value provided as the current password is not correct",
"0xC000006C":  "Password policy not met",
"0xC000006D":  "The attempted logon is invalid due to a bad username",
"0xC000006E":  "User account restriction has prevented successful login",
"0xC000006F":  "The user account has time restrictions and may not be logged onto at this time",
"0xC0000070":  "The user is restricted and may not log on from the source workstation",
"0xC0000071":  "The user account’s password has expired",
"0xC0000072":  "The user account is currently disabled",
"0xC000009A":  "Insufficient system resources",
"0xC0000193":  "The user’s account has expired",
"0xC0000224":  "User must change his password before he logs on the first time",
"0xC0000234":  "The user account has been automatically locked"
}


class auth_record:
 
  def __init__(self, record_type,meta, message):
        self.record_type=record_type
        self.timestamp= self.format_time(meta)
        self.domain,self.authenticate_user =self.extract_user(message)
        self.computer_src, self.computer_targted  = self.extract_computers(message)

  def format_time(self,meta):
        #Input Format: string MM/Day HH:MM:SS [LOGON] [PID]

        dt,time = meta.group(0).split("[")[0].split()
        mon,day=dt.split('/')
        if (int(mon) >datetime.now().month):
            year= datetime.now().year -1
        else:
            year= datetime.now().year

        Mon = datetime.now().month

        #Adjust Time to UTC+0 
        local = pytz.timezone(TIMEZONE_ADJUST)
        naive = datetime.strptime("{}-{:02d}-{:02d} {}".format(year,int(mon),int(day),time), "%Y-%m-%d %H:%M:%S")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        timestamp = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")
        return timestamp

  def extract_user(self,message):
        user = DOMAIN_USER.search(message).group()
        if user:
            try:
                user = user[:-5] # to execulde the "From" delimiter
                domain = user.split('\\')[0].split()[-1]
                user =domain+'\\'+user.split('\\')[1] 
                return domain,user
            except (IndexError,TypeError):
                return 'Failed to parse','Failed to parse'
        else:
            return 'Failed to parse','Failed to parse'

  def extract_computers(self,message):
        try:
         computers = COMPUTERS.search(message).group()
         if computers:
                dest_comp = computers.split('(')[-1].split(' ')[1][:-1]
                src_comp = computers.split('(')[0].split(' ')[1]
                return src_comp,dest_comp
         else:
            return 'Failed to parse','Failed to parse'
        except (IndexError,TypeError):
           return 'Failed to parse','Failed to parse'
class auth_reponse_record(auth_record):
    def __init__(self, record_type,meta, message):
        super(auth_reponse_record, self).__init__(record_type,meta, message)
        self.dc_response,self.dc_response_code = self.extract_response(message)

    def extract_response(self,msg):
        resp_code = AUTH_ENTRY_TYPE2.search(msg).group()
        if resp_code:
            try:
                code = resp_code.split()[1]
                message= RESPONSE_CODES[code]
                return code,message
            except (IndexError,TypeError):
                return 'Failed to parse','Failed to parse'
        else:
            return 'Failed to parse','Failed to parse'
def process_lines_mode1(filename):
    
    #Read File
    try:
        with open(filename) as f:
             lines = f.readlines()
    except OSError as e:
        print(str(e))
    
    complete_records = []

    for line in lines:
        logon_request =META_DATA.match(line)
        if (logon_request): # Then, parse this line   
            msg_delimiter = len(logon_request.group(0))
            message= line[msg_delimiter:]

            if (AUTH_ENTRY.match(message)): #It's an authentication related record             
                if (AUTH_ENTRY_TYPE1.search(message)): #It's a request for authentication record
                    req = auth_record(RECORDS_TYPES[0],logon_request,message)
                    complete_records.append(req)
                elif (AUTH_ENTRY_TYPE2.search(message)):
                    req = auth_reponse_record(RECORDS_TYPES[1],logon_request,message)
                    complete_records.append(req)
            else:
                pass 
    return complete_records



class auth_record_consolidated:
 
  def __init__(self,meta, message):
        self.timestamp,pid = self.format_time(meta)
        self.domain,self.authenticate_user =self.extract_user(message)
        self.computer_src, self.computer_targted  = self.extract_computers(message)
        self.dc_response_code = "" 
        self.dc_response = ""
        self.dc_response_timestamp = ""
        self.complete = False
        self.key = ':'.join([pid,self.authenticate_user,self.computer_src,self.computer_targted])

  def update_response(self,meta, message):
        self.dc_response_timestamp,pid = self.format_time(meta)
        self.dc_response,self.dc_response_code = self.extract_response(message)
        self.complete = True
 
  def get_key(self):
        #Timestamp:PID:username:src_cmp:dst_cm
        return self.key
 
  def is_complete(self):
        return self.complete

  def format_time(self,meta):
        #Input Format: string MM/Day HH:MM:SS [LOGON] [PID]
        pid = meta.group(0).split("[")[-1][:-1]
        dt,time = meta.group(0).split("[")[0].split()
        mon,day=dt.split('/')
        if (int(mon) >datetime.now().month):
            year= datetime.now().year -1
        else:
            year= datetime.now().year

        Mon = datetime.now().month
        #Adjust Time to UTC+0 
        local = pytz.timezone(TIMEZONE_ADJUST)
        naive = datetime.strptime("{}-{:02d}-{:02d} {}".format(year,int(mon),int(day),time), "%Y-%m-%d %H:%M:%S")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        timestamp = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")
        return timestamp

  def extract_user(self,message):
        user = DOMAIN_USER.search(message).group()
        if user:
            try:
                user = user[:-5] # to execulde the "From" delimiter
                domain = user.split('\\')[0].split()[-1]
                user =domain+'\\'+user.split('\\')[1] 
                return domain,user
            except (IndexError,TypeError):
                return 'Failed to parse','Failed to parse'
        else:
            return 'Failed to parse','Failed to parse'

  def extract_computers(self,message):
        try:
         computers = COMPUTERS.search(message).group()
         if computers:
                dest_comp = computers.split('(')[-1].split(' ')[1][:-1]
                src_comp = computers.split('(')[0].split(' ')[1]
                return src_comp,dest_comp
         else:
            return 'Failed to parse','Failed to parse'
        except (IndexError,TypeError):
           return 'Failed to parse','Failed to parse'

  def extract_response(self,msg):
        resp_code = AUTH_ENTRY_TYPE2.search(msg).group()
        if resp_code:
            try:
                code = resp_code.split()[1]
                message= RESPONSE_CODES[code]
                return code,message
            except (IndexError,TypeError):
                return 'Failed to parse','Failed to parse'
        else:
            return 'Failed to parse','Failed to parse'
def process_lines_mode2(filename):
    with open(filename) as f:
         lines = f.readlines()

    unresolved_auths = {} #PID:username:src_cmp:dst_cmp -> [objects] (FIFO)
    complete_records = []

    for line in lines:
        logon_request =META_DATA.match(line)
        if (logon_request): # Then, parse this line
            msg_delimiter = len(logon_request.group(0))
            message= line[msg_delimiter:]

            if (AUTH_ENTRY.match(message)): #It's an authentication related record
               
                if (AUTH_ENTRY_TYPE1.search(message)): #It's a request for authentication record
                    req = auth_record_consolidated(logon_request,message)
                    k = req.get_key()
                    if k not in unresolved_auths:
                            unresolved_auths[k] =[req]
                    else:
                           unresolved_auths[k].append(req)

                elif (AUTH_ENTRY_TYPE2.search(message)):
                    tmp = auth_record_consolidated(logon_request,message)
                    key = tmp.get_key()
                    if key in unresolved_auths:
                        obj = unresolved_auths[key].pop()
                        obj.update_response(logon_request,message)
                        complete_records.append(obj)
                    else:
                        pass
                    del tmp
    return complete_records



            


if __name__ == "__main__":
  
    # Initialize parser
    parser = argparse.ArgumentParser( prog = 'NetLogOn Parser',
                    description = 'This script parses the NetLogOn logs records related to NTLM authentication.\n Be aware that the final results are on UTC time',
                    epilog = '....')
    #Positional argument
    parser.add_argument('filename')
    # Adding optional argument
    parser.add_argument('-m', '--mode',choices=[MODE_1,MODE_2],default=MODE_1,help = 'Set parsing mode: 1) Singular parsing will parse each record separately\n 2) Consolidated parsing will consolidate the authentication request and response into a single record')
    # Read arguments from command line
    parser.add_argument('-t', '--timezone',help = 'The Netlogon logs are logged according to the local system timezone. By default the parser will adjust the "Asia/Riyadh" timezone to UTC+0 , provide the another timezone as an argument to override the default "Asia/Riyadh".\n Example: --TimeZone=America/Anchorage')
    
    args = parser.parse_args()
    

    if args:
        if args.timezone:
            TIMEZONE_ADJUST = args.timezone
        if args.mode == MODE_1:
           recs = process_lines_mode1(args.filename)
           recs_dict =[]
           for i in recs:
                temp_dic= i.__dict__
                temp_dic['@timestamp'] = temp_dic['timestamp']
                recs_dict.append(json.dumps(temp_dic))
  
           print (recs_dict)
        elif args.mode == MODE_2:
           recs = process_lines_mode2(args.filename)

           for i in recs:
                temp_dic= i.__dict__
                temp_dic['@timestamp'] = temp_dic['timestamp']
                recs_dict.append(json.dumps(temp_dic))
           print(recs_dict)

    
