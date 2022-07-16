from WindowsPowerShell import *

def imain(file , parser):
	try:
		with Evtx(os.path.abspath(file)) as evtx: 
			script_data = Magic(evtx)
			return OutPut(script_data)

	except Exception:
		pass
