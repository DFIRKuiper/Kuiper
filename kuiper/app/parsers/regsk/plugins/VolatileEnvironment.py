import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *
from lib.helper import strip_control_characters





class VolatileEnvironment():

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        print ("HI"*100)
        lst= []
        VolatileEnvironment_user_settings_path = u"Volatile Environment"
        hive = get_hive(self.prim_hive,self.log_files)
        VolatileEnvironment_user_settings_key = hive.find_key(VolatileEnvironment_user_settings_path)
        print('Found a key: {}'.format(VolatileEnvironment_user_settings_key.path()))
        #return None
        if VolatileEnvironment_user_settings_key:
            print("gg")
        #     for sid_key in VolatileEnvironment_user_settings_key.subkeys():
        #         sid_name = sid_key.name()
        #
        #         def get_date (value_name):
        #             value = sid_key.value(name=value_name)
        #             if value:
        #                 value = value.data()
        #             else:
        #                 value ="None"
        #             return value
        #
        #         dict_values_data = {'VolatileEnvironmentIPAddress' : strip_control_characters(get_date('VolatileEnvironmentIPAddress')),
        #                                 'VolatileEnvironmentServer' : strip_control_characters(get_date('VolatileEnvironmentServer')),
        #                                 'VolatileEnvironmentSubnetMask' : strip_control_characters(get_date('VolatileEnvironmentSubnetMask')),
        #                                 'Domain' : strip_control_characters(get_date('Domain')),
        #                                 'NameServer' : strip_control_characters(get_date('NameServer')),
        #                                 'EnableVolatileEnvironment' : get_date('EnableVolatileEnvironment'),
        #                                 'VolatileEnvironmentConnForceBroadcastFlag' : get_date('VolatileEnvironmentConnForceBroadcastFlag'),
        #                                 'IsServerNapAware' : get_date('IsServerNapAware'),
        #                                 'RegisterAdapterName' : get_date('RegisterAdapterName'),
        #                                 'RegistrationEnabled' : get_date('RegistrationEnabled')}
        #
        #
        #         record = OrderedDict([
        #             ("_plugin", u"VolatileEnvironment"),
        #             ("VolatileEnvironment IP Address", dict_values_data['VolatileEnvironmentIPAddress']),
        #             ("VolatileEnvironment Server", dict_values_data['VolatileEnvironmentServer']),
        #             ("VolatileEnvironmentSubnetMask", dict_values_data['VolatileEnvironmentSubnetMask']),
        #             ("Domain", dict_values_data['Domain']),
        #             ("Name Server", dict_values_data['NameServer']),
        #             ("Enable VolatileEnvironment", dict_values_data['EnableVolatileEnvironment']),
        #             ("VolatileEnvironmentConnForceBroadcastFlag", dict_values_data['VolatileEnvironmentConnForceBroadcastFlag']),
        #             ("Is Server NapAware", dict_values_data['IsServerNapAware']),
        #             ("Register Adapter Name", dict_values_data['RegisterAdapterName']),
        #             ("Registration Enabled", dict_values_data['RegistrationEnabled'])
        #
        #         ])
        #
        #         lst.append(u"{}".format(json.dumps(record, cls=ComplexEncoder)))
        else:
            logging.info(u"[{}] {} not found.".format('VolatileEnvironment', VolatileEnvironment_user_settings_path))
        #
        # return lst
