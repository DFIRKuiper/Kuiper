from os import walk
import os

def get_files(path):
    dict ={}
    for folder in os.listdir(path):
        fl = os.path.join(path,folder)
        if os.path.isdir(fl):
            dir = fl
        files =[]
        for file in os.listdir(dir) :
            files.append(os.path.join(dir,file))
        dict[dir]= files
    return dict


def defind_files_logs(files,target):
    lst = []
    for values in files:
        logs={}
        hive_file = ''
        if target in values:
            for val in files[values]:
                if "LOG" in val:
                    logs['LOG']= val
                if "LOG1" in val:
                    logs['LOG1']= val
                if "LOG2" in val:
                    logs['LOG2']= val
                if "LOG2" and "LOG1" and "LOG" not in val:
                    hive_file = val
            lst.append({"hive":hive_file,"logs":logs})
        else:
            pass
    return lst

def defind_single_file_logs(file,logs):
    loggs={}
    for val in logs:
        if val.endswith('.LOG'):
            loggs['LOG']= val
        else:
            loggs['LOG']= None

        if  val.endswith('.LOG1'):
            loggs['LOG1']= val

        if  val.endswith('.LOG2'):
            loggs['LOG2']= val
        else:
            loggs['LOG2']= None
    return {"hive":file,"logs":loggs}
    #return lst

def logs_folder(file):
    files = []
    path= os.path.dirname(file)
    if os.path.isdir(path):
        for log in os.listdir(path) :
            if log.endswith(".LOG") or log.endswith(".LOG1") or log.endswith(".LOG2"):
                files.append(os.path.join(path,log))
    return files
