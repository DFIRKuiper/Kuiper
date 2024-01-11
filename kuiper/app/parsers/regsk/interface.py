import os
import sys
import subprocess
import json
import ast

def auto_interface(file,parser):

    lst = ["REGTimeLine","UserAssist","Bam","OpenSaveMRU","LastVisitedMRU","MuiCache","AppCompatFlags","LaunchTracing","ProfileList","Uninstall","InstalledApp","InstalledComponents","ShellExtensions","Sysinternals","RunMRU","StreamMRU ","TimeZoneInformation","ComputerName","TypedUrls","DHCP","TypedPaths","WordWheelQuery","TerminalServerClient","BagMRU","VolatileEnvironment","PortForwading","Amcache","Services"]
    try:
        CurrentPath=os.path.dirname(os.path.abspath(__file__))
        if parser in lst:
            cmd = 'python3 '+ CurrentPath+'/regsk.py -k -f "' + file.replace("$" , '\$') + '" -pl ' + parser
            proc = subprocess.Popen(cmd, shell=True ,stdin=None , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
            res , err = proc.communicate()
            # the error "An error has occurred when recovering a hive using a transaction log" occured on REGTimeLine
            if err != "" and err != "An error has occurred when recovering a hive using a transaction log":
                raise Exception(err.split("\n")[-2])
            res = res.split('\n')
            data = ""
            for line in res:
                if line.startswith('['):
                    data += line
                elif line.startswith("saleh:"):
                    print line
            if data == "":
                return []
            d = []

            for i in json.loads(data):
                if not isinstance(i , dict):
                    i = json.loads(i)
                if type(i) == dict:
                    if len(i.keys()):
                        d.append(i)
                    else:
                        print i
                        continue
                else:
                    d.append(i)
            return d
        else:
            return (None, "[-] [Error] "+str(parser)+" Parser: is not exists")

    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)

if __name__ == "__main__":
    res = auto_interface("/app/files/files/test4/test4_S2/2022-10-17T15:15:54-S2.zip/PhysicalDrive1_0/Ntuser/Users/smuha/NTUSER.DAT" , "LastVisitedMRU")
    # res = auto_interface("/app/files/files/test3/test3_test_registries2/2022-10-17T08:26:16-test_registries2.zip/NTUSER.DAT" , "REGTimeLine")
    if res[0]:
        for i in res:            
            print i
    else:
        print res[1]