from __future__ import print_function

import pyesedb
import json
import struct
import datetime
import uuid

# resources:
# https://programtalk.com/vs2/?source=python/3146/SrumMonkey/SrumMonkey.py
# https://github.com/libyal/esedb-kb/blob/master/documentation/System%20Resource%20Usage%20Monitor%20(SRUM).asciidoc
# https://github.com/MarkBaggett/srum-dump/


def stringify_values(d):
	return {k: str(v) for k, v in d.items()}


class SRUM_Parser():

	wildcard_SID = {
        'S-1-5-5-': 'Logon Session',
	}

	domain_SID_prefix = "S-1-5-21-"
	domain_SID_suffix = {
        '-498': 'Enterprise Read-only Domain Controllers',
        '-500': 'Administrator',
        '-501': 'Guest',
        '-502': 'KRBTGT',
        '-512': 'Domain Admins',
        '-513': 'Domain Users',
        '-514': 'Domain Guests',
        '-515': 'Domain Computers',
        '-516': 'Domain Controllers',
        '-517': 'Cert Publishers',
        '-518': 'Schema Admins',
        '-519': 'Enterprise Admins',
        '-520': 'Group Policy Creator Owners',
        '-521': 'Read-only Domain Controllers',
        '-522': 'Cloneable Domain Controllers',
        '-526': 'Key Admins',
        '-527': 'Enterprise Key Admins',
        '-553': 'RAS and IAS Servers',
        '-571': 'Allowed RODC Password Replication Group',
        '-572': 'Denied RODC Password Replication Group',
	}

	known_SID = {
        'S-1-0': 'Null Authority',
        'S-1-0-0': 'Nobody',
        'S-1-1': 'World Authority',
        'S-1-1-0': 'Everyone',
        'S-1-2': 'Local Authority',
        'S-1-2-0': 'Local',
        'S-1-2-1': 'Console Logon',
        'S-1-3': 'Creator Authority',
        'S-1-3-0': 'Creator Owner',
        'S-1-3-1': 'Creator Group',
        'S-1-3-2': 'Creator Owner Server',
        'S-1-3-3': 'Creator Group Server',
        'S-1-3-4': 'Owner Rights',
        'S-1-4': 'Non-unique Authority',
        'S-1-5': 'NT Authority',
        'S-1-5-1': 'Dialup',
        'S-1-5-2': 'Network',
        'S-1-5-3': 'Batch',
        'S-1-5-4': 'Interactive',
        'S-1-5-6': 'Service',
        'S-1-5-7': 'Anonymous',
        'S-1-5-8': 'Proxy',
        'S-1-5-9': 'Enterprise Domain Controllers',
        'S-1-5-10': 'Principal Self',
        'S-1-5-11': 'Authenticated Users',
        'S-1-5-12': 'Restricted Code',
        'S-1-5-13': 'Terminal Server Users',
        'S-1-5-14': 'Remote Interactive Logon',
        'S-1-5-15': 'This Organization',
        'S-1-5-17': 'This Organization',
        'S-1-5-18': 'Local System',
        'S-1-5-19': 'NT Authority',
        'S-1-5-20': 'NT Authority',

        'S-1-5-32-544': 'Administrators',
        'S-1-5-32-545': 'Users',
        'S-1-5-32-546': 'Guests',
        'S-1-5-32-547': 'Power Users',
        'S-1-5-32-548': 'Account Operators',
        'S-1-5-32-549': 'Server Operators',
        'S-1-5-32-550': 'Print Operators',
        'S-1-5-32-551': 'Backup Operators',
        'S-1-5-32-552': 'Replicators',
        'S-1-5-32-554': 'BUILTIN\\Pre-Windows 2000 Compatible Access',
        'S-1-5-32-555': 'BUILTIN\\Remote Desktop Users',
        'S-1-5-32-556': 'BUILTIN\\Network Configuration Operators',
        'S-1-5-32-557': 'BUILTIN\\Incoming Forest Trust Builders',
        'S-1-5-32-558': 'BUILTIN\\Performance Monitor Users',
        'S-1-5-32-559': 'BUILTIN\\Performance Log Users',
        'S-1-5-32-560': 'BUILTIN\\Windows Authorization Access Group',
        'S-1-5-32-561': 'BUILTIN\\Terminal Server License Servers',
        'S-1-5-32-562': 'BUILTIN\\Distributed COM Users',
        'S-1-5-32-569': 'BUILTIN\\Cryptographic Operators',
        'S-1-5-32-573': 'BUILTIN\\Event Log Readers',
        'S-1-5-32-574': 'BUILTIN\\Certificate Service DCOM Access',
        'S-1-5-32-575': 'BUILTIN\\RDS Remote Access Servers',
        'S-1-5-32-576': 'BUILTIN\\RDS Endpoint Servers',
        'S-1-5-32-577': 'BUILTIN\\RDS Management Servers',
        'S-1-5-32-578': 'BUILTIN\\Hyper-V Administrators',
        'S-1-5-32-579': 'BUILTIN\\Access Control Assistance Operators',
        'S-1-5-32-580': 'BUILTIN\\Remote Management Users',

        'S-1-5-64-10': 'NTLM Authentication',
        'S-1-5-64-14': 'SChannel Authentication',
        'S-1-5-64-21': 'Digest Authentication',

        'S-1-5-80': 'NT Service',
        'S-1-5-80-0': 'All Services',
        'S-1-5-83-0': 'NT VIRTUAL MACHINE\\Virtual Machines',

        'S-1-16-0': 'Untrusted Mandatory Level',
        'S-1-16-4096': 'Low Mandatory Level',
        'S-1-16-8192': 'Medium Mandatory Level',
        'S-1-16-8448': 'Medium Plus Mandatory Level',
        'S-1-16-12288': 'High Mandatory Level',
        'S-1-16-16384': 'System Mandatory Level',
        'S-1-16-20480': 'Protected Process Mandatory Level',
        'S-1-16-28672': 'Secure Process Mandatory Level',
    }

	known_interface_Luid = {
		0:'Unknown Interface',
		1:'IF_TYPE_OTHER',
		2:'IF_TYPE_REGULAR_1822',
		3:'IF_TYPE_HDH_1822',
		4:'IF_TYPE_DDN_X25',
		5:'IF_TYPE_RFC877_X25',
		6:'IF_TYPE_ETHERNET_CSMACD',
		7:'IF_TYPE_IS088023_CSMACD',
		8:'IF_TYPE_ISO88024_TOKENBUS',
		9:'IF_TYPE_ISO88025_TOKENRING',
		10:'IF_TYPE_ISO88026_MAN',
		11:'IF_TYPE_STARLAN',
		12:'IF_TYPE_PROTEON_10MBIT',
		13:'IF_TYPE_PROTEON_80MBIT',
		14:'IF_TYPE_HYPERCHANNEL',
		15:'IF_TYPE_FDDI',
		16:'IF_TYPE_LAP_B',
		17:'IF_TYPE_SDLC',
		18:'IF_TYPE_DS1',
		19:'IF_TYPE_E1',
		20:'IF_TYPE_BASIC_ISDN',
		21:'IF_TYPE_PRIMARY_ISDN',
		22:'IF_TYPE_PROP_POINT2POINT_SERIAL',
		23:'IF_TYPE_PPP',
		24:'IF_TYPE_SOFTWARE_LOOPBACK',
		25:'IF_TYPE_EON',
		26:'IF_TYPE_ETHERNET_3MBIT',
		27:'IF_TYPE_NSIP',
		28:'IF_TYPE_SLIP',
		29:'IF_TYPE_ULTRA',
		30:'IF_TYPE_DS3',
		31:'IF_TYPE_SIP',
		32:'IF_TYPE_FRAMERELAY',
		33:'IF_TYPE_RS232',
		34:'IF_TYPE_PARA',
		35:'IF_TYPE_ARCNET',
		36:'IF_TYPE_ARCNET_PLUS',
		37:'IF_TYPE_ATM',
		38:'IF_TYPE_MIO_X25',
		39:'IF_TYPE_SONET',
		40:'IF_TYPE_X25_PLE',
		41:'IF_TYPE_ISO88022_LLC',
		42:'IF_TYPE_LOCALTALK',
		43:'IF_TYPE_SMDS_DXI',
		44:'IF_TYPE_FRAMERELAY_SERVICE',
		45:'IF_TYPE_V35',
		46:'IF_TYPE_HSSI',
		47:'IF_TYPE_HIPPI',
		48:'IF_TYPE_MODEM',
		49:'IF_TYPE_AAL5',
		50:'IF_TYPE_SONET_PATH',
		51:'IF_TYPE_SONET_VT',
		52:'IF_TYPE_SMDS_ICIP',
		53:'IF_TYPE_PROP_VIRTUAL',
		54:'IF_TYPE_PROP_MULTIPLEXOR',
		55:'IF_TYPE_IEEE80212',
		56:'IF_TYPE_FIBRECHANNEL',
		57:'IF_TYPE_HIPPIINTERFACE',
		58:'IF_TYPE_FRAMERELAY_INTERCONNECT',
		59:'IF_TYPE_AFLANE_8023',
		60:'IF_TYPE_AFLANE_8025',
		61:'IF_TYPE_CCTEMUL',
		62:'IF_TYPE_FASTETHER',
		63:'IF_TYPE_ISDN',
		64:'IF_TYPE_V11',
		65:'IF_TYPE_V36',
		66:'IF_TYPE_G703_64K',
		67:'IF_TYPE_G703_2MB',
		68:'IF_TYPE_QLLC',
		69:'IF_TYPE_FASTETHER_FX',
		70:'IF_TYPE_CHANNEL',
		71:'IF_TYPE_IEEE80211',
		72:'IF_TYPE_IBM370PARCHAN',
		73:'IF_TYPE_ESCON',
		74:'IF_TYPE_DLSW',
		75:'IF_TYPE_ISDN_S',
		76:'IF_TYPE_ISDN_U',
		77:'IF_TYPE_LAP_D',
		78:'IF_TYPE_IPSWITCH',
		79:'IF_TYPE_RSRB',
		80:'IF_TYPE_ATM_LOGICAL',
		81:'IF_TYPE_DS0',
		82:'IF_TYPE_DS0_BUNDLE',
		83:'IF_TYPE_BSC',
		84:'IF_TYPE_ASYNC',
		85:'IF_TYPE_CNR',
		86:'IF_TYPE_ISO88025R_DTR',
		87:'IF_TYPE_EPLRS',
		88:'IF_TYPE_ARAP',
		89:'IF_TYPE_PROP_CNLS',
		90:'IF_TYPE_HOSTPAD',
		91:'IF_TYPE_TERMPAD',
		92:'IF_TYPE_FRAMERELAY_MPI',
		93:'IF_TYPE_X213',
		94:'IF_TYPE_ADSL',
		95:'IF_TYPE_RADSL',
		96:'IF_TYPE_SDSL',
		97:'IF_TYPE_VDSL',
		98:'IF_TYPE_ISO88025_CRFPRINT',
		99:'IF_TYPE_MYRINET',
		100:'IF_TYPE_VOICE_EM',
		101:'IF_TYPE_VOICE_FXO',
		102:'IF_TYPE_VOICE_FXS',
		103:'IF_TYPE_VOICE_ENCAP',
		104:'IF_TYPE_VOICE_OVERIP',
		105:'IF_TYPE_ATM_DXI',
		106:'IF_TYPE_ATM_FUNI',
		107:'IF_TYPE_ATM_IMA',
		108:'IF_TYPE_PPPMULTILINKBUNDLE',
		109:'IF_TYPE_IPOVER_CDLC',
		110:'IF_TYPE_IPOVER_CLAW',
		111:'IF_TYPE_STACKTOSTACK',
		112:'IF_TYPE_VIRTUALIPADDRESS',
		113:'IF_TYPE_MPC',
		114:'IF_TYPE_IPOVER_ATM',
		115:'IF_TYPE_ISO88025_FIBER',
		116:'IF_TYPE_TDLC',
		117:'IF_TYPE_GIGABITETHERNET',
		118:'IF_TYPE_HDLC',
		119:'IF_TYPE_LAP_F',
		120:'IF_TYPE_V37',
		121:'IF_TYPE_X25_MLP',
		122:'IF_TYPE_X25_HUNTGROUP',
		123:'IF_TYPE_TRANSPHDLC',
		124:'IF_TYPE_INTERLEAVE',
		125:'IF_TYPE_FAST',
		126:'IF_TYPE_IP',
		127:'IF_TYPE_DOCSCABLE_MACLAYER',
		128:'IF_TYPE_DOCSCABLE_DOWNSTREAM',
		129:'IF_TYPE_DOCSCABLE_UPSTREAM',
		130:'IF_TYPE_A12MPPSWITCH',
		131:'IF_TYPE_TUNNEL',
		132:'IF_TYPE_COFFEE',
		133:'IF_TYPE_CES',
		134:'IF_TYPE_ATM_SUBINTERFACE',
		135:'IF_TYPE_L2_VLAN',
		136:'IF_TYPE_L3_IPVLAN',
		137:'IF_TYPE_L3_IPXVLAN',
		138:'IF_TYPE_DIGITALPOWERLINE',
		139:'IF_TYPE_MEDIAMAILOVERIP',
		140:'IF_TYPE_DTM',
		141:'IF_TYPE_DCN',
		142:'IF_TYPE_IPFORWARD',
		143:'IF_TYPE_MSDSL',
		144:'IF_TYPE_IEEE1394',
		145:'IF_TYPE_IF_GSN',
		146:'IF_TYPE_DVBRCC_MACLAYER',
		147:'IF_TYPE_DVBRCC_DOWNSTREAM',
		148:'IF_TYPE_DVBRCC_UPSTREAM',
		149:'IF_TYPE_ATM_VIRTUAL',
		150:'IF_TYPE_MPLS_TUNNEL',
		151:'IF_TYPE_SRP',
		152:'IF_TYPE_VOICEOVERATM',
		153:'IF_TYPE_VOICEOVERFRAMERELAY',
		154:'IF_TYPE_IDSL',
		155:'IF_TYPE_COMPOSITELINK',
		156:'IF_TYPE_SS7_SIGLINK',
		157:'IF_TYPE_PROP_WIRELESS_P2P',
		158:'IF_TYPE_FR_FORWARD',
		159:'IF_TYPE_RFC1483',
		160:'IF_TYPE_USB',
		161:'IF_TYPE_IEEE8023AD_LAG',
		162:'IF_TYPE_BGP_POLICY_ACCOUNTING',
		163:'IF_TYPE_FRF16_MFR_BUNDLE',
		164:'IF_TYPE_H323_GATEKEEPER',
		165:'IF_TYPE_H323_PROXY',
		166:'IF_TYPE_MPLS',
		167:'IF_TYPE_MF_SIGLINK',
		168:'IF_TYPE_HDSL2',
		169:'IF_TYPE_SHDSL',
		170:'IF_TYPE_DS1_FDL',
		171:'IF_TYPE_POS',
		172:'IF_TYPE_DVB_ASI_IN',
		173:'IF_TYPE_DVB_ASI_OUT',
		174:'IF_TYPE_PLC',
		175:'IF_TYPE_NFAS',
		176:'IF_TYPE_TR008',
		177:'IF_TYPE_GR303_RDT',
		178:'IF_TYPE_GR303_IDT',
		179:'IF_TYPE_ISUP',
		180:'IF_TYPE_PROP_DOCS_WIRELESS_MACLAYER',
		181:'IF_TYPE_PROP_DOCS_WIRELESS_DOWNSTREAM',
		182:'IF_TYPE_PROP_DOCS_WIRELESS_UPSTREAM',
		183:'IF_TYPE_HIPERLAN2',
		184:'IF_TYPE_PROP_BWA_P2MP',
		185:'IF_TYPE_SONET_OVERHEAD_CHANNEL',
		186:'IF_TYPE_DIGITAL_WRAPPER_OVERHEAD_CHANNEL',
		187:'IF_TYPE_AAL2',
		188:'IF_TYPE_RADIO_MAC',
		189:'IF_TYPE_ATM_RADIO',
		190:'IF_TYPE_IMT',
		191:'IF_TYPE_MVL',
		192:'IF_TYPE_REACH_DSL',
		193:'IF_TYPE_FR_DLCI_ENDPT',
		194:'IF_TYPE_ATM_VCI_ENDPT',
		195:'IF_TYPE_OPTICAL_CHANNEL',
		196:'IF_TYPE_OPTICAL_TRANSPORT',
		243:'IF_TYPE_WWANPP',
		244:'IF_TYPE_WWANPP2'
	}

	def __init__(self , ese_file):
		self.ese_db = pyesedb.open(ese_file)
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
		res_account = self.known_SID.get(sid, None)
		if res_account:
			return res_account

		if sid.startswith(self.domain_SID_prefix):
			for suffix in self.domain_SID_suffix:
				if sid.endswith(suffix):
					return self.domain_SID_suffix[suffix]
			else:
				# if the sid has none of the specified suffixes,
				# it represent a normal user account
				return "User Account"

		for logon_sid in self.wildcard_SID:
			if sid.startswith(logon_sid):
				return self.wildcard_SID[logon_sid]

		return None

	# ================================= get the SID in bytes and return it as string 'S-1-5-18'..
	def SID_converter(self, sid):
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
		if sid is None:
			return 'None'

		if not sid:
			return 'None'

		sid_components = [ ord(sid[0]) ]
		# Now decode the 48-byte portion

		if len(sid) >= 8:
			subauthority_count = ord(sid[1])
			identifier_authority = struct.unpack(">H", sid[2:4])[0]
			identifier_authority <<= 32
			identifier_authority |= struct.unpack(">L", sid[4:8])[0]
			sid_components.append(identifier_authority)
			start = 8
			#print subauthority_count.encode('hex')
			for i in range( subauthority_count ):
				authority = sid[start:start + 4]
				if not authority:
					break
				if len(authority) < 4:
					raise ValueError("In binary SID '%s', component %d has been truncated. "
									"Expected 4 bytes, found %d: (%s)",
									",".join([str(ord(c)) for c in sid]), i,
									len(authority), authority)
				sid_components.append(struct.unpack("<L", authority)[0])
				start += 4

		return "S-%s" % ("-".join([str(x) for x in sid_components]))



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
		if timestamp < 0:
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

		if column_type in (pyesedb.column_types.BINARY_DATA , pyesedb.column_types.LARGE_BINARY_DATA, pyesedb.column_types.SUPER_LARGE_VALUE):
			return data

		if column_type in [pyesedb.column_types.LARGE_TEXT , pyesedb.column_types.TEXT ]:
			return data.decode("utf16").rstrip("\x00").encode("utf8")

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
			print(msg)
			return None

		return value

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

			current_record_data = {}

			record_type = current_record.get_value_data_as_integer( 0 )
			current_record_data['IdType'] = record_type

			if record_type == 3:
				current_record_data['IdBlob'] = self.record_get_value(current_record , 2 , pyesedb.column_types.BINARY_DATA )
			else:
				current_record_data['IdBlob'] = self.record_get_value(current_record , 2 , pyesedb.column_types.TEXT )

			SruDbIdMapTable_res[ current_record.get_value_data_as_integer( 1 ) ] = current_record_data

		return SruDbIdMapTable_res



	# ================================= get NetworkDataUsageMonitor statistics from the srum
	def get_NetworkDataUsageMonitor_details(self ):

		NetworkDataUsageMonitor_table = self.ese_db.get_table_by_name( self.GUID_tables['NetworkDataUsageMonitor'] )
		if not NetworkDataUsageMonitor_table:
			return []

		NetworkDataUsageMonitor_num_col = NetworkDataUsageMonitor_table.get_number_of_columns()

		columns_names = [ (str(NetworkDataUsageMonitor_table.get_column( x ).name) , NetworkDataUsageMonitor_table.get_column( x ).type)  for x in range( NetworkDataUsageMonitor_num_col ) ]

		# get number of records in the table
		num_of_records = NetworkDataUsageMonitor_table.get_number_of_records()

		network_details_list = []
		for record_num in range(num_of_records): # num_of_records
			# get the record details
			current_record = NetworkDataUsageMonitor_table.get_record( record_num )

			# check if the application index in the self.SruDbIdMapTable, used to get the application path
			if current_record.get_value_data_as_integer( 2 ) in self.SruDbIdMapTable:
				current_app_details = {} # contain information of current application
				for column in range(NetworkDataUsageMonitor_num_col):
					current_app_details[ columns_names[ column ][0] ] = self.record_get_value(current_record , column , columns_names[ column ][1] )

				current_app_details[ 'App' ] = self.SruDbIdMapTable[ current_app_details['AppId'] ]['IdBlob']
				current_app_details[ 'AppType' ] = self.SruDbIdMapTable[ current_app_details['AppId'] ]['IdType']

				if current_app_details['UserId'] in self.SruDbIdMapTable:

					current_app_details[ 'UserSID' ] = self.SID_converter( self.SruDbIdMapTable[ current_app_details['UserId'] ]['IdBlob'] )

					# get user name for the SID
					UserName = self.get_SID_name( current_app_details[ 'UserSID' ] )
					current_app_details[ 'UserName' ] = 'None' if UserName is None else UserName
				else:
					current_app_details[ 'UserSID' ] = 'None'
					current_app_details[ 'UserName' ] = 'None'

				current_app_details['InterfaceType'] = self.known_interface_Luid[ (current_app_details[ 'InterfaceLuid' ] >> 48) & 0xFFFF ]

				current_app_details['SRUM_Type'] = 'NetworkDataUsageMonitor'

				# change TimeStamp key to @timestamp
				current_app_details['@timestamp'] = current_app_details.pop('TimeStamp')


				network_details_list.append( stringify_values(current_app_details) )

		return network_details_list


	# ================================= get application statistics from the srum
	def get_ApplicationResourceUsage_details(self ):

		ApplicationResourceUsage_table = self.ese_db.get_table_by_name( self.GUID_tables['ApplicationResourceUsage'] )
		if not ApplicationResourceUsage_table:
			return []

		ApplicationResourceUsage_num_col = ApplicationResourceUsage_table.get_number_of_columns()

		columns_names = [ (str(ApplicationResourceUsage_table.get_column( x ).name) , ApplicationResourceUsage_table.get_column( x ).type)  for x in range( ApplicationResourceUsage_num_col ) ]

		# get number of records in the table
		num_of_records = ApplicationResourceUsage_table.get_number_of_records()

		application_details_list = []
		for record_num in range(num_of_records): # num_of_records
			# get the record details
			current_record = ApplicationResourceUsage_table.get_record( record_num )

			# check if the application index in the self.SruDbIdMapTable, used to get the application path
			if current_record.get_value_data_as_integer( 2 ) in self.SruDbIdMapTable:
				current_app_details = {} # contain information of current application
				for column in range(ApplicationResourceUsage_num_col):
					current_app_details[ columns_names[ column ][0] ] = self.record_get_value(current_record , column , columns_names[ column ][1] )

				current_app_details[ 'App' ] = self.SruDbIdMapTable[ current_app_details['AppId'] ]['IdBlob']
				current_app_details[ 'AppType' ] = self.SruDbIdMapTable[ current_app_details['AppId'] ]['IdType']

				if current_app_details['UserId'] in self.SruDbIdMapTable:

					current_app_details[ 'UserSID' ] = self.SID_converter( self.SruDbIdMapTable[ current_app_details['UserId'] ]['IdBlob'] )

					# get user name for the SID
					UserName = self.get_SID_name( current_app_details[ 'UserSID' ] )
					current_app_details[ 'UserName' ] = 'None' if UserName is None else UserName
				else:
					current_app_details[ 'UserSID' ] = 'None'
					current_app_details[ 'UserName' ] = 'None'

				current_app_details['SRUM_Type'] = 'ApplicationResourceUsage'

				# change TimeStamp key to @timestamp
				current_app_details['@timestamp'] = current_app_details.pop('TimeStamp')

				application_details_list.append( stringify_values(current_app_details) )

		return application_details_list


	# ================================= get NetworkConnectivityUsageMonitor statistics from the srum
	def get_NetworkConnectivityUsageMonitor_details(self ):

		NetworkConnectivityUsageMonitor_table = self.ese_db.get_table_by_name( self.GUID_tables['NetworkConnectivityUsageMonitor'] )
		if not NetworkConnectivityUsageMonitor_table:
			return []

		NetworkConnectivityUsageMonitor_num_col = NetworkConnectivityUsageMonitor_table.get_number_of_columns()

		columns_names = [ (str(NetworkConnectivityUsageMonitor_table.get_column( x ).name) , NetworkConnectivityUsageMonitor_table.get_column( x ).type)  for x in range( NetworkConnectivityUsageMonitor_num_col ) ]

		# get number of records in the table
		num_of_records = NetworkConnectivityUsageMonitor_table.get_number_of_records()

		network_details_list = []
		for record_num in range(num_of_records): # num_of_records
			# get the record details
			current_record = NetworkConnectivityUsageMonitor_table.get_record( record_num )

			# check if the application index in the self.SruDbIdMapTable, used to get the application path
			if current_record.get_value_data_as_integer( 2 ) in self.SruDbIdMapTable:
				current_app_details = {} # contain information of current application
				for column in range(NetworkConnectivityUsageMonitor_num_col):
					current_app_details[ columns_names[ column ][0] ] = self.record_get_value(current_record , column , columns_names[ column ][1] )

				current_app_details[ 'App' ] = self.SruDbIdMapTable[ current_app_details['AppId'] ]['IdBlob']
				current_app_details[ 'AppType' ] = self.SruDbIdMapTable[ current_app_details['AppId'] ]['IdType']

				if current_app_details['UserId'] in self.SruDbIdMapTable:

					current_app_details[ 'UserSID' ] = self.SID_converter( self.SruDbIdMapTable[ current_app_details['UserId'] ]['IdBlob'] )

					# get user name for the SID
					UserName = self.get_SID_name( current_app_details[ 'UserSID' ] )
					current_app_details[ 'UserName' ] = 'None' if UserName is None else UserName
				else:
					current_app_details[ 'UserSID' ] = 'None'
					current_app_details[ 'UserName' ] = 'None'

				# convert connection start time to humen readable format
				current_app_details['ConnectStartTime'] = self.GetWinTimeStamp( current_app_details['ConnectStartTime'])
				# get interface type
				current_app_details['InterfaceType'] = self.known_interface_Luid[ (current_app_details[ 'InterfaceLuid' ] >> 48) & 0xFFFF ]

				current_app_details['SRUM_Type'] = 'NetworkConnectivityUsageMonitor'

				# change TimeStamp key to @timestamp
				current_app_details['@timestamp'] = current_app_details.pop('TimeStamp')

				network_details_list.append( stringify_values(current_app_details) )

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
			print("[-] srum_type ["+srum_type+"] not exists ")
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

		print("[+] output [ "+str(len(data))+" records ] written to file ["+file+"], SRUM type ["+srum_type+"]")
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
				print("[+] output [ "+str(len(data))+" records ] written to file ["+file + "-" + i + ".json], SRUM type ["+i+"]")
