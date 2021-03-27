import sys
import srum

def SRUM_interface(file, parser):
    try:
		srum_obj = srum.SRUM_Parser( file )
		return_data = []
		if srum_obj.ApplicationResourceUsage is not None:
			return_data += srum_obj.ApplicationResourceUsage
		if srum_obj.ApplicationResourceUsage is not None:
			return_data += srum_obj.NetworkDataUsageMonitor
		if srum_obj.ApplicationResourceUsage is not None:
			return_data += srum_obj.NetworkConnectivityUsageMonitor
		return return_data

    except Exception as e:
    	exc_type, exc_obj, exc_tb = sys.exc_info()
    	msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
    	return (None , msg)



print SRUM_interface("/home/kuiper/kuiper/files/sr2008015/sr2008015_V28-0046R3-BC01/2020-12-18T15:15:44-V28-0046R3-BC01.zip//PhysicalDrive0_1/srum/Windows/System32/sru/SRUDB.dat" , 'SRUM')