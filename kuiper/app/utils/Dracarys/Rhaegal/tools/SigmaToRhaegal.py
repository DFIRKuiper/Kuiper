import yaml
import argparse
import os
from datetime import datetime
from sys import exit

__author__ = "AbdulRhman Alfaifi"
__version__ = "0.1"
__maintainer__ = "AbdulRhman Alfaifi"
__license__ = "GPL"
__status__ = "Development"

parser = argparse.ArgumentParser(description="Convert SIGMA rules to Rhaegal rules")
parser.add_argument("-r","--rulesDir",help="Path that contains SIGMA rules.")
parser.add_argument("-o","--output",help="The path where the results will be saved.")
parser.add_argument("-v","--version",help="Print version number",action="store_true",default=False)

if "__main__" == __name__:
    args = parser.parse_args()
    if args.version:
        print(f"v{__version__}")
        exit()
    else:
        print("error: the following arguments are required: -r/--rulesDir, -o/--output")
        exit()
    map = {'application': 'Application', 'security': 'Security', 'system': 'System', 'sysmon': 'Microsoft-Windows-Sysmon/Operational', 'powershell': 'Microsoft-Windows-PowerShell/Operational', 'taskscheduler': 'Microsoft-Windows-TaskScheduler/Operational', 'wmi': 'Microsoft-Windows-WMI-Activity/Operational', 'dhcp': 'Microsoft-Windows-DHCP-Server/Operational','powershell-classic': 'Windows PowerShell'}
    outfile = open(args.output,"w")
    counter = 0
    for root, dirs, files in os.walk(args.rulesDir):
        for file in files:
            if file.endswith(".yml"):
                RhaegalRule = {"metadata": {"author": "", "reference": "", "creationDate": "", "score": 0, "description": ""}, "Channel": "", "include": {}}
                fullpath = os.path.abspath(os.path.join(root,file))
                try:
                    rule = yaml.load(open(fullpath,"r").read(),Loader=yaml.FullLoader)
                except:
                    pass
                if rule.get("logsource").get("product").lower() == "windows":
                    RhaegalRule["metadata"]["author"] = rule.get("author")
                    if rule.get("references"):
                        RhaegalRule["metadata"]["reference"] = ", ".join(rule.get("references"))
                    RhaegalRule["metadata"]["creationDate"] = str(datetime.now().date()) if rule.get("date") == None else rule.get("date")

                    level = rule.get("level").lower()
                    if level == "low":
                        RhaegalRule["metadata"]["score"] = 40
                    if level == "medium":
                        RhaegalRule["metadata"]["score"] = 60
                    if level == "high":
                        RhaegalRule["metadata"]["score"] = 80
                    if level == "critical":
                        RhaegalRule["metadata"]["score"] = 100
                    
                    RhaegalRule["metadata"]["description"] = rule.get("description")
                    RhaegalRule["Channel"] = map.get(rule.get("logsource").get("service")) if map.get(rule.get("logsource").get("service")) else rule.get("logsource").get("service")
                    if rule.get("detection").get("selection") and isinstance(rule.get("detection").get("selection"),dict):
                        include = {}
                        for key,val in rule.get("detection").get("selection").items():
                            if key == "EventID":
                                if isinstance(val,list):
                                    strList = [str(v) for v in val]
                                    include.update({key:strList})
                                else:
                                    include.update({key:str(val)})
                            else:
                                if isinstance(val,list):
                                    strList = [str(v) for v in val]
                                    include.update({"Data."+key:strList})
                                else:
                                    include.update({"Data."+key:str(val)})
                        RhaegalRule["include"] = include
                    else:
                        RhaegalRule["include"] = None

                    if rule.get("detection").get("filter") and isinstance(rule.get("detection").get("filter"),dict):
                        exclude = {}
                        for key,val in rule.get("detection").get("filter").items():
                            if key == "EventID":
                                if isinstance(val,list):
                                    strList = [str(v) for v in val]
                                    exclude.update({key:strList})
                                else:
                                    exclude.update({key:str(val)})
                            else:
                                if isinstance(val,list):
                                    strList = [str(v) for v in val]
                                    exclude.update({"Data."+key:strList})
                                else:
                                    exclude.update({"Data."+key:str(val)})
                                #print(key,val)
                        RhaegalRule["exclude"] = exclude

                    if rule.get("logsource").get("service") and RhaegalRule.get("include"):
                        outfile.write(f"public {rule.get('title').replace(' ','_').replace('-','_')} \n{{\n")
                        #print(f"public {rule.get('title').replace(' ','_')} \n{{")
                        for line in yaml.dump(RhaegalRule,default_flow_style=False,sort_keys=False).split("\n"):
                            if line:
                                outfile.write("    "+line+"\n")
                                #print("    "+line)
                        #print("\n}")
                        outfile.write("}\n# "+"-"*100+"\n")
                        #print("# "+"-"*100)
                        #print("\x1b[31m"+"-"*100+"\x1b[0m")
                        counter += 1
    print(f"# {counter} Rules parsered !")

