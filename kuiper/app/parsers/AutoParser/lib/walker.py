#from os import walk
import os
import pathlib
from regipy.recovery import apply_transaction_logs


def Get_Files(path):
    dict ={}
    Hives = {}
    LOG1 = {}
    LOG2 = {}
    for path, currentDirectory, files in os.walk(path):
        for file in files:            
            if file.endswith('.LOG1'):
                LOG1[os.path.join(path,file).lower()] = os.path.join(path,file)
            if file.endswith('.LOG2'):
                LOG2[os.path.join(path,file).lower()] = os.path.join(path,file)
            elif file == "SECURITY" or file == "SYSTEM" or file == "SOFTWARE" or file == "NTUSER.DAT":
                Hives[os.path.join(path,file)] = os.path.join(path,file)
    return Hives, LOG1, LOG2

def Hives_Recovery(path, Tran = False):
    Hives, LOG1, LOG2 = Get_Files(path)
    NEW_Hives = {}
    if Tran:
        for file in Hives:
            try:
                restored_hive_path, count = apply_transaction_logs(file, LOG1[file.lower()+'.log1'], secondary_log_path=LOG2[file.lower()+'.log2'])
                NEW_Hives[restored_hive_path] = restored_hive_path
            except:
                NEW_Hives[file] = file
        
        return NEW_Hives
    else:
        return Hives

def Hives_Recovery_Kuiper(file, Tran=False):
    if Tran:
        try:
            restored_hive_path, count = apply_transaction_logs(file, file+'.LOG1', secondary_log_path=file+'.LOG2')
            return restored_hive_path
        except:
            return file
    else:
        return file
