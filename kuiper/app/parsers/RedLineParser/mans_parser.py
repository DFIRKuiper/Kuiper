import xmltodict
import json
import sys
import zipfile
from datetime import datetime
from string import Template 

# ================================ update json failed
# get the value of specific 
def json_get_val_by_path(j , p):
    try:
        p_l = p.split('.')
        if len(p_l) == 1:
            return [True, j[p] ]
        k = p_l[0]
        if k not in j.keys():
            return [False, "Key ["+str(k)+"] not in the json"]
            
        return json_get_val_by_path( j[k] , '.'.join(p_l[1:]))
    except Exception as e:
        return [False , str(e)]


mans_fields = {
    "Issue" : {
        "message"           : "$generator: [$@level] $@summary"
    },
    "PersistenceItem": {
        "timestamp"         : "pathAttributes.createdTime",
        "timestamp_format"  : "%Y-%m-%dT%H:%M:%SZ",
        "message"           : "$generator: Name [$name], Path [$path], Owner [$pathAttributes.owner]",
    },
    "UserItem" : {
        "message"           : "$generator: $Username [$fullname]",
    },
    "DiskItem" : {
        "message"           : "$generator: Name [$DiskName], Path [$DevicePath], Size [$DiskSize bytes]",
    },
    "VolumeItem" : {
        "message"           : "$generator: Name [$VolumeName], Path [$DevicePath], Size [$TotalSize bytes], Mounted [$IsMounted]",
    },
    "FileDownloadHistoryItem" : {
        "timestamp"         : "StartDate",
        "timestamp_format"  : "%Y-%m-%dT%H:%M:%SZ",
        "message"           : "$generator: [$BrowserName] User [$Username] Downloaded [$SourceURL]",
    },
    "QuarantineEventItem" : {
        "timestamp"         : "TimeStamp",
        "timestamp_format"  : "%Y-%m-%dT%H:%M:%SZ",
        "message"           : "$generator: [$AgentName] User [$User] URL [$DataURLString]",
    },
    "RouteEntryItem" : {
        "message"           : "$generator: Interface [$Interface], Destination [$Destination], Gateway [$Gateway]",
    },
    "SystemInfoItem" : {
        "timestamp"         : "date",
        "timestamp_format"  : "%Y-%m-%dT%H:%M:%SZ",
        "message"           : "$generator: Host [$hostname] OS [$platform $OSbitness] [$OS] IP [$primaryIpAddress]"
    },


    "TaskItem" : {
        "timestamp"         : "MostRecentRunTime",
        "timestamp_format"  : "%Y-%m-%dT%H:%M:%SZ",
        "message"           : "$generator: Task [$Name|name]",
    },
    "UrlHistoryItem": {
        "timestamp"         : "LastVisitDate",
        "timestamp_format"  : "%Y-%m-%dT%H:%M:%SZ",
        "message"           : "$generator: [$BrowserName] User [$Username] visited [$URL]",
    },
    "ArpEntryItem" : {
        "message"           : "$generator: Interface [$Interface], MAC [$PhysicalAddress]",
    },
    "DnsEntryItem": {
        "message"           : "$generator: Host [$Host], Record Type [$RecordType], Data [$RecordData.Host|RecordData.IPv4Address]",
    },
    "PortItem": {
        "message"           : "$generator: Process [$path], Local [$localIP:$localPort] - Remote [$remoteIP:$remotePort], state [$state]",
    },
    "ProcessItem": {
        "timestamp"         : "startTime",
        "timestamp_format"  : "%Y-%m-%dT%H:%M:%SZ",
        "message"           : "$generator: PID[$pid], User [$Username], Process [$arguments]",
    },
    "ServiceItem": {
        "message"           : "$generator: Name [$name], Args [$arguments]",
    },
    
}

class CustomTemplate(Template):
    idpattern = r'[_a-z@][_@.a-z0-9|]*'


class ParseMans:
    mans_file = None
    mans_zip = None
    mans_xml_files = []
    excluded_files = ["manifest.json" , "platform.xml" , "Script.xml" , "metadata.json" , "script.json"]

    def __init__(self , mans_file):
        self.mans_file = mans_file
        with zipfile.ZipFile(self.mans_file,) as zf:
            
            self.mans_xml_files = [name for name in zf.namelist() if name not in self.excluded_files]
    

    # xml to json 
    def parse_file(self , file_name):
        with zipfile.ZipFile(self.mans_file,) as zf:
            with zf.open(file_name) as read_f:
                xml_file = read_f.read()
                dict_data = xmltodict.parse(xml_file)
                return json.loads(json.dumps(dict_data))



    # iterate all files in .mans and parse its content 
    def parse_files(self):
        global_records = []
        for xml_file in self.mans_xml_files:
            json_records = self.parse_file(xml_file)
            records = []
            if 'itemList' in json_records.keys() or 'IssueList' in json_records.keys():
                item_list = 'itemList' if 'itemList' in json_records.keys() else 'IssueList'
                generator = json_records[item_list]['@generator'] 
                for item in json_records[item_list].keys():
                    if not item.startswith(u"@"):
                        # this to solve SystemInfoItem since it is not list 
                        if isinstance(json_records[item_list][item] , dict):
                            json_records[item_list][item] = [json_records[item_list][item]]


                        for r in json_records[item_list][item]:
                            r['generator']      = generator
                            r['source_file']    = xml_file
                            r['item']           = item

                            item_mans_fields    = mans_fields.get(item , None)

                            # timestamp 
                            timestamp = json_get_val_by_path(r, item_mans_fields['timestamp']) if item_mans_fields is not None and 'timestamp' in item_mans_fields.keys() else [False]
                            if timestamp[0] == True:
                                timestamp_format = item_mans_fields['timestamp_format']
                                timestamp_object = datetime.strptime(timestamp[1], timestamp_format)
                                r['@timestamp']    = timestamp_object.isoformat()
                            else:
                                r['@timestamp']    = "1700-01-01T00:00:00"

                            # message
                            message = item_mans_fields['message'] if item_mans_fields is not None and 'message' in item_mans_fields.keys() else ""
                            tpl = CustomTemplate(message)
                            fields = {}
                            pattern_fields = [m.group('named') or m.group('braced') for m in tpl.pattern.finditer(tpl.template) if m.group('named') or m.group('braced')]
                            for f in pattern_fields:
                                for fs in f.split("|"): # handle 'or' condition
                                    value = json_get_val_by_path(r , fs)
                                    if value[0]:
                                        fields[f] = value[1]
                                        break

                            r['message'] = tpl.safe_substitute(fields)



                            records.append( r )
            global_records += records
        return global_records
