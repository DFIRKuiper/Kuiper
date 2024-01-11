import json
import logging
import traceback
from collections import OrderedDict
from lib.helper import convert_datetime
from lib.helper import ComplexEncoder
from lib.hive_yarp import get_hive
from yarp import *
from lib.helper import strip_control_characters
from construct import *


class Services():

    Service_Type = {
            0x1: "KernalDriver" , 
            0x2: "FileSystemDriver" , 
            0x4: "AdapterArguments", 
            0x8: "RecognizerDriver", 
            0x10: "Win32OwnProcess" , 
            0x20: "Win32ShareProcess",
            0x100: "InteractiveProcess"
        }

    


    # get map the service type with Service_Type 
    def get_service_type(self, data):
        s_type = []
        for i in self.Service_Type:
            if data & i:
                s_type.append(self.Service_Type[i])
        return '|'.join(s_type)

    def get_TriggerInfo_subkey(self, trigger_info_subkey):

        # trigger type
        TriggerType = {
            20 : 'CUSTOM',
            1 : 'DEVICE_INTERFACE_ARRIVAL',
            2 : 'IP_ADDRESS_AVAILABILITY',
            3 : 'DOMAIN_JOIN',
            4 : 'FIREWALL_PORT_EVENT',
            5 : 'GROUP_POLICY',
            6 : 'NETWORK_ENDPOINT'
        }

        # dwAction when triggered 
        Action = {
            1 : 'START_SERVICE',
            2 : 'STOP_SERVICE',
        }

        # list of pTriggerSubtype GUID 
        TriggerSubtype = {
            "1f81d131-3fac-4537-9e0c-7e7b0c2f4b55" : "NAMED_PIPE_EVENT",
            "bc90d167-9470-4139-a9ba-be0bbbf5b74d" : "RPC_INTERFACE_EVENT",
            "1ce20aba-9851-4421-9430-1ddeb766e809" : "DOMAIN_JOIN",
            "ddaf516e-58c2-4866-9574-c3b615d42ea1" : "DOMAIN_LEAVE",
            "b7569e07-8421-4ee0-ad10-86915afdad09" : "FIREWALL_PORT_OPEN",
            "a144ed38-8e12-4de4-9d96-e64740b1a524" : "FIREWALL_PORT_CLOSE",
            "659fcae6-5bdb-4da9-b1ff-ca2a178d46e0" : "MACHINE_POLICY_PRESENT",
            "4f27f2de-14e2-430b-a549-7cd48cbc8245" : "NETWORK_MANAGER_FIRST_IP_ADDRESS_ARRIVAL",
            "cc4ba62a-162e-4648-847a-b6bdf993e335" : "NETWORK_MANAGER_LAST_IP_ADDRESS_REMOVAL",
            "54fb46c8-f089-464c-b1fd-59d1b62c3b50" : "USER_POLICY_PRESENT",
            "18f4a5fd-fd3b-40a5-8fc2-e5d261c5d02e" : "ETW_PROVIDER",
            "d02a9c27-79b8-40d6-9b97-cf3f8b7b5d60" : "ETW_PROVIDER",
            "6863e644-dd5d-43a2-a8b5-7a81b46672e6" : "ETW_PROVIDER",
            "ce20d1c3-a247-4c41-bcb8-3c7f52c8b805" : "ETW_PROVIDER",
            "e46eead8-0c54-4489-9898-8fa79d059e0e" : "ETW_PROVIDER",
            "2e35aaeb-857f-4beb-a418-2e6c0e54d988" : "ETW_PROVIDER",
            "4d1e55b2-f16f-11cf-88cb-001111000030" : "DEVINTERFACE_HID",
            "53f56307-b6bf-11d0-94f2-00a0c91efb8b" : "DEVINTERFACE_DISK"
        }


        trigger_info  = {}
        for v in trigger_info_subkey.values():
            value_name = v.name().replace("." , "_")

            if value_name == "Type":
                trigger_info["Type"] = TriggerType[v.data()] if v.data() in TriggerType.keys() else str(v.data())
            elif value_name == "Action":
                trigger_info["Action"] = Action[v.data()]
            elif value_name == "GUID":

                guid_format = Struct(
                    "data1" / Int32ul,
                    "data2" / Int16ul,
                    "data3" / Int16ul,
                    "data4" / Int16ub,
                    "data5" / Bytes(6),
                )

                guid_struct = guid_format.parse(v.data())


                guid = hex(guid_struct.data1)[2:].zfill(8) + "-" + hex(guid_struct.data2)[2:].zfill(4) + "-" + hex(guid_struct.data3)[2:].zfill(4) + "-" + hex(guid_struct.data4)[2:].zfill(4) + "-" + guid_struct.data5.hex().zfill(12)
                
                trigger_info["SubType"] = TriggerSubtype[guid] if guid in TriggerSubtype.keys() else guid


        return trigger_info



    # get the data from the subkey "Parameters" for the service
    def get_service_parameters_subkey(self, service_parameters_key):
        parameters_dict = {}
        for v in service_parameters_key.values():
            value_name = v.name().replace("." , "_")
            if type(v.data()) == str:
                parameters_dict[value_name] = strip_control_characters(v.data())
            elif type(v.data()) == bytes:
                parameters_dict[value_name] = v.data().hex()
            elif type(v.data()) == list:
                parameters_dict[value_name] = "|".join([value.rstrip('\x00') for value in v.data() ])
            else:
                parameters_dict[value_name] = v.data()
                
        return parameters_dict



    # parse the FailureActions faild 
    def parse_SERVICE_FAILURE_ACTIONS(self, data):
        res_failure_actions = {}
        # mapping for SC_ACTION type
        SC_ACTION_Types = ['NONE' , 'RESTART' , 'REBOOT' , 'RUN_COMMAND']

        # _SERVICE_FAILURE_ACTIONSA
        SERVICE_FAILURE_ACTIONS_format = Struct( 
                'dwResetPeriod' / Int32ul,
                'lpRebootMsg' / Int32ul,
                'lpCommand'/ Int32ul,
                'cActions' / Int32ul,
                'lpsaActions' / Int32ul
            )
        
        # _SC_ACTION
        SC_ACTION_format = Struct(
                'Type' / Int32ul,
                'Delay' / Int32ul,
        )

        # parse the failure actions
        SERVICE_FAILURE_ACTIONS = SERVICE_FAILURE_ACTIONS_format.parse(data)

        # parse the array service controller actions
        array_SC_ACTIONS = []

        # the starting offset of the SC_ACTIONS array 
        array_SC_ACTIONS_data_offset = SERVICE_FAILURE_ACTIONS["lpsaActions"] if SERVICE_FAILURE_ACTIONS["lpsaActions"] != 0 else 0x14        

        # the SC_ACTIONS data
        data_SC_ACTIONs = data[array_SC_ACTIONS_data_offset:]
        
        # parse the SC_ACTIONS data into array of SC_ACTIONS
        for action in range(0 , len(data_SC_ACTIONs) , 8):
            action_data = data_SC_ACTIONs[action:action+8]
            SC_ACTION = SC_ACTION_format.parse(action_data)
            action_type = SC_ACTION_Types[SC_ACTION.Type] if SC_ACTION.Type < len(SC_ACTION_Types) else SC_ACTION.Type
            array_SC_ACTIONS.append( str(action_type) + '_' + str(SC_ACTION.Delay) + "millisec")
            
        
        # combine the array_SC_ACTIONS actions
        res_failure_actions["SC_ACTIONS"] = '|'.join(array_SC_ACTIONS)

        
        # parse the reset_period 
        res_failure_actions["ResetPeriod"] = "INFINITE" if SERVICE_FAILURE_ACTIONS["dwResetPeriod"] == 0xFFFFFFFF else str(SERVICE_FAILURE_ACTIONS["dwResetPeriod"]) + "s"
        
        

        # no needed since it will be included in the service registry value
        #res_failure_actions["Command"] = SERVICE_FAILURE_ACTIONS["lpCommand"]
        #res_failure_actions["RebootMsg"] = SERVICE_FAILURE_ACTIONS["lpRebootMsg"]

        return res_failure_actions

    def __init__(self,prim_hive,log_files):
        self.prim_hive = prim_hive
        self.log_files = log_files

    def run(self):
        lst = []
        # list of service data mapping
        Service_Start           = ['Boot' , 'System' , 'Automatic' , 'Manual' , 'Disabled' , "DelayedStart"]
        Service_ErrorControl    = ['Ignore' , 'Normal' , 'Severe' , 'Critical']
        Service_ServiceSidType  = ['NONE' , 'UNRESTRICTED' , 0 , 'RESTRICTED']

        hive = get_hive(self.prim_hive,self.log_files)
        ControlSet_Services_Paths = [] # this contains the list of paths for ControlSets

        main_key = hive.find_key("\\")
        for main_key_subkey in main_key.subkeys():
            if main_key_subkey.name().startswith("ControlSet"):
                ControlSet_Services_Paths.append(main_key_subkey.path() + "\\services")

        for ControlSet_Services_Path in ControlSet_Services_Paths:
            
            ControlSet_Services_Key = hive.find_key(ControlSet_Services_Path)
            
            
            if ControlSet_Services_Key:
                #print('Found a key: {}'.format(ControlSet_Services_Key.path()))
                timestamp = ControlSet_Services_Key.last_written_timestamp().isoformat()
                #print("timestamp: " + timestamp)

                for subkey in ControlSet_Services_Key.subkeys():
                    
                    service = {}
                    service['Name'] = subkey.name()
                    service['Path'] = subkey.path()
                    service["@timestamp"] = subkey.last_written_timestamp().isoformat()
                    values = list(subkey.values())
                    for v in values:
                        value_name = v.name().replace("." , "_")
                        #print(value_name + " ---> " + str(type(v.data())))
                        # get the start type if the value name is Start
                        if value_name == 'Start':
                            service[value_name] = Service_Start[v.data()]

                        # get the ErrorControl if the value name is ErrorControl
                        elif value_name == 'ErrorControl':
                            service[value_name] = Service_ErrorControl[v.data()]
                        
                        # get the ServiceSidType if the value name is ServiceSidType
                        elif value_name == 'ServiceSidType':
                            service[value_name] = Service_ServiceSidType[v.data()]


                        # parse the FailureActions field 
                        elif value_name == 'FailureActions':
                            failure_actions = self.parse_SERVICE_FAILURE_ACTIONS(v.data())
                            service[value_name] = failure_actions['SC_ACTIONS']
                            service["FailureCountResetPeriod"] = failure_actions['SC_ACTIONS']
                            
                        # get the service type if the value name is Type
                        elif value_name == 'Type':
                            service[value_name] = self.get_service_type(v.data())
                        
                        # if the data is a list, then combine the list
                        elif type(v.data()) == list:
                            service[value_name] = "|".join([strip_control_characters(element) for element in v.data() if element != "\x00"])
                        # if the data is str, ensure to strip null bytes
                        elif type(v.data()) == str:
                            service[value_name] = strip_control_characters(v.data())
                        elif type(v.data()) == bytes:
                            service[value_name] = v.data().hex()
                        else:
                            service[value_name] = v.data()


                    # check and retrive parameters subkey from the key
                    for service_subkey in subkey.subkeys():
                        if service_subkey.name() == 'Parameters':
                            service['Parameters'] = self.get_service_parameters_subkey(service_subkey)
                        elif service_subkey.name() == 'TriggerInfo':
                            triggers = {}
                            for trigger in service_subkey.subkeys():
                                triggers[str(len(triggers))] =  self.get_TriggerInfo_subkey(trigger)
                            service["TriggerInfo"] = triggers
                    
                    
                    #print(service)
                    print( json.dumps(service, indent=4, sort_keys=True) )
                    lst.append(service)
                    

            else:
                pass
        else:
            logging.info(u"[{}] {} not found.".format('Services', ControlSet_Services_Paths))

        print(len(lst))
        return lst
