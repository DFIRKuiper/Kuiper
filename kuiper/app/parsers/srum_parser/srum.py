
import pyesedb
import binascii
import json
import struct
import datetime
import codecs
import argparse
import os

# resources: 
# https://programtalk.com/vs2/?source=python/3146/SrumMonkey/SrumMonkey.py
# https://github.com/libyal/esedb-kb/blob/master/documentation/System%20Resource%20Usage%20Monitor%20(SRUM).asciidoc
# https://github.com/MarkBaggett/srum-dump/


class SRUM_Parser():

	known_SID = [
			{'SID': 'S-1-0', 			'Name': 'Null Authority'},
			{'SID': 'S-1-0-0', 			'Name': 'Nobody'},
			{'SID': 'S-1-1',			'Name': 'World Authority'},
			{'SID': 'S-1-1-0', 			'Name': 'Everyone'},
			{'SID': 'S-1-2', 			'Name': 'Local Authority'},
			{'SID': 'S-1-2-0', 			'Name': 'Local'},
			{'SID': 'S-1-2-1', 			'Name': 'Console Logon'},
			{'SID': 'S-1-3', 			'Name': 'Creator Authority'},
			{'SID': 'S-1-3-0', 			'Name': 'Creator Owner'},
			{'SID': 'S-1-3-1', 			'Name': 'Creator Group'},
			{'SID': 'S-1-3-2', 			'Name': 'Creator Owner Server'},
			{'SID': 'S-1-3-3', 			'Name': 'Creator Group Server'},
			{'SID': 'S-1-3-4', 			'Name': 'Owner Rights'},
			{'SID': 'S-1-4', 			'Name': 'Non-unique Authority'},
			{'SID': 'S-1-5', 			'Name': 'NT Authority'},
			{'SID': 'S-1-5-1', 			'Name': 'Dialup'},
			{'SID': 'S-1-5-2', 			'Name': 'Network'},
			{'SID': 'S-1-5-3', 			'Name': 'Batch'},
			{'SID': 'S-1-5-4', 			'Name': 'Interactive'},
			{'SID': 'S-1-5-5-*', 		'Name': 'Logon Session'},
			{'SID': 'S-1-5-6', 			'Name': 'Service'},
			{'SID': 'S-1-5-7', 			'Name': 'Anonymous'},
			{'SID': 'S-1-5-8', 			'Name': 'Proxy'},
			{'SID': 'S-1-5-9', 			'Name': 'Enterprise Domain Controllers'},
			{'SID': 'S-1-5-10', 		'Name': 'Principal Self'},
			{'SID': 'S-1-5-11', 		'Name': 'Authenticated Users'},
			{'SID': 'S-1-5-12', 		'Name': 'Restricted Code'},
			{'SID': 'S-1-5-13', 		'Name': 'Terminal Server Users'},
			{'SID': 'S-1-5-14', 		'Name': 'Remote Interactive Logon'},
			{'SID': 'S-1-5-15', 		'Name': 'This Organization'},
			{'SID': 'S-1-5-17', 		'Name': 'This Organization'},
			{'SID': 'S-1-5-18', 		'Name': 'Local System'},
			{'SID': 'S-1-5-19', 		'Name': 'NT Authority'},
			{'SID': 'S-1-5-20', 		'Name': 'NT Authority'},

			{'SID': 'S-1-5-21-*-498', 'Name': 'Enterprise Read-only Domain Controllers'},
			{'SID': 'S-1-5-21-*-500', 'Name': 'Administrator'},
			{'SID': 'S-1-5-21-*-501', 'Name': 'Guest'},
			{'SID': 'S-1-5-21-*-502', 'Name': 'KRBTGT'},
			{'SID': 'S-1-5-21-*-512', 'Name': 'Domain Admins'},
			{'SID': 'S-1-5-21-*-513', 'Name': 'Domain Users'},
			{'SID': 'S-1-5-21-*-514', 'Name': 'Domain Guests'},
			{'SID': 'S-1-5-21-*-515', 'Name': 'Domain Computers'},
			{'SID': 'S-1-5-21-*-516', 'Name': 'Domain Controllers'},
			{'SID': 'S-1-5-21-*-517', 'Name': 'Cert Publishers'},
			{'SID': 'S-1-5-21-*-518', 'Name': 'Schema Admins'},
			{'SID': 'S-1-5-21-*-519', 'Name': 'Enterprise Admins'},
			{'SID': 'S-1-5-21-*-520', 'Name': 'Group Policy Creator Owners'},
			{'SID': 'S-1-5-21-*-521', 'Name': 'Read-only Domain Controllers'},
			{'SID': 'S-1-5-21-*-522', 'Name': 'Cloneable Domain Controllers'},
			{'SID': 'S-1-5-21-*-526', 'Name': 'Key Admins'},
			{'SID': 'S-1-5-21-*-527', 'Name': 'Enterprise Key Admins'},
			{'SID': 'S-1-5-21-*-553', 'Name': 'RAS and IAS Servers'},
			{'SID': 'S-1-5-21-*-571', 'Name': 'Allowed RODC Password Replication Group'},
			{'SID': 'S-1-5-21-*-572', 'Name': 'Denied RODC Password Replication Group'},
			{'SID': 'S-1-5-21-*', 	  'Name': 'User Account'},

			{'SID': 'S-1-5-32-544', 'Name': 'Administrators'},
			{'SID': 'S-1-5-32-545', 'Name': 'Users'},
			{'SID': 'S-1-5-32-546', 'Name': 'Guests'},
			{'SID': 'S-1-5-32-547', 'Name': 'Power Users'},
			{'SID': 'S-1-5-32-548', 'Name': 'Account Operators'},
			{'SID': 'S-1-5-32-549', 'Name': 'Server Operators'},
			{'SID': 'S-1-5-32-550', 'Name': 'Print Operators'},
			{'SID': 'S-1-5-32-551', 'Name': 'Backup Operators'},
			{'SID': 'S-1-5-32-552', 'Name': 'Replicators'},
			{'SID': 'S-1-5-32-554', 'Name': 'BUILTIN\\Pre-Windows 2000 Compatible Access'},
			{'SID': 'S-1-5-32-555', 'Name': 'BUILTIN\\Remote Desktop Users'},
			{'SID': 'S-1-5-32-556', 'Name': 'BUILTIN\\Network Configuration Operators'},
			{'SID': 'S-1-5-32-557', 'Name': 'BUILTIN\\Incoming Forest Trust Builders'},
			{'SID': 'S-1-5-32-558', 'Name': 'BUILTIN\\Performance Monitor Users'},
			{'SID': 'S-1-5-32-559', 'Name': 'BUILTIN\\Performance Log Users'},
			{'SID': 'S-1-5-32-560', 'Name': 'BUILTIN\\Windows Authorization Access Group'},
			{'SID': 'S-1-5-32-561', 'Name': 'BUILTIN\\Terminal Server License Servers'},
			{'SID': 'S-1-5-32-562', 'Name': 'BUILTIN\\Distributed COM Users'},
			{'SID': 'S-1-5-32-569', 'Name': 'BUILTIN\\Cryptographic Operators'},
			{'SID': 'S-1-5-32-573', 'Name': 'BUILTIN\\Event Log Readers'},
			{'SID': 'S-1-5-32-574', 'Name': 'BUILTIN\\Certificate Service DCOM Access'},
			{'SID': 'S-1-5-32-575', 'Name': 'BUILTIN\\RDS Remote Access Servers'},
			{'SID': 'S-1-5-32-576', 'Name': 'BUILTIN\\RDS Endpoint Servers'},
			{'SID': 'S-1-5-32-577', 'Name': 'BUILTIN\\RDS Management Servers'},
			{'SID': 'S-1-5-32-578', 'Name': 'BUILTIN\\Hyper-V Administrators'},
			{'SID': 'S-1-5-32-579', 'Name': 'BUILTIN\\Access Control Assistance Operators'},
			{'SID': 'S-1-5-32-580', 'Name': 'BUILTIN\\Remote Management Users'},

			{'SID': 'S-1-5-64-10', 	'Name': 'NTLM Authentication'},
			{'SID': 'S-1-5-64-14', 	'Name': 'SChannel Authentication'},
			{'SID': 'S-1-5-64-21', 	'Name': 'Digest Authentication'},

			{'SID': 'S-1-5-80', 	'Name': 'NT Service'},
			{'SID': 'S-1-5-80-0', 	'Name': 'All Services'},
			{'SID': 'S-1-5-83-0', 	'Name': 'NT VIRTUAL MACHINE\\Virtual Machines'},

			{'SID': 'S-1-16-0', 	'Name': 'Untrusted Mandatory Level'},
			{'SID': 'S-1-16-4096', 	'Name': 'Low Mandatory Level'},
			{'SID': 'S-1-16-8192', 	'Name': 'Medium Mandatory Level'},
			{'SID': 'S-1-16-8448', 	'Name': 'Medium Plus Mandatory Level'},
			{'SID': 'S-1-16-12288', 'Name': 'High Mandatory Level'},
			{'SID': 'S-1-16-16384', 'Name': 'System Mandatory Level'},
			{'SID': 'S-1-16-20480', 'Name': 'Protected Process Mandatory Level'},
			{'SID': 'S-1-16-28672', 'Name': 'Secure Process Mandatory Level'}
		]

	known_interface_Luid = {
		'0':'Unknown Interface',
		'1':'IF_TYPE_OTHER',
		'2':'IF_TYPE_REGULAR_1822',
		'3':'IF_TYPE_HDH_1822',
		'4':'IF_TYPE_DDN_X25',
		'5':'IF_TYPE_RFC877_X25',
		'6':'IF_TYPE_ETHERNET_CSMACD',
		'7':'IF_TYPE_IS088023_CSMACD',
		'8':'IF_TYPE_ISO88024_TOKENBUS',
		'9':'IF_TYPE_ISO88025_TOKENRING',
		'10':'IF_TYPE_ISO88026_MAN',
		'11':'IF_TYPE_STARLAN',
		'12':'IF_TYPE_PROTEON_10MBIT',
		'13':'IF_TYPE_PROTEON_80MBIT',
		'14':'IF_TYPE_HYPERCHANNEL',
		'15':'IF_TYPE_FDDI',
		'16':'IF_TYPE_LAP_B',
		'17':'IF_TYPE_SDLC',
		'18':'IF_TYPE_DS1',
		'19':'IF_TYPE_E1',
		'20':'IF_TYPE_BASIC_ISDN',
		'21':'IF_TYPE_PRIMARY_ISDN',
		'22':'IF_TYPE_PROP_POINT2POINT_SERIAL',
		'23':'IF_TYPE_PPP',
		'24':'IF_TYPE_SOFTWARE_LOOPBACK',
		'25':'IF_TYPE_EON',
		'26':'IF_TYPE_ETHERNET_3MBIT',
		'27':'IF_TYPE_NSIP',
		'28':'IF_TYPE_SLIP',
		'29':'IF_TYPE_ULTRA',
		'30':'IF_TYPE_DS3',
		'31':'IF_TYPE_SIP',
		'32':'IF_TYPE_FRAMERELAY',
		'33':'IF_TYPE_RS232',
		'34':'IF_TYPE_PARA',
		'35':'IF_TYPE_ARCNET',
		'36':'IF_TYPE_ARCNET_PLUS',
		'37':'IF_TYPE_ATM',
		'38':'IF_TYPE_MIO_X25',
		'39':'IF_TYPE_SONET',
		'40':'IF_TYPE_X25_PLE',
		'41':'IF_TYPE_ISO88022_LLC',
		'42':'IF_TYPE_LOCALTALK',
		'43':'IF_TYPE_SMDS_DXI',
		'44':'IF_TYPE_FRAMERELAY_SERVICE',
		'45':'IF_TYPE_V35',
		'46':'IF_TYPE_HSSI',
		'47':'IF_TYPE_HIPPI',
		'48':'IF_TYPE_MODEM',
		'49':'IF_TYPE_AAL5',
		'50':'IF_TYPE_SONET_PATH',
		'51':'IF_TYPE_SONET_VT',
		'52':'IF_TYPE_SMDS_ICIP',
		'53':'IF_TYPE_PROP_VIRTUAL',
		'54':'IF_TYPE_PROP_MULTIPLEXOR',
		'55':'IF_TYPE_IEEE80212',
		'56':'IF_TYPE_FIBRECHANNEL',
		'57':'IF_TYPE_HIPPIINTERFACE',
		'58':'IF_TYPE_FRAMERELAY_INTERCONNECT',
		'59':'IF_TYPE_AFLANE_8023',
		'60':'IF_TYPE_AFLANE_8025',
		'61':'IF_TYPE_CCTEMUL',
		'62':'IF_TYPE_FASTETHER',
		'63':'IF_TYPE_ISDN',
		'64':'IF_TYPE_V11',
		'65':'IF_TYPE_V36',
		'66':'IF_TYPE_G703_64K',
		'67':'IF_TYPE_G703_2MB',
		'68':'IF_TYPE_QLLC',
		'69':'IF_TYPE_FASTETHER_FX',
		'70':'IF_TYPE_CHANNEL',
		'71':'IF_TYPE_IEEE80211',
		'72':'IF_TYPE_IBM370PARCHAN',
		'73':'IF_TYPE_ESCON',
		'74':'IF_TYPE_DLSW',
		'75':'IF_TYPE_ISDN_S',
		'76':'IF_TYPE_ISDN_U',
		'77':'IF_TYPE_LAP_D',
		'78':'IF_TYPE_IPSWITCH',
		'79':'IF_TYPE_RSRB',
		'80':'IF_TYPE_ATM_LOGICAL',
		'81':'IF_TYPE_DS0',
		'82':'IF_TYPE_DS0_BUNDLE',
		'83':'IF_TYPE_BSC',
		'84':'IF_TYPE_ASYNC',
		'85':'IF_TYPE_CNR',
		'86':'IF_TYPE_ISO88025R_DTR',
		'87':'IF_TYPE_EPLRS',
		'88':'IF_TYPE_ARAP',
		'89':'IF_TYPE_PROP_CNLS',
		'90':'IF_TYPE_HOSTPAD',
		'91':'IF_TYPE_TERMPAD',
		'92':'IF_TYPE_FRAMERELAY_MPI',
		'93':'IF_TYPE_X213',
		'94':'IF_TYPE_ADSL',
		'95':'IF_TYPE_RADSL',
		'96':'IF_TYPE_SDSL',
		'97':'IF_TYPE_VDSL',
		'98':'IF_TYPE_ISO88025_CRFPRINT',
		'99':'IF_TYPE_MYRINET',
		'100':'IF_TYPE_VOICE_EM',
		'101':'IF_TYPE_VOICE_FXO',
		'102':'IF_TYPE_VOICE_FXS',
		'103':'IF_TYPE_VOICE_ENCAP',
		'104':'IF_TYPE_VOICE_OVERIP',
		'105':'IF_TYPE_ATM_DXI',
		'106':'IF_TYPE_ATM_FUNI',
		'107':'IF_TYPE_ATM_IMA',
		'108':'IF_TYPE_PPPMULTILINKBUNDLE',
		'109':'IF_TYPE_IPOVER_CDLC',
		'110':'IF_TYPE_IPOVER_CLAW',
		'111':'IF_TYPE_STACKTOSTACK',
		'112':'IF_TYPE_VIRTUALIPADDRESS',
		'113':'IF_TYPE_MPC',
		'114':'IF_TYPE_IPOVER_ATM',
		'115':'IF_TYPE_ISO88025_FIBER',
		'116':'IF_TYPE_TDLC',
		'117':'IF_TYPE_GIGABITETHERNET',
		'118':'IF_TYPE_HDLC',
		'119':'IF_TYPE_LAP_F',
		'120':'IF_TYPE_V37',
		'121':'IF_TYPE_X25_MLP',
		'122':'IF_TYPE_X25_HUNTGROUP',
		'123':'IF_TYPE_TRANSPHDLC',
		'124':'IF_TYPE_INTERLEAVE',
		'125':'IF_TYPE_FAST',
		'126':'IF_TYPE_IP',
		'127':'IF_TYPE_DOCSCABLE_MACLAYER',
		'128':'IF_TYPE_DOCSCABLE_DOWNSTREAM',
		'129':'IF_TYPE_DOCSCABLE_UPSTREAM',
		'130':'IF_TYPE_A12MPPSWITCH',
		'131':'IF_TYPE_TUNNEL',
		'132':'IF_TYPE_COFFEE',
		'133':'IF_TYPE_CES',
		'134':'IF_TYPE_ATM_SUBINTERFACE',
		'135':'IF_TYPE_L2_VLAN',
		'136':'IF_TYPE_L3_IPVLAN',
		'137':'IF_TYPE_L3_IPXVLAN',
		'138':'IF_TYPE_DIGITALPOWERLINE',
		'139':'IF_TYPE_MEDIAMAILOVERIP',
		'140':'IF_TYPE_DTM',
		'141':'IF_TYPE_DCN',
		'142':'IF_TYPE_IPFORWARD',
		'143':'IF_TYPE_MSDSL',
		'144':'IF_TYPE_IEEE1394',
		'145':'IF_TYPE_IF_GSN',
		'146':'IF_TYPE_DVBRCC_MACLAYER',
		'147':'IF_TYPE_DVBRCC_DOWNSTREAM',
		'148':'IF_TYPE_DVBRCC_UPSTREAM',
		'149':'IF_TYPE_ATM_VIRTUAL',
		'150':'IF_TYPE_MPLS_TUNNEL',
		'151':'IF_TYPE_SRP',
		'152':'IF_TYPE_VOICEOVERATM',
		'153':'IF_TYPE_VOICEOVERFRAMERELAY',
		'154':'IF_TYPE_IDSL',
		'155':'IF_TYPE_COMPOSITELINK',
		'156':'IF_TYPE_SS7_SIGLINK',
		'157':'IF_TYPE_PROP_WIRELESS_P2P',
		'158':'IF_TYPE_FR_FORWARD',
		'159':'IF_TYPE_RFC1483',
		'160':'IF_TYPE_USB',
		'161':'IF_TYPE_IEEE8023AD_LAG',
		'162':'IF_TYPE_BGP_POLICY_ACCOUNTING',
		'163':'IF_TYPE_FRF16_MFR_BUNDLE',
		'164':'IF_TYPE_H323_GATEKEEPER',
		'165':'IF_TYPE_H323_PROXY',
		'166':'IF_TYPE_MPLS',
		'167':'IF_TYPE_MF_SIGLINK',
		'168':'IF_TYPE_HDSL2',
		'169':'IF_TYPE_SHDSL',
		'170':'IF_TYPE_DS1_FDL',
		'171':'IF_TYPE_POS',
		'172':'IF_TYPE_DVB_ASI_IN',
		'173':'IF_TYPE_DVB_ASI_OUT',
		'174':'IF_TYPE_PLC',
		'175':'IF_TYPE_NFAS',
		'176':'IF_TYPE_TR008',
		'177':'IF_TYPE_GR303_RDT',
		'178':'IF_TYPE_GR303_IDT',
		'179':'IF_TYPE_ISUP',
		'180':'IF_TYPE_PROP_DOCS_WIRELESS_MACLAYER',
		'181':'IF_TYPE_PROP_DOCS_WIRELESS_DOWNSTREAM',
		'182':'IF_TYPE_PROP_DOCS_WIRELESS_UPSTREAM',
		'183':'IF_TYPE_HIPERLAN2',
		'184':'IF_TYPE_PROP_BWA_P2MP',
		'185':'IF_TYPE_SONET_OVERHEAD_CHANNEL',
		'186':'IF_TYPE_DIGITAL_WRAPPER_OVERHEAD_CHANNEL',
		'187':'IF_TYPE_AAL2',
		'188':'IF_TYPE_RADIO_MAC',
		'189':'IF_TYPE_ATM_RADIO',
		'190':'IF_TYPE_IMT',
		'191':'IF_TYPE_MVL',
		'192':'IF_TYPE_REACH_DSL',
		'193':'IF_TYPE_FR_DLCI_ENDPT',
		'194':'IF_TYPE_ATM_VCI_ENDPT',
		'195':'IF_TYPE_OPTICAL_CHANNEL',
		'196':'IF_TYPE_OPTICAL_TRANSPORT',
		'243':'IF_TYPE_WWANPP',
		'244':'IF_TYPE_WWANPP2'
	}

	def __init__(self , ese_file):
		self.ese_db = pyesedb.open(ese_file)
		print "here"
		self.GUID_tables = {
			'SruDbIdMapTable' 					: 'SruDbIdMapTable',
			'NetworkDataUsageMonitor' 			: '{973F5D5C-1D90-4944-BE8E-24B94231A174}',
			'ApplicationResourceUsage' 			: '{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}',
			'EnergyEstimator' 					: '{DA73FB89-2BEA-4DDC-86B8-6E048C6DA477}',
			'NetworkConnectivityUsageMonitor' 	: '{DD6636C4-8929-4683-974E-22C046A43763}',
			'EnergyUsage' 						: '{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}',
			'LongTermEnergyUsage' 				: '{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}LT'
		}

		# list all types used in ese DBs 
		"""
		self.ese_db_columns_types = {
			'BINARY_DATA' 				: pyesedb.column_types.BINARY_DATA,
			'BOOLEAN' 					: pyesedb.column_types.BOOLEAN,
			'CURRENCY' 					: pyesedb.column_types.CURRENCY,
			'DATE_TIME' 				: pyesedb.column_types.DATE_TIME,
			'DOUBLE_64BIT' 				: pyesedb.column_types.DOUBLE_64BIT,
			'FLOAT_32BIT' 				: pyesedb.column_types.FLOAT_32BIT,
			'GUID' 						: pyesedb.column_types.GUID,
			'INTEGER_16BIT_SIGNED' 		: pyesedb.column_types.INTEGER_16BIT_SIGNED,
			'INTEGER_16BIT_UNSIGNED' 	: pyesedb.column_types.INTEGER_16BIT_UNSIGNED,
			'INTEGER_32BIT_SIGNED' 		: pyesedb.column_types.INTEGER_32BIT_SIGNED,
			'INTEGER_32BIT_UNSIGNED' 	: pyesedb.column_types.INTEGER_32BIT_UNSIGNED,
			'INTEGER_64BIT_SIGNED' 		: pyesedb.column_types.INTEGER_64BIT_SIGNED,
			'INTEGER_8BIT_UNSIGNED' 	: pyesedb.column_types.INTEGER_8BIT_UNSIGNED,
			'LARGE_BINARY_DATA' 		: pyesedb.column_types.LARGE_BINARY_DATA,
			'LARGE_TEXT' 				: pyesedb.column_types.LARGE_TEXT,
			'NULL' 						: pyesedb.column_types.NULL,
			'SUPER_LARGE_VALUE' 		: pyesedb.column_types.SUPER_LARGE_VALUE,
			'TEXT' 						: pyesedb.column_types.TEXT
		}
		"""

		# get all indices from the table
		self.SruDbIdMapTable = self.get_SruDbIdMapTable_details()

		# get all application usage from table
		self.ApplicationResourceUsage = self.get_ApplicationResourceUsage_details()
		
		# get all network data usage from the table
		self.NetworkDataUsageMonitor = self.get_NetworkDataUsageMonitor_details()

		# get all network connectivity usage from the table
		self.NetworkConnectivityUsageMonitor = self.get_NetworkConnectivityUsageMonitor_details()



	# ================================= get known SID name if exists
	def get_SID_name(self, sid):
		res_account = None
		for k_sid in self.known_SID:
			
			if sid == k_sid['SID']:
				res_account = k_sid['Name']

			# if ends with *
			elif k_sid['SID'].endswith('*'):
				if sid.startswith( str(k_sid['SID'][0:-1]) ):
					res_account = k_sid['Name']

			# if domain name it will contain * in middle
			elif '*' in k_sid['SID']:
				k_sid_domain = k_sid['SID'].split('*')
				if sid.startswith( k_sid_domain[0] ) and sid.endswith( k_sid_domain[1] ):
					res_account = k_sid['Name']


		return res_account

	# ================================= get the SID in bytes and return it as string 'S-1-5-18'..
	def SID_converter(self, sid_hex):
		#Original form Source: https://github.com/google/grr/blob/master/grr/parsers/wmi_parser.py
		"""[Modified] Converts a binary SID to its string representation.
		https://msdn.microsoft.com/en-us/library/windows/desktop/aa379597.aspx
		The byte representation of an SID is as follows:
			Offset  Length  Description
			00      01      revision
			01      01      sub-authority count
			02      06      authority (big endian)
			08      04      subauthority #1 (little endian)
			0b      04      subauthority #2 (little endian)
			...
		Args:
			sid: A byte array.
		Returns:
			SID in string form.
		Raises:
			ValueError: If the binary SID is malformed.
		"""
		if sid_hex is None:
			return 'None'
		sid = sid_hex.decode('hex')

		if not sid:
			return ""
		str_sid_components = [ sid[0].encode('hex').lstrip('0') ]
		# Now decode the 48-byte portion
		sid_str = ''
		if len(sid) >= 8:
			subauthority_count = sid[1]
			identifier_authority = struct.unpack(">H", sid[2:4])[0]
			identifier_authority <<= 32
			identifier_authority |= struct.unpack(">L", sid[4:8])[0]
			str_sid_components.append(identifier_authority)
			start = 8
			#print subauthority_count.encode('hex')
			for i in range( int( subauthority_count.encode('hex') , 16 ) ):
				authority = sid[start:start + 4]
				if not authority:
					break
				if len(authority) < 4:
					raise ValueError("In binary SID '%s', component %d has been truncated. "
									"Expected 4 bytes, found %d: (%s)",
									",".join([str(ord(c)) for c in sid]), i,
									len(authority), authority)
				str_sid_components.append(struct.unpack("<L", authority)[0])
				start += 4
				sid_str = "S-%s" % ("-".join([str(x) for x in str_sid_components]))

		return sid_str



	# ================================= get the timestamp in iso format
	# https://programtalk.com/vs2/?source=python/3146/SrumMonkey/SrumMonkey.py
	def GetOleTimeStamp(self, raw_timestamp):
		timestamp = struct.unpack("d",raw_timestamp)[0]
		origDateTime = datetime.datetime(1899,12,30,0,0,0)
		timeDelta = datetime.timedelta(days=timestamp)
		new_datetime = origDateTime + timeDelta
		new_datetime = new_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")
		return new_datetime

	# ================================= get the timestamp in iso format from win timestamp
	# https://programtalk.com/vs2/?source=python/3146/SrumMonkey/SrumMonkey.py
	def GetWinTimeStamp(self, raw_timestamp):
		timestamp = raw_timestamp#struct.unpack("Q",raw_timestamp)[0]
		if datetime < 0:
			return None
		microsecs, _ = divmod(timestamp,10)
		timeDelta = datetime.timedelta(microseconds=microsecs)
		origDateTime = datetime.datetime(1601,1,1)
		new_datetime = origDateTime + timeDelta
		new_datetime = new_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")
		
		return new_datetime

	# ================================= get the value of a column from record
	def record_get_value(self, record , column_indx , column_type = None):
		# if the record is empty
		if record is None:
			return None
		# if column type not provided, get it from columns object
		if column_type is None:
			column_type = record.get_column_type(column_indx)

		data = record.get_value_data(column_indx)
		if data is None:
			return None
		
		if column_type in [pyesedb.column_types.LARGE_TEXT , pyesedb.column_types.SUPER_LARGE_VALUE , pyesedb.column_types.TEXT , pyesedb.column_types.BINARY_DATA , pyesedb.column_types.LARGE_BINARY_DATA]:
			return data


		if column_type == pyesedb.column_types.DOUBLE_64BIT:
			value = struct.unpack('d',data)[0]
		elif column_type == pyesedb.column_types.FLOAT_32BIT:
			value = struct.unpack('f',data)[0]
		elif column_type == pyesedb.column_types.BOOLEAN:
			value = struct.unpack('?',data)[0]
		elif column_type == pyesedb.column_types.INTEGER_8BIT_UNSIGNED:
			value = struct.unpack('B',data)[0]
		elif column_type == pyesedb.column_types.INTEGER_16BIT_SIGNED:
			value = struct.unpack('h',data)[0]
		elif column_type == pyesedb.column_types.INTEGER_16BIT_UNSIGNED:
			value = struct.unpack('H',data)[0]
		elif column_type == pyesedb.column_types.INTEGER_32BIT_SIGNED:
			value = struct.unpack('i',data)[0]
		elif column_type == pyesedb.column_types.INTEGER_32BIT_UNSIGNED:
			value = struct.unpack('I',data)[0]
		elif column_type == pyesedb.column_types.INTEGER_64BIT_SIGNED:
			value = struct.unpack('q',data)[0]
		elif column_type == pyesedb.column_types.GUID:
			value = uuid.UUID(bytes=data)
		elif column_type == pyesedb.column_types.DATE_TIME:
			value = self.GetOleTimeStamp(data)
		else:
			msg = 'UNKNOWN TYPE {}'.format(column_type)
			print msg
			return None

		return str(value)

	# ================================= return dict of the ID Mapping Table, key is the IdIndex, the content is {'IdType' : (0-3) , 'IdBlob' : (hex if type 3, string otherwise) }
	def get_SruDbIdMapTable_details(self):

		SruDbIdMapTable_table = self.ese_db.get_table_by_name( self.GUID_tables['SruDbIdMapTable'] )

		# details of the columns
		columns_names = [('IdType' ,2 ) , ( 'IdIndex' , 4 ) , ( 'IdBlob' , 11 )]

		# store the esult
		SruDbIdMapTable_res = {} 

		# get number of records in the table
		num_of_records = SruDbIdMapTable_table.get_number_of_records() 

		for record_num in range(num_of_records): # num_of_records
			# get the record details
			current_record = SruDbIdMapTable_table.get_record( record_num ) 

			current_record_value = self.record_get_value(current_record , 2 , 11 )
			current_record_data = {}
			current_record_data['IdType'] = int( current_record.get_value_data_as_integer( 0 ) )

			# if there is no data
			if current_record_value is None:
				current_record_data['IdBlob'] = None
			
			# if type 3 convert the IdBlob to hex value (SID values)
			elif current_record_data[ 'IdType' ] == 3:
				current_record_data[ 'IdBlob' ] = binascii.hexlify( current_record_value )

			# if not 3 (application names)
			else:
				current_record_data[ 'IdBlob' ] = current_record_value.replace('\x00' , '')

			SruDbIdMapTable_res[ str(current_record.get_value_data_as_integer( 1 ) ) ] = current_record_data
		
		return SruDbIdMapTable_res



	# ================================= get NetworkDataUsageMonitor statistics from the srum
	def get_NetworkDataUsageMonitor_details(self ):
		
		NetworkDataUsageMonitor_table = self.ese_db.get_table_by_name( self.GUID_tables['NetworkDataUsageMonitor'] )

		NetworkDataUsageMonitor_num_col = NetworkDataUsageMonitor_table.get_number_of_columns()

		columns_names = [ (NetworkDataUsageMonitor_table.get_column( x ).name , NetworkDataUsageMonitor_table.get_column( x ).type)  for x in range( NetworkDataUsageMonitor_num_col ) ]
		
		# get number of records in the table
		num_of_records = NetworkDataUsageMonitor_table.get_number_of_records() 

		network_details_list = []
		for record_num in range(num_of_records): # num_of_records
			# get the record details
			current_record = NetworkDataUsageMonitor_table.get_record( record_num ) 

			# check if the application index in the self.SruDbIdMapTable, used to get the application path
			if str(current_record.get_value_data_as_integer( 2 )) in self.SruDbIdMapTable.keys():
				current_app_details = {} # contain information of current application
				for column in range(NetworkDataUsageMonitor_num_col):
					current_app_details[ columns_names[ column ][0] ] = self.record_get_value(current_record , column , columns_names[ column ][1] )
				
				current_app_details[ 'App' ] = self.SruDbIdMapTable[ str(current_app_details['AppId']) ]['IdBlob'] 
				current_app_details[ 'AppType' ] = str(self.SruDbIdMapTable[ str(current_app_details['AppId']) ]['IdType'] )

				if str(current_app_details['UserId']) in self.SruDbIdMapTable.keys():

					current_app_details[ 'UserSID' ] = self.SID_converter( self.SruDbIdMapTable[ str(current_app_details['UserId']) ]['IdBlob'] )

					# get user name for the SID 
					UserName = self.get_SID_name( current_app_details[ 'UserSID' ] )
					current_app_details[ 'UserName' ] = 'None' if UserName is None else UserName
				else:
					current_app_details[ 'UserSID' ] = 'None'
					current_app_details[ 'UserName' ] = 'None'

				inttype = struct.unpack(">H6B", codecs.decode(format( int(current_app_details[ 'InterfaceLuid' ]) ,'016x'),'hex'))[0]

				current_app_details['InterfaceType'] = self.known_interface_Luid[ str(inttype) ]
				current_app_details['SRUM_Type'] = 'NetworkDataUsageMonitor'
				
				# change TimeStamp key to @timestamp
				current_app_details['@timestamp'] = current_app_details.pop('TimeStamp')


				network_details_list.append( current_app_details )

		return network_details_list


	# ================================= get application statistics from the srum
	def get_ApplicationResourceUsage_details(self ):
		
		ApplicationResourceUsage_table = self.ese_db.get_table_by_name( self.GUID_tables['ApplicationResourceUsage'] )

		ApplicationResourceUsage_num_col = ApplicationResourceUsage_table.get_number_of_columns()

		columns_names = [ (ApplicationResourceUsage_table.get_column( x ).name , ApplicationResourceUsage_table.get_column( x ).type)  for x in range( ApplicationResourceUsage_num_col ) ]

		# get number of records in the table
		num_of_records = ApplicationResourceUsage_table.get_number_of_records() 

		application_details_list = []
		for record_num in range(num_of_records): # num_of_records
			# get the record details
			current_record = ApplicationResourceUsage_table.get_record( record_num ) 

			# check if the application index in the self.SruDbIdMapTable, used to get the application path
			if str(current_record.get_value_data_as_integer( 2 )) in self.SruDbIdMapTable.keys():
				current_app_details = {} # contain information of current application
				for column in range(ApplicationResourceUsage_num_col):
					current_app_details[ columns_names[ column ][0] ] = self.record_get_value(current_record , column , columns_names[ column ][1] )
				
				current_app_details[ 'App' ] = self.SruDbIdMapTable[ str(current_app_details['AppId']) ]['IdBlob'] 
				current_app_details[ 'AppType' ] = str(self.SruDbIdMapTable[ str(current_app_details['AppId']) ]['IdType'] )

				if str(current_app_details['UserId']) in self.SruDbIdMapTable.keys():

					current_app_details[ 'UserSID' ] = self.SID_converter( self.SruDbIdMapTable[ str(current_app_details['UserId']) ]['IdBlob'] )

					# get user name for the SID 
					UserName = self.get_SID_name( current_app_details[ 'UserSID' ] )
					current_app_details[ 'UserName' ] = 'None' if UserName is None else UserName
				else:
					current_app_details[ 'UserSID' ] = 'None'
					current_app_details[ 'UserName' ] = 'None'

				current_app_details['SRUM_Type'] = 'ApplicationResourceUsage'

				# change TimeStamp key to @timestamp
				current_app_details['@timestamp'] = current_app_details.pop('TimeStamp')

				application_details_list.append( current_app_details )

		return application_details_list


	# ================================= get NetworkConnectivityUsageMonitor statistics from the srum
	def get_NetworkConnectivityUsageMonitor_details(self ):
		
		NetworkConnectivityUsageMonitor_table = self.ese_db.get_table_by_name( self.GUID_tables['NetworkConnectivityUsageMonitor'] )

		NetworkConnectivityUsageMonitor_num_col = NetworkConnectivityUsageMonitor_table.get_number_of_columns()

		columns_names = [ (NetworkConnectivityUsageMonitor_table.get_column( x ).name , NetworkConnectivityUsageMonitor_table.get_column( x ).type)  for x in range( NetworkConnectivityUsageMonitor_num_col ) ]

		# get number of records in the table
		num_of_records = NetworkConnectivityUsageMonitor_table.get_number_of_records() 

		network_details_list = []
		for record_num in range(num_of_records): # num_of_records
			# get the record details
			current_record = NetworkConnectivityUsageMonitor_table.get_record( record_num ) 

			# check if the application index in the self.SruDbIdMapTable, used to get the application path
			if str(current_record.get_value_data_as_integer( 2 )) in self.SruDbIdMapTable.keys():
				current_app_details = {} # contain information of current application
				for column in range(NetworkConnectivityUsageMonitor_num_col):
					current_app_details[ columns_names[ column ][0] ] = self.record_get_value(current_record , column , columns_names[ column ][1] )
				
				current_app_details[ 'App' ] = self.SruDbIdMapTable[ str(current_app_details['AppId']) ]['IdBlob'] 
				current_app_details[ 'AppType' ] = str(self.SruDbIdMapTable[ str(current_app_details['AppId']) ]['IdType'] )

				if str(current_app_details['UserId']) in self.SruDbIdMapTable.keys():

					current_app_details[ 'UserSID' ] = self.SID_converter( self.SruDbIdMapTable[ str(current_app_details['UserId']) ]['IdBlob'] )

					# get user name for the SID 
					UserName = self.get_SID_name( current_app_details[ 'UserSID' ] )
					current_app_details[ 'UserName' ] = 'None' if UserName is None else UserName
				else:
					current_app_details[ 'UserSID' ] = 'None'
					current_app_details[ 'UserName' ] = 'None'
				
				# convert connection start time to humen readable format
				current_app_details['ConnectStartTime'] = self.GetWinTimeStamp( int(current_app_details['ConnectStartTime']) )
				# get interface type
				inttype = struct.unpack(">H6B", codecs.decode(format( int(current_app_details[ 'InterfaceLuid' ]) ,'016x'),'hex'))[0]
				current_app_details['InterfaceType'] = self.known_interface_Luid[ str(inttype) ]

				current_app_details['SRUM_Type'] = 'NetworkConnectivityUsageMonitor'

				# change TimeStamp key to @timestamp
				current_app_details['@timestamp'] = current_app_details.pop('TimeStamp')
				
				network_details_list.append( current_app_details )

		return network_details_list
	
	# write the output to the provided file, srum type to specifiy the table (ApplicationResourceUsage,NetworkDataUsageMonitor,...)
	def write_output(self, file , srum_type):
		if srum_type == 'ApplicationResourceUsage':
			columns = ['@timestamp','SRUM_Type','App','UserName','UserSID','AppType','FaceTime','BackgroundContextSwitches','ForegroundCycleTime','ForegroundNumWriteOperations','ForegroundContextSwitches','UserId','ForegroundNumReadOperations','BackgroundBytesWritten','ForegroundBytesWritten','BackgroundBytesRead','AutoIncId','ForegroundBytesRead','BackgroundNumReadOperations','ForegroundNumberOfFlushes','BackgroundNumWriteOperations','AppId','BackgroundCycleTime','BackgroundNumberOfFlushes']
			data = self.ApplicationResourceUsage

		elif srum_type == 'NetworkDataUsageMonitor':
			columns = ['@timestamp','SRUM_Type','App','UserName','UserSID','InterfaceType','InterfaceLuid','AppType','UserId','AppId','AutoIncId','BytesRecvd','BytesSent','L2ProfileFlags','L2ProfileId']
			data = self.NetworkDataUsageMonitor

		elif srum_type == 'NetworkConnectivityUsageMonitor':
			columns = ['@timestamp','SRUM_Type','App','UserName','UserSID','ConnectStartTime','ConnectedTime','InterfaceType','InterfaceLuid','AppType','UserId','AppId','AutoIncId','L2ProfileFlags','L2ProfileId']
			data = self.NetworkConnectivityUsageMonitor

		else:
			print "[-] srum_type ["+srum_type+"] not exists "
			return False

		res = [','.join(columns)]
		for app in data:
			a = []
			for k in columns:
				a.append( str(app[k]) )
			res.append( ','.join(a) )

		res_csv = '\n'.join(res)
		
		f = open(file , 'w')
		f.write(res_csv)
		f.close()
		
		print "[+] output [ "+str(len(data))+" records ] written to file ["+file+"], SRUM type ["+srum_type+"]"
		return res_csv

	def write_output_main(self, file , res_type):
		file = file.split('.')[0]
		types = ['ApplicationResourceUsage','NetworkDataUsageMonitor','NetworkConnectivityUsageMonitor']
		for i in types:
			if res_type == 'csv':
				self.write_output( file + "-" + i + ".csv" , i )
			elif res_type == 'json':
				
				if i == 'ApplicationResourceUsage':
					data = self.ApplicationResourceUsage
				elif i == 'NetworkDataUsageMonitor':
					data = self.NetworkDataUsageMonitor
				elif i == 'NetworkConnectivityUsageMonitor':
					data = self.NetworkConnectivityUsageMonitor
				
				f = open(file + "-" + i + ".json" , 'w')
				f.write( json.dumps(data) )
				f.close()
				print "[+] output [ "+str(len(data))+" records ] written to file ["+file + "-" + i + ".json], SRUM type ["+i+"]"
		
