import os
import sys
import subprocess
import json
import ast

def auto_interface(file,parser):
    lst = ["UserAssist","Bam","OpenSaveMRU","LastVisitedMRU","MuiCache","AppCompatFlags","LaunchTracing","ProfileList","Uninstall","InstalledApp","InstalledComponents","ShellExtensions","Sysinternals","RunMRU","StreamMRU ","TimeZoneInformation ","ComputerName","TypedUrls","DHCP","TypedPaths","WordWheelQuery","TerminalServerClient","BagMRU","VolatileEnvironment","PortForwading","Amcache"]
    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        if(parser in lst):
            proc = subprocess.Popen('python3 '+ CurrentPath+'/regsk.py -k -f ' + file + ' -pl ' +parser , shell=True ,stdout=subprocess.PIPE)

        data = proc.communicate()[0]
        data = ast.literal_eval(data)
        lst = []
        for d in data:
            lst.append(json.loads(d))
        return lst

    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print msg
        return (None , msg)
