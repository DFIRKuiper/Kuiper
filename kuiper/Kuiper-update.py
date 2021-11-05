


import zipfile
import sys
import os
import yaml 
import urllib
import json
import subprocess
import time
from datetime import datetime 
import argparse
import signal

class Kuiper_Update:

    def __init__(self, args):
        self.args = args
        # =================== get configuration
        self.y                       = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )
        self.kuiper_update_log_file  = self.y['Logs']['log_folder'] + self.y['Logs']['update_log']
        self.release_url             = self.y['Git']['git_url_release']
        self.current_version         = self.y['Git']['k_version']
        self.kuiper_backup           = 'kuiper-backup.zip'
        self.kuiper_package          = "Kuiper-update.zip"

        if not os.path.exists(self.y['Logs']['log_folder']):
            os.makedirs(self.y['Logs']['log_folder'])
        
        self.kuiper_update_log       = open(self.kuiper_update_log_file , 'w')
        

        # exclude dirs: such as raw and files folders
        self.backup_dirs_exclude     = [
            os.path.join( self.y['Directories']['artifacts_upload'][0] ,self.y['Directories']['artifacts_upload'][1] ) , 
            os.path.join( self.y['Directories']['artifacts_upload_raw'][0] ,self.y['Directories']['artifacts_upload_raw'][1] ),
            self.y['Logs']['log_folder']
            ]

        # exclude files: such as the backup, package file, and update log file 
        self.backup_files_exclude    = [
            self.kuiper_backup,
            self.kuiper_package,
            self.kuiper_update_log_file
        ]



    # print the kuiper update logs
    def write_log(self, msg):
        msg = str(datetime.now()) + ": " + msg
        # be quiet and dont print the messages if -q enabled
        if not self.args.quiet:
            print msg
        self.kuiper_update_log.write( msg  + "\n")



    # print the download progress 
    def DownloadProgress(self, count, block_size, total_size):
        global start_time
        if count == 0:
            start_time = time.time()
            return
        duration = time.time() - start_time
        progress_size = int(count * block_size)
        speed = int(progress_size / (1024 * duration))
        percent = int((float(progress_size)  / total_size) * 100 )
        sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                        (percent, progress_size / (1024 * 1024), speed, duration))
        


    # backup current Kuiper files
    def backup_files(self):
        try:
            self.write_log( "Start backup for Kuiper")
            # backup the current Kuiper files before updating it
            backup = zipfile.ZipFile(self.kuiper_backup , 'w')
            
            backup_files = []
            for root, dirs, files in os.walk(self.y['Directories']['platform_folder']):
                
                for file in files: 
                    
                    # exclude files in backup_files_exclude
                    if file in self.backup_files_exclude:
                        continue

                    file_path = os.path.join(root.lstrip("."), file)
                    # if file in folders backup_dirs_exclude skip it
                    if not file_path.startswith(tuple(self.backup_dirs_exclude)):
                        self.write_log( "Backup file: " + file_path )
                        backup_files.append( file_path )
                        backup.write(os.path.join(root, file))
            
            backup.close()
            self.write_log("Current Kuiper backup done")
            return [True, "Current Kuiper backup done"]

        except Exception as e:
            self.write_log("Failed to backup current Kuiper: " + str(e))
            return [False, "Failed to backup Kuiper"]


    # ============================ Remove old files
    # remove all files from the current Kuiper version

    def Remove_Old_Files(self):
        count = 0
        all_files = []
        for root, dirs, files in os.walk('./'):
            # if the directory is in the excluded list then skip it 
            if root in self.backup_dirs_exclude:
                continue
            
            for name in files:
                all_files.append( os.path.join(root, name) )

        for f in all_files:
            # if the file in the excluded list then skip it
            if f in self.backup_files_exclude:
                continue
                
            try:
                # delete the old file
                self.write_log("Delete file: " + f)
                count += 1 
            except Exception as e:
                self.write_log("Failed to delete file: " + f )
                self.write_log("Error: " + str(e) )    
                return False

        self.write_log("Successfuly removed all old files: " + str(count) + " files")
        return True

    # ============================ Update kuiper files
    def Decompress_Files(self):

        # ============== Update Kuiper 
        zip_update = zipfile.ZipFile(self.kuiper_package) 
        
        bUpdateSuccess = [True , "done"]
        for file in zip_update.namelist():
            # skip folders
            if file.endswith("/"):
                continue
            
            # read the file
            fileobj = zip_update.open(file)
            
            dst_path = "/".join(file.split("/")[1:])
            self.write_log("update file: " + dst_path)

            try:
                # if the folder not exists, then create folder
                if os.path.dirname(dst_path) != "" and os.path.exists(os.path.dirname(dst_path)) == False:
                    os.makedirs(os.path.dirname(dst_path))
            except Exception as e:
                self.write_log( "Failed to create folder ["+dst_path+"]" )
                bUpdateSuccess = [False , "Failed to create folder ["+dst_path+"] - " + str(e)]
                break


            try:
                # read and write the new files
                with open(dst_path , 'wb') as df:
                    df.write(fileobj.read())
                    df.close()
            except Exception as e:
                self.write_log( "Couldn't update file ["+dst_path+"]")
                bUpdateSuccess = [False , "[-] Couldn't update file ["+dst_path+"]" + str(e)]
                break

        return bUpdateSuccess



    # ========================== check update
    # check if update avaliable
    def check_update(self):
        self.write_log("Check latest update version")
        link = self.release_url
        current_version = self.current_version
        try:
            request     = urllib.urlopen(link)
            response    = request.read()
            data        = json.loads(response)
        
            self.write_log("Kuiper current version \t["+str(current_version)+"]")
            if current_version < data['tag_name']:
                self.write_log("Kuiper new release version \t["+str(data['tag_name'])+"]")
                
                new_release_link = data['zipball_url'] # get the link to download the package
                self.write_log("Kuiper New release link \t["+new_release_link+"]")

                return {
                    'status'    : True,
                    "up-to-date": False,
                    "link"      : new_release_link , 
                    "version"   : data['tag_name'] 
                }
            else:
                self.write_log("Kuiper is up-to-date")
                return {
                    'status'    : True,
                    "up-to-date": True
                }

        except Exception as e:
            self.write_log("Failed to check latest update: " + str(e))
            return {
                'status': False,
                'error' : "Failed to check latest update: " + str(e)
            }






    # ========================== update function
    def update(self):

        kuiper_package = self.kuiper_package if self.args.package is None else self.args.package
        use_package = False if self.args.package is None else True



        self.write_log("Start updating Kuiper")  
        # =========================== if package provided
        # if package provided check the version from the package
        if use_package:
            try:
                zip_package     = zipfile.ZipFile(kuiper_package) 
                zip_config      = zip_package.read('configuration.yaml')
                zip_config_yaml = yaml.safe_load(zip_config)
                
                zip_package.close()

                package_version = zip_config_yaml['Git']['k_version']
                self.write_log("Package verson: " + zip_config_yaml['Git']['k_version'] )


                # check if the current version newer than the provided package
                if self.current_version >= package_version:
                    self.write_log("The installed version is newer than the provided package version")
                    self.write_log("current version: " + str(self.current_version ) + " , package version: " + package_version)
                    return False

            except Exception as e:
                self.write_log("Failed opening the package file: " + str(e))
                return False

        # =========================== download package if not provided 
        # if there is not package provided check from github 
        else:
            update_version = self.check_update()
            if update_version['status'] and not update_version['up-to-date']:
                
                self.write_log( "Start Downloading Kuiper " + update_version['version'] )
                self.write_log( "GitHub URL zip file: " + update_version['link'] )

                # downloaded zip file from github (link, target, print_download_progress)
                download_success = True # 
                try:
                    urllib.urlretrieve(update_version['link'], kuiper_package , self.DownloadProgress )
                    print "done"
                    self.write_log("Download success: " +update_version['link'] + " >>> " + kuiper_package)

                except Exception as e:
                    self.write_log("Failed to download the Kuiper package from Github: " + update_version['link'] )
                    self.write_log("Error message: " + str(e))
                    return False

            else:
                return False 
        
        # ====================== backup
        # if package is exists/downloaded, then start backup the old files
        backup = self.backup_files()

        # if failed to backup
        if not backup[0]:
            return False

        # ====================== Remove files
        # if failed to remove old files
        bRemoveOldFiles = self.Remove_Old_Files()
        if not bRemoveOldFiles:
            return False 

        # ====================== Decompress the package
        bDecompressFiles = self.Decompress_Files()
        if not bDecompressFiles[0]:
            return False
        
        # ====================== Install new dependencies
        # install new dependinces

        
        # the user wasn't authenticated as a sudoer, exit?
        self.write_log("Start install dependencies")
        proc_install_dep = subprocess.call(['sudo','./kuiper_install.sh' , '-install'])
        
        
        # ====================== Remove 
        # remove backup and new update release
        self.write_log("Remove file: " + self.kuiper_backup)
        os.remove(self.kuiper_backup)

        # if the package is not provided by client (means it has been downloaded) then remove the downloaded package file
        if self.args.package is None:
            self.write_log("Remove file: " + kuiper_package)
            os.remove(kuiper_package)


        # ====================== Close logging file
        self.write_log("Update successfuly done")


        # close the logging 
        self.kuiper_update_log.close()
    



def main():

    # ================== arguments
    a_parser = argparse.ArgumentParser('Python script tool to update Kuiper')

    requiredargs = a_parser.add_argument_group('Required [choose one]')
    requiredargs.add_argument('-c', dest='check_update', help='Check if update avaliable from Github', action="store_true")
    requiredargs.add_argument('-u' , dest='update' , help='Update Kuiper', action="store_true")

    a_parser.add_argument('-p' , dest='package' , help='The path of update package, if not specified it will download it from Github')
    a_parser.add_argument('-q' , dest='quiet', action="store_true" , help="Don't print the update log messages")

    args = a_parser.parse_args()



    # if command check_update nor update has been provided 
    if args.check_update==False and args.update==False:
        print "Specifiy the options -c (check_update) or -u (update)"
        a_parser.print_help()


    # if check update used
    elif args.check_update:
        obj_checkupdate = Kuiper_Update(args)
        obj_checkupdate.check_update()

    # if update request
    elif args.update:
        obj_checkupdate = Kuiper_Update(args)
        obj_checkupdate.update()


    # if nothing requested
    else:
        a_parser.print_help()
    


main()
