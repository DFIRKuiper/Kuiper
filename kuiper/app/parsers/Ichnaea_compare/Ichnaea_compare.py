import os
import sys
import time
import difflib

#  _____     ____   __    __      __      _     ____      _____     ____    
# (_   _)   / ___) (  \  /  )    /  \    / )   (    )    / ___/    (    )   
#   | |    / /      \ (__) /    / /\ \  / /    / /\ \   ( (__      / /\ \   
#   | |   ( (        ) __ (     ) ) ) ) ) )   ( (__) )   ) __)    ( (__) )  
#   | |   ( (       ( (  ) )   ( ( ( ( ( (     )    (   ( (        )    (   
#  _| |__  \ \___    ) )( (    / /  \ \/ /    /  /\  \   \ \___   /  /\  \  
# /_____(   \____)  /_/  \_\  (_/    \__/    /__(  )__\   \____\ /__(  )__\ 
                                                                           
#[*] Version 1.0 
#[*] Compare IIS ApplicationHost files


class Ichnaea:
	def __init__(self, file_path, history_path):
		self.extenstion = "applicationHost.config"
		self.config_files = self.list_dir(file_path)
		self.history_files = self.list_dir(history_path) + self.config_files
		self.compareResult=[]
		rfile = range(len(self.history_files)-1)
		count = 0
		countnew = 1 
		for count in rfile:
			self.get_diff_files(self.history_files[count],self.history_files[countnew])
			count+=1
			countnew = count + 1

	# list csv file in a given path
	def list_dir(self, path):
		configFiles = []
		# with disable_file_system_redirection():
		for root, dirs, files in os.walk(path):
			configFiles += [os.path.join(root, f) for f in files if f.endswith(self.extenstion)]
		configFiles.sort()
		if not configFiles:
			print("No config files were found")
		return configFiles

	# compare file from list of files
	def get_diff_files(self , pre , new): 
		text1 = open(pre).readlines()
		text2 = open(new).readlines()
		for comp in difflib.unified_diff(text1, text2):
			if comp.startswith('++') or comp.startswith('---'):
				continue
			elif comp.startswith('-'):
				dic_data= {'History Filename' : new, 'Modification Time' :time.strftime( "%Y-%m-%d %H:%M:%S" ,time.gmtime(os.path.getmtime(new))), 'Removed Lines' : comp.strip().strip("- ")}
				dic_data['@timestamp'] = dic_data['Modification Time']
				self.compareResult.append(dic_data)
			elif comp.startswith('+'):
				dic_data= {'History Filename' : new, 'Modification Time' :time.strftime( "%Y-%m-%d %H:%M:%S" ,time.gmtime(os.path.getmtime(new))), 'Added Lines' : comp.strip().strip('+ 	')}
				dic_data['@timestamp'] = dic_data['Modification Time']
				self.compareResult.append(dic_data)