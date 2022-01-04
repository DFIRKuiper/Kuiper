
'''
The MIT License (MIT)

Copyright (c) 2015 Patrick Olsen


'''

import struct
import os
import json
import argparse
import sys 


def imain(file, parser):
	try:
		with open(file, "rb") as f:
			# Offset
			offset = 0x14
			# Go to beginning of file.
			f.seek(0)
			# Checking if signature is correct
			if (f.read(1) != b'\xfe'):
				raise Exception("Not RCF File")
			# Read forward 0x14 (20).
			f.seek(offset)
			res = []
			while (True):
				read = f.read(1)
				if not read:
					break
				# Reading 3 bytes
				f.read(3)
				rl = struct.unpack('>B', read)[0]
				fnlen = (rl + 1) * 2
				foundpath = f.read(fnlen).replace("\x00" , "")
				P =foundpath.split("\\")
				data = {
					'Folder': "\\".join(P[:-1]) + "\\",
					'Path':foundpath,
					'FileName': P[-1]
				}
				res.append(data)
			return res 

	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
		return (None , msg)


