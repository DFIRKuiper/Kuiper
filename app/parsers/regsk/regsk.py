import os,sys
from lib.walker import defind_files_logs,defind_single_file_logs,get_files,logs_folder
from os import walk
import argparse
from plugins import UserAssist,Bam,OpenSaveMRU,LastVisitedMRU,MuiCache,AppCompatFlags,LaunchTracing,ProfileList,Uninstall,InstalledApp,InstalledComponents,ShellExtensions,Sysinternals,RunMRU,StreamMRU ,TimeZoneInformation ,ComputerName,TypedUrls,DHCP,TypedPaths,WordWheelQuery,TerminalServerClient,BagMRU,VolatileEnvironment,PortForwading,Amcache,Services
import glob
"""This function is to include the address function of each praser as well as the trget hive with some discription"""
def all_plugins():
    plugins = {"UserAssist":{'function': UserAssist.UserAssist,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "Bam": {'function':Bam.Bam,"Target_hives":"SYSTEM","Discription":"test"},
                "OpenSaveMRU": {'function':OpenSaveMRU.OpenSaveMRU,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "LastVisitedMRU": {'function':LastVisitedMRU.LastVisitedMRU,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "MuiCache": {'function':MuiCache.MuiCache,"Target_hives":"UsrClass.dat","Discription":"test"},
                "AppCompatFlags": {'function':AppCompatFlags.AppCompatFlags,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "LaunchTracing":{'function': LaunchTracing.LaunchTracing,"Target_hives":"SOFTWARE","Discription":"test"},
                "ProfileList": {'function':ProfileList.ProfileList,"Target_hives":"SOFTWARE","Discription":"test"},
                "Uninstall": {'function':Uninstall.Uninstall,"Target_hives":"SOFTWARE","Discription":"test"},
                "InstalledApp": {'function':InstalledApp.InstalledApp,"Target_hives":"SOFTWARE","Discription":"test"},
                "InstalledComponents": {'function':InstalledComponents.InstalledComponents,"Target_hives":"SOFTWARE","Discription":"test"},
                "ShellExtensions": {'function':ShellExtensions.ShellExtensions,"Target_hives":"SOFTWARE","Discription":"test"},
                "Sysinternals": {'function':Sysinternals.Sysinternals,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "RunMRU": {'function':RunMRU.RunMRU,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "TimeZoneInformation": {'function':TimeZoneInformation.TimeZoneInformation,"Target_hives":"SYSTEM","Discription":"test"},
                "ComputerName": {'function':ComputerName.ComputerName,"Target_hives":"SYSTEM","SYSTEM":"test"},
                "TypedUrls": {'function':TypedUrls.TypedUrls,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "DHCP":{'function': DHCP.DHCP,"Target_hives":"SYSTEM","Discription":"test"},
                "WordWheelQuery": {'function':WordWheelQuery.WordWheelQuery,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "TerminalServerClient":{'function':TerminalServerClient.TerminalServerClient,"Target_hives":"NTUSER.DAT","Discription":"test"},
                "PortForwading":{'function':PortForwading.PortForwading,"Target_hives":"SYSTEM","Discription":"test"},
                "Amcache":{'function':Amcache.Amcache,"Target_hives":"Amcache.hve","Discription":"test"},
                "Services":{'function':Services.Services,"Target_hives":"SYSTEM","Discription":"Collect services from the SYSTEM registry"}
                }

    return plugins

"""create hive folder"""
def create_folder(file):
    path, folder = os.path.split(file)
    us_folder = path.split("/")[-1]
    path = os.path.join('results',us_folder)
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)
    return path

"""this function is parse hive with a single plugin"""
def get_single_plugin(file,log,plugin):
    if file is not None:
        #rsult_fd = create_folder(file)
        defined_f = defind_single_file_logs(file,log)
        plugins = all_plugins()

        pl1 = plugins[plugin]['function'](defined_f['hive'],defined_f['logs'])
        results = pl1.run()
        path = os.path.join('results',plugin)
        result = open(path+".log","a+")
        if results is not None:
            for d in results:
                result.write(d+"\n")
        result.close()

"""print outpit for kuiper"""
def print_for_kuiper(file,log,plugin):
    if file is not None:
        #print(file)
        #rsult_fd = create_folder(file)
        defined_f = defind_single_file_logs(file,log)
        plugins = all_plugins()
        pl1 = plugins[plugin]['function'](defined_f['hive'],defined_f['logs'])
        dd = pl1.run()
        print (dd)

"""Get the main running argsparser"""
def main(argv=None):
    # if argv is None:
    argv = sys.argv
    parser = argparse.ArgumentParser()
    parser.add_argument("-p",  "--path", action="store",help="Path to all hives")
    parser.add_argument("-f", "--file", action="store", help="Parse single file")
    parser.add_argument("-l", "--log", nargs='*',action="store", help="Parse the log files")
    parser.add_argument("-pl", "--plugin", action="store", help="select single plugin")
    parser.add_argument("-a", "--all_plugins", action="store_true", help="select all plugins")
    parser.add_argument("-ls",  "--list", action="store_true", help="list all plugins")
    parser.add_argument("-v", "--verbose",  action="store_true", help="Enable verbose output")
    parser.add_argument("-k", "--kuiper",  action="store_true", help="Enable kuiper output")
    args = parser.parse_args(argv[1:])
    parser = argparse.ArgumentParser(description="Parse Registry hives")

    # list all plugin avaiable
    if args.list:
        plugins = all_plugins()
        lst = []
        for plg in plugins:
            lst.append(plg)
        print ("List of avaiable plugins:\t")
        print ("["+",".join(lst)+"]")

    # parse  files with all plugin avaiable
    if args.all_plugins:
        path = args.path
        fix = glob.glob('results/*')
        for f in fix:
            os.remove(f)
        if path is not None:
            files = get_files(path)
            plugins = all_plugins()
            for plu in plugins:
                for key in files:
                    logs= []
                    for fl in files[key]:
                        if fl.endswith(".LOG") or fl.endswith(".LOG1") or fl.endswith(".LOG2"):
                            logs.append(fl)
                    if plugins[plu]['Target_hives'] in files[key][0]:
                        get_single_plugin(files[key][0],logs,plu)
                        print ("[*] Parsing "+plu + " :" + files[key][0])
    
    # parse single file with specific plugin
    if args.plugin and args.kuiper == False:
        file = args.file
        log = args.log
        get_single_plugin(file,log,args.plugin)

    if args.kuiper:
        file = args.file
        
        logs =logs_folder(file)
        print_for_kuiper(file,logs,args.plugin)


if __name__ == "__main__":
    main(argv=sys.argv)
