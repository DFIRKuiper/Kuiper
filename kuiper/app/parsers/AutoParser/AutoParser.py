import os,sys
from lib.walker import Hives_Recovery, Hives_Recovery_Kuiper
import argparse
from plugins import AppinitDLLs, BootExecute, Codecs, CompresseApp, Explorer, ImageHijacks,InternetExplorerAddons, KnownDLLs, Logon, LSAsecurityProviders, OfficeAddins, PrintMonitorDLLs, RDP, SMB, VSS, Winlogon, WinServices, Winsock
import glob
import csv
import json


def all_plugins():
    plugins = {
                'AppinitDLLs':{'function':AppinitDLLs.AppinitDLLs, 'Hives':['SOFTWARE', 'SYSTEM'], 'Discription':'Lists all DLLs that are arbitrary loaded into each user mode process on the system.'},
                'BootExecute':{'function':BootExecute.BootExecute, 'Hives':['SYSTEM'], 'Discription':'Lists Windows native-mode executables that are started by the Session Manager (Smss.exe) during system boot.'},
                'Codecs':{'function':Codecs.Codecs,'Hives':['SOFTWARE', 'NTUSER.DAT'], 'Discription':'Lists executable code that can be loaded by media playback applications.'},
                'CompresseApp':{'function':CompresseApp.CompresseApp,'Hives':['NTUSER.DAT'], 'Discription':'Lists the compressed and decompressed file history.'},
                'Explorer':{'function':Explorer.Explorer, 'Hives':['SOFTWARE', 'NTUSER.DAT'], 'Discription':'Lists common autostart entries that hook directly into Windows Explorer.'},
                'ImageHijacks':{'function':ImageHijacks.ImageHijacks,'Hives':['SOFTWARE', 'NTUSER.DAT'], 'Discription':'Image hijacks means running a different program from the one you specify and expect to be running.'},
                'InternetExplorerAddons':{'function':InternetExplorerAddons.InternetExplorerAddons,'Hives':['SOFTWARE', 'NTUSER.DAT'], 'Discription':'Lists all add-ins and extensions that load whenever an Internet Explorer is launched.'},
                'KnownDLLs':{'function':KnownDLLs.KnownDLLs,'Hives':['SYSTEM'], 'Discription':'Lists Known DLLs that loaded by Session Manager during startup.'},
                'Logon':{'function':Logon.Logon,'Hives':['SOFTWARE', 'SYSTEM', 'NTUSER.DAT'], 'Discription':'Lists all scripts and binary files that will be execute when Windows starts up and a user logs on.'},
                'LSAsecurityProviders':{'function':LSAsecurityProviders.LSAsecurityProviders,'Hives':['SYSTEM'], 'Discription':'Lists all DLLs that are loaded by Lsass.exe or Winlogon.exe and run as Local System.'},
                'OfficeAddins':{'function':OfficeAddins.OfficeAddins,'Hives':['SOFTWARE', 'NTUSER.DAT'], 'Discription':'Lists add-ins and plug-ins registered to hook into documented interfaces for Access, Excel, Outlook, PowerPoint, and Word.'},
                'PrintMonitorDLLs':{'function':PrintMonitorDLLs.PrintMonitorDLLs,'Hives':['SOFTWARE', 'SYSTEM'], 'Discription':'Lists all DLLs that are loaded into the Spooler service.'},
                'RDP':{'function':RDP.RDP,'Hives':['NTUSER.DAT'], 'Discription':'Lists outbound RDP connection.'},
                'SMB':{'function':SMB.SMB,'Hives':['NTUSER.DAT'], 'Discription':'Lists outbound SMB connection.'},
                'VSS':{'function':VSS.VSS,'Hives':['SYSTEM'], 'Discription':'Lists registry keys that indicate on creating volume shadow snapshot.'},
                'Winlogon':{'function':Winlogon.Winlogon,'Hives':['SOFTWARE', 'SYSTEM', 'NTUSER.DAT'], 'Discription':'Lists entries that hook into Winlogon.exe, which manages the Windows interactive-logon user interface.'},
                'WinServices':{'function':WinServices.WinServices,'Hives':['SYSTEM'], 'Discription':'Lists services and drivers that load at boot up a system.'},
                'Winsock':{'function':Winsock.Winsock,'Hives':['SYSTEM'], 'Discription':'Lists registered Winsock protocols and Winsock service providers.'},           
            }
    return plugins
#Parsing hive with a single plugin
def Parsing(file, plugin, output, csv_o, json_o):
    if file is not None:
        pl1 = plugins[plugin]['function'](file)
        lst_json, lst_csv, header = pl1.run()
        if lst_json:
            if json_o:
                result = open(output + plugin + '.log','a+')
                for d in lst_json:
                    result.write(d+'\n')
                result.close()
        if lst_csv:
            if csv_o:
                file_exists = os.path.isfile(output + plugin + '.csv')
                result = open(output + plugin + '.csv', 'a+', newline ='')
                dict_writer = csv.DictWriter(result, fieldnames=header)
                if not file_exists:
                    dict_writer.writeheader()
                dict_writer.writerows(lst_csv)
#Print output for kuiper
def Parsingkuiper(file,plugin):
    if file is not None:
        plugins = all_plugins()
        pl1 = plugins[plugin]['function'](file)
        lst_json, lst_csv, header = pl1.run()
        print(lst_json)

def main(argv=None):
    argv = sys.argv
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',  '--path', action='store',help='Path to all hives and trasaction logs')
    parser.add_argument('-f', '--file', action='store', help='Parse single hive')
    parser.add_argument('-o', '--output', action='store', help='Path to store output')
    parser.add_argument('-pl', '--plugin', action='store', help='Select single plugin')
    parser.add_argument('-a', '--all_plugins', action='store_true', help='Select all plugins')
    parser.add_argument('-t', '--apply_transaction_logs', action='store_true', help='Apply transaction logs to hives')
    parser.add_argument('-csv', '--csv', action='store_true', help='Export results as CSV file')
    parser.add_argument('-json', '--json', action='store_true', help='Export results as JSON file')
    parser.add_argument('-ls',  '--list', action='store_true', help='List all plugins')
    parser.add_argument('-v', '--verbose',  action='store_true', help='Enable verbose output')
    parser.add_argument('-k', '--kuiper',  action='store_true', help='Enable kuiper output')
    args = parser.parse_args(argv[1:])
    parser = argparse.ArgumentParser(description='Parse Registry hives')

    #List all plugin 
    if args.list:
        lst = []
        print ('List of avaiable plugins:\t')
        print ("{:<25} {:<10} ".format('Plugin', 'Discription'))
        for plg in plugins:
            print ("{:<25} {:<10} ".format(plg, plugins[plg]['Discription']))

    #Parsing with all plugins
    if args.all_plugins:
        path = args.path
        if path is not None:
            Hives = Hives_Recovery(path, args.apply_transaction_logs)
            for plu in plugins:
                for key in Hives:
                    for Hive in plugins[plu]['Hives']:
                        if Hive in Hives[key]:
                            print ('[*] Parsing '+plu + ' :' + Hive)
                            Parsing(Hives[key], plu, args.output, args.csv, args.json)

    #Parsing with specific plugin
    if args.plugin and args.kuiper == False:
        path = args.path
        if path is not None:
            Hives = Hives_Recovery(path, args.apply_transaction_logs)
            for key in Hives:
                for Hive in plugins[args.plugin]['Hives']:
                    if Hive in Hives[key]:
                        print ('[*] Parsing '+args.plugin + ' :' + Hive)
                        Parsing(Hives[key], args.plugin, args.output, args.csv, args.json)
    #Parsing with Kuiper Platform       
    if args.kuiper:
        file = args.file
        Parsingkuiper(Hives_Recovery_Kuiper(file, args.apply_transaction_logs),args.plugin)

        
if __name__ == '__main__':
    plugins = all_plugins()
    main(argv=sys.argv)
