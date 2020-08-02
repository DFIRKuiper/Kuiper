import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *
from lib.helper import strip_control_characters





class DHCP():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        hive = get_hive(self.prim_hive,self.log_files)
        select_key = hive.find_key(u'Select')
        current_path=''
        if select_key:
            current_value = select_key.value(name=u"Current")
            current_path = u"ControlSet{:03d}".format(current_value.data())
        else:
            current_path ='ControlSet001'
        lst= []
        DHCP_user_settings_path = u"\\".join([current_path,u"Services\\Tcpip\\Parameters\\Interfaces"])
        DHCP_user_settings_key = hive.find_key(DHCP_user_settings_path)
        if DHCP_user_settings_key:
            for sid_key in DHCP_user_settings_key.subkeys():
                timestamp = sid_key.last_written_timestamp().isoformat()
                sid_name = sid_key.name()

                def get_date (value_name):
                    value = sid_key.value(name=value_name)
                    if value:
                        value = value.data()
                    else:
                        value ="None"
                    return value

                dict_values_data = {'DhcpIPAddress' : strip_control_characters(get_date('DhcpIPAddress')),
                                        'DhcpServer' : strip_control_characters(get_date('DhcpServer')),
                                        'DhcpSubnetMask' : strip_control_characters(get_date('DhcpSubnetMask')),
                                        'Domain' : strip_control_characters(get_date('Domain')),
                                        'NameServer' : strip_control_characters(get_date('NameServer')),
                                        'EnableDHCP' : get_date('EnableDHCP'),
                                        'DhcpConnForceBroadcastFlag' : get_date('DhcpConnForceBroadcastFlag'),
                                        'IsServerNapAware' : get_date('IsServerNapAware'),
                                        'RegisterAdapterName' : get_date('RegisterAdapterName'),
                                        'RegistrationEnabled' : get_date('RegistrationEnabled')}


                record = OrderedDict([
                    ("Dhcp IP Address", dict_values_data['DhcpIPAddress']),
                    ("Dhcp Server", dict_values_data['DhcpServer']),
                    ("DhcpSubnetMask", dict_values_data['DhcpSubnetMask']),
                    ("Domain", dict_values_data['Domain']),
                    ("Name Server", dict_values_data['NameServer']),
                    ("Enable DHCP", dict_values_data['EnableDHCP']),
                    ("DhcpConnForceBroadcastFlag", dict_values_data['DhcpConnForceBroadcastFlag']),
                    ("Is Server NapAware", dict_values_data['IsServerNapAware']),
                    ("Register Adapter Name", dict_values_data['RegisterAdapterName']),
                    ("Registration Enabled", dict_values_data['RegistrationEnabled']),
                    ('@timestamp',timestamp)
                ])

                lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('DHCP', DHCP_user_settings_path))

        return lst
