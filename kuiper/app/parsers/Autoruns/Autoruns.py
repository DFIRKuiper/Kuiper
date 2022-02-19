import os,sys
from lib.walker import defind_files_logs,defind_single_file_logs,get_files,logs_folder
from os import walk
import argparse
from plugins import Logon,AppinitDLLs,BootExecute,KnownDLLs,Explorer,ImageHijacks,InternetExplorerAddons, Winsock, Codecs, OfficeAddins, PrintMonitorDLLs, LSAsecurityProviders, Winlogon
import glob
"""This function lists all praser"""
def all_plugins():
    plugins = {
                "Explorer":{'function':Explorer.Explorer},
                "KnownDLLs":{'function':KnownDLLs.KnownDLLs},
                "BootExecute":{'function':BootExecute.BootExecute},
                "AppinitDLLs":{'function':AppinitDLLs.AppinitDLLs},
                "Logon":{'function':Logon.Logon},
                "ImageHijacks":{'function':ImageHijacks.ImageHijacks},
                "InternetExplorerAddons":{'function':InternetExplorerAddons.InternetExplorerAddons,},
                "Winsock":{'function':Winsock.Winsock},
                "Codecs":{'function':Codecs.Codecs},
                "OfficeAddins":{'function':OfficeAddins.OfficeAddins},
                "PrintMonitorDLLs":{'function':PrintMonitorDLLs.PrintMonitorDLLs},
                "LSAsecurityProviders":{'function':LSAsecurityProviders.LSAsecurityProviders},
                "Winlogon":{'function':Winlogon.Winlogon}}

    return plugins


"""this function is parse hive with a single plugin"""
def get_single_plugin(file,log,plugin):
    if file is not None:
        defined_f = defind_single_file_logs(file,log)
        plugins = all_plugins()
        pl1 = plugins[plugin]['function'](defined_f['hive'],defined_f['logs'])
        dd = pl1.run()
        result = open("results\\"+plugin+".log","a+")
        if dd is not None:
            for d in dd:
                result.write(d+"\n")
        result.close()

"""print outpit for kuiper"""
def print_for_kuiper(file,log,plugin):
    if file is not None:
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
        if path is not None:
            files = get_files(path)
            plugins = all_plugins()
            for plu in plugins:
                for key in files:
                    logs= []
                    for fl in files[key]:
                        print(fl)
                        if fl.endswith(".LOG") or fl.endswith(".LOG1") or fl.endswith(".LOG2"):
                            logs.append(fl)
                        get_single_plugin(fl,logs,plu)
                        print ("[*] Parsing "+plu + " :" + fl)

    # parse single file with specific plugin
    if args.plugin and args.kuiper == False:
        file = args.file
        log = args.log
        get_single_plugin(file,log,args.plugin)

    if args.kuiper:
        file = args.file
        log = args.log
        logs =logs_folder(file)
        print_for_kuiper(file,logs,args.plugin)

if __name__ == "__main__":
    main(argv=sys.argv)
