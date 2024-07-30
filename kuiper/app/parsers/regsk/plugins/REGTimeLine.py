#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# yarp: yet another registry parser
# (c) Maxim Suhanov

# from yarp import *
from yarp import RegistryHelpers,Registry,RegistryCarve,RegistryFile,RegistryRecords,RegistryRecover
from yarp import __version__
import argparse
from collections import namedtuple
import os
import sys


gretl =[]
all_values =[]

def print_value(value,key):
	
	try:
		value_name = value.name()
		dict ={}
		dict['key_path'] = key.path()
		dict['type'] ='value'
		if value_name == '':
			dict['value_name'] = ''
		else:
			dict['value_name'] = value_name
		
		try:
			dict['value_type'] = value.type_str()
		except Exception as e:
			dict['value_type'] = ""

		dict['data_size'] = value.data_size()

		value_flags = value.flags_str()
		if value_flags is not None:
			dict['flags'] = value_flags
		try:
			dict['@timestamp'] = key.last_written_timestamp().isoformat()
		except (ValueError, OverflowError):
			dict['@timestamp'] ="1700-01-01T00:00:00"

		try:
			data = value.data()
		except UnicodeDecodeError:
			data = value.data_raw()
		
		if type(data) is bytes:
			dict['data'] = RegistryHelpers.HexDump(data)
			
		elif type(data) is list:
			dict['data'] = ','.join([str(d) for d in data])

		else:
			dict['data'] = data
		
		dict['data'] = str(dict['data'])
		if len(dict['data']) > 32700:
			dict['data'] = dict['data'][:32700] + "..truncated"


		dict['deleted'] ="false"
		gretl.append(dict)
	except :
		pass
	#return dict

def print_key(key):
	key_path = key.path()
	dict_v = {}
	dict_v['type'] = "key"
	if key_path == '':
		dict_v['key_path'] = 'Root'
		
	else:
		dict_v['key_path'] = key_path


	classname = key.classname()
	if classname is not None:
		dict_v['class_name'] = classname


	#dict_v['@timestamp'] = key.last_written_timestamp().isoformat()
	try:
		dict_v['@timestamp'] = key.last_written_timestamp().isoformat()
	except (ValueError, OverflowError):
		dict_v['@timestamp'] ="1700-01-01T00:00:00"

	dict_v['access_bits'] = key.access_bits()
	dict_v['deleted'] ="false"

	key_flags = key.flags_str()
	if key_flags is not None:
		dict_v['flags'] = key_flags


	security = key.security()
	if security is not None:
		security_descriptor = security.descriptor()
		try:
			owner_sid = RegistryHelpers.ParseSecurityDescriptorRelative(security_descriptor).owner_sid
		except Exception:
			owner_sid = 'invalid'

		dict_v['owner_sid'] = owner_sid


	
	# values = []
	for value in key.values():
		print_value(value,key)
	#dict_v['values']=values
	do_deleted =True
	if do_deleted:
		print_note = True
		try:
			for value in key.remnant_values():
				if print_note:
					print_note = False

				print_deleted_value(value,key)
		except (Registry.RegistryException, UnicodeDecodeError):
			pass
	gretl.append(dict_v)


def print_key_recursive(key):
	
	print_key(key)

	for subkey in key.subkeys():
		print_key_recursive(subkey)

def print_deleted_value(value,key=None):
	dict ={}
	if key != None :
		dict['key_path'] =key.path()
		try:
			dict['@timestamp'] = key.last_written_timestamp().isoformat()
		except (ValueError, OverflowError):
			dict['@timestamp'] ="1700-01-01T00:00:00"
	else:
		dict['key_path'] =""
		dict['@timestamp'] ="1700-01-01T00:00:00"

	
	
	
	
	value_name = value.name()
	if value_name == '':
		dict['value_name'] = 'not recovered name'
	else:
		dict['value_name'] = value_name

	#dict['value_type'] = value.type_str()
	try:
		dict['value_type'] = value.type_str()
	except Exception as e:
		dict['value_type'] = ""

	dict['data_size'] = value.data_size()
	dict['deleted'] ="true"
	dict['type'] = "value"

	

	value_flags = value.flags_str()
	if value_flags is not None:
		dict['flags'] = value_flags

	try:
		data = value.data()
	except Registry.RegistryException:
		data = None
	except UnicodeDecodeError:
		data = value.data_raw()

	
	if data is None:
		dict['data'] = 'Data not recovered'
	else:
		if type(data) is bytes:
			dict['data'] = RegistryHelpers.HexDump(data)

		elif type(data) is list:
			dict['data'] = ','.join([str(d) for d in data ])

		else:
			dict['data'] = data

		dict['data'] = str(dict['data'])
		if len(dict['data']) > 32700:
			dict['data'] = dict['data'][:32700] + "..truncated"


	gretl.append(dict)
	# return dict
	




def print_deleted_key(key):
	dict_v={}
	dict_v['type'] = "key"
	try:
		key_path = key.path()
	except Registry.RegistryException:
		key_path = None

	if key_path is None:
		# print('Unknown key path')
		dict_v['note_path'] = 'unkown key path'
		dict_v['key_path'] = key.path_partial()
		dict_v['key_name'] = key.name()

	else:
		if key_path == '':
			dict_v['key_path'] = 'Root'
			
		else:
			dict_v['key_path'] = key_path


	try:
		classname = key.classname()
	except (Registry.RegistryException, UnicodeDecodeError):
		classname = None

	if classname is not None:
		dict_v['class_name'] = classname
		

	try:
		dict_v['@timestamp'] = key.last_written_timestamp().isoformat()
	except (ValueError, OverflowError):
		dict_v['@timestamp'] ="1700-01-01T00:00:00"

	dict_v['access_bit'] =key.access_bits()


	key_flags = key.flags_str()
	if key_flags is not None:
		dict_v['flags'] =key_flags


	try:
		security = key.security()
	except Registry.RegistryException:
		security = None

	if security is not None:
		security_descriptor = security.descriptor()
		try:
			owner_sid = RegistryHelpers.ParseSecurityDescriptorRelative(security_descriptor).owner_sid
		except Exception:
			owner_sid = 'invalid'

		dict_v['owner_sid'] =owner_sid
	dict_v['deleted'] ="true"


	
	#values=[]
	#try:
	#	for value in key.values():
	#		values.append(print_deleted_value(value))
			
	#except (Registry.RegistryException, UnicodeDecodeError):
	#	pass

	#try:
	#	for value in key.remnant_values():
	#		values.append(print_deleted_value(value))
	#except (Registry.RegistryException, UnicodeDecodeError):
	#	pass

	#dict_v['values'] = values
	gretl.append(dict_v)

# Currently, we can use functions for deleted keys and values to print keys and values in a truncated hive.
print_truncated_value = print_deleted_value
print_truncated_key = print_deleted_key

def process_normal_hive(hive):
	

	print_key_recursive(hive.root_key())
	do_deleted =True
	if do_deleted:
	

		scanner = RegistryRecover.Scanner(hive)
		deleted_values = []

		for item in scanner.scan():
			if type(item) is Registry.RegistryKey:
				print_deleted_key(item)
			elif type(item) is Registry.RegistryValue:
				deleted_values.append(item)
		for value in deleted_values:
			print_deleted_value(value)

def process_truncated_hive(hive):
	

	all_values = []
	for item in hive.scan():
		if type(item) is Registry.RegistryValue:
			all_values.append(item)
		elif type(item) is Registry.RegistryKey:
			print_truncated_key(item)

	for value in all_values:
		print_truncated_value(value)
	do_deleted=True
	if do_deleted:
		scanner = RegistryRecover.Scanner(hive, False)
		deleted_values = []

		for item in scanner.scan():
			if type(item) is Registry.RegistryKey:
				print_deleted_key(item)
			elif type(item) is Registry.RegistryValue:
				deleted_values.append(item)

		for value in deleted_values:
			print_deleted_value(value)



class regtimeline():
	def __init__(self,prim_hive,log_files):
		self.prim_hive = prim_hive
		self.log_files = log_files
	def run(self):
		primary = open(self.prim_hive, 'rb')
		recovery= True
		logs = {'log': None, 'log1' : None, 'log2' : None}

		try:
			# load hive
			hive = Registry.RegistryHive(primary)
			truncated = False
		except (RegistryFile.NotSupportedException , RegistryFile.BaseBlockException):
			log = RegistryFile.NewLogFile(primary)
			primary = log.rebuild_primary_file_using_remnant_log_entries(True)
			truncated = True
		except Registry.RegistryException:
			truncated = True
		
		# load truncated primary hive
		if truncated:
			hive = Registry.RegistryHiveTruncated(primary)

		# recover the log hives
		if recovery and not truncated:
			
			for l in self.log_files.keys():
				if l.lower() in ['log' , 'log1' , 'log2'] and self.log_files[l] is not None:
					try:
						logs[l.lower()] = open(self.log_files[l], 'rb')
					except:
						pass

			try:
				recovery_result = hive.recover_auto(logs['log'], logs['log1'], logs['log2'])
				recovered = recovery_result.recovered
			except Registry.AutoRecoveryException:
				recovered = False

		try:
			if truncated:
				process_truncated_hive(hive)
			else:
				hive.walk_everywhere()
				process_normal_hive(hive)
		except (RegistryFile.CellOffsetException, RegistryFile.ReadException):
			pass
		
		hive = None
		primary.close()
		if recovery:
			for i in logs.keys():
				if logs[i] is not None:
					logs[i].close()
		
		return gretl
