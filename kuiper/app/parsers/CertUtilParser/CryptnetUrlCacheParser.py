# This is a parser for the certutil cache files
#
# The following is the structure of the cache files:
# 12 bytes unknown
# 4 bytes (uint32) urlSize
# 8 bytes (uint64) FILETIME
# 76 bytes unkown
# 4 bytes (uint32) hashSize
# 8 bytes unkown
# 4 bytes (uint32) file size
# urlSize utf-16-le URL string
# hashSize utf-16-le MD5 hash string (Sometimes)
# =========================================
# For more details refere to my blog post : https://u0041.co/blog/post/3


import struct
import os
from datetime import datetime, timedelta
import hashlib


__author__ = "AbdulRhman Alfaifi"
__version__ = "1.1"
__maintainer__ = "AbdulRhman Alfaifi"
__license__ = "GPL"
__status__ = "Development"


class CertutilCacheParser:
    def __init__(self,filePath):
        self.filePath = filePath
        if not os.path.isfile(self.filePath):
            raise FileNotFoundError("The cache file '"+self.filePath+"' not found.")

    # Not used anymore. I was using this before I found hashSize and urlSize.
    def ReadUTF16String(self,file):
        string = b""
        while True:
            c = struct.unpack("s",file.read(1))[0]
            c2 = struct.unpack("s",file.read(1))[0]
            if c == b"\x00" and c2 == b"\x00":
                break
            string+=c
        return string.decode()

    # https://stackoverflow.com/questions/2150739/iso-time-iso-8601-in-python
    def FILETIMEToISO(self,ft):
        us = (ft - 116444736000000000) // 10
        dtObj = datetime(1970, 1, 1) + timedelta(microseconds = us)
        return dtObj.isoformat()

    def MD5(self,fname):
        try:
            hash_md5 = hashlib.md5()
            with open(fname, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return "00000000000000000000000000000000"


    def Parse(self,useContent=True):
        parsedData = {}
        cacheFile = open(self.filePath,"rb")
        header = struct.unpack("<12xIQ76xI8xI",cacheFile.read(116))
        urlSize = header[0]
        timestamp = self.FILETIMEToISO(header[1])
        hashSize = header[2]
        fileSize = header[3]
        # Read url string with the urlSize-1 (ignore null byte).
        try:
            url = b"".join(struct.unpack(str(urlSize)+"c",cacheFile.read(urlSize))).decode("utf-16-le")[0:-1]
        except:
            return None
        
        
        # Read hash string with the hashSize-1 (ignore null byte) and remove double quotation.
        try:
            hash = b"".join(struct.unpack(str(hashSize)+"c",cacheFile.read(hashSize))).decode("utf-16-le").replace('"','')[0:-1]
        except:
            hash = "Not Found"
        

        parsedData.update({
            "Timestamp": timestamp,
            "URL": url,
            "FileSize": fileSize,
            "MetadataHash": hash,
            "FullPath": cacheFile.name,
        })

        # Check if the file exsistes in the Content folder. If it does then calculate the file MD5 hash.
        if useContent:
            contentFilePath = os.path.dirname(cacheFile.name)+"/../Content/{os.path.basename(cacheFile.name)}"
            md5 = self.MD5(contentFilePath)
            parsedData.update({"MD5": md5}) 
        
        return parsedData


if __name__ == "__main__":
    import glob
    import argparse
    import sys
    import json
    import csv

    certutilCachePaths = [
        "C:\\Windows\\System32\\config\\systemprofile\\AppData\\LocalLow\\Microsoft\\CryptnetUrlCache\\Metadata",
        "C:\\Windows\\SysWOW64\\config\\systemprofile\\AppData\\LocalLow\\Microsoft\\CryptnetUrlCache\\Metadata"
    ] + glob.glob("C:\\Users\\*\\AppData\\LocalLow\\Microsoft\\CryptnetUrlCache\\MetaData")

    parser = argparse.ArgumentParser(description='CryptnetUrlCache Metadata Parser - Developded by AbdulRhman Alfaifi')
    parser.add_argument("-f","--files",nargs='+',help='A list of files that contain certutil cache files')
    parser.add_argument("-d","--dirs",nargs='+',help='A list of dirs that contain certutil cache files (default: all certutil cache paths)',default=certutilCachePaths)
    parser.add_argument("-o","--output",help='The file path to write the output to (default: stdout)',default=sys.stdout)
    parser.add_argument("--outputFormat",help='The output formate (default: csv)',default="csv", choices=["csv","json","jsonl"])
    parser.add_argument("--useContent",action='store_true',help='Try finding the cached file and calculate the MD5 hash for it',default=False)
    parser.add_argument("--noHeaders",action='store_true',help='Don\'t print headers when using CSV as the output format',default=False)
    
    args = parser.parse_args()

    if args.outputFormat == "csv":
        if isinstance(args.output,str):
            f = open(args.output,"w")
            results = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC,lineterminator="\n")
        else:
            results = csv.writer(args.output, quoting=csv.QUOTE_NONNUMERIC,lineterminator="\n")
        if args.useContent and not args.noHeaders:
            results.writerow(["Timestamp","URL","FileSize","MetadataHash","FullPath", "MD5"])
        elif not args.noHeaders:
            results.writerow(["Timestamp","URL","FileSize","MetadataHash","FullPath"])
    elif args.outputFormat == "json":
        results = []
    else:
        if isinstance(args.output,str):
            results = open(args.output,"w")
        else:
            results = args.output
    files = []
    if args.files:
        files = args.files
    else:
        for path in args.dirs:
            for root,dirs,all_files in os.walk(path):
                for file in all_files:
                    fullPath = os.path.join(root,file)
                    files.append(fullPath)
    
    for file in files:
        res = CertutilCacheParser(file).Parse(useContent=args.useContent)
        if res:
            if args.outputFormat == "csv":
                if args.useContent:
                    results.writerow([res.get("Timestamp"),res.get("URL"),res.get("FileSize"),res.get("MetadataHash"),res.get("FullPath"), res.get("MD5")])
                else:
                    results.writerow([res.get("Timestamp"),res.get("URL"),res.get("FileSize"),res.get("MetadataHash"),res.get("FullPath")])
            elif args.outputFormat == "json":
                results.append(res)
            else:
                results.write(json.dumps(res)+"\n")
    if args.outputFormat == "json":
        if isinstance(args.output,str):
            out = open(args.output,"w")
        else:
            out = args.output
        out.write(json.dumps(results))
                        