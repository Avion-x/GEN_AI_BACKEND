import re
import pandas as pd
import numpy as np
import time
import datetime

class ChassisConfig:
    def __init__(self, router_name, dataframe_columns):
        
        self.router_name = router_name
        self.dataframe_columns = dataframe_columns

        dataframe_name = "fpcs"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name', 'fpc', 'pic', 'port', 'speed']
        
        self.fpcs = pd.DataFrame(columns= list_of_columns)
        self.fpcs.set_index(['router_name','fpc', 'pic', 'port'], inplace=True)

        dataframe_name = "configs"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['config' , 'key', 'value']

        self.configs = pd.DataFrame(columns= list_of_columns)
        self.configs.set_index(['router_name','config' , 'key'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_fpc(self, fpc, **kwargs):       
        fpc_index = (self.router_name, fpc, '-','-')
        for column, value in kwargs.items():
            if value is not None:
                self.fpcs.at[fpc_index, column] = value

    def add_pic(self, fpc, pic , **kwargs):      
        fpc_index = (self.router_name, fpc, pic,'-')
        for column, value in kwargs.items():
            if value is not None:
                self.fpcs.at[fpc_index, column] = value

    def add_port(self, fpc, pic, port, **kwargs):
        fpc_index = (self.router_name, fpc, pic, port)
        for column, value in kwargs.items():
            if value is not None:
                self.fpcs.at[fpc_index, column] = value

    def add_pic_tunnel_services(self, fpc, pic, bandwidth=None):
        self.add_pic( fpc, pic , tunnel_services = 'True')
        if bandwidth:
            self.add_pic( fpc, pic , bandwidth = bandwidth)

    def add_config(self, config, key, value):
        config_index=(self.router_name, config, key)
        if value is not None:
            column = 'value'
            self.configs.at[config_index,column] = value

        
    def __repr__(self):
        return f"ChassisConfig(fpcs={self.fpcs}, configs={self.configs})"


class InterfaceConfig:
    def __init__(self,  router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "interfaces"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns= ['router_name','interface_name', 'unit', 'channel', 'tunnel','interface_type', 'source', 'destination', 
                    'routing_instance','family_mpls','family_inet','family_inet6','family_ccc','inet_address','inet_primary','inet6_address','inet6_primary',
                    'iso_address', 'protocols', 
                    'esi', 'esi_id', 'esi_mode','encapsulation',
                    'rpf_check','fail_filter','mode',
                    'vrrp_group','vrrp_inet6_group',
                    'virtual_address','priority','accept_data','virtual_inet6_address',
                    'filter','input_list', 'output_list', 'vlan_id_list',
                    'vlan_tags', 'outer', 'inner','input',
                    'maximum_labels',
                    'load_balance', 'minimum_links','lacp_mode', 'lacp_transmission_rate',
                    'system_id', 'tolerance', 'anchor_point', 'ether_options',
                    'track', 'interface' ,'priority_cost'

                    ]
        self.interface_name = ''
        self.interfaces = pd.DataFrame( columns= list_of_columns )
        self.interfaces.set_index(['router_name', 'interface_name', 'unit'], inplace=True)
        self.configs = pd.DataFrame(columns=['config' , 'key', 'value'])

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_unit(self, interface_name, unit, ignore_duplicates=False, **kwargs):       
        interface_index = (self.router_name, interface_name, unit)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = interface_index in self.interfaces.index
                if record_exist and column in self.interfaces:
                    current_value = self.interfaces.loc[interface_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        if ignore_duplicates:
                            current_value_set = set(current_value)
                            # in case of 1 distinct value covert a list to a value
                            if len(current_value_set) ==1:
                                self.interfaces.at[interface_index, column] = value
                            else:
                                self.interfaces.at[interface_index, column] = list(current_value_set)
                        else:
                            self.interfaces.at[interface_index, column] = current_value
                    else:
                        self.interfaces.at[interface_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.interfaces.at[interface_index, column] = ""
                   self.interfaces.at[interface_index, column] = value

    def add_config(self, config, key, value):
        if value is not None:
            self.configs.loc[len(self.configs.index)] = [self.router_name, config,key,value]

    def get_channel_vlan_tag(self, interface_name):
        # this interface has a unit and a vlan_tag separated by . e.g. xe-5/1/1:0.3151
        if not pd.isnull(interface_name) and interface_name != '-':
            interface_id = interface_name.split(":")[0].split(".")[0]
            if len(interface_name.split(":")) ==2:
                if len(interface_name.split(":")[1].split(".")) ==2:
                    interface_id = interface_name.split(":")[0]
                    channel = interface_name.split(":")[1].split(".")[0]
                    vlan_tag = interface_name.split(":")[1].split(".")[1]
                    return interface_id, channel, vlan_tag
            return interface_id , None, None


    def get_interface_id(self, interface_name):
        interface_id, unit,vlan_tag,channel = None, None, None, None
        if not pd.isnull(interface_name) and interface_name != '-':
            interface_id = interface_name.split(":")[0].split(".")[0]           
            if len(interface_name.split(":")) ==2:
                interface_id, channel, vlan_tag = self.get_channel_vlan_tag(interface_name)
            else:    
                if len(interface_name.split(".")) ==2:
                    match interface_id[:2]:
                        case 'ae':
                            unit = interface_name.split(".")[1]
                        case 'ir':
                            vlan_tag = interface_name.split(".")[1]
                        case 'lo':
                            unit = interface_name.split(".")[1]
        return interface_id , unit,vlan_tag,channel
    
    def get_interface_fpc_pic_port(self, interface_name):
        # this interface has a channel separated by : e.g. xe-5/1/1
        interface_id, fpc, pic, port = None, None, None, None
        if not pd.isnull(interface_name) and interface_name != '-':
            interface_id = interface_name.split(":")[0].split(".")[0]
            if len(interface_id.split("-")) >= 2:
                if len(interface_id.split("-")[1].split("/")) ==3:
                    fpc = str(interface_id.split("-")[1].split("/")[0])
                    pic = str(interface_id.split("-")[1].split("/")[1])
                    port = str(interface_id.split("-")[1].split("/")[2])
        
        return interface_id, fpc, pic, port
    
    
    def update_data(self):
        print("Processing interface.update_data")
        self.interfaces.loc[self.interfaces.index.get_level_values('interface_name').str.startswith('gr'), 'interface_type'] = 'GRE Tunnel'
        self.interfaces.loc[self.interfaces.index.get_level_values('interface_name').str.startswith('et'), 'interface_type'] = 'Ethernet'
        self.interfaces.loc[self.interfaces.index.get_level_values('interface_name').str.startswith('ae'), 'interface_type'] = 'AE Interface'
        self.interfaces.loc[self.interfaces.index.get_level_values('interface_name').str.startswith('lo'), 'interface_type'] = 'Loopback Interface'
        self.interfaces.loc[self.interfaces.index.get_level_values('interface_name').str.startswith('vt'), 'interface_type'] = 'Virtual Tunnel Interface'
        self.interfaces.loc[self.interfaces.index.get_level_values('interface_name').str.startswith('xe'), 'interface_type'] = '10-Gigabit Ethernet'

        for index, row in self.interfaces.iterrows():
            router_name , interface_name, unit = index
            if pd.isnull(interface_name):
                interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                interface_id, fpc, pic, port =  self.get_interface_fpc_pic_port(interface_name)
                self.interfaces.at[index, 'interface_id'] = interface_id
                if not pd.isnull(fpc):
                    self.interfaces.at[index, 'fpc'] = fpc
                    self.interfaces.at[index, 'pic'] = pic
                    self.interfaces.at[index, 'port'] = port
                if not pd.isnull(channel):
                    self.interfaces.at[index, 'channel'] = channel
                if not pd.isnull(unit):
                    self.interfaces.at[index, 'unit'] = unit
                if not pd.isnull(vlan_tag):
                    self.interfaces.at[index, 'vlan_tag'] = vlan_tag

    def __repr__(self):
        return f"InterfaceConfig(interfaces={self.interfaces})"

class FirewallConfig:
    def __init__(self,  router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "filters"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns= ['router_name','filter_name', 'term', 'term_name',
                     'source', 'source_source_address', 'source_protocol', 'source_destination_address', 
                     'action', 'action_accept', 'action_count', 'action_discard', 'action_log'
                    ]

        self.filter_name = ''
        self.filters = pd.DataFrame(
            columns= list_of_columns)
        self.filters.set_index(['router_name','filter_name', 'term', 'term_name'], inplace=True)
        
        dataframe_name = "policers"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=  ['router_name','policer_name', 
                     'condition_if_exceeding', 'condition_filter_specific', 'condition_logical_interface_policer',
                     'action', 
                     'action_bandwidth_limit',
                     'action_burst_size_limit',
                     'action_loss_priority',
                     'action_forwarding_class',
                     'action_discard'
                    ]
        self.policers = pd.DataFrame(columns= list_of_columns)
        self.policers.set_index(['router_name','policer_name'], inplace=True)

        dataframe_name = "families"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=  ['router_name','family_name','filter_name', 'term_name', 'interface_specific',
                     'source', 'source_source_address', 'source_protocol', 'source_destination_address', 
                     'action', 'action_accept', 'action_count', 'action_discard', 'action_log'
                            ]

        self.families = pd.DataFrame(columns= list_of_columns)
        self.families.set_index(['router_name','family_name','filter_name', 'term_name'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_filter_source(self, filter_name, term, term_name,source, **kwargs):       
        filter_index = (self.router_name, filter_name, term, term_name)
        if source is not None:
            self.filters.loc[filter_index, 'source'] = source
        for column, value in kwargs.items():
            if value is not None:
                self.filters.loc[filter_index, column] = value
                
    def add_filter_action(self, filter_name, term, term_name,action, **kwargs):       
        filter_index = (self.router_name, filter_name, term, term_name)
        if action is not None:
            self.filters.loc[filter_index, 'action'] = action
        for column, value in kwargs.items():
            if value is not None:
                self.filters.loc[filter_index, column] = value

    def add_policer(self, policer_name, **kwargs):       
        policer_index = (self.router_name, policer_name)
        for column, value in kwargs.items():
            if value is not None:
                self.policers.loc[policer_index, column] = value

    def add_family(self, family_name,filter_name, term_name, **kwargs):       
        family_index = (self.router_name, family_name,filter_name, term_name)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = family_index in self.families.index
                if record_exist and column in self.families:
                    current_value = self.families.loc[family_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        self.families.at[family_index, column] = current_value
                    else:
                        self.families.at[family_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.families.at[family_index, column] = ""
                   self.families.at[family_index, column] = value

    def update_data(self):
        None

    def __repr__(self):
        return f"FirewallConfig(filters={self.filters}, policers={self.policers}, families={self.families})"

class ProtocolConfig:
    def __init__(self, router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "protocols"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns= ['router_name','protocol', 'config_name','config_value','config_type','config_type_name', 'family_type','interface_name',
                     'unit','vlan_tag']

        self.protocols = pd.DataFrame( columns= list_of_columns)
        self.protocols.set_index(['router_name','protocol',  'config_name','config_value','config_type','config_type_name','family_type','interface_name'], inplace=True)

        dataframe_name = "protocol_config_kv"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns= ['router_name','protocol', 'config_name', 'key','value',
                     'count']
        self.protocol_config_kv = pd.DataFrame(columns= list_of_columns)
        self.protocol_config_kv.astype({'count': 'int32'}).dtypes
        self.protocol_config_kv.set_index(['router_name','protocol', 'config_name', 'key','value'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_protocol_config_kv(self, protocol,config_name, key, value): 
        protocol_index = (self.router_name, protocol,config_name, key ,value)
        record_exist = protocol_index in self.protocols.index
        if record_exist:
            current_value = self.protocol_config_kv.loc[protocol_index]['count']
        else:
            current_value = 0
        current_value += 1
        self.protocol_config_kv.at[protocol_index, 'count'] = current_value
 

    def add_protocol(self, protocol,config_name,config_value,config_type, config_type_name, family_type,  ignore_duplicates=False, **kwargs): 
        interface_name = '-'
        protocol_index = (self.router_name, protocol,config_name,config_value,config_type,config_type_name, family_type,interface_name)
        for column, value in kwargs.items():
            if column not in self.protocols.columns:
                self.protocols[column]= ''
                self.protocols[column]=self.protocols[column].astype(str)
                
            if value is not None :
                record_exist = protocol_index in self.protocols.index
                if record_exist and column in self.protocols:
                    current_value = self.protocols.loc[protocol_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        if ignore_duplicates:
                            current_value_set = set(current_value)
                            # in case of 1 distinct value covert a list to a value
                            if len(current_value_set) ==1:
                                self.protocols.at[protocol_index, column] = value
                            else:
                                self.protocols.at[protocol_index, column] = list(current_value_set)
                        else:
                            self.protocols.at[protocol_index, column] = current_value
                    else:
                        self.protocols.at[protocol_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.protocols.at[protocol_index, column] = ""
                   self.protocols.at[protocol_index, column] = value

    def add_protocol_interface(self, protocol,interface_name,config_name,config_value, config_type, config_type_name, family_type="-", ignore_duplicates=False, **kwargs): 
        protocol_index = (self.router_name, protocol,config_name,config_value,config_type,config_type_name, family_type,interface_name)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = protocol_index in self.protocols.index
                if record_exist and column in self.protocols:
                    current_value = self.protocols.loc[protocol_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        if ignore_duplicates:
                            current_value_set = set(current_value)
                            # in case of 1 distinct value covert a list to a value
                            if len(current_value_set) ==1:
                                self.protocols.at[protocol_index, column] = value
                            else:
                                self.protocols.at[protocol_index, column] = list(current_value_set)
                        else:
                            self.protocols.at[protocol_index, column] = current_value
                    else:
                        self.protocols.at[protocol_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.protocols.at[protocol_index, column] = ""
                   self.protocols.at[protocol_index, column] = value

    def get_channel_vlan_tag(self, interface_name):
        # this interface has a unit and a vlan_tag separated by . e.g. xe-5/1/1:0.3151
        if not pd.isnull(interface_name) and interface_name != '-':
            interface_id = interface_name.split(":")[0].split(".")[0]
            if len(interface_name.split(":")) ==2:
                if len(interface_name.split(":")[1].split(".")) ==2:
                    interface_id = interface_name.split(":")[0]
                    channel = interface_name.split(":")[1].split(".")[0]
                    vlan_tag = interface_name.split(":")[1].split(".")[1]
                    return interface_id, channel, vlan_tag
            return interface_id , None, None


    def get_interface_id(self, interface_name):
        interface_id, unit,vlan_tag,channel = None, None, None, None
        if not pd.isnull(interface_name) and interface_name != '-':
            interface_id = interface_name.split(":")[0].split(".")[0]           
            if len(interface_name.split(":")) ==2:
                interface_id, channel, vlan_tag = self.get_channel_vlan_tag(interface_name)
            else:    
                if len(interface_name.split(".")) ==2:
                    match interface_id[:2]:
                        case 'ae':
                            unit = interface_name.split(".")[1]
                        case 'ir':
                            vlan_tag = interface_name.split(".")[1]
                        case 'lo':
                            unit = interface_name.split(".")[1]
        return interface_id , unit,vlan_tag,channel
    
    def get_interface_fpc_pic_port(self, interface_name):
        # this interface has a channel separated by : e.g. xe-5/1/1
        interface_id, fpc, pic, port = None, None, None, None
        if not pd.isnull(interface_name) and interface_name != '-':
            interface_id = interface_name.split(":")[0].split(".")[0]
            if len(interface_id.split("-")) >= 2:
                if len(interface_id.split("-")[1].split("/")) ==3:
                    fpc = str(interface_id.split("-")[1].split("/")[0])
                    pic = str(interface_id.split("-")[1].split("/")[1])
                    port = str(interface_id.split("-")[1].split("/")[2])
        
        return interface_id, fpc, pic, port


    def update_data(self):
        for index, row in self.protocols.iterrows():
            router_name, protocol,config_name,config_value,config_type,config_type_name, family_type,interface_name = index
            if not pd.isnull(interface_name) and interface_name != '-':
                interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                interface_id, fpc, pic, port =  self.get_interface_fpc_pic_port(interface_name)
                self.protocols.at[index, 'interface_id'] = interface_id
                if not pd.isnull(fpc):
                    self.protocols.at[index, 'fpc'] = fpc
                    self.protocols.at[index, 'pic'] = pic
                    self.protocols.at[index, 'port'] = port
                if not pd.isnull(channel):
                    self.protocols.at[index, 'channel'] = channel
                if not pd.isnull(unit):
                    self.protocols.at[index, 'unit'] = unit
                if not pd.isnull(vlan_tag):
                    self.protocols.at[index, 'vlan_tag'] = vlan_tag
            else:
                if not pd.isnull(row['interface']):
                    interface_id, unit,vlan_tag, channel  = self.get_interface_id(row['interface'])
                    interface_id, fpc, pic, port =  self.get_interface_fpc_pic_port(row['interface'])
                    self.protocols.at[index, 'interface_id'] = interface_id
                    if not pd.isnull(fpc):
                        self.protocols.at[index, 'fpc'] = fpc
                        self.protocols.at[index, 'pic'] = pic
                        self.protocols.at[index, 'port'] = port
                    if not pd.isnull(channel):
                        self.protocols.at[index, 'channel'] = channel
                    if not pd.isnull(unit):
                        self.protocols.at[index, 'unit'] = unit
                    if not pd.isnull(vlan_tag):
                        self.protocols.at[index, 'vlan_tag'] = vlan_tag


    def __repr__(self):
        return f"ProtocolConfig(protocols={self.protocols}, protocol_config_kv ={self.protocol_config_kv} )"

class BridgeDomainConfig:
    def __init__(self,  router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "bridgedomains"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns= ['router_name','bridgedomain_name', 
                     'domain_type']

        self.bridgedomains = pd.DataFrame(columns= list_of_columns)
        self.bridgedomains.set_index(['router_name','bridgedomain_name'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_bridgedomain(self, bridgedomain_name, **kwargs):       
        bridgedomain_index = (self.router_name, bridgedomain_name)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = bridgedomain_index in self.bridgedomains.index
                if record_exist and column in self.bridgedomains:
                    current_value = self.bridgedomains.loc[bridgedomain_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        self.bridgedomains.at[bridgedomain_index, column] = current_value
                    else:
                        self.bridgedomains.at[bridgedomain_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.bridgedomains.at[bridgedomain_index, column] = ""
                   self.bridgedomains.at[bridgedomain_index, column] = value

    def update_data(self):
        None

    def __repr__(self):
        return f"BridgeDomainConfig(bridgedomains={self.bridgedomains})"


class ServiceConfig:
    def __init__(self,  router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "services"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns= ['router_name','service_type', 'version', 'template',
                     'nexthop_learning']

        self.services = pd.DataFrame(columns= list_of_columns)
        self.services.set_index(['router_name','service_type', 'version', 'template'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_service(self, service_type, version, template, **kwargs):       
        service_index = (self.router_name, service_type, version, template)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = service_index in self.services.index
                if record_exist and column in self.services:
                    current_value = self.services.loc[service_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        self.services.at[service_index, column] = current_value
                    else:
                        self.services.at[service_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.services.at[service_index, column] = ""
                   self.services.at[service_index, column] = value

    def update_data(self):
        None

    def __repr__(self):
        return f"ServiceConfig(services={self.services})"

class RoutingInstanceConfig:
    def __init__(self,  router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "routing_instances"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','routing_instance','config_name','config_value','config_type','config_type_name',
                     'instance_type','interface','unit','vlan_tag'] 

        self.routing_instances = pd.DataFrame(columns= list_of_columns)
        self.routing_instances.set_index(['router_name','routing_instance','config_name','config_value','config_type','config_type_name'], inplace=True)

        dataframe_name = "routing_instances_config_kv"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','routing_instance', 'config_name', 'key','value',
                     'count'] 

        self.routing_instances_config_kv = pd.DataFrame(columns=list_of_columns)
        self.routing_instances_config_kv.astype({'count': 'int32'}).dtypes
        self.routing_instances_config_kv.set_index(['router_name','routing_instance', 'config_name', 'key','value'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_routing_instance_config_kv(self, routing_instance,config_name, key, value): 
        routing_instance_index = (self.router_name, routing_instance,config_name, key ,value)
        record_exist = routing_instance_index in self.routing_instances_config_kv.index
        if record_exist:
            current_value = self.routing_instances_config_kv.loc[routing_instance_index]['count']
        else:
            current_value = 0
        current_value += 1
        self.routing_instances_config_kv.at[routing_instance_index, 'count'] = current_value


    def add_routing_instance(self, routing_instance,config_name,config_value,config_type, config_type_name,ignore_duplicates=False, **kwargs):       
        routing_instance_index = (self.router_name, routing_instance ,config_name,config_value,config_type,config_type_name)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = routing_instance_index in self.routing_instances.index
                if record_exist and column in self.routing_instances:
                    current_value = self.routing_instances.loc[routing_instance_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        if ignore_duplicates:
                            current_value_set = set(current_value)
                            # in case of 1 distinct value covert a list to a value
                            if len(current_value_set) ==1:
                                self.routing_instances.at[routing_instance_index, column] = value
                            else:
                                self.routing_instances.at[routing_instance_index, column] = list(current_value_set)
                        else:
                            self.routing_instances.at[routing_instance_index, column] = current_value
                    else:
                        self.routing_instances.at[routing_instance_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.routing_instances.at[routing_instance_index, column] = ""
                   self.routing_instances.at[routing_instance_index, column] = value

    def update_data(self):
        None

    def __repr__(self):
        return f"RoutingInstanceConfig(routing_instances={self.routing_instances}, routing_instances_config_kv ={self.routing_instances_config_kv})"

class PolicyOptionConfig:
    def __init__(self,  router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "policy_options"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','policy_option','config_name','config_value','config_type','config_type_name',
                     'count'] 

        self.policy_options = pd.DataFrame( columns= list_of_columns)
        self.policy_options.set_index(['router_name','policy_option','config_name','config_value','config_type','config_type_name'], inplace=True)

        dataframe_name = "policy_options_config_kv"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','policy_option', 'config_name', 'key','value',
                     'count'] 

        self.policy_options_config_kv = pd.DataFrame(columns=list_of_columns)
        self.policy_options_config_kv.astype({'count': 'int32'}).dtypes
        self.policy_options_config_kv.set_index(['router_name','policy_option', 'config_name', 'key','value'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_policy_option_config_kv(self, policy_option,config_name, key, value): 
        policy_option_index = (self.router_name, policy_option,config_name, key ,value)
        record_exist = policy_option_index in self.policy_options_config_kv.index
        if record_exist:
            current_value = self.policy_options_config_kv.loc[policy_option_index]['count']
        else:
            current_value = 0
        current_value += 1
        self.policy_options_config_kv.at[policy_option_index, 'count'] = current_value


    def add_policy_option(self, policy_option,config_name,config_value,config_type, config_type_name,ignore_duplicates=False, **kwargs):       
        policy_option_index = (self.router_name, policy_option ,config_name,config_value,config_type,config_type_name)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = policy_option_index in self.policy_options.index
                if record_exist and column in self.policy_options:
                    current_value = self.policy_options.loc[policy_option_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        if ignore_duplicates:
                            current_value_set = set(current_value)
                            # in case of 1 distinct value covert a list to a value
                            if len(current_value_set) ==1:
                                self.policy_options.at[policy_option_index, column] = value
                            else:
                                self.policy_options.at[policy_option_index, column] = list(current_value_set)
                        else:
                            self.policy_options.at[policy_option_index, column] = current_value
                    else:
                        self.policy_options.at[policy_option_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.policy_options.at[policy_option_index, column] = ""
                   self.policy_options.at[policy_option_index, column] = value

    def update_data(self):
        None

    def __repr__(self):
        return f"PolicyOptionConfig(policy_options={self.policy_options}, policy_options_config_kv ={self.policy_options_config_kv})"

class ClassOfServiceConfig:
    def __init__(self, router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "class_of_services"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','class_of_service_name','config_name','config_value','config_type','config_type_name',
                     'count'] 

        self.class_of_services = pd.DataFrame(columns= list_of_columns )
        self.class_of_services.set_index(['router_name','class_of_service_name','config_name','config_value','config_type','config_type_name'], inplace=True)

        dataframe_name = "class_of_services_config_kv"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','class_of_service_name', 'config_name', 'key','value',
                     'count'] 


        self.class_of_services_config_kv = pd.DataFrame(columns= list_of_columns )
        self.class_of_services_config_kv.astype({'count': 'int32'}).dtypes
        self.class_of_services_config_kv.set_index(['router_name','class_of_service_name', 'config_name', 'key','value'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_class_of_service_config_kv(self, class_of_service_name, config_name, key, value): 

        class_of_service_index = (self.router_name, class_of_service_name, config_name, key ,value)
        
        record_exist = class_of_service_index in self.class_of_services_config_kv.index
        if record_exist:
            current_value = self.class_of_services_config_kv.loc[class_of_service_index]['count']
        else:
            current_value = 0
        current_value += 1
        self.class_of_services_config_kv.at[class_of_service_index, 'count'] = current_value


    def add_class_of_service(self, class_of_service_name, config_name,config_value,config_type, config_type_name,ignore_duplicates=False, **kwargs):       
        class_of_service_index = (self.router_name, class_of_service_name ,config_name,config_value,config_type,config_type_name)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = class_of_service_index in self.class_of_services.index
                if record_exist and column in self.class_of_services:
                    current_value = self.class_of_services.loc[class_of_service_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        if ignore_duplicates:
                            current_value_set = set(current_value)
                            # in case of 1 distinct value covert a list to a value
                            if len(current_value_set) ==1:
                                self.class_of_services.at[class_of_service_index, column] = value
                            else:
                                self.class_of_services.at[class_of_service_index, column] = list(current_value_set)
                        else:
                            self.class_of_services.at[class_of_service_index, column] = current_value
                    else:
                        self.class_of_services.at[class_of_service_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.class_of_services.at[class_of_service_index, column] = ""
                   self.class_of_services.at[class_of_service_index, column] = value

    def update_data(self):
        None

    def __repr__(self):
        return f"ClassOfServiceConfig(class_of_services={self.class_of_services}, class_of_services_config_kv ={self.class_of_services_config_kv})"

class RoutingOptionConfig:
    def __init__(self,  router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "routing_options"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','routing_option','config_name','config_value','config_type','config_type_name',
                     'count']  

        self.routing_options = pd.DataFrame(
            columns= list_of_columns)
        self.routing_options.set_index(['router_name','routing_option','config_name','config_value','config_type','config_type_name'], inplace=True)

        dataframe_name = "routing_options_config_kv"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','routing_option', 'config_name', 'key','value',
                     'count'] 

        self.routing_options_config_kv = pd.DataFrame(
            columns=list_of_columns)
        self.routing_options_config_kv.astype({'count': 'int32'}).dtypes
        self.routing_options_config_kv.set_index(['router_name','routing_option', 'config_name', 'key','value'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_routing_option_config_kv(self, routing_option,config_name, key, value): 
        routing_option_index = (self.router_name, routing_option,config_name, key ,value)
        record_exist = routing_option_index in self.routing_options_config_kv.index
        if record_exist:
            current_value = self.routing_options_config_kv.loc[routing_option_index]['count']
        else:
            current_value = 0
        current_value += 1
        self.routing_options_config_kv.at[routing_option_index, 'count'] = current_value


    def add_routing_option(self, routing_option,config_name,config_value,config_type, config_type_name,ignore_duplicates=False, **kwargs):       
        routing_option_index = (self.router_name, routing_option ,config_name,config_value,config_type,config_type_name)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = routing_option_index in self.routing_options.index
                if record_exist and column in self.routing_options:
                    current_value = self.routing_options.loc[routing_option_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        if ignore_duplicates:
                            current_value_set = set(current_value)
                            # in case of 1 distinct value covert a list to a value
                            if len(current_value_set) ==1:
                                self.routing_options.at[routing_option_index, column] = value
                            else:
                                self.routing_options.at[routing_option_index, column] = list(current_value_set)
                        else:
                            self.routing_options.at[routing_option_index, column] = current_value
                    else:
                        self.routing_options.at[routing_option_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.routing_options.at[routing_option_index, column] = ""
                   self.routing_options.at[routing_option_index, column] = value

    def update_data(self):
        None

    def __repr__(self):
        return f"RoutingOptionConfig(routing_options={self.routing_options}, routing_options_config_kv ={self.routing_options_config_kv})"

class ForwardingOptionConfig:
    def __init__(self,  router_name, dataframe_columns):

        self.router_name = router_name
        self.dataframe_columns = dataframe_columns
        
        dataframe_name = "forwarding_options"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','forwarding_option','config_name','config_value','config_type','config_type_name',
                     'count']  

        self.forwarding_options = pd.DataFrame(
            columns=list_of_columns)
        self.forwarding_options.set_index(['router_name','forwarding_option','config_name','config_value','config_type','config_type_name'], inplace=True)


        dataframe_name = "forwarding_options_config_kv"
        list_of_columns = self.get_dataframe_columns(dataframe_name)
        if len(list_of_columns) ==0:
            list_of_columns=['router_name','forwarding_option', 'config_name', 'key','value',
                     'count']  

        self.forwarding_options_config_kv = pd.DataFrame(
            columns= list_of_columns )
        self.forwarding_options_config_kv.astype({'count': 'int32'}).dtypes
        self.forwarding_options_config_kv.set_index(['router_name','forwarding_option', 'config_name', 'key','value'], inplace=True)

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns

    def add_forwarding_option_config_kv(self, forwarding_option,config_name, key, value): 
        forwarding_option_index = (self.router_name, forwarding_option,config_name, key ,value)
        record_exist = forwarding_option_index in self.forwarding_options_config_kv.index
        if record_exist:
            current_value = self.forwarding_options_config_kv.loc[forwarding_option_index]['count']
        else:
            current_value = 0
        current_value += 1
        self.forwarding_options_config_kv.at[forwarding_option_index, 'count'] = current_value


    def add_forwarding_option(self, forwarding_option,config_name,config_value,config_type, config_type_name,ignore_duplicates=False, **kwargs):       
        forwarding_option_index = (self.router_name, forwarding_option ,config_name,config_value,config_type,config_type_name)
        for column, value in kwargs.items():
            if value is not None :
                record_exist = forwarding_option_index in self.forwarding_options.index
                if record_exist and column in self.forwarding_options:
                    current_value = self.forwarding_options.loc[forwarding_option_index][column]
                    if type(current_value) != list:
                        if type(current_value) == float:
                            if not np.isnan(current_value):
                                current_value = [current_value]
                        if type(current_value) == str:
                            if current_value:
                                current_value = [current_value]
                    if type(current_value) == list:
                        current_value.append(value)
                        if ignore_duplicates:
                            current_value_set = set(current_value)
                            # in case of 1 distinct value covert a list to a value
                            if len(current_value_set) ==1:
                                self.forwarding_options.at[forwarding_option_index, column] = value
                            else:
                                self.forwarding_options.at[forwarding_option_index, column] = list(current_value_set)
                        else:
                            self.forwarding_options.at[forwarding_option_index, column] = current_value
                    else:
                        self.forwarding_options.at[forwarding_option_index, column] = value
                else:
                   ## if we do not initialize with str and try to update list
                   ## it results in error "Must have equal len keys and value when setting with an iterable"
                   if type(value) == list:
                        self.forwarding_options.at[forwarding_option_index, column] = ""
                   self.forwarding_options.at[forwarding_option_index, column] = value

    def update_data(self):
        None

    def __repr__(self):
        return f"ForwardingOptionConfig(forwarding_options={self.forwarding_options}, forwarding_options_config_kv ={self.forwarding_options_config_kv})"



class RouterConfig:
    def __init__(self, name, dataframe_columns):
        self.name = name
        self.dataframe_columns = dataframe_columns
        self.chassis = ChassisConfig(self.name, self.dataframe_columns)
        self.interface = InterfaceConfig(self.name, self.dataframe_columns)
        self.firewall = FirewallConfig(self.name, self.dataframe_columns)
        self.protocol = ProtocolConfig(self.name, self.dataframe_columns)
        self.routing_instance = RoutingInstanceConfig(self.name, self.dataframe_columns)
        self.service = ServiceConfig(self.name, self.dataframe_columns)
        self.bridgedomain = BridgeDomainConfig(self.name, self.dataframe_columns)
        self.policy_option = PolicyOptionConfig(self.name, self.dataframe_columns)
        self.class_of_service = ClassOfServiceConfig(self.name, self.dataframe_columns)
        self.routing_option = RoutingOptionConfig(self.name, self.dataframe_columns)
        self.forwarding_option = ForwardingOptionConfig(self.name, self.dataframe_columns)
        
    def __repr__(self):
        return f"RouterConfig(name={self.name}, chassis={self.chassis}, interfaces={self.interface}, filewalls={self.firewall}, protocols={self.protocol})"

class NetworkConfig:
    def __init__(self):
        self.routers = {}

    def add_router(self, router_name, dataframe_columns):
        if router_name not in self.routers:
            self.routers[router_name] = RouterConfig(router_name, dataframe_columns)

    def get_router(self, router_name):
        return self.routers.get(router_name)

    def get_router_config(self, router_name):
        return self.routers[router_name]

    def __repr__(self):
        return f"NetworkConfig(routers={self.routers})"


class NetworkConfigParser:
    def __init__(self, config_file,dataframe_columns_file):
        self.config_file = config_file
        self.dataframe_columns_file = dataframe_columns_file
        self.dataframe_columns =[]
        self.network_config = NetworkConfig()
        self.interfaces = {}
        self.vlans = {}
        self.protocols = {}
        self.lineno = 0
        self.parsed = 0
        self.config_row = pd.Series()
        self.files = []
        self.column_in_config_file = 30

    def row_to_string(data_series, columns_in_row):
        data_string = [str(item) for item in data_series.values.tolist()[:columns_in_row] if not (isinstance(item, float) and np.isnan(item))]
        result_string = " ".join(data_string)
        return result_string


    def get_columns_with_a_char_as_list(self, data_series,columns_in_row, opening_bracket = '"', closing_bracket = '"'):
        
        data_notnull = [str(item) for item in data_series.values.tolist()[:columns_in_row] if not (isinstance(item, float) and np.isnan(item))]
        data_containg_substr = [str(item) for item in data_notnull if item.find('"') >= 0]
        row=data_series.to_frame().transpose()
        first_column = row.columns[(row == data_containg_substr[0]).iloc[0]]
        last_column = row.columns[(row == data_containg_substr[1]).iloc[0]]
        if any(first_column) & any(last_column):
            start = row.columns.get_loc(first_column[0])
            end = row.columns.get_loc(last_column[0])
            values_list = []
            ## Include both first and last column in the list
            for i in range(start, end +1):
                values_list.append(row[row.columns[i]].iloc[0])
        return values_list, end + 1 ## add 1 as list starts from index 0

    def get_columns_data_as_list(self,data_series, opening_bracket = '[', closing_bracket = ']'):
        row=data_series.to_frame().transpose()
        first_column = row.columns[(row == "[").iloc[0]]
        last_column = row.columns[(row == "]").iloc[0]]
        values_list = []
        if any(first_column) & any(last_column):
            start = row.columns.get_loc(first_column[0])
            end = row.columns.get_loc(last_column[0])
            for i in range(start +1, end):
                values_list.append(row[row.columns[i]].iloc[0])
        return values_list, end + 1 ## add 1 as list starts from index 0

    def get_interface_fpc_pic_port(self, interface_name):
        # this interface has a channel separated by : e.g. xe-5/1/1
        interface_id = interface_name.split(":")[0].split(".")[0]
        if len(interface_id.split("-")) >= 2:
            if len(interface_id.split("-")[1].split("/")) ==3:
                fpc = str(interface_id.split("-")[1].split("/")[0])
                pic = str(interface_id.split("-")[1].split("/")[1])
                port = str(interface_id.split("-")[1].split("/")[2])
                return interface_id, fpc, pic, port
            else:
                return interface_id, None, None, None
        else:
            return interface_id, None, None, None
    
    def get_interface_channel(self, interface_name):
        # this interface has a channel separated by : e.g. xe-5/1/1:1
        if len(interface_name.split(":")) ==2:
            channel = interface_name.split(":")[1]
            return channel
        return None

    def get_channel_vlan_tag(self, interface_name):
        # this interface has a unit and a vlan_tag separated by . e.g. xe-5/1/1:0.3151
        interface_id = interface_name.split(":")[0].split(".")[0]
        if len(interface_name.split(":")) ==2:
            if len(interface_name.split(":")[1].split(".")) ==2:
                interface_id = interface_name.split(":")[0]
                channel = interface_name.split(":")[1].split(".")[0]
                vlan_tag = interface_name.split(":")[1].split(".")[1]
                return interface_id, channel, vlan_tag
        return interface_id , None, None

    def get_interface_id(self, interface_name):

        interface_id = interface_name.split(":")[0].split(".")[0]
        unit,vlan_tag,channel = None, None, None
        if len(interface_name.split(":")) ==2:
            interface_id, channel, vlan_tag = self.get_channel_vlan_tag(interface_name)
        else:    
            if len(interface_name.split(".")) ==2:
                match interface_id[:2]:
                    case 'ae':
                        unit = interface_name.split(".")[1]
                    case 'ir':
                        vlan_tag = interface_name.split(".")[1]
                    case 'lo':
                        unit = interface_name.split(".")[1]
        return interface_id , unit,vlan_tag,channel


    def get_unit_vlan_tag(self, interface_name):
        # this interface has a unit and a vlan_tag separated by . e.g. xe-5/1/1:0.3151
        if len(interface_name.split(":")) ==2:
            if len(interface_name.split(":")[1].split(".")) ==2:
                unit = interface_name.split(":")[1].split(".")[0]
                vlan_tag = interface_name.split(":")[1].split(".")[1]
                return unit, vlan_tag
        return None , None

    def get_dataframe_columns(self, dataframe_name):
        columns = self.dataframe_columns[self.dataframe_columns['dataframe_name'] == dataframe_name]['column_name'].values
        columns.sort()
        return columns
    
    def parse(self):
        
        config_data = pd.read_csv(self.config_file, low_memory=False)
        self.dataframe_columns = pd.read_csv(self.dataframe_columns_file, low_memory=False)

        self.files = [file[0:3].replace("_","") for file in config_data["File"].unique()]
        print(self.files)
        if len(config_data.columns) == self.column_in_config_file:
            config_data['Parsed'] = 0
            config_data['Size'] = 0
            config_data['Parsed_size'] = 0
        print(config_data[(config_data["Parsed"]==0) ][["Command","Parsed"]].value_counts())
#        print(config_data[(config_data["Parsed"]==0) & (config_data["Command"]=='routing-instances')][["Command","Name","Parsed"]].value_counts())
            
           
        for self.lineno, self.config_row in config_data[config_data["Parsed"]==0].iterrows(): 
            self.parsed = 0
            ## 4 Base columns + 26 Arg + 3 Parsing Status columns
            ## Reduce 3 parsing columns from total as these are always nut null
            self.config_row["Size"]=self.config_row.value_counts().sum() - 3 
            self._parse_config()
            
            if  self.config_row["Size"] == self.config_row["Parsed_size"]:
                self.config_row["Parsed"] = 1 
            config_data.loc[self.lineno,"Parsed"] = self.config_row["Parsed"]
            config_data.loc[self.lineno,"Size"] = self.config_row["Size"]
            config_data.loc[self.lineno,"Parsed_size"] = self.config_row["Parsed_size"]
    
        print(config_data[(config_data["Parsed"]==0) ][["Command","Parsed"]].value_counts())
#        print(config_data[(config_data["Parsed"]==0) & (config_data["Command"]=='routing-instances')][["Command","Name","Parsed"]].value_counts())
        config_data.to_csv(r'data\combined_data_new.csv', index=False)

    def _parse_config(self):
        # Extract router names and their respective configurations
        filename= self.config_row['File'][0:3].replace('_',"")
        self.network_config.add_router(filename, self.dataframe_columns)      
        router = self.network_config.get_router(filename)
        # remember to return object from function _parse_<object>
        development = 'N'
        if development == 'Y':
            match (self.config_row['Command']):
                case "protocols":
                    router.protocol = self._parse_protocol(router.protocol)
        else:
            match (self.config_row['Command']):
                case 'interfaces':
                    router.interface = self._parse_interfaces(router.interface)
                case "chassis":
                    router.chassis = self._parse_chassis(router.chassis)
                case "firewall":
                    router.firewall = self._parse_firewall(router.firewall)
                case "services":
                    router.service = self._parse_service(router.service)
                case "protocols":
                    router.protocol = self._parse_protocol(router.protocol)
                case "routing-instances":
                    router.routing_instance = self._parse_routing_instance(router.routing_instance)
                case "policy-options":
                    router.policy_option = self._parse_policy_option(router.policy_option)
                case "bridge-domains":
                    router.bridgedomain = self._parse_bridgedomain(router.bridgedomain)
                case "class-of-service":
                    router.class_of_service = self._parse_class_of_service(router.class_of_service)
                case "routing-options":
                    router.routing_option = self._parse_routing_options(router.routing_option)
                case "forwarding-options":
                    router.forwarding_option = self._parse_forwarding_options(router.forwarding_option)
                case _:
                    None
                    

#     routing-instances     75246
#     protocols             44079
#     interfaces            37405
#     policy-options        35488
#     bridge-domains         7100
#     firewall               1779
#     class-of-service       1469
#     chassis                 490
#     routing-options         330
#     forwarding-options       99
#     services                 60 
    def _parse_forwarding_options(self, forwarding_option):
        config_name = '-'
        config_value = '-'
        config_type = '-'
        config_type_name = '-'
        forwarding_option_name = self.config_row['Name']
        match self.config_row['Name']:
            case 'sampling':
                match self.config_row['Arg1']:
                    case 'instance':
                        forwarding_option_name = self.config_row['Name'] + ' ' + self.config_row['Arg1']
                        config_name = self.config_row['Arg2']
                        match self.config_row['Arg3']:
                            case 'input':
                                match self.config_row['Arg4']:
                                    case 'rate':
                                        key = self.config_row['Arg3']  + ' ' + self.config_row['Arg4']
                                        value = self.config_row['Arg5']
                                        forwarding_option.add_forwarding_option_config_kv(forwarding_option_name , config_name, key, value)
                                        self.config_row["Parsed_size"]  = 9
                            case 'family':
                                config_type = self.config_row['Arg3']
                                config_type_name = self.config_row['Arg4']
                                family = self.config_row['Arg4']
                                match self.config_row['Arg5']:
                                    case 'output':
                                        output = 'True'
                                        forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, output = output)
                                        self.config_row["Parsed_size"]  = 9
                                        match self.config_row['Arg6']:
                                            case 'flow-server':
                                                flow_server =  self.config_row['Arg7']
                                                forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, flow_server = flow_server)
                                                self.config_row["Parsed_size"]  = 11
                                                match self.config_row['Arg8']:
                                                    case 'port':
                                                        port = self.config_row['Arg9']
                                                        forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, port = port)
                                                        self.config_row["Parsed_size"]  = 13
                                                    case 'forwarding-class':
                                                        forwarding_class = self.config_row['Arg9']
                                                        forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, forwarding_class = forwarding_class)
                                                        self.config_row["Parsed_size"]  = 13
                                                    case 'version9':
                                                        version9 = 'True'
                                                        forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, version9 = version9)
                                                        self.config_row["Parsed_size"]  = 13
                                                        match self.config_row['Arg9']:
                                                            case 'template':
                                                                template = self.config_row['Arg10']
                                                                forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, template = template)
                                                                self.config_row["Parsed_size"]  = 14
                                            case 'inline-jflow':                                                                
                                                inline_jflow =  'True'
                                                forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, inline_jflow = inline_jflow)
                                                self.config_row["Parsed_size"]  = 11
                                                match self.config_row['Arg7']:
                                                    case 'source-address':
                                                        source_address =  self.config_row['Arg8']
                                                        forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, source_address = source_address)
                                                        self.config_row["Parsed_size"]  = 12
            case 'enhanced-hash-key':
                forwarding_option_name = self.config_row['Name']
                enhanced_hash_key = 'True'
                match self.config_row['Arg1']:
                    case 'family':
                        config_type = self.config_row['Arg1']
                        config_type_name = self.config_row['Arg2']
                        family = self.config_row['Arg2']
                        forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, enhanced_hash_key = enhanced_hash_key)
                        self.config_row["Parsed_size"]  = 6
                        match self.config_row['Arg3']:
                            case 'incoming-interface-index':
                                incoming_interface_index = 'True'
                                forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, incoming_interface_index = incoming_interface_index)
                                self.config_row["Parsed_size"]  = 7
            case 'rpf-loose-mode-discard':
                forwarding_option_name = self.config_row['Name']
                rpf_loose_mode_discard = 'True'
                match self.config_row['Arg1']:
                    case 'family':
                        config_type = self.config_row['Arg1']
                        config_type_name = self.config_row['Arg2']
                        family = self.config_row['Arg2']
                        forwarding_option.add_forwarding_option(forwarding_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, rpf_loose_mode_discard = rpf_loose_mode_discard)
                        self.config_row["Parsed_size"]  = 6
            case 'load-balance-label-capability':
                config_name = self.config_row['Name']
                key = self.config_row['Name']
                value = 'True'
                forwarding_option.add_forwarding_option_config_kv(forwarding_option_name , config_name, key, value)
                self.config_row["Parsed_size"]  = 4

        return forwarding_option

    def _parse_routing_options(self, routing_option):
        config_name = '-'
        config_value = '-'
        config_type = '-'
        config_type_name = '-'
        routing_option_name = self.config_row['Name']
        match self.config_row['Name']:
            case 'route-distinguisher-id':
                config_name = self.config_row['Name']
                key = self.config_row['Name']
                value = self.config_row['Arg1']
                routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                self.config_row["Parsed_size"]  = 5
            case 'router-id':
                config_name = self.config_row['Name']
                key = self.config_row['Name']
                value = self.config_row['Arg1']
                routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                self.config_row["Parsed_size"]  = 5
            case 'autonomous-system':
                config_name = self.config_row['Name']
                key = self.config_row['Name']
                value = self.config_row['Arg1']
                routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                self.config_row["Parsed_size"]  = 5
            case 'ppm':
                config_name = self.config_row['Name']
                key = self.config_row['Arg1']
                value = self.config_row['Arg2']
                routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                self.config_row["Parsed_size"]  = 6
            case 'forwarding-table':
                config_name = self.config_row['Name']
                match self.config_row['Arg1']:
                    case 'krt-nexthop-ack-timeout':                        
                        key = self.config_row['Arg1']
                        value = self.config_row['Arg2']
                        routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                        self.config_row["Parsed_size"]  = 6
                    case 'krt-route-ack-timeout':
                        key = self.config_row['Arg1']
                        value = self.config_row['Arg2']
                        routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                        self.config_row["Parsed_size"]  = 6
                    case 'export':
                        config_name = '-'
                        match self.config_row['Arg2']:
                            case '[':
                                export, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                            case _:
                                export = self.config_row['Arg2']
                                self.config_row["Parsed_size"]  = 6
                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name,ignore_duplicates=True,  export = export)
                    case 'ecmp-fast-reroute':
                        key = self.config_row['Arg1']
                        value = 'True'
                        routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                        self.config_row["Parsed_size"]  = 5
                    case 'indirect-next-hop':
                        key = self.config_row['Arg1']
                        value = 'True'
                        routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                        self.config_row["Parsed_size"]  = 5
                    case 'indirect-next-hop-change-acknowledgements':
                        key = self.config_row['Arg1']
                        value = 'True'
                        routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                        self.config_row["Parsed_size"]  = 5
                    case 'chained-composite-next-hop':
                        config_name = '-'
                        chained_composite_next_hop = 'True'
                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, chained_composite_next_hop = chained_composite_next_hop)
                        self.config_row["Parsed_size"]  = 5
                        match self.config_row['Arg2']:
                            case 'ingress':
                                ingress = 'True'
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True,  ingress = ingress)
                                self.config_row["Parsed_size"]  = 6
                                match self.config_row['Arg3']:
                                    case 'l2vpn':
                                        l2vpn = 'True'
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name,ignore_duplicates=True,  l2vpn = l2vpn)
                                        self.config_row["Parsed_size"]  = 7
                                    case 'l2ckt':
                                        l2ckt = 'True'
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, l2ckt = l2ckt)
                                        self.config_row["Parsed_size"]  = 7
                                    case 'l3vpn':
                                        l3vpn = 'True'
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, l3vpn = l3vpn)
                                        self.config_row["Parsed_size"]  = 7
                                        match self.config_row['Arg4']:
                                            case 'extended-space':
                                                extended_space = 'True'
                                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, extended_space = extended_space)
                                                self.config_row["Parsed_size"]  = 8
                    case 'unicast-reverse-path':
                        key = self.config_row['Arg1']
                        value = self.config_row['Arg2']
                        routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                        self.config_row["Parsed_size"]  = 6
            case 'kernel-options':
                config_name = self.config_row['Name']
                key = self.config_row['Arg1']
                value = self.config_row['Arg2']
                routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                self.config_row["Parsed_size"]  = 6
            case 'multicast':
                match self.config_row['Arg1']:
                    case 'forwarding-cache':
                        config_name = self.config_row['Arg1']
                        match self.config_row['Arg2']:
                            case 'threshold':
                                config_type = self.config_row['Arg2']
                                match self.config_row['Arg3']:
                                    case 'suppress':
                                        suppress = self.config_row['Arg4']
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, suppress = suppress)
                                        self.config_row["Parsed_size"]  = 8
                                    case 'reuse':
                                        reuse = self.config_row['Arg4']
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, reuse = reuse)
                                        self.config_row["Parsed_size"]  = 8
                            case 'timeout':
                                timeout = self.config_row['Arg3']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, timeout = timeout)
                                self.config_row["Parsed_size"]  = 7                           
            case 'rib':
                ## Add family in Arg1 when adding all children like source , destination after building the key
                family = self.config_row['Arg1']
                config_name = self.config_row['Arg2'] + ' ' + self.config_row['Arg3']
                config_value = self.config_row['Arg4']
                match self.config_row['Arg5']:
                    case 'match':
                        config_type = 'condition'
                        config_type_name = self.config_row['Arg5']
                        match self.config_row['Arg6']:
                            case 'destination':
                                destination = self.config_row['Arg7']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, destination = destination)
                                family = self.config_row['Arg1']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, family = family)
                                self.config_row["Parsed_size"]  = 11
                            case 'source':
                                source = self.config_row['Arg7']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, source = source)
                                family = self.config_row['Arg1']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, family = family)
                                self.config_row["Parsed_size"]  = 11
                    case 'then':
                        config_type = 'action'
                        config_type_name = self.config_row['Arg5']
                        match self.config_row['Arg6']:
                            case 'community':
                                community = self.config_row['Arg7']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, community = community)
                                family = self.config_row['Arg1']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, family = family)
                                self.config_row["Parsed_size"]  = 11
                            case 'rate-limit':
                                rate_limit = self.config_row['Arg7']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, rate_limit = rate_limit)
                                family = self.config_row['Arg1']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, family = family)
                                self.config_row["Parsed_size"]  = 11
                    case 'receive':
                        config_type = 'receive'
                        config_type_name = self.config_row['Arg5']
                        family = self.config_row['Arg1']
                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, family = family)
                        self.config_row["Parsed_size"]  = 9
            case 'no-multi-topology-routing':
                config_name = self.config_row['Name']
                key = self.config_row['Name']
                value = 'True'
                routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                self.config_row["Parsed_size"]  = 4
            case 'static':
                config_name = self.config_row['Arg1']
                config_value = self.config_row['Arg2']
                match self.config_row['Arg3']:
                    case 'next-hop':
                        next_hop = self.config_row['Arg4']
                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, next_hop = next_hop)
                        self.config_row["Parsed_size"]  = 8
            case 'interface-routes':
                config_name = '-'
                match self.config_row['Arg1']:
                    case 'rib-group':
                        rib_group = 'True'
                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, rib_group = rib_group)
                        self.config_row["Parsed_size"]  = 5
                        match self.config_row['Arg2']:
                            case 'inet':
                                family = self.config_row['Arg2']
                                routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, family = family)
                                self.config_row["Parsed_size"]  = 6
                                match self.config_row['Arg3']:
                                    case 'fbf-group':
                                        fbf_group = 'True'
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, fbf_group = fbf_group)
                                        self.config_row["Parsed_size"]  = 7
            case 'rib-groups':
                config_name = self.config_row['Name']
                config_value = self.config_row['Arg1']
                match self.config_row['Arg2']:
                    case 'import-rib':
                        match self.config_row['Arg3']:
                            case '[':
                                import_rib, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                            case _:
                                import_rib = self.config_row['Arg3']
                                self.config_row["Parsed_size"]  = 7
                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, import_rib = import_rib)
                    case 'import-policy':
                        import_policy = self.config_row['Arg3']
                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, import_policy = import_policy)
                        self.config_row["Parsed_size"]  = 7
            case 'nonstop-routing':
                config_name = self.config_row['Name']
                key = self.config_row['Name']
                value = 'True'
                routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                self.config_row["Parsed_size"]  = 4
            case 'flow':
                config_name = self.config_row['Name']
                match self.config_row['Arg1']:
                    case 'term-order':
                        key = self.config_row['Arg1']
                        value = self.config_row['Arg2']
                        routing_option.add_routing_option_config_kv(routing_option_name , config_name, key, value)
                        self.config_row["Parsed_size"]  = 6
                    case 'route':
                        config_name = self.config_row['Arg1']
                        config_value = self.config_row['Arg2']
                        match self.config_row['Arg3']:
                            case 'match':
                                config_type = 'condition'
                                config_type_name = self.config_row['Arg3']
                                match self.config_row['Arg4']:
                                    case 'destination':
                                        destination = self.config_row['Arg5']
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, destination = destination)
                                        self.config_row["Parsed_size"]  = 9
                                    case 'source':
                                        source = self.config_row['Arg5']
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, source = source)
                                        self.config_row["Parsed_size"]  = 9
                            case 'then':
                                config_type = 'action'
                                config_type_name = self.config_row['Arg3']
                                match self.config_row['Arg4']:
                                    case 'community':
                                        community = self.config_row['Arg5']
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, community = community)
                                        self.config_row["Parsed_size"]  = 9
                                    case 'rate-limit':
                                        rate_limit = self.config_row['Arg5']
                                        routing_option.add_routing_option(routing_option_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, rate_limit = rate_limit)
                                        self.config_row["Parsed_size"]  = 9
        return routing_option

    def _parse_class_of_service(self, class_of_service):
        config_name = '-'
        config_value = '-'
        config_type = '-'
        config_type_name = '-'
        class_of_service_name = self.config_row['Name']
        match self.config_row['Name']:
            case 'apply-groups':
                config_name = self.config_row['Name']
                value = self.config_row['Arg1']
                class_of_service.add_class_of_service_config_kv(class_of_service_name ,config_name, config_name, value)
                self.config_row["Parsed_size"]  = 5
            case 'classifiers':
                config_name = self.config_row['Arg1']
                config_value =  self.config_row['Arg2']
                match self.config_row['Arg3']:
                    case 'forwarding-class':
                        config_type = self.config_row['Arg3']
                        config_type_name = self.config_row['Arg4']
                        match self.config_row['Arg5']:
                            case 'loss-priority':
                                loss_priority = self.config_row['Arg6']
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  loss_priority = loss_priority)
                                self.config_row["Parsed_size"]  = 10
                                match self.config_row['Arg7']:
                                    case 'code-points':
                                        code_points = self.config_row['Arg8']
                                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  code_points = code_points)
                                        self.config_row["Parsed_size"]  = 12
            case 'host-outbound-traffic':
                config_name = self.config_row['Name']
                key = self.config_row['Arg1']
                value = self.config_row['Arg2']
                class_of_service.add_class_of_service_config_kv(class_of_service_name ,config_name, key, value)
                self.config_row["Parsed_size"]  = 6
            case 'drop-profiles':
                config_name = self.config_row['Name']
                config_value = self.config_row['Arg1']
                match self.config_row['Arg2']:
                    case 'fill-level':
                        fill_level = self.config_row['Arg3']
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  fill_level = fill_level)
                        self.config_row["Parsed_size"]  = 7
                        match self.config_row['Arg4']:
                            case 'drop-probability':
                                drop_probability = self.config_row['Arg5']
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  drop_probability = drop_probability)
                                self.config_row["Parsed_size"]  = 9
                    case 'interpolate':
                        interpolate = 'True'
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  interpolate = interpolate)
                        self.config_row["Parsed_size"]  = 7
                        match self.config_row['Arg3']:
                            case 'drop-probability':
                                match self.config_row['Arg4']:
                                    case '[':
                                        drop_probability, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                    case _:
                                        drop_probability = self.config_row['Arg4']
                                        self.config_row["Parsed_size"]  = 8
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  drop_probability = drop_probability)
                            case 'fill-level':
                                match self.config_row['Arg4']:
                                    case '[':
                                        fill_level, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                    case _:
                                        fill_level = self.config_row['Arg4']
                                        self.config_row["Parsed_size"]  = 8
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  fill_level = fill_level)
            case 'forwarding-classes':
                config_type = self.config_row['Arg1']
                config_type_name = self.config_row['Arg2']
                match self.config_row['Arg3']:
                    case 'queue-num':
                        queue_num = self.config_row['Arg4']
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  queue_num = queue_num)
                        self.config_row["Parsed_size"]  = 8
            case 'interfaces':
                config_name = self.config_row['Name']
                config_value = self.config_row['Arg1']
                match self.config_row['Arg2']:
                    case 'scheduler-map':
                        scheduler_map = self.config_row['Arg3']
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  scheduler_map = scheduler_map)
                        self.config_row["Parsed_size"]  = 7
                    case 'unit':
                        config_type = self.config_row['Arg2']
                        config_type_name = self.config_row['Arg3']
                        match self.config_row['Arg4']:
                            case 'classifiers':
                                classifiers = 'True'
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  classifiers = classifiers)
                                self.config_row["Parsed_size"]  = 7
                                match self.config_row['Arg5']:
                                    case 'exp':
                                        exp = self.config_row['Arg6']
                                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  exp = exp)
                                        self.config_row["Parsed_size"]  = 10
                                    case 'inet-precedence':
                                        inet_precedence = self.config_row['Arg6']
                                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  inet_precedence = inet_precedence)
                                        self.config_row["Parsed_size"]  = 10
                            case 'rewrite-rules':
                                rewrite_rules = 'True'
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  rewrite_rules = rewrite_rules)
                                self.config_row["Parsed_size"]  = 7
                                match self.config_row['Arg5']:
                                    case 'exp':
                                        exp = self.config_row['Arg6']
                                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  exp = exp)
                                        self.config_row["Parsed_size"]  = 10
                                    case 'inet-precedence':
                                        inet_precedence = self.config_row['Arg6']
                                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  inet_precedence = inet_precedence)
                                        self.config_row["Parsed_size"]  = 10
            case 'rewrite-rules':
                config_name = self.config_row['Arg1']
                config_value =  self.config_row['Arg2']
                match self.config_row['Arg3']:
                    case 'forwarding-class':
                        config_type = self.config_row['Arg3']
                        config_type_name = self.config_row['Arg4']
                        match self.config_row['Arg5']:
                            case 'loss-priority':
                                loss_priority = self.config_row['Arg6']
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  loss_priority = loss_priority)
                                self.config_row["Parsed_size"]  = 10
                                match self.config_row['Arg7']:
                                    case 'code-point':
                                        code_points = self.config_row['Arg8']
                                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  code_points = code_points)
                                        self.config_row["Parsed_size"]  = 12
            case 'scheduler-maps':
                config_name = self.config_row['Name']
                config_value = self.config_row['Arg1']
                config_type = self.config_row['Arg2']
                config_type_name = self.config_row['Arg3']
                match self.config_row['Arg4']:
                    case 'scheduler':
                        scheduler = self.config_row['Arg5']
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  scheduler = scheduler)
                        self.config_row["Parsed_size"]  = 9
            case 'schedulers':
                config_name = self.config_row['Name']
                config_value = self.config_row['Arg1']
                match self.config_row['Arg2']:
                    case 'transmit-rate':
                        transmit_rate = 'True'
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  transmit_rate = transmit_rate)
                        self.config_row["Parsed_size"]  = 6
                        match self.config_row['Arg3']:
                            case 'remainder':
                                remainder = 'True'
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  remainder = remainder)
                                self.config_row["Parsed_size"]  = 7
                            case 'percent':
                                percent = self.config_row['Arg4']
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  percent = percent)
                                self.config_row["Parsed_size"]  = 8
                    case 'buffer-size':
                        buffer_size = 'True'
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  buffer_size = buffer_size)
                        self.config_row["Parsed_size"]  = 6
                        match self.config_row['Arg3']:
                            case 'remainder':
                                remainder = 'True'
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  remainder = remainder)
                                self.config_row["Parsed_size"]  = 7
                            case 'percent':
                                percent = self.config_row['Arg4']
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  percent = percent)
                                self.config_row["Parsed_size"]  = 8
                    case 'priority':
                        priority = self.config_row['Arg3']
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  priority = priority)
                        self.config_row["Parsed_size"]  = 7
                    case 'drop-profile-map':
                        drop_profile_map = 'True'
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  drop_profile_map = drop_profile_map)
                        self.config_row["Parsed_size"]  = 5
                        match self.config_row['Arg3']:
                            case 'loss-priority':
                                loss_priority = self.config_row['Arg4']
                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  loss_priority = loss_priority)
                                self.config_row["Parsed_size"]  = 8
                                match self.config_row['Arg5']:
                                    case 'protocol':
                                        protocol = self.config_row['Arg6']
                                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  protocol = protocol)
                                        self.config_row["Parsed_size"]  = 10
                                        match self.config_row['Arg7']:
                                            case 'drop-profile':
                                                drop_profile = self.config_row['Arg8']
                                                class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  drop_profile = drop_profile)
                                                self.config_row["Parsed_size"]  = 12
            case 'forwarding-policy':
                config_name = self.config_row['Arg1']
                config_value = self.config_row['Arg2']
                config_type = self.config_row['Arg3']
                config_type_name = self.config_row['Arg4']
                match self.config_row['Arg5']:
                    case 'lsp-next-hop':
                        lsp_next_hop = self.config_row['Arg6']
                        class_of_service.add_class_of_service(class_of_service_name ,config_name,config_value,config_type,config_type_name,  lsp_next_hop = lsp_next_hop)
                        self.config_row["Parsed_size"]  = 10
                
        return class_of_service

    def _parse_policy_option(self, policy_option):
        config_name = '-'
        config_value = '-'
        config_type = '-'
        config_type_name = '-'
        policy_option_name = self.config_row['Name']
        config_name = policy_option_name
        match policy_option_name:
            case 'policy-statement':
                config_value = self.config_row['Arg1'] 
                match self.config_row['Arg2']:
                    case 'from':
                        config_type = self.config_row['Arg2']
                        match self.config_row['Arg3']:
                            case 'protocol':
                                match self.config_row['Arg4']:
                                    case '[':
                                        protocol, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                    case _:
                                        protocol = self.config_row['Arg4']
                                        self.config_row["Parsed_size"]  = 8
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  protocol = protocol)
                            case 'rib':
                                rib = self.config_row['Arg4']
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  rib = rib)
                                self.config_row["Parsed_size"] = 8
                    case 'term':
                        config_type = self.config_row['Arg2']
                        config_type_name = self.config_row['Arg3']
                        match self.config_row['Arg4']:
                            case 'from':
                                from_ = 'True'
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  from_ = from_)
                                match self.config_row['Arg5']:
                                    case 'protocol':
                                        match self.config_row['Arg6']:
                                            case '[':
                                                protocol, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                            case _:
                                                protocol = self.config_row['Arg6']
                                                self.config_row["Parsed_size"]  = 10
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  protocol = protocol)
                                    case 'rib':
                                        rib = self.config_row['Arg6']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  rib = rib)
                                        self.config_row["Parsed_size"] = 10
                                    case 'community':
                                        match self.config_row['Arg6']:
                                            case '[':
                                                community, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                            case _:
                                                community = self.config_row['Arg6']
                                                self.config_row["Parsed_size"]  = 10
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  community = community)
                                    case 'family':
                                        family = self.config_row['Arg6']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                        self.config_row["Parsed_size"] = 10
                                    case 'tag':
                                        tag = self.config_row['Arg6']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  tag = tag)
                                        self.config_row["Parsed_size"] = 10
                                    case 'route-filter':
                                        route_filter = self.config_row['Arg6']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  route_filter = route_filter)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7']:
                                            case 'orlonger':
                                                orlonger = 'True'
                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  orlonger = orlonger)
                                                self.config_row["Parsed_size"] = 11
                                            case 'exact':
                                                exact = 'True'
                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  exact = exact)
                                                self.config_row["Parsed_size"] = 11
                                            case 'prefix-length-range':
                                                prefix_length_range = self.config_row['Arg8']
                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  prefix_length_range = prefix_length_range)
                                                self.config_row["Parsed_size"] = 12
                            case 'then':
                                then = 'True'
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  then = then)
                                match self.config_row['Arg5']:
                                    case 'community':
                                        community = 'True'
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  community = community)
                                        self.config_row["Parsed_size"] = 9
                                        match self.config_row['Arg6']:
                                            case 'add':
                                                add = self.config_row['Arg7']
                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  add = add)
                                                self.config_row["Parsed_size"] = 11
                                    case 'accept':
                                        accept = 'True'
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  accept = accept)
                                        self.config_row["Parsed_size"] = 9
                                    case 'reject':
                                        reject = 'True'
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  reject = reject)
                                        self.config_row["Parsed_size"] = 9
                                    case 'tag':
                                        tag = self.config_row['Arg6']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  tag = tag)
                                        self.config_row["Parsed_size"] = 10
                                    case 'next':
                                        next = self.config_row['Arg6']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  next = next)
                                        self.config_row["Parsed_size"] = 10
                                    case 'cos-next-hop-map':
                                        cos_next_hop_map = self.config_row['Arg6']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  cos_next_hop_map = cos_next_hop_map)
                                        self.config_row["Parsed_size"] = 10
                                    case 'next-hop':
                                        next_hop = self.config_row['Arg6']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  next_hop = next_hop)
                                        self.config_row["Parsed_size"] = 10
                    case 'then':
                        config_type = self.config_row['Arg2']
                        match self.config_row['Arg3']:
                            case 'load-balance':
                                load_balance = self.config_row['Arg4']
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  load_balance = load_balance)
                                self.config_row["Parsed_size"] = 8
                            case 'next-hop':
                                next_hop = self.config_row['Arg4']
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  next_hop = next_hop)
                                self.config_row["Parsed_size"] = 8
                            case 'next':
                                next = self.config_row['Arg4']
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  next = next)
                                self.config_row["Parsed_size"] = 8
                            case 'accept':
                                accept = self.config_row['Arg4']
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  accept = accept)
                                self.config_row["Parsed_size"] = 7
                            case 'community':
                                community = 'True'
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  community = community)
                                self.config_row["Parsed_size"] = 7
                                match self.config_row['Arg4']:
                                    case 'add':
                                        add = self.config_row['Arg5']
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  add = add)
                                        self.config_row["Parsed_size"] = 9
            case 'community':
                config_value =self.config_row['Arg1'] 
                match self.config_row['Arg2']:
                    case 'members':
                        members = self.config_row['Arg3']
                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  members = members)
                        if len(members.split(":")) ==3:
                            target =":".join(members.split(":")[1:])
                            policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  target = target)
                        self.config_row["Parsed_size"] = 7
            case 'prefix-list':
                config_name = 'configuration_parameter'
                config_value = self.config_row['Arg1'] 
                prefix_list = 'True'
                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  prefix_list = prefix_list)
                self.config_row["Parsed_size"] = 5 
                match self.config_row['Arg2']:
                    case 'apply-path':
                        apply_path_list, self.config_row["Parsed_size"] = self.get_columns_with_a_char_as_list(self.config_row,self.column_in_config_file, '"', '"')
                        apply_path = ' '.join(apply_path_list)
                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  apply_path = apply_path)
                        ## Parsed size is rolled back to 6 as we will process all options individually too
                        self.config_row["Parsed_size"] = 6
                        match self.config_row['Arg3'].replace('"',''):
                            case 'forwarding-options':
                                forwarding_options = 'True'
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  forwarding_options = forwarding_options)
                                self.config_row["Parsed_size"] = 7
                                match self.config_row['Arg4'].replace('"',''):
                                    case 'helpers':
                                        helpers = 'True'
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  helpers = helpers)
                                        self.config_row["Parsed_size"] = 8
                                        match self.config_row['Arg5'].replace('"',''):
                                            case 'bootp':
                                                bootp = 'True'
                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  bootp = bootp)
                                                self.config_row["Parsed_size"] = 9
                                                match self.config_row['Arg6'].replace('"',''):
                                                    case 'interface':
                                                        interface = self.config_row['Arg7']
                                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  interface = interface)
                                                        self.config_row["Parsed_size"] = 11
                                                        match self.config_row['Arg8'].replace('"',''):
                                                            case 'server':
                                                                server = self.config_row['Arg9'].replace('"','')
                                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  server = server)
                                                                self.config_row["Parsed_size"] = 13
                            case 'protocols':
                                protocols = self.config_row['Arg4']
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  protocols = protocols)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5'].replace('"',''):
                                    case 'group':
                                        group = self.config_row['Arg6'].replace('"','')
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  group = group)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7'].replace('"',''):
                                            case 'neighbor':
                                                neighbor = self.config_row['Arg8'].replace('"','')
                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  neighbor = neighbor)
                                                self.config_row["Parsed_size"] = 12
                            case 'routing-instances':
                                routing_instances = self.config_row['Arg4'].replace('"','')
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  routing_instances = routing_instances)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5'].replace('"',''):
                                    case 'protocols':
                                        protocols = self.config_row['Arg6'].replace('"','')
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  protocols = protocols)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7'].replace('"',''):
                                            case 'group':
                                                group = self.config_row['Arg8'].replace('"','')
                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  group = group)
                                                self.config_row["Parsed_size"] = 12
                                                match self.config_row['Arg9'].replace('"',''):
                                                    case 'neighbor':
                                                        neighbor = self.config_row['Arg10'].replace('"','')
                                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  neighbor = neighbor)
                                                        self.config_row["Parsed_size"] = 14
                            case 'interfaces':
                                interfaces = self.config_row['Arg4']
                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  interfaces = interfaces)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5'].replace('"',''):
                                    case 'unit':
                                        unit = self.config_row['Arg6'].replace('"','')
                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  unit = unit)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7'].replace('"',''):
                                            case 'family':
                                                family = self.config_row['Arg8'].replace('"','')
                                                policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                                self.config_row["Parsed_size"] = 12
                                                match self.config_row['Arg9'].replace('"',''):
                                                    case 'address':
                                                        address = self.config_row['Arg10'].replace('"','')
                                                        policy_option.add_policy_option(policy_option_name ,config_name,config_value,config_type,config_type_name,  address = address)
                                                        self.config_row["Parsed_size"] = 14

        return policy_option



    def _parse_bridgedomain(self, bridgedomain):
       
       bridgedomain_name = self.config_row['Name']
       match self.config_row['Arg1']:
           case 'domain-type':
               domain_type = self.config_row['Arg2']
               bridgedomain.add_bridgedomain(bridgedomain_name , domain_type = domain_type)
               self.config_row["Parsed_size"] = 6 
           case 'vlan-id':
               vlan_id = self.config_row['Arg2']
               bridgedomain.add_bridgedomain(bridgedomain_name , vlan_id = vlan_id)
               self.config_row["Parsed_size"] = 6 
           case 'interface':
               interface = self.config_row['Arg2']
               bridgedomain.add_bridgedomain(bridgedomain_name , interface = interface)
               self.config_row["Parsed_size"] = 6 
           case 'routing-interface':
               routing_interface = self.config_row['Arg2']
               bridgedomain.add_bridgedomain(bridgedomain_name , routing_interface = routing_interface)
               self.config_row["Parsed_size"] = 6 
       return bridgedomain

    def _parse_service(self, service):
        
        service_type = self.config_row['Name']
        version = self.config_row['Arg1']
        match self.config_row['Arg2']:
            case 'template':
                template = self.config_row['Arg3']
                self.config_row["Parsed_size"] = 7 
                match self.config_row['Arg4']:
                    case 'nexthop-learning':
                        nexthop_learning= self.config_row['Arg5']
                        service.add_service(service_type , version,template,  nexthop_learning = nexthop_learning)
                        self.config_row["Parsed_size"] = 9 
                    case 'template-refresh-rate':
                        template_refresh_rate= self.config_row['Arg5'] + ' ' + self.config_row['Arg6']
                        service.add_service(service_type , version,template,  template_refresh_rate = template_refresh_rate)
                        self.config_row["Parsed_size"] = 10
                    case 'option-refresh-rate':
                        option_refresh_rate=  self.config_row['Arg5'] + ' ' + self.config_row['Arg6']
                        service.add_service(service_type , version,template,  option_refresh_rate = option_refresh_rate)
                        self.config_row["Parsed_size"] = 10 
                    case 'ipv4-template':
                        ipv4_template= 'True'
                        service.add_service(service_type , version,template,  ipv4_template = ipv4_template)
                        self.config_row["Parsed_size"] = 8 
                    case 'ipv6-template':
                        ipv6_template= 'True'
                        service.add_service(service_type , version,template,  ipv6_template = ipv6_template)
                        self.config_row["Parsed_size"] = 8 
                    case 'mpls-template':
                        mpls_template= 'True'
                        service.add_service(service_type , version,template,  mpls_template = mpls_template)
                        self.config_row["Parsed_size"] = 8 
        
        return service

    def _parse_routing_instance(self, routing_instance):
        config_name = '-'
        config_value = '-'
        config_type = '-'
        config_type_name = '-'
        routing_instance_name = self.config_row['Name']
        match self.config_row['Arg1']:
            case 'instance-type':
                instance_type = self.config_row['Arg2']
                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  instance_type = instance_type)
                self.config_row["Parsed_size"] = 6 
                match  self.config_row['Arg4']:
                    case 'protect':
                        router = self.config_row['Arg3']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  router = router)
                        protect = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protect = protect)
                        self.config_row["Parsed_size"] = 8
                        match  self.config_row['Arg7']:
                            case 'protocols':
                                protocols = self.config_row['Arg8']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protocols = protocols)
                                self.config_row["Parsed_size"] = 12
                                match  self.config_row['Arg9']:
                                    case 'area':
                                        area = self.config_row['Arg10']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  area = area )
                                        self.config_row["Parsed_size"] = 14
                                        match  self.config_row['Arg11']:
                                            case 'interface':
                                                interface = self.config_row['Arg12']
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  interface = interface )
                                                self.config_row["Parsed_size"] = 16
                                                match  self.config_row['Arg13']:
                                                    case 'node-link-protection':
                                                        node_link_protection = self.config_row['Arg13']
                                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  node_link_protection = node_link_protection )
                                                        self.config_row["Parsed_size"] = 17
                            case 'routing-options': 
                                routing_options = self.config_row['Arg8']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  routing_options = routing_options)
                                self.config_row["Parsed_size"] = 12
                                match  self.config_row['Arg10']:
                                    case 'protect':
                                        match  self.config_row['Arg11']:
                                            case 'core':
                                                self.config_row["Parsed_size"] = 15
                                                ## Protection is defined in routing options of this instance
            case 'routing-options':
                config_name = self.config_row['Arg1']
                config_value = self.config_row['Arg2']
                match self.config_row['Arg2']:
                    case 'rib':
                        rib_name = self.config_row['Arg3']
                        if len(rib_name.split(".")) ==3:
                            family = rib_name.split(".")[1]
                            routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                            self.config_row["Parsed_size"] = 7
                        match self.config_row['Arg4']:
                            case 'protect':
                                protect = self.config_row['Arg5']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protect = protect)
                                self.config_row["Parsed_size"] = 9
                            case 'static':
                                static = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  static = static)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'route':
                                        route = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  route = route)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7']:
                                            case 'next-hop':
                                                next_hop = self.config_row['Arg8']
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  next_hop = next_hop)
                                                self.config_row["Parsed_size"] = 12
                                            case 'resolve':
                                                match  self.config_row['Arg9']:
                                                    case 'protect':
                                                        protect = 'True'
                                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protect = protect)
                                                        self.config_row["Parsed_size"] = 13
                                                        match  self.config_row['Arg15']:
                                                            case 'protect':
                                                                match  self.config_row['Arg16']:
                                                                    case 'core':
                                                                        self.config_row["Parsed_size"] = 20
                                                                        ## Protection is defined in routing options of this instance
                    case 'graceful-restart':
                        value = 'True'
                        routing_instance.add_routing_instance_config_kv(routing_instance_name,config_name, self.config_row['Arg2'] ,  value )
                        self.config_row["Parsed_size"] = 6
                    case 'multipath':
                        value = 'True'
                        routing_instance.add_routing_instance_config_kv(routing_instance_name,config_name,self.config_row['Arg2']  ,  value )
                        self.config_row["Parsed_size"] = 6
                        if not pd.isnull(self.config_row['Arg3']):
                            match  self.config_row['Arg4']:
                                case 'protect':
                                    protect = 'True'
                                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protect = protect)
                                    self.config_row["Parsed_size"] = 8
                                    match  self.config_row['Arg8']:
                                        case 'protect':
                                            match  self.config_row['Arg9']:
                                                case 'core':
                                                    self.config_row["Parsed_size"] = 13
                                                    value = self.config_row['Arg8'] + ' ' + self.config_row['Arg9']
                                                    routing_instance.add_routing_instance_config_kv(routing_instance_name,config_name, self.config_row['Arg2'] ,  value )
                    case 'protect':
                        value = self.config_row['Arg3']
                        routing_instance.add_routing_instance_config_kv(routing_instance_name,config_name, self.config_row['Arg2'] ,  value )
                        self.config_row["Parsed_size"] = 7
                        if not pd.isnull(self.config_row['Arg4']):
                            match  self.config_row['Arg5']:
                                case 'protect':
                                    protect = 'True'
                                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protect = protect)
                                    self.config_row["Parsed_size"] = 9
                                    match  self.config_row['Arg8']:
                                        case 'protocols':
                                            protocols = self.config_row['Arg9']
                                            routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protocols = protocols)
                                            self.config_row["Parsed_size"] = 13
                                            match  self.config_row['Arg10']:
                                                case 'area':
                                                    area = self.config_row['Arg11']
                                                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  area = area)
                                                    self.config_row["Parsed_size"] = 15
                                                    match  self.config_row['Arg12']:
                                                        case 'interface':
                                                            interface = self.config_row['Arg13']
                                                            routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  interface = interface)
                                                            self.config_row["Parsed_size"] = 17
                                                            match  self.config_row['Arg14']:
                                                                case 'node-link-protection':
                                                                    node_link_protection = 'True'
                                                                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  node_link_protection = node_link_protection)
                                                                    self.config_row["Parsed_size"] = 18
                    case 'static':
                        self.config_row["Parsed_size"] = 6 
                        match  self.config_row['Arg3']:
                            case 'route':
                                route =  self.config_row['Arg4']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  route = route)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'next-hop':
                                        next_hop = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  next_hop = next_hop)
                                        self.config_row["Parsed_size"] = 10
                                    case 'resolve':
                                        resolve = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  resolve = resolve)
                                        self.config_row["Parsed_size"] = 9
                    case 'auto-export':
                        value = 'True'
                        routing_instance.add_routing_instance_config_kv(routing_instance_name,config_name, self.config_row['Arg2'] ,value  )
                        self.config_row["Parsed_size"] = 6
                        if not pd.isnull(self.config_row['Arg3']):
                            match  self.config_row['Arg4']:
                                case 'protect':
                                    protect = 'True'
                                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protect = protect)
                                    self.config_row["Parsed_size"] = 8
                                    match  self.config_row['Arg7']:
                                        case 'protocols':
                                            protocols = self.config_row['Arg8']
                                            routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  protocols = protocols)
                                            self.config_row["Parsed_size"] = 12
                                            match  self.config_row['Arg9']:
                                                case 'area':
                                                    area = self.config_row['Arg10']
                                                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  area = area)
                                                    self.config_row["Parsed_size"] = 14
                                                    match  self.config_row['Arg11']:
                                                        case 'interface':
                                                            interface = self.config_row['Arg12']
                                                            routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  interface = interface)
                                                            self.config_row["Parsed_size"] = 16
                                                            match  self.config_row['Arg13']:
                                                                case 'node-link-protection':
                                                                    node_link_protection = 'True'
                                                                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  node_link_protection = node_link_protection)
                                                                    self.config_row["Parsed_size"] = 17
            case 'protocols':
                protocol_name = self.config_row['Arg2']
                config_name = 'protocol'
                config_value = protocol_name
                self.config_row["Parsed_size"] = 6 
                ## For protocol groups did not parse protocol configurations as they are all in protocol groupconfiguration
                match self.config_row['Arg3']:
                    case 'log-updown':
                        log_updown = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  log_updown = log_updown)
                        self.config_row["Parsed_size"] = 7      
                    case 'multipath':
                        multipath = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, multipath = multipath)
                        self.config_row["Parsed_size"] = 7      
                    case 'group':
                        config_type = self.config_row['Arg3']
                        protocol_group_name = self.config_row['Arg4']
                        config_type_name = self.config_row['Arg4']
                        ## Protocol Group Name is part of index as config_type_name
                        group = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  group = group)
                        self.config_row["Parsed_size"] = 8
                        match self.config_row['Arg5']:
                            case 'type':
                                type = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name , config_name,config_value,config_type,config_type_name, ignore_duplicates=True, type = type)
                                self.config_row["Parsed_size"] += 2
                                match self.config_row['Arg8']:
                                    case 'protect':
                                        protect = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protect = protect)
                                        self.config_row["Parsed_size"] = 12
                                match self.config_row['Arg15']:
                                    case 'family':
                                        family = self.config_row['Arg16']
                                        routing_instance.add_routing_instance(routing_instance_name , config_name,config_value,config_type,config_type_name, ignore_duplicates=True, family = family)
                                        self.config_row["Parsed_size"] = 20
                                        match self.config_row['Arg17']:
                                            case 'unicast':
                                                unicast = 'True'
                                                routing_instance.add_routing_instance(routing_instance_name , config_name,config_value,config_type,config_type_name, ignore_duplicates=True, unicast = unicast)
                                                self.config_row["Parsed_size"] = 21                                            
                                                match self.config_row['Arg18']:
                                                    case 'protection':
                                                        protection = 'True'
                                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protection = protection)
                                                        self.config_row["Parsed_size"] = 22                                             
                            case 'family':
                                family = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name , config_name,config_value,config_type,config_type_name, ignore_duplicates=True, family = family)
                                self.config_row["Parsed_size"] += 2
                                match self.config_row['Arg7']:
                                    case 'unicast':
                                        unicast = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name , config_name,config_value,config_type,config_type_name, ignore_duplicates=True, unicast = unicast)
                                        self.config_row["Parsed_size"] += 1
                                        match self.config_row['Arg8']:
                                            case 'protection':
                                                protection = 'True'
                                                routing_instance.add_routing_instance(routing_instance_name , config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protection = protection)
                                                self.config_row["Parsed_size"] += 1
                                            case 'prefix-limit':
                                                prefix_limit = 'True'
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  prefix_limit = prefix_limit)
                                                self.config_row["Parsed_size"] = 12
                                                match self.config_row['Arg9']:
                                                    case 'maximum':
                                                        maximum = self.config_row['Arg10']
                                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  maximum = maximum)
                                                        self.config_row["Parsed_size"] = 14
                                                    case 'teardown':
                                                        match self.config_row['Arg10']:
                                                            case 'idle-timeout':
                                                                idle_timeout = self.config_row['Arg11']
                                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  idle_timeout = idle_timeout)
                                                                self.config_row["Parsed_size"] = 15
                                                                match self.config_row['Arg13']:
                                                                    case 'protect':
                                                                        protect = 'True'
                                                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protect = protect)
                                                                        self.config_row["Parsed_size"] = 17
                                                                        match self.config_row['Arg22']:
                                                                            case 'unicast':
                                                                                ## No need to update Unicast as it is already updated in this path like many other columns like family
                                                                                match self.config_row['Arg23']:
                                                                                    case 'protection':
                                                                                        protection = 'True'
                                                                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protection = protection)
                                                                                        self.config_row["Parsed_size"] = 27                                             
                                                            case _:
                                                                teardown = self.config_row['Arg10']
                                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  teardown = teardown)
                                                                self.config_row["Parsed_size"] = 14
                                    case 'labeled-unicast':
                                        labeled_unicast = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value, config_type,config_type_name, ignore_duplicates=True,labeled_unicast = labeled_unicast)
                                        self.config_row["Parsed_size"] += 1
                            case 'peer-as':
                                automomous_system = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, automomous_system = automomous_system)
                                self.config_row["Parsed_size"] += 2
                            case 'as-override':
                                as_override = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, as_override = as_override)
                                self.config_row["Parsed_size"] += 1
                            case 'neighbor':
                                neighbor = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, neighbor = neighbor)
                                self.config_row["Parsed_size"] += 2
                            case 'import':
                                import_name = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, import_name = import_name)
                                self.config_row["Parsed_size"] += 2
                                match self.config_row['Arg8']:
                                    case 'protect':
                                        protect = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protect = protect)
                                        self.config_row["Parsed_size"] = 12
                                match self.config_row['Arg17']:
                                    case 'unicast':
                                        match self.config_row['Arg18']:
                                            case 'protection':
                                                unicast_protection = 'True'
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, unicast_protection = unicast_protection)
                                                self.config_row["Parsed_size"] = 22                                             
                            case 'export':
                                export = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, export = export)
                                self.config_row["Parsed_size"] += 2
                            case 'tcp-aggressive-transmission':
                                tcp_aggressive_transmission = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, tcp_aggressive_transmission = tcp_aggressive_transmission)
                                self.config_row["Parsed_size"] += 1
                            case 'bfd-liveness-detection':
                                bfd_liveness_detection = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, bfd_liveness_detection = bfd_liveness_detection)
                                self.config_row["Parsed_size"] += 1
                                match self.config_row['Arg6']:
                                    case "minimum-interval":
                                        minimum_interval = self.config_row['Arg7']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, minimum_interval = minimum_interval)
                                        self.config_row["Parsed_size"] += 2
                                    case "multiplier":
                                        multiplier = self.config_row['Arg7']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, multiplier = multiplier)
                                        self.config_row["Parsed_size"] += 2
                    case 'interface':
                        config_type = self.config_row['Arg3']
                        config_type_name = self.config_row['Arg4']
                        interface = self.config_row['Arg4']
                        unit , vlan_tag = self.get_unit_vlan_tag(interface)
                        if not pd.isnull(unit):
                            routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  unit = unit)
                        if not pd.isnull(vlan_tag):
                            routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vlan_tag = vlan_tag)
                        self.config_row["Parsed_size"] = 8
                        match self.config_row['Arg5']:
                            case 'point-to-point':
                                point_to_point = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  point_to_point = point_to_point)
                                self.config_row["Parsed_size"] = 9
                            case 'mode':
                                mode = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  mode = mode)
                                self.config_row["Parsed_size"] = 10
                            case 'vpws-service-id':
                                vpws_service_id = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vpws_service_id = vpws_service_id)                                
                                vpws_service_id_value = self.config_row['Arg7']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vpws_service_id_value = vpws_service_id_value)                               
                                self.config_row["Parsed_size"] = 11
                    case 'area':
                        match self.config_row['Arg5']:
                            case 'interface':
                                # Set interface in the key
                                config_type = self.config_row['Arg5']
                                config_type_name = self.config_row['Arg6']
                        area = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  area = area)
                        self.config_row["Parsed_size"] = 10
                        match self.config_row['Arg5']:
                            case 'interface': 
                                interface = self.config_row['Arg6']
                                match self.config_row['Arg7']:
                                    case 'node-link-protection':
                                        node_link_protection = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, node_link_protection = node_link_protection)
                                        self.config_row["Parsed_size"] = 11
                                match self.config_row['Arg9']:
                                    case 'protect':
                                        protect = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protect = protect)
                                        self.config_row["Parsed_size"] = 13
                                match self.config_row['Arg18']:
                                    case 'node-link-protection':
                                        node_link_protection = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, node_link_protection = node_link_protection)
                                        self.config_row["Parsed_size"] = 22
                    case 'bum-hashing':
                        bum_hashing = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  bum_hashing = bum_hashing)
                        self.config_row["Parsed_size"] = 7
                    case 'dense-groups':
                        dense_groups = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  dense_groups = dense_groups)
                        self.config_row["Parsed_size"] = 8
                    case 'domain-id':
                        domain_id = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  domain_id = domain_id)
                        self.config_row["Parsed_size"] = 8
                    case 'encapsulation-type':
                        encapsulation_type = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  encapsulation_type = encapsulation_type)
                        self.config_row["Parsed_size"] = 8
                    case 'export':
                        export = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  export = export)
                        self.config_row["Parsed_size"] = 8
                    case 'extended-vlan-list':
                        ## The functions returns column no of closing bracket
                        extended_vlan_list, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  extended_vlan_list = extended_vlan_list)
                    case 'family':
                        family = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                        self.config_row["Parsed_size"] = 8
                        match self.config_row['Arg5']:
                            case 'autodiscovery-only':
                                autodiscovery_only = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  autodiscovery_only = autodiscovery_only)
                                self.config_row["Parsed_size"] = 9
                                match self.config_row['Arg6']:
                                    case 'intra-as':
                                        intra_as = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  intra_as = intra_as)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7']:
                                            case 'inclusive':
                                                inclusive = 'True'
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  inclusive = inclusive)
                                                self.config_row["Parsed_size"] = 11
                    case 'import':
                        neighbor = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, neighbor = neighbor)
                        self.config_row["Parsed_size"] = 8
                        match self.config_row['Arg6']:
                            case 'protect':
                                protect = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protect = protect)
                                self.config_row["Parsed_size"] = 10
                                match self.config_row['Arg13']:
                                    case 'interface':
                                        interface = self.config_row['Arg14']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, interface = interface)
                                        self.config_row["Parsed_size"] = 18
                                        match self.config_row['Arg15']:
                                            case 'node-link-protection':
                                                node_link_protection = 'True'
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, node_link_protection = node_link_protection)
                                                self.config_row["Parsed_size"] = 19
                    case 'ip-prefix-routes':
                        match self.config_row['Arg4']:
                            case 'advertise':
                                advertise = self.config_row['Arg5']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, advertise = advertise)
                                self.config_row["Parsed_size"] = 9
                            case 'encapsulation':
                                encapsulation = self.config_row['Arg5']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, encapsulation = encapsulation)
                                self.config_row["Parsed_size"] = 9
                    case 'join-load-balance':
                        join_load_balance = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  join_load_balance = join_load_balance)
                        self.config_row["Parsed_size"] = 7
                    case 'label-block-size':
                        label_block_size = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, label_block_size = label_block_size)
                        self.config_row["Parsed_size"] = 8
                    case 'level':
                        level = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  level = level)
                        match self.config_row['Arg5']:
                            case 'disable': 
                                disable = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  disable = disable)
                                self.config_row["Parsed_size"] = 9
                    case 'mac-table-size':
                        mac_table_size = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, mac_table_size = mac_table_size)
                        self.config_row["Parsed_size"] = 8
                    case 'mvpn':
                        mvpn = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, mvpn = mvpn)
                        self.config_row["Parsed_size"] = 7
                        match self.config_row['Arg4']:
                            case 'family':
                                family = self.config_row['Arg5']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                self.config_row["Parsed_size"] = 9
                                match self.config_row['Arg6']:
                                    case 'autodiscovery':
                                        autodiscovery = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  autodiscovery = autodiscovery)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7']:
                                            case 'inet-mdt':
                                                inet_mdt = 'True'
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  inet_mdt = inet_mdt)
                                                self.config_row["Parsed_size"] = 11
                    case 'mvpn-mode':
                        mvpn_mode = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  mvpn_mode = mvpn_mode)
                        self.config_row["Parsed_size"] = 8
                        match self.config_row['Arg6']:
                            case 'protect':
                                protect = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protect = protect)
                                self.config_row["Parsed_size"] = 10
                                match self.config_row['Arg13']:
                                    case 'interface':
                                        interface = self.config_row['Arg14']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, interface = interface)
                                        self.config_row["Parsed_size"] = 18
                                        match self.config_row['Arg15']:
                                            case 'node-link-protection':
                                                node_link_protection = 'True'
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, node_link_protection = node_link_protection)
                                                self.config_row["Parsed_size"] = 19
                    case 'no-control-word':
                        no_control_word = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  no_control_word = no_control_word)
                        self.config_row["Parsed_size"] = 7
                    case 'no-tunnel-services':
                        no_tunnel_services = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  no_tunnel_services = no_tunnel_services)
                        self.config_row["Parsed_size"] = 7
                    case 'rp':
                        match self.config_row['Arg4']:
                            case 'static':
                                rp = self.config_row['Arg4']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  rp = rp)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'address':
                                        address = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  address = address)
                                        self.config_row["Parsed_size"] = 10
                                    case 'family':
                                        family = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7']:
                                            case 'address':
                                                address = self.config_row['Arg8']
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  address = address)
                                                self.config_row["Parsed_size"] = 12
                                            case 'priority':
                                                family = self.config_row['Arg8']
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                                self.config_row["Parsed_size"] = 12
                            case 'local':
                                rp = self.config_row['Arg4']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  rp = rp)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'family':
                                        family = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7']:
                                            case 'address':
                                                address = self.config_row['Arg8']
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  address = address)
                                                self.config_row["Parsed_size"] = 12
                                            case 'priority':
                                                family = self.config_row['Arg8']
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                                self.config_row["Parsed_size"] = 12
                            case 'bootstrap':
                                rp = self.config_row['Arg4']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  rp = rp)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'family':
                                        family = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg7']:
                                            case 'priority':
                                                family = self.config_row['Arg8']
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                                                self.config_row["Parsed_size"] = 12
                            case 'auto-rp':
                                rp = self.config_row['Arg4']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  rp = rp)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'mapping':
                                        mapping = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  mapping = mapping)
                                        self.config_row["Parsed_size"] = 9
                    case 'site':
                        site = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  site = site)
                        self.config_row["Parsed_size"] = 8
                        match self.config_row['Arg5']:
                            case 'interface':
                                interface = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  interface = interface)
                                self.config_row["Parsed_size"] = 10
                                match self.config_row['Arg7']:
                                    case 'remote-site-id':
                                        remote_site_id = self.config_row['Arg8']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  remote_site_id = remote_site_id)
                                        self.config_row["Parsed_size"] = 12                                
                            case 'multi-homing':
                                multi_homing = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  multi_homing = multi_homing)
                                self.config_row["Parsed_size"] = 9                                
                            case 'site-identifier':
                                site_identifier = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  site_identifier = site_identifier)
                                self.config_row["Parsed_size"] = 10                                
                            case 'site-preference':
                                site_preference = self.config_row['Arg6']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  site_preference = site_preference)
                                self.config_row["Parsed_size"] = 10                                
                    case 'site-range':
                        site_range = self.config_row['Arg4']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  site_range = site_range)
                        self.config_row["Parsed_size"] = 8
                    case 'spf-options':
                        spf_options = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  spf_options = spf_options)
                        match self.config_row['Arg4']:
                            case 'rapid-runs': 
                                rapid_runs = self.config_row['Arg5']
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  rapid_runs = rapid_runs)
                                self.config_row["Parsed_size"] = 9
                                match self.config_row['Arg7']:
                                    case 'protect':
                                        protect = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, protect = protect)
                                        self.config_row["Parsed_size"] = 11
                                match self.config_row['Arg16']:
                                    case 'node-link-protection':
                                        node_link_protection = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name, ignore_duplicates=True, node_link_protection = node_link_protection)
                                        self.config_row["Parsed_size"] = 20
            case 'interface':
                config_type = self.config_row['Arg1']
                config_type_name = self.config_row['Arg2']
                interface = self.config_row['Arg2']
                unit , vlan_tag = self.get_unit_vlan_tag(interface)
                if not pd.isnull(unit):
                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  unit = unit)
                if not pd.isnull(vlan_tag):
                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vlan_tag = vlan_tag)
                self.config_row["Parsed_size"] = 6
            case 'vrf-target':
                if self.config_row['Arg2'] == 'import':
                    import_route = 'True' 
                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  import_route = import_route)
                    self.config_row["Parsed_size"] = 6
                    vrf_target = str(self.config_row['Arg3'])
                    if len(vrf_target.split(":")) ==3:
                        vrf_target =":".join(vrf_target.split(":")[1:])
                    routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vrf_target = vrf_target)
                    self.config_row["Parsed_size"] = 7
                else:
                        vrf_target = str(self.config_row['Arg2'])
                        if len(vrf_target.split(":")) ==3:
                            vrf_target =":".join(vrf_target.split(":")[1:])
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vrf_target = vrf_target)
                        self.config_row["Parsed_size"] = 6
            case 'vrf-table-label':
                value = 'True'
                routing_instance.add_routing_instance_config_kv(routing_instance_name,config_name, self.config_row['Arg1'] ,  value )
                self.config_row["Parsed_size"] = 5
            case 'no-vrf-propagate-ttl':
                value = 'True'
                routing_instance.add_routing_instance_config_kv(routing_instance_name,config_name, self.config_row['Arg1'] ,  value )
                self.config_row["Parsed_size"] = 5
            case 'vlan-id':
                vlan_id = self.config_row['Arg2']
                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vlan_id = vlan_id)
                self.config_row["Parsed_size"] = 6
            case 'routing-interface':
                routing_interface = self.config_row['Arg2']
                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  routing_interface = routing_interface)
                self.config_row["Parsed_size"] = 6
            case 'route-distinguisher':
                route_distinguisher = str(self.config_row['Arg2'])
                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  route_distinguisher = route_distinguisher)
                self.config_row["Parsed_size"] = 6
            case 'bridge-domains':
                config_name = self.config_row['Arg1']
                config_value = self.config_row['Arg2']
                match self.config_row['Arg3']:
                    case 'interface':
                        interface = self.config_row['Arg4'] 
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  interface = interface)
                    case 'vlan-id':
                        vlan_id = self.config_row['Arg4'] 
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vlan_id = vlan_id)
                self.config_row["Parsed_size"] = 8
            case 'vrf-import':
                vrf_import = self.config_row['Arg2']
                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vrf_import = vrf_import)
                self.config_row["Parsed_size"] = 6
            case 'vrf-export':
                vrf_export = self.config_row['Arg2']
                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vrf_export = vrf_export)
                self.config_row["Parsed_size"] = 6
            case 'provider-tunnel':
                provider_tunnel = 'True'
                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  provider_tunnel = provider_tunnel)
                self.config_row["Parsed_size"] = 5
                match self.config_row['Arg2']:
                    case 'ldp-p2mp':
                        ldp_p2mp = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  ldp_p2mp = ldp_p2mp)
                        self.config_row["Parsed_size"] = 6
                    case 'ingress-replication':
                        ingress_replication = 'True'
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  ingress_replication = ingress_replication)
                        self.config_row["Parsed_size"] = 6
                        match self.config_row['Arg3']:
                            case 'label-switched-path':
                                label_switched_path = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  label_switched_path = label_switched_path)
                                self.config_row["Parsed_size"] = 7
                    case 'family':
                        family = self.config_row['Arg3']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                        self.config_row["Parsed_size"] = 7
                        match self.config_row['Arg4']:
                            case 'mdt':
                                mdt = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  mdt = mdt)
                                self.config_row["Parsed_size"] = 8                        
                                match self.config_row['Arg5']:
                                    case 'threshold':
                                        threshold = 'True'
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  threshold = threshold)
                                        self.config_row["Parsed_size"] = 9                        
                                        match self.config_row['Arg6']:
                                            case 'group':
                                                group = self.config_row['Arg7']
                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  threshold = threshold)
                                                self.config_row["Parsed_size"] = 11                       
                                                match self.config_row['Arg8']:
                                                    case 'source':
                                                        source = self.config_row['Arg9']
                                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  source = source)
                                                        self.config_row["Parsed_size"] = 13                       
                                                        match self.config_row['Arg10']:
                                                            case 'rate':
                                                                rate = self.config_row['Arg11']
                                                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  rate = rate)
                                                                self.config_row["Parsed_size"] = 15                      
                                    case 'tunnel-limit':
                                        tunnel_limit = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  tunnel_limit = tunnel_limit)
                                        self.config_row["Parsed_size"] = 10                        
                                    case 'group-range':
                                        group_range = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  group_range = group_range)
                                        self.config_row["Parsed_size"] = 10                        
                            case 'pim-asm':
                                pim_asm = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  pim_asm = pim_asm)
                                self.config_row["Parsed_size"] = 6                        
                                match self.config_row['Arg5']:
                                    case 'group-address':
                                        group_address = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  group_address = group_address)
                                        self.config_row["Parsed_size"] = 10                        
                            case 'pim-ssm':
                                pim_ssm = 'True'
                                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  pim_ssm = pim_ssm)
                                self.config_row["Parsed_size"] = 6                        
                                match self.config_row['Arg5']:
                                    case 'group-address':
                                        group_address = self.config_row['Arg6']
                                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  group_address = group_address)
                                        self.config_row["Parsed_size"] = 10                        
            case 'vrf-advertise-selective':
                vrf_advertise_selective = 'True'
                routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  vrf_advertise_selective = vrf_advertise_selective)
                self.config_row["Parsed_size"] = 5
                match self.config_row['Arg2']:
                    case 'family':
                        family = self.config_row['Arg3']
                        routing_instance.add_routing_instance(routing_instance_name ,config_name,config_value,config_type,config_type_name,  family = family)
                        self.config_row["Parsed_size"] = 7               
        return routing_instance
   
    def _parse_protocol(self, protocol):
        
        protocol_name = self.config_row['Name']
        config_name = '-'
        config_value = '-'
        family_type = '-'
        config_type= '-'
        config_type_name = '-'

        match protocol_name:
            case 'bgp':
                config_name = self.config_row['Arg1']
                config_value = '-'
                match config_name:
                    case 'log-updown':
                        log_updown = 'True'
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], log_updown) 
                        self.config_row["Parsed_size"] = 5      
                    case 'group':
                        config_name = self.config_row['Arg1']
                        config_value = self.config_row['Arg2']
                        match self.config_row['Arg3']:
                            case 'bmp':
                                bmp = 'True'
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, bmp = bmp)
                                self.config_row["Parsed_size"] = 7  
                                match self.config_row['Arg4']:
                                    case 'monitor':
                                        bmp_monitor = self.config_row['Arg5']
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, bmp_monitor = bmp_monitor)
                                        self.config_row["Parsed_size"] = 9  
                            case 'local-as':
                                local_as = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, local_as = local_as)
                                self.config_row["Parsed_size"] = 8  
                            case 'accept-remote-nexthop':
                                accept_remote_nexthop = 'True'
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, accept_remote_nexthop = accept_remote_nexthop)
                                self.config_row["Parsed_size"] = 7  
                            case 'cluster':
                                cluster_address = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, cluster_address = cluster_address)
                                self.config_row["Parsed_size"] = 8  
                            case 'multihop':
                                multihop = self.config_row['Arg4']
                                if type(multihop) is float:
                                    if np.isnan(multihop):
                                        multihop = ''                              
                                if len(multihop) ==0:
                                    multihop = 'True'
                                    self.config_row["Parsed_size"] = 7
                                else:
                                    self.config_row["Parsed_size"] = 8  
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, multihop = multihop)
                            case 'type':
                                group_type = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, group_type = group_type)
                                self.config_row["Parsed_size"] = 8  
                            case 'local-address':
                                local_address = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, local_address = local_address)
                                self.config_row["Parsed_size"] = 8  
                                match self.config_row['Arg6']: 
                                    case 'deactivate':
                                        deactivate = 'True'
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, deactivate = deactivate)
                                        self.config_row["Parsed_size"] = 10
                                match self.config_row['Arg11']: 
                                    case 'advertise-inactive':
                                        advertise_inactive = 'True'
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, advertise_inactive = advertise_inactive)
                                        self.config_row["Parsed_size"] = 15
                            case 'peer-as':
                                automomous_system = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, automomous_system = automomous_system)
                                self.config_row["Parsed_size"] = 8  
                            case 'export':
                                export_policy = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, export_policy = export_policy)
                                self.config_row["Parsed_size"] = 8  
                            case 'import':
                                import_policy = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, import_policy = import_policy)
                                self.config_row["Parsed_size"] = 8  
                            case 'advertise-inactive':
                                advertise_inactive = 'True'
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, advertise_inactive = advertise_inactive)
                                self.config_row["Parsed_size"] = 7  
                            case 'as-override':
                                as_override = 'True'
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, as_override = as_override)
                                self.config_row["Parsed_size"] = 7  
                            case 'family':
                                family_type = self.config_row['Arg4']
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'unicast':
                                        unicast = 'True'
                                        protocol.add_protocol(protocol_name,config_name,config_value,config_type_name,family_type, family_type,  unicast = unicast)
                                        self.config_row["Parsed_size"] += 1
                                    case 'labeled-unicast':
                                        labeled_unicast = 'True'
                                        protocol.add_protocol(protocol_name,config_name,config_value,config_type_name,family_type, family_type,  labeled_unicast = labeled_unicast)
                                        self.config_row["Parsed_size"] += 1
                                        match self.config_row['Arg6']:
                                            case 'resolve-vpn':
                                                resolve_vpn = 'True'
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  resolve_vpn = resolve_vpn)
                                                self.config_row["Parsed_size"] += 1
                                            case 'rib':
                                                rib_instance = self.config_row['Arg7']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  rib_instance = rib_instance)
                                                self.config_row["Parsed_size"] += 2
                                            case 'rib-group':
                                                rib_group = self.config_row['Arg7']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  rib_group = rib_group)
                                                self.config_row["Parsed_size"] += 2                                               
                                    case 'signaling':
                                        signaling = 'True'
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  signaling = signaling)
                                        self.config_row["Parsed_size"] += 1
                                    case 'flow':
                                        flow = 'True'
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, flow = flow)
                                        self.config_row["Parsed_size"] += 1
                                        match self.config_row['Arg6']:
                                            case 'resolve-vpn':
                                                resolve_vpn = 'True'
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  resolve_vpn = resolve_vpn)
                                                self.config_row["Parsed_size"] += 1
                                            case 'accepted-prefix-limit':
                                                accepted_prefix_limit = 'True'
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True,  accepted_prefix_limit = accepted_prefix_limit)
                                                self.config_row["Parsed_size"] += 1
                                                match self.config_row['Arg7']:
                                                    case 'maximum':
                                                        maximum = self.config_row['Arg8']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  maximum = maximum)
                                                        self.config_row["Parsed_size"] += 2
                                                    case 'teardown':
                                                        teardown = 'True'
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  teardown = teardown)
                                                        self.config_row["Parsed_size"] += 1
                                            case 'no-validate':
                                                no_validate = self.config_row['Arg7']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  no_validate = no_validate)
                                                self.config_row["Parsed_size"] += 2
                                            case 'rib':
                                                rib = self.config_row['Arg7']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  rib = rib)
                                                self.config_row["Parsed_size"] += 2
                                            case 'rib-group':
                                                rib_group = self.config_row['Arg7']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  rib_group = rib_group)
                                                self.config_row["Parsed_size"] += 2
                                    case 'inet':
                                        match self.config_row['Arg5']:
                                            case 'labeled-unicast':
                                                labeled_unicast = 'True'
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  labeled_unicast = labeled_unicast)
                                                self.config_row["Parsed_size"] += 1
                                                match self.config_row['Arg6']:
                                                    case 'resolve-vpn':
                                                        resolve_vpn = 'True'
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  resolve_vpn = resolve_vpn)
                                                        self.config_row["Parsed_size"] += 1
                                                    case 'rib':
                                                        rib = self.config_row['Arg7']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  rib = rib)
                                                        self.config_row["Parsed_size"] += 2
                                                    case 'rib-group':
                                                        rib_group = self.config_row['Arg7']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  rib_group = rib_group)
                                                        self.config_row["Parsed_size"] += 2                                               
                            case 'neighbor':
                                neighbor = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  neighbor = neighbor)
                                self.config_row["Parsed_size"] = 8
            case 'igmp':
                match self.config_row['Arg1']:
                    case 'interface':
                        interface_name = self.config_row['Arg2']
                        ## Add Interface_id and if applicable  unit,vlan_tag, channel
                        interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                        protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                        if channel:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                        if unit:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                        if vlan_tag:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        
                        self.config_row["Parsed_size"] = 6      
                        match self.config_row['Arg3']:
                            case 'version':
                                version = self.config_row['Arg4']
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value, config_type, config_type_name,  version = version)
                                self.config_row["Parsed_size"] = 8      
                            case 'static':
                                static = 'True'
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value, config_type, config_type_name,ignore_duplicates=True,  static = static)
                                match self.config_row['Arg4']:
                                    case 'group':
                                        multicast_group_address = self.config_row['Arg5']
                                        protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value, config_type, config_type_name,  ignore_duplicates=True, multicast_group_address = multicast_group_address)
                                        self.config_row["Parsed_size"] = 9
                                        match self.config_row['Arg6']:
                                            case 'group-count':
                                                multicast_group_count = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   multicast_group_count = multicast_group_count)
                                                self.config_row["Parsed_size"] = 11
                                            case 'group-increment':
                                                multicast_group_increment = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   multicast_group_increment = multicast_group_increment)
                                                self.config_row["Parsed_size"] = 11
                                            case 'source':
                                                multicast_group_source = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   multicast_group_source = multicast_group_source)
                                                self.config_row["Parsed_size"] = 11
            case 'l2circuit':
                match self.config_row['Arg1']:
                    case 'neighbor':
                        if self.config_row['Arg3'] == "interface":
                            interface_name = self.config_row['Arg4']
                            neighbor = self.config_row['Arg2']
                            protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, ignore_duplicates=True,  neighbor = neighbor)
                            ## Add Interface_id and if applicable  unit,vlan_tag, channel
                            interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                            if channel:
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                            if unit:
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                            if vlan_tag:
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        
                            self.config_row["Parsed_size"] = 8      
                            match self.config_row['Arg5']:
                                case 'virtual-circuit-id':
                                    virtual_circuit_id = self.config_row['Arg6']
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   virtual_circuit_id = virtual_circuit_id)
                                    self.config_row["Parsed_size"] += 2
                                case 'description':
                                    description = self.config_row['Arg6']
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   description = description)
                                    self.config_row["Parsed_size"] += 2
                                case 'no-control-word':
                                    no_control_word = 'True'
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   no_control_word = no_control_word)
                                    self.config_row["Parsed_size"] += 1
                                case 'encapsulation-type':
                                    encapsulation_type = self.config_row['Arg6']
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   encapsulation_type = encapsulation_type)
                                    self.config_row["Parsed_size"] += 2
                                case 'ignore-encapsulation-mismatch':
                                    ignore_encapsulation_mismatch = 'True'
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   ignore_encapsulation_mismatch = ignore_encapsulation_mismatch)
                                    self.config_row["Parsed_size"] += 1
                                case 'ignore-mtu-mismatch':
                                    ignore_mtu_mismatch = 'True'
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   ignore_mtu_mismatch = ignore_mtu_mismatch)
                                    self.config_row["Parsed_size"] += 1
                                case 'pseudowire-status-tlv':
                                    pseudowire_status_tlv = 'True'
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   pseudowire_status_tlv = pseudowire_status_tlv)
                                    self.config_row["Parsed_size"] += 1
                                case 'revert-time':
                                    revert_time = self.config_row['Arg6']
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   revert_time = revert_time)
                                    self.config_row["Parsed_size"] += 2
                                case 'backup-neighbor':
                                    backup_neighbor = self.config_row['Arg6']
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   backup_neighbor = backup_neighbor)
                                    self.config_row["Parsed_size"] += 2
                                    match self.config_row['Arg7']:
                                        case 'virtual-circuit-id':
                                            virtual_circuit_id = self.config_row['Arg8']
                                            protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   virtual_circuit_id = virtual_circuit_id)
                                            self.config_row["Parsed_size"] += 2
                                        case 'hot-standby':
                                            hot_standby = 'True'
                                            protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   hot_standby = hot_standby)
                                            self.config_row["Parsed_size"] += 1
                    case 'local-switching':
                        if self.config_row['Arg2'] == "interface":
                            interface_name = self.config_row['Arg3']
                            ## Add Interface_id and if applicable  unit,vlan_tag, channel
                            interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                            if channel:
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                            if unit:
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                            if vlan_tag:
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        
                            local_switching ='True'
                            protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,  ignore_duplicates=True, local_switching = local_switching)
                            self.config_row["Parsed_size"] = 7      
                            match self.config_row['Arg4']:
                                case 'description':
                                    description = self.config_row['Arg5']
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   description = description)
                                    self.config_row["Parsed_size"] += 2
                                case 'encapsulation-type':
                                    encapsulation_type = self.config_row['Arg5']
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   encapsulation_type = encapsulation_type)
                                    self.config_row["Parsed_size"] += 2
                                case 'ignore-encapsulation-mismatch':
                                    ignore_encapsulation_mismatch = 'True'
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   ignore_encapsulation_mismatch = ignore_encapsulation_mismatch)
                                    self.config_row["Parsed_size"] += 1
                                case 'ignore-mtu-mismatch':
                                    ignore_mtu_mismatch = 'True'
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   ignore_mtu_mismatch = ignore_mtu_mismatch)
                                    self.config_row["Parsed_size"] += 1
                                case 'end-interface':
                                    if self.config_row['Arg5'] == "interface":
                                        end_interface_name = self.config_row['Arg6']
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   end_interface_name = end_interface_name)
                                        self.config_row["Parsed_size"] = 10
                                        if len(end_interface_name.split(".")) ==2:
                                            end_interface_vlan_tag = end_interface_name.split(".")[1]
                                            protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,  ignore_duplicates=True,  end_interface_vlan_tag = end_interface_vlan_tag)
            case 'layer2-control':
                match self.config_row['Arg1']:
                    case 'nonstop-bridging':
                        nonstop_bridging = 'True'
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], nonstop_bridging)
                        self.config_row["Parsed_size"] = 5      
            case 'ldp':
                config_name = self.config_row['Arg1']
                match config_name:
                    case 'interface':
                        interface_name = self.config_row['Arg2']
                        ## Add Interface_id and if applicable  unit,vlan_tag, channel
                        interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                        protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                        if channel:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                        if unit:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                        if vlan_tag:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        
                                        
                        self.config_row["Parsed_size"] = 6      
                    case 'p2mp':
                        p2mp = "True"
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], p2mp)
                        self.config_row["Parsed_size"] = 5      
                    case 'session-group':
                        session_group = self.config_row['Arg2']
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], session_group)
                        self.config_row["Parsed_size"] = 6  
                        match self.config_row['Arg3']:
                            case 'authentication-key':
                                 authentication_key = self.config_row['Arg4']
                                 protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg3'], authentication_key)
                                 self.config_row["Parsed_size"] = 8  
                    case 'entropy-label':
                        entropy_label = "True"
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], entropy_label)
                        self.config_row["Parsed_size"] = 5      
                        match self.config_row['Arg2']:
                            case 'ingress-policy':
                                 ingress_policy = self.config_row['Arg3']
                                 protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg3'], ingress_policy)
                                 self.config_row["Parsed_size"] = 7                                 
            case 'lldp':
                config_name = self.config_row['Arg1']
                match self.config_row['Arg1']:
                    case 'advertisement-interval':
                            advertisement_interval = self.config_row['Arg2']
                            protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], advertisement_interval)
                            self.config_row["Parsed_size"] = 6      
                    case 'hold-multiplier':
                            hold_multiplier = self.config_row['Arg2']
                            protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], hold_multiplier)
                            self.config_row["Parsed_size"] = 6      
                    case 'port-id-subtype':
                            port_id_subtype = self.config_row['Arg2']
                            protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], port_id_subtype)
                            self.config_row["Parsed_size"] = 6      
                    case 'interface':
                            interface = self.config_row['Arg2']
                            protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], interface)
                            self.config_row["Parsed_size"] = 6      
            case 'mld':
                match self.config_row['Arg1']:
                    case 'interface':
                        interface_name = self.config_row['Arg2']
                        ## Add Interface_id and if applicable  unit,vlan_tag, channel
                        interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                        protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                        if channel:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                        if unit:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                        if vlan_tag:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        

                        self.config_row["Parsed_size"] = 6
                        match self.config_row['Arg3']:
                            case 'version':
                                version = self.config_row['Arg4']
                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   version = version)
                                self.config_row["Parsed_size"] = 8
                            case 'static':
                                static = 'True'
                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   ignore_duplicates=True, static = static)
                                match self.config_row['Arg4']:
                                    case 'group':
                                        multicast_group_address = self.config_row['Arg5']
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   ignore_duplicates=True, multicast_group_address = multicast_group_address)
                                        self.config_row["Parsed_size"] = 9
                                        match self.config_row['Arg6']:
                                            case 'group-count':
                                                multicast_group_count = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   multicast_group_count = multicast_group_count)
                                                self.config_row["Parsed_size"] = 11
                                            case 'group-increment':
                                                multicast_group_increment = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   multicast_group_increment = multicast_group_increment)
                                                self.config_row["Parsed_size"] = 11
                                            case 'source':
                                                multicast_group_source = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   multicast_group_source = multicast_group_source)
                                                self.config_row["Parsed_size"] = 11
            case 'mpls':
                config_name = self.config_row['Arg1']
                match config_name:
                    case 'ipv6-tunneling':
                        ipv6_tunneling = "True"
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], ipv6_tunneling)
                        self.config_row["Parsed_size"] = 5      
                    case 'no-propagate-ttl':
                        no_propagate_ttl = "True"
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], no_propagate_ttl)
                        self.config_row["Parsed_size"] = 5      
                    case 'explicit-null':
                        explicit_null = "True"
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], explicit_null)
                        self.config_row["Parsed_size"] = 5      
                    case 'icmp-tunneling':
                        icmp_tunneling = "True"
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], icmp_tunneling)
                        self.config_row["Parsed_size"] = 5      
                    case 'record':
                        record = "True"
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], record)
                        self.config_row["Parsed_size"] = 5
                    case 'interface':
                        interface_name = self.config_row['Arg2']
                        ## Add Interface_id and if applicable  unit,vlan_tag, channel
                        interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                        protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                        if channel:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                        if unit:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                        if vlan_tag:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        

                        self.config_row["Parsed_size"] = 6
                        match self.config_row['Arg3']:
                            case 'admin-group':
                                if  self.config_row['Arg4'] == "[":
                                    ## The functions returns column no of closing bracket
                                    admin_group, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   admin_group = admin_group)
                                else:
                                    admin_group = self.config_row['Arg4']
                                    protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   admin_group = admin_group)
                                    self.config_row["Parsed_size"] = 8
                    case 'statistics':
                        statistics = "True"
                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  statistics = statistics)
                        self.config_row["Parsed_size"] = 5
                        match self.config_row['Arg2']:
                            case 'interval':
                                interval = self.config_row['Arg3']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  interval = interval)
                                self.config_row["Parsed_size"] = 7
                            case 'file':
                                file = self.config_row['Arg3']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  file = file)
                                self.config_row["Parsed_size"] = 7
                                match self.config_row['Arg4']:
                                    case 'size':
                                        max_file_size = self.config_row['Arg5']
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  max_file_size = max_file_size)
                                        self.config_row["Parsed_size"] = 9
                                        ## Context means the size is for value in context i.e. files
                                        context = self.config_row['Arg6']
                                        if pd.isnull(self.config_row['Arg7']):
                                            protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  context = context)
                                            self.config_row["Parsed_size"] = 10                                
                                        else:
                                            max_no_of_files = self.config_row['Arg7']
                                            protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  max_no_of_files = max_no_of_files)
                                            self.config_row["Parsed_size"] = 11                               
                                        if not pd.isnull(self.config_row['Arg8']):
                                            file_permissions = self.config_row['Arg8']
                                            protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  file_permissions = file_permissions)
                                            self.config_row["Parsed_size"] = 12                                
                                            
                    case 'log-updown':
                        log_updown = self.config_row['Arg2']
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], log_updown)
                        self.config_row["Parsed_size"] = 6
                    case 'admin-groups':
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg2'], self.config_row['Arg3'])
                        self.config_row["Parsed_size"] = 7
                    case 'label-range':
                        match self.config_row['Arg2']:
                            case 'static-label-range': 
                                static_label_range = self.config_row['Arg3'] + ' - ' + self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  static_label_range = static_label_range)
                                self.config_row["Parsed_size"] = 8
                    case 'label-switched-path':
                        config_name = self.config_row['Arg1']
                        config_value = self.config_row['Arg2']
                        self.config_row["Parsed_size"] = 6
                        match self.config_row['Arg3']:
                            case 'to':
                                destination_address = self.config_row['Arg4'] 
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  destination_address = destination_address)
                                self.config_row["Parsed_size"] = 8
                            case 'ldp-tunneling':
                                ldp_tunneling = 'True'
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  ldp_tunneling = ldp_tunneling)
                                self.config_row["Parsed_size"] = 7
                                match self.config_row['Arg5']:
                                    case 'protect':
                                        protect = 'True'
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  protect = protect)
                                        self.config_row["Parsed_size"] = 9
                                        match self.config_row['Arg10']:
                                            case 'node-link-protection':
                                                node_link_protection = 'True'
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  node_link_protection = node_link_protection)
                                                self.config_row["Parsed_size"] = 14
                            case 'node-link-protection':
                                node_link_protection = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  node_link_protection = node_link_protection)
                                self.config_row["Parsed_size"] = 7
                            case 'primary':
                                primary =  self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  primary = primary)
                                self.config_row["Parsed_size"] = 8
                            case 'secondary':
                                secondary =  self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  secondary = secondary)
                                self.config_row["Parsed_size"] = 8
                            case 'install':
                                install =  self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  install = install)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg6']:
                                    case 'protect':
                                        ensure_protection_of_node = self.config_row['Arg5']
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  ensure_protection_of_node = ensure_protection_of_node)
                                        self.config_row["Parsed_size"] = 10
                                if not pd.isnull(self.config_row['Arg11']):
                                    node_link_protection = self.config_row['Arg11']
                                    if  node_link_protection == 'node-link-protection':
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  node_link_protection = node_link_protection)
                                        self.config_row["Parsed_size"] = 15
                            case 'adaptive':
                                adaptive =  'True'
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  adaptive = adaptive)
                                self.config_row["Parsed_size"] = 7
                            case 'apply-groups':
                                apply_groups =  self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  apply_groups = apply_groups)
                                self.config_row["Parsed_size"] = 8
                            case 'from':
                                source_source_address =  self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  source_source_address = source_source_address)
                                self.config_row["Parsed_size"] = 8
                    case 'path':
                        path = self.config_row['Arg2']
                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  patn = path)
                        self.config_row["Parsed_size"] = 6
                        if not pd.isnull(self.config_row['Arg3']):
                            transit_path_router = self.config_row['Arg3']
                            protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  transit_path_router = transit_path_router)
                            self.config_row["Parsed_size"] = 7
                            if not pd.isnull(self.config_row['Arg4']):
                                transit_path_router_hop = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  transit_path_router_hop = transit_path_router_hop)
                                self.config_row["Parsed_size"] = 8                            
            case 'msdp':
                match self.config_row['Arg1']:
                    case 'group':
                        group = self.config_row['Arg2']
                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True ,  group = group)
                        self.config_row["Parsed_size"] = 6      
                        match self.config_row['Arg3']:
                            case 'mode':
                                mode = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  mode = mode)
                                self.config_row["Parsed_size"] += 2  
                            case 'local-address':
                                local_address = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  local_address = local_address)
                                self.config_row["Parsed_size"] += 2  
                            case 'peer':
                                peer = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  peer = peer)
                                self.config_row["Parsed_size"] += 2  
            case 'oam':
                config_name = '-'
                interface_name ='-'
                config_type= '-'
                config_type_name = '-'
                match self.config_row['Arg1']:
                    case 'ethernet':
                        configuration = self.config_row['Arg1']
                        ## Add after building Key
                        config_name = self.config_row['Arg2']
                        match self.config_row['Arg2']:
                            case 'link-fault-management':
                                self.config_row["Parsed_size"] = 5      
                                ## Add after building Key
                                self.config_row["Parsed_size"] = 6      
                                match self.config_row['Arg3']:
                                    case 'action-profile':
                                        config_value = self.config_row['Arg3']
                                        match self.config_row['Arg4']:
                                            case 'link_degrade':
                                                config_type = self.config_row['Arg4']
                                                config_type_name = self.config_row['Arg5']
                                                protocol.add_protocol(protocol_name,config_name,config_value,config_type, config_type_name, family_type,ignore_duplicates=True,configuration = configuration)
                                                self.config_row["Parsed_size"] = 8      
                                                match self.config_row['Arg5']:
                                                    case 'event': 
                                                        ## Added as part ok key
                                                        event = self.config_row['Arg6']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name, family_type,ignore_duplicates=True, event = event)
                                                        self.config_row["Parsed_size"] = 9      
                                                        match self.config_row['Arg6']:
                                                            case 'link-event-rate':
                                                                link_event_rate = 'True'
                                                                protocol.add_protocol(protocol_name,config_name,config_value,config_type, config_type_name, family_type,ignore_duplicates=True, link_event_rate = link_event_rate)
                                                                self.config_row["Parsed_size"] = 10      
                                                                match self.config_row['Arg7']:
                                                                    case 'frame-period-summary':
                                                                        frame_period_summary = self.config_row['Arg8']
                                                                        protocol.add_protocol(protocol_name,config_name,config_value,config_type, config_type_name, family_type,ignore_duplicates=True, frame_period_summary = frame_period_summary)
                                                                        self.config_row["Parsed_size"] = 12     
                                                    case 'action':
                                                        ## Added as part ok key
                                                        action = self.config_row['Arg6']
                                                        protocol.add_protocol(protocol_name,config_name,config_value,config_type, config_type_name,  family_type, ignore_duplicates=True, action = action)
                                                        self.config_row["Parsed_size"] = 10     
                                            case 'syslog_only':
                                                config_type = self.config_row['Arg4']
                                                config_type_name = self.config_row['Arg5']
                                                protocol.add_protocol(protocol_name,config_name,config_value,config_type, config_type_name, family_type,ignore_duplicates=True,configuration = configuration)
                                                self.config_row["Parsed_size"] = 8      
                                                match self.config_row['Arg5']:
                                                    case 'event':
                                                        event = self.config_row['Arg6']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name, family_type,ignore_duplicates=True, event = event)
                                                        self.config_row["Parsed_size"] = 10     
                                                    case 'action':
                                                        action = self.config_row['Arg6']
                                                        protocol.add_protocol(protocol_name,config_name,config_value,config_type, config_type_name,  family_type, ignore_duplicates=True, action = action)
                                                        self.config_row["Parsed_size"] = 10     
                                    case 'interface':
                                        config_value = self.config_row['Arg3']
                                        interface_name = self.config_row['Arg4']
                                        config_type = self.config_row['Arg5']
                                        if self.config_row['Arg6'] == '[':
                                            config_type_name = '-'
                                        else:
                                            config_type_name = self.config_row['Arg6']
                                        ## Add Interface_id and if applicable  unit,vlan_tag, channel
                                        interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                                        protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                                        if channel:
                                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                                        if unit:
                                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                                        if vlan_tag:
                                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        
                                        match self.config_row['Arg5']:
                                            case 'apply-action-profile':
                                                apply_action_profile, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, apply_action_profile = apply_action_profile)
                                            case 'link-discovery':
                                                link_discovery= self.config_row['Arg6']
                                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, link_discovery = link_discovery)
                                                self.config_row["Parsed_size"] = 10
                                            case 'negotiation-options':
                                                negotiation_options= self.config_row['Arg6']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value,config_type, config_type_name,  ignore_duplicates=True, negotiation_options = negotiation_options)
                                                self.config_row["Parsed_size"] = 10
                                            case 'pdu-interval':
                                                pdu_interval= self.config_row['Arg6']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, pdu_interval = pdu_interval)
                                                self.config_row["Parsed_size"] = 10
                                            case 'pdu-threshold':
                                                pdu_threshold= self.config_row['Arg6']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value,config_type, config_type_name,  ignore_duplicates=True, pdu_threshold = pdu_threshold)
                                                self.config_row["Parsed_size"] = 10
                            case 'connectivity-fault-management':
                                match self.config_row['Arg5']:
                                    case 'maintenance-association':
                                        config_name = self.config_row['Arg5']
                                        config_value = self.config_row['Arg6']
                                match self.config_row['Arg4']:
                                    case 'sla-iterator-profiles':
                                        config_name = self.config_row['Arg4']
                                        config_value = self.config_row['Arg5']
                                connectivity_fault_management = 'True'
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, connectivity_fault_management = connectivity_fault_management)
                                self.config_row["Parsed_size"] = 6
                                match self.config_row['Arg3']:
                                    case 'performance-monitoring':
                                        match self.config_row['Arg4']:
                                            case 'delegate-server-processing':
                                                delegate_server_processing = 'True'
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, delegate_server_processing = delegate_server_processing)
                                                self.config_row["Parsed_size"] = 8
                                            case 'hardware-assisted-keepalives':
                                                hardware_assisted_keepalives = self.config_row['Arg5']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, hardware_assisted_keepalives = hardware_assisted_keepalives)
                                                self.config_row["Parsed_size"] = 9
                                            case 'enhanced-sla-iterator':
                                                enhanced_sla_iterator = 'True'
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, enhanced_sla_iterator = enhanced_sla_iterator)
                                                self.config_row["Parsed_size"] = 8
                                            case 'measurement-interval':
                                                measurement_interval = self.config_row['Arg5']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, measurement_interval = measurement_interval)
                                                self.config_row["Parsed_size"] = 9
                                            case 'sla-iterator-profiles':
                                                match self.config_row['Arg6']:
                                                    case 'measurement-type':
                                                        measurement_type = self.config_row['Arg7']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, measurement_type = measurement_type)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'cycle-time':
                                                        cycle_time = self.config_row['Arg7']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, cycle_time = cycle_time)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'iteration-period':
                                                        iteration_period = self.config_row['Arg7']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, iteration_period = iteration_period)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'calculation-weight':
                                                        calculation_weight = self.config_row['Arg7'] + ' ' + self.config_row['Arg8']
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, calculation_weight = calculation_weight)
                                                        self.config_row["Parsed_size"] = 12
                                    case 'maintenance-domain':                                        
                                        maintenance_domain = self.config_row['Arg4']
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, maintenance_domain = maintenance_domain)
                                        self.config_row["Parsed_size"] = 8
                                        match self.config_row['Arg5']:
                                            case 'level':
                                                level =  self.config_row['Arg6']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,ignore_duplicates=True, level = level)
                                                self.config_row["Parsed_size"] = 10
                                            case 'mip-half-function':
                                                mip_half_function =  self.config_row['Arg6']
                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, mip_half_function = mip_half_function)
                                                self.config_row["Parsed_size"] = 10
                                            case 'maintenance-association':
                                                maintenance_association =  self.config_row['Arg6']
                                                ## Added as a config_name 
                                                self.config_row["Parsed_size"] = 10
                                                match self.config_row['Arg7']:
                                                    case 'continuity-check':
                                                        continuity_check =  'True'
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, continuity_check = continuity_check)
                                                        self.config_row["Parsed_size"] = 11
                                                        match self.config_row['Arg8']:
                                                            case 'interval':
                                                                interval =  self.config_row['Arg9']
                                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,ignore_duplicates=True, interval = interval)
                                                                self.config_row["Parsed_size"] = 13
                                                            case 'loss-threshold':
                                                                loss_threshold =  self.config_row['Arg9']
                                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,ignore_duplicates=True, loss_threshold = loss_threshold)
                                                                self.config_row["Parsed_size"] = 13
                                                            case 'hold-interval':
                                                                hold_interval =  self.config_row['Arg9']
                                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,ignore_duplicates=True, hold_interval = hold_interval)
                                                                self.config_row["Parsed_size"] = 13
                                                    case 'mep':
                                                        mep =  self.config_row['Arg8']                   
                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, mep = mep)
                                                        self.config_row["Parsed_size"] = 12
                                                        match self.config_row['Arg9']:
                                                            case 'interface':
                                                                interface =  self.config_row['Arg10']
                                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,ignore_duplicates=True, interface = interface)
                                                                ## Add Interface_id and if applicable  unit,vlan_tag, channel
                                                                interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface)
                                                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                                                                if channel:
                                                                    protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                                                                if unit:
                                                                    protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                                                                if vlan_tag:
                                                                    protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        
                                                                self.config_row["Parsed_size"] = 14
                                                            case 'direction':
                                                                direction =  self.config_row['Arg10']
                                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,ignore_duplicates=True, direction = direction)
                                                                self.config_row["Parsed_size"] = 14
                                                            case 'remote-mep':
                                                                remote_mep =  self.config_row['Arg10']
                                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,ignore_duplicates=True, remote_mep = remote_mep)
                                                                self.config_row["Parsed_size"] = 14
                                                                match self.config_row['Arg11']:
                                                                    case 'sla-iterator-profile':
                                                                        sla_iterator_profile =  self.config_row['Arg12']
                                                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True,sla_iterator_profile = sla_iterator_profile)
                                                                        self.config_row["Parsed_size"] = 16
                                                                        match self.config_row['Arg13']:
                                                                            case 'priority':
                                                                                priority =  self.config_row['Arg14']
                                                                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,ignore_duplicates=True, priority = priority)
                                                                                self.config_row["Parsed_size"] = 18                                                                       
            case 'ospf' | 'ospf3':
                config_name = self.config_row['Arg1']
                match self.config_row['Arg1']:
                    case 'traffic-engineering':
                        if type(self.config_row['Arg2']) is float:
                            if np.isnan(self.config_row['Arg2']):
                                traffic_engineering = 'True'
                                self.config_row["Parsed_size"] = 5
                        else:
                            if len(self.config_row['Arg2']) > 0:
                                traffic_engineering = self.config_row['Arg2']
                                self.config_row["Parsed_size"] = 6
                            else:
                                traffic_engineering = 'True'
                                self.config_row["Parsed_size"] = 5
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], traffic_engineering)                              
                    case 'area':
                        config_value = self.config_row['Arg2']
                        self.config_row["Parsed_size"] = 6      
                        match self.config_row['Arg3']:
                            case 'interface':
                                interface_name = self.config_row['Arg4']
                                ## Add Interface_id and if applicable  unit,vlan_tag, channel
                                interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                                protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                                if channel:
                                    protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                                if unit:
                                    protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                                if vlan_tag:
                                    protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        

                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'interface-type':
                                        interface_type = self.config_row['Arg6']
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type,  interface_type = interface_type)
                                        self.config_row["Parsed_size"] = 10                                         
                                        match self.config_row['Arg8']:
                                            case 'protect':
                                                protect = 'True'
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type,  protect = protect)
                                                self.config_row["Parsed_size"] = 12
                                                match self.config_row['Arg15']:
                                                    case 'node-link-protection':
                                                        node_link_protection = 'True'
                                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type, ignore_duplicates=True,  node_link_protection = node_link_protection)
                                                        self.config_row["Parsed_size"] = 19
                                    case 'node-link-protection':
                                        node_link_protection = 'True'
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type,ignore_duplicates=True,  node_link_protection = node_link_protection)
                                        self.config_row["Parsed_size"] = 9
                                    case 'bfd-liveness-detection':
                                        bfd_liveness_detection = 'True'
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type, ignore_duplicates=True, bfd_liveness_detection = bfd_liveness_detection)
                                        self.config_row["Parsed_size"] = 9
                                        match self.config_row['Arg6']:
                                            case 'minimum-interval':
                                                minimum_interval = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type,  minimum_interval = minimum_interval)
                                                self.config_row["Parsed_size"] = 11
                                            case 'multiplier':
                                                multiplier = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type, multiplier = multiplier)
                                                self.config_row["Parsed_size"] = 11
                                    case 'passive':
                                        passive = 'True'
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,  family_type,  passive = passive)
                                        self.config_row["Parsed_size"] = 9
            case 'pim':
                ## Get key columns first
                family_type= '-'
                match self.config_row['Arg3']:
                    case 'family':
                        family_type = self.config_row['Arg4']
                match self.config_row['Arg1']:
                    case 'join-load-balance':
                        join_load_balance = 'True'
                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  join_load_balance = join_load_balance)
                        self.config_row["Parsed_size"] = 5     
                    case 'interface':
                        interface_name = self.config_row['Arg2']
                        ## Add Interface_id and if applicable  unit,vlan_tag, channel
                        interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                        protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                        if channel:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                        if unit:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                        if vlan_tag:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        

                        self.config_row["Parsed_size"] = 6 
                        match self.config_row['Arg3']:
                            case 'mode':
                                mode = self.config_row['Arg4']
                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,family_type,  mode = mode)
                                self.config_row["Parsed_size"] = 8
                            case 'family':
                                family_type = self.config_row['Arg4']
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'bfd-liveness-detection':
                                        bfd_liveness_detection = 'True'
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type, ignore_duplicates=True,  bfd_liveness_detection = bfd_liveness_detection)
                                        self.config_row["Parsed_size"] = 9
                                        match self.config_row['Arg6']:
                                            case 'minimum-interval':
                                                minimum_interval = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type,  minimum_interval = minimum_interval)
                                                self.config_row["Parsed_size"] = 11
                                            case 'multiplier':
                                                multiplier = self.config_row['Arg7']
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name, family_type,  multiplier = multiplier)
                                                self.config_row["Parsed_size"] = 11
                    case 'rp':
                        rp = 'True'
                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, rp = rp)
                        rp_config = self.config_row['Arg2'] 
                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type, ignore_duplicates=True, rp_config = rp_config)
                        self.config_row["Parsed_size"] = 6   
                        match self.config_row['Arg3']:
                            case 'address':
                                address = self.config_row['Arg4']
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  address = address)
                                self.config_row["Parsed_size"] = 8
                            case 'process-non-null-as-null-register':
                                process_non_null_as_null_register = 'True'
                                protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  process_non_null_as_null_register = process_non_null_as_null_register)
                                self.config_row["Parsed_size"] = 7
                            case 'family':
                                family_type = self.config_row['Arg4']
                                match self.config_row['Arg5']:
                                    case 'address':
                                        address = self.config_row['Arg6']
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  address = address)
                                        self.config_row["Parsed_size"] = 10
                                    case 'priority':
                                        priority = self.config_row['Arg6']
                                        protocol.add_protocol(protocol_name,config_name,config_value, config_type, config_type_name,family_type,  priority = priority)
                                        self.config_row["Parsed_size"] = 10
            case 'rsvp':
                config_name = self.config_row['Arg1']
                match self.config_row['Arg1']:
                    case 'refresh-time':
                        refresh_time = self.config_row['Arg2']
                        protocol.add_protocol_config_kv(protocol_name,config_name, self.config_row['Arg1'], refresh_time)
                        self.config_row["Parsed_size"] = 6      
                    case 'interface':
                        interface_name = self.config_row['Arg2']
                        ## Add Interface_id and if applicable  unit,vlan_tag, channel
                        interface_id, unit,vlan_tag, channel  = self.get_interface_id(interface_name)
                        protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, interface_id = interface_id)                                        
                        if channel:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, channel = channel)                                        
                        if unit:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, unit = unit)                                        
                        if vlan_tag:
                            protocol.add_protocol_interface(protocol_name,interface_name,config_name,config_value,config_type, config_type_name,   ignore_duplicates=True, vlan_tag = vlan_tag)                                        

                        self.config_row["Parsed_size"] = 6 
                        match self.config_row['Arg3']:
                            case 'aggregate':
                                aggregate = 'True'
                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   aggregate = aggregate)
                                self.config_row["Parsed_size"] = 7
                            case 'reliable':
                                reliable = 'True'
                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   reliable = reliable)
                                self.config_row["Parsed_size"] = 7
                            case 'hello-interval':
                                hello_interval = self.config_row['Arg4']
                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   hello_interval = hello_interval)
                                self.config_row["Parsed_size"] = 8
                            case 'subscription':
                                subscription = self.config_row['Arg4']
                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   subscription = subscription)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg6']:
                                    case 'protect':
                                        protect = 'True'
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   protect = protect)
                                        self.config_row["Parsed_size"] = 10
                                        match self.config_row['Arg11']:
                                            case 'link-protection':
                                                link_protection = 'True'
                                                protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   link_protection = link_protection)
                                                self.config_row["Parsed_size"] = 15
                            case 'link-protection':
                                match self.config_row['Arg4']:
                                    case 'admin-group':
                                        admin_group_policy = self.config_row['Arg5']
                                        protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   admin_group_policy = admin_group_policy)
                                        self.config_row["Parsed_size"] = 9
                                        if  self.config_row['Arg6'] == "[":
                                            ## The functions returns column no of closing bracket
                                            admin_group, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                            protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   admin_group = admin_group)
                                        else:
                                            admin_group = self.config_row['Arg6']
                                            protocol.add_protocol_interface(protocol_name,interface_name, config_name,config_value, config_type, config_type_name,   admin_group = admin_group)
                                            self.config_row["Parsed_size"] = 10
        return protocol

    def _parse_firewall(self, firewall):
        match self.config_row['Name']:
            case 'family':
                family_interface = self.config_row['Arg1']
                filter_name = self.config_row['Arg3']
                match family_interface:
                    case 'ccc':
                        match self.config_row['Arg2']:
                            case 'filter':
                                match self.config_row['Arg4']:
                                    case 'interface-specific':
                                        interface_specific = 'True'
                                        term_name = '-'
                                        firewall.add_family(family_interface,filter_name,term_name,  interface_specific = interface_specific)
                                        self.config_row["Parsed_size"] = 8                                
                                    case 'term':
                                        term_name = self.config_row['Arg5']
                                        match self.config_row['Arg6']:
                                            case 'from':
                                                source = self.config_row['Arg7']
                                                match source:
                                                    case 'forwarding-class':
                                                        source_forwarding_class = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_forwarding_class = source_forwarding_class)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'user-vlan-1p-priority':
                                                        source_user_vlan_1p_priority = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_user_vlan_1p_priority = source_user_vlan_1p_priority)
                                                        self.config_row["Parsed_size"] = 12
                                            case 'then':
                                                action = self.config_row['Arg7']
                                                match action:
                                                    case 'accept':
                                                        action_accept = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,   action_accept = action_accept)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'count':
                                                        action_count = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,   action_count = action_count)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'forwarding-class':
                                                        action_forwarding_class = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_forwarding_class = action_forwarding_class)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'loss-priority':
                                                        action_loss_priority = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,   action_loss_priority = action_loss_priority)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'next':
                                                        action_next = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,   action_next = action_next)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'policer':
                                                        action_policer = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,   action_policer = action_policer)
                                                        self.config_row["Parsed_size"] = 12
                    case 'inet':
                        match self.config_row['Arg2']:
                            case 'filter':
                                match self.config_row['Arg4']:
                                    case 'interface-specific':
                                        interface_specific = 'True'
                                        term_name = '-'
                                        firewall.add_family(family_interface,filter_name,term_name,  interface_specific = interface_specific)
                                        self.config_row["Parsed_size"] = 8                                
                                    case 'term':
                                        term_name = self.config_row['Arg5']
                                        match self.config_row['Arg6']:
                                            case 'from':
                                                source = self.config_row['Arg7']
                                                match source:
                                                    case 'first-fragment':
                                                        first_fragment = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  first_fragment = first_fragment)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'tcp-established':
                                                        tcp_established = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  tcp_established = tcp_established)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'forwarding-class':
                                                        source_forwarding_class = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_forwarding_class = source_forwarding_class)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'source-prefix-list':
                                                        source_prefix_list = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_prefix_list = source_prefix_list)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'source-port':
                                                        source_port = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_port = source_port)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'destination-port':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            destination_port, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  destination_port = destination_port)
                                                        else:
                                                            destination_port = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  destination_port = destination_port)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'port':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_port, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_port = source_port)
                                                        else:
                                                            source_port = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_port = source_port)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'dscp':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_dscp, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_dscp = source_dscp)
                                                        else:
                                                            source_dscp = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_dscp = source_dscp)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'icmp-type':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_icmp_type, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_icmp_type = source_icmp_type)
                                                        else:
                                                            source_icmp_type = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_icmp_type = source_icmp_type)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'destination-address':
                                                        destination_address = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  destination_address = destination_address)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'destination-prefix-list':
                                                        destination_prefix_list = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  destination_prefix_list = destination_prefix_list)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'source-address':
                                                        source_source_address = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_source_address = source_source_address)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'protocol':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_protocol, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_protocol = source_protocol)
                                                        else:
                                                            source_protocol = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_protocol = source_protocol)
                                                            self.config_row["Parsed_size"] = 12
                                            case 'then':
                                                action = self.config_row['Arg7']
                                                match action:
                                                    case 'sample':
                                                        action_sample = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_sample = action_sample)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'accept':
                                                        action_accept = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_accept = action_accept)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'discard':
                                                        action_discard = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_discard = action_discard)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'reject':
                                                        action_reject = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_reject = action_reject)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'count':
                                                        action_count = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_count = action_count)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'policer':
                                                        action_policer = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_policer = action_policer)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'loss-priority':
                                                        action_loss_priority = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_loss_priority = action_loss_priority)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'forwarding-class':
                                                        action_forwarding_class = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_forwarding_class = action_forwarding_class)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'dscp':
                                                        action_dscp = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_dscp = action_dscp)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'routing-instance':
                                                        action_routing_instance = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_routing_instance = action_routing_instance)
                                                        self.config_row["Parsed_size"] = 12
                    case 'inet6':
                        match self.config_row['Arg2']:
                            case 'filter':
                                match self.config_row['Arg4']:
                                    case 'interface-specific':
                                        interface_specific = 'True'
                                        term_name = '-'
                                        firewall.add_family(family_interface,filter_name,term_name,  interface_specific = interface_specific)
                                        self.config_row["Parsed_size"] = 8                                
                                    case 'term':
                                        term_name = self.config_row['Arg5']
                                        match self.config_row['Arg6']:
                                            case 'from':
                                                source = self.config_row['Arg7']
                                                match source:
                                                    case 'first-fragment':
                                                        first_fragment = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  first_fragment = first_fragment)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'tcp-established':
                                                        tcp_established = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  tcp_established = tcp_established)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'forwarding-class':
                                                        source_forwarding_class = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_forwarding_class = source_forwarding_class)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'source-prefix-list':
                                                        source_prefix_list = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_prefix_list = source_prefix_list)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'source-port':
                                                        source_port = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_port = source_port)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'destination-port':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            destination_port, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  destination_port = destination_port)
                                                        else:
                                                            destination_port = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  destination_port = destination_port)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'port':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_port, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_port = source_port)
                                                        else:
                                                            source_port = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_port = source_port)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'dscp':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_dscp, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_dscp = source_dscp)
                                                        else:
                                                            source_dscp = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_dscp = source_dscp)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'icmp-type':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_icmp_type, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_icmp_type = source_icmp_type)
                                                        else:
                                                            source_icmp_type = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_icmp_type = source_icmp_type)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'destination-address':
                                                        destination_address = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  destination_address = destination_address)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'destination-prefix-list':
                                                        destination_prefix_list = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  destination_prefix_list = destination_prefix_list)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'source-address':
                                                        source_source_address = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  source_source_address = source_source_address)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'protocol':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_protocol, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_protocol = source_protocol)
                                                        else:
                                                            source_protocol = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_protocol = source_protocol)
                                                            self.config_row["Parsed_size"] = 12
                                                    # Net6 Only cases
                                                    
                                                    case 'next-header':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_next_header, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_next_header = source_next_header)
                                                        else:
                                                            source_next_header = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_next_header = source_next_header)
                                                            self.config_row["Parsed_size"] = 12
                                                    case 'traffic-class':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_traffic_class, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_traffic_class = source_traffic_class)
                                                        else:
                                                            source_traffic_class = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_traffic_class = source_traffic_class)
                                                            self.config_row["Parsed_size"] = 12
                                            case 'then':
                                                action = self.config_row['Arg7']
                                                match action:
                                                    case 'sample':
                                                        action_sample = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_sample = action_sample)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'accept':
                                                        action_accept = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_accept = action_accept)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'discard':
                                                        action_discard = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_discard = action_discard)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'reject':
                                                        action_reject = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_reject = action_reject)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'count':
                                                        action_count = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_count = action_count)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'policer':
                                                        action_policer = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_policer = action_policer)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'loss-priority':
                                                        action_loss_priority = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_loss_priority = action_loss_priority)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'forwarding-class':
                                                        action_forwarding_class = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_forwarding_class = action_forwarding_class)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'dscp':
                                                        action_dscp = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_dscp = action_dscp)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'routing-instance':
                                                        action_routing_instance = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_routing_instance = action_routing_instance)
                                                        self.config_row["Parsed_size"] = 12
                                                    # Net6 Only cases
                                                    case 'traffic-class':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            action_traffic_class, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  action_traffic_class = action_traffic_class)
                                                        else:
                                                            action_traffic_class = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  action_traffic_class = action_traffic_class)
                                                            self.config_row["Parsed_size"] = 12
                                
                        
                    case 'mpls':
                        match self.config_row['Arg2']:
                            case 'filter':
                                match self.config_row['Arg4']:
                                    case 'interface-specific':
                                        interface_specific = 'True'
                                        term_name = '-'
                                        firewall.add_family(family_interface,filter_name,term_name,  interface_specific = interface_specific)
                                        self.config_row["Parsed_size"] = 8                                
                                    case 'term':
                                        term_name = self.config_row['Arg5']
                                        match self.config_row['Arg6']:
                                            case 'then':
                                                action = self.config_row['Arg7']
                                                match action:
                                                    case 'sample':
                                                        action_sample = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_sample = action_sample)
                                                        self.config_row["Parsed_size"] = 11
                                                    case 'accept':
                                                        action_accept = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_accept = action_accept)
                                                        self.config_row["Parsed_size"] = 11                        
                    case 'vpls':
                        match self.config_row['Arg2']:
                            case 'filter':
                                match self.config_row['Arg4']:
                                    case 'interface-specific':
                                        interface_specific = 'True'
                                        term_name = '-'
                                        firewall.add_family(family_interface,filter_name,term_name,  interface_specific = interface_specific)
                                        self.config_row["Parsed_size"] = 8                                
                                    case 'term':
                                        term_name = self.config_row['Arg5']
                                        match self.config_row['Arg6']:
                                            case 'from':
                                                source = self.config_row['Arg7']
                                                match source:
                                                    case 'forwarding-class':
                                                       source_forwarding_class = self.config_row['Arg8']
                                                       firewall.add_family(family_interface,filter_name,term_name,  source_forwarding_class = source_forwarding_class)
                                                       self.config_row["Parsed_size"] = 12
                                                    case 'user-vlan-1p-priority':
                                                       source_user_vlan_1p_priority = self.config_row['Arg8']
                                                       firewall.add_family(family_interface,filter_name,term_name,  source_user_vlan_1p_priority = source_user_vlan_1p_priority)
                                                       self.config_row["Parsed_size"] = 12                
                                                    case 'traffic-type':
                                                        if  self.config_row['Arg8'] == "[":
                                                            ## The functions returns column no of closing bracket
                                                            source_traffic_type, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_traffic_type = source_traffic_type)
                                                        else:
                                                            source_traffic_type = self.config_row['Arg8']
                                                            firewall.add_family(family_interface,filter_name,term_name,  source_traffic_type = source_traffic_type)
                                                            self.config_row["Parsed_size"] = 12
                                            case 'then':
                                                action = self.config_row['Arg7']
                                                match action:
                                                    case 'accept':
                                                        action_accept = 'True'
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_accept = action_accept)
                                                        self.config_row["Parsed_size"] = 11                        
                                                    case 'count':
                                                        action_count = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_count = action_count)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'forwarding-class':
                                                        action_forwarding_class = self.config_row['Arg8']
                                                        firewall.add_family(family_interface,filter_name,term_name,  action_forwarding_class = action_forwarding_class)
                                                        self.config_row["Parsed_size"] = 12
                                                    case 'loss-priority':
                                                         action_loss_priority = self.config_row['Arg8']
                                                         firewall.add_family(family_interface,filter_name,term_name,  action_loss_priority = action_loss_priority)
                                                         self.config_row["Parsed_size"] = 12
                                                    case 'next':
                                                         action_next = self.config_row['Arg8']
                                                         firewall.add_family(family_interface,filter_name,term_name,  action_next = action_next)
                                                         self.config_row["Parsed_size"] = 12
                                                    case 'policer':
                                                         action_policer = self.config_row['Arg8']
                                                         firewall.add_family(family_interface,filter_name,term_name,  action_policer = action_policer)
                                                         self.config_row["Parsed_size"] = 12                    
            case 'policer':
                policer_name = self.config_row['Arg1']
                condition = self.config_row['Arg2']      
                match condition:
                    case 'if-exceeding':
                        condition_if_exceeding = 'True'
                        firewall.add_policer(policer_name, condition_if_exceeding = condition_if_exceeding)
                        self.config_row["Parsed_size"] = 6
                        parameter = self.config_row['Arg3']
                        match parameter:
                            case 'bandwidth-limit':
                                action_bandwidth_limit = self.config_row['Arg4']
                                firewall.add_policer(policer_name, action_bandwidth_limit = action_bandwidth_limit)
                                self.config_row["Parsed_size"] = 8                                
                            case 'burst-size-limit':
                                action_burst_size_limit = self.config_row['Arg4']
                                firewall.add_policer(policer_name, action_burst_size_limit = action_burst_size_limit)
                                self.config_row["Parsed_size"] = 8                                
                    case 'filter-specific':
                        condition_filter_specific = 'True'
                        firewall.add_policer(policer_name, condition_filter_specific = condition_filter_specific)
                        self.config_row["Parsed_size"] = 6
                    case 'logical-interface-policer':
                        condition_logical_interface_policer = 'True'
                        firewall.add_policer(policer_name, condition_logical_interface_policer = condition_logical_interface_policer)
                        self.config_row["Parsed_size"] = 6
                    case 'then':
                        action = 'True'
                        self.config_row["Parsed_size"] = 6
                        parameter = self.config_row['Arg3']
                        match parameter:
                            case 'discard':
                                action_discard = 'True'
                                firewall.add_policer(policer_name, action_discard = action_discard)
                                self.config_row["Parsed_size"] = 7
                            case 'loss-priority':
                                action_loss_priority = self.config_row['Arg4']
                                firewall.add_policer(policer_name, action_loss_priority = action_loss_priority)
                                self.config_row["Parsed_size"] = 8
                            case 'forwarding-class':
                                action_forwarding_class = self.config_row['Arg4']
                                firewall.add_policer(policer_name, action_forwarding_class = action_forwarding_class)
                                self.config_row["Parsed_size"] = 8               
            case 'filter':
                filter_name = self.config_row['Arg1']
                term = self.config_row['Arg2']
                match term:
                    case 'term': 
                        term_name = self.config_row['Arg3']
                        match self.config_row['Arg4']:
                            case 'from':
                                source = self.config_row['Arg4']
                                match self.config_row['Arg5']:
                                    case 'source-address':
                                        source_source_address = self.config_row['Arg6']
                                        firewall.add_filter_source(filter_name, term, term_name,source, source_source_address=source_source_address)
                                        self.config_row["Parsed_size"] = 10
                                    case 'destination-address':
                                        source_destination_address = self.config_row['Arg6']
                                        firewall.add_filter_source( filter_name, term, term_name,source, source_destination_address=source_destination_address)
                                        self.config_row["Parsed_size"] = 10
                                    case 'protocol':
                                        source_protocol = self.config_row['Arg6']
                                        firewall.add_filter_source( filter_name, term, term_name,source, source_protocol=source_protocol)
                                        self.config_row["Parsed_size"] = 10
                            case 'then':
                                action = self.config_row['Arg4']
                                match self.config_row['Arg5']:
                                    case 'count':
                                        action_count = self.config_row['Arg6']
                                        firewall.add_filter_action(filter_name, term, term_name,action, action_count=action_count)
                                        self.config_row["Parsed_size"] = 10
                                    case 'accept':
                                        action_accept = 'True'
                                        firewall.add_filter_action(filter_name, term, term_name,action, action_accept=action_accept)
                                        self.config_row["Parsed_size"] = 9
                                    case 'log':
                                        action_log = 'True'
                                        firewall.add_filter_action(filter_name, term, term_name,action, action_log=action_log)
                                        self.config_row["Parsed_size"] = 9
                                    case 'discard':
                                        action_discard = 'True'
                                        firewall.add_filter_action(filter_name, term, term_name,action, action_discard=action_discard)       
                                        self.config_row["Parsed_size"] = 9
        return firewall

    def _parse_chassis(self, chassis):
        
        # Parsing FPC configurations
        match self.config_row['Name']:
          case "aggregated-devices":
              key = self.config_row['Name']
              value = self.config_row['Arg1']
              chassis.add_config(self.config_row['Name'] , key , value) 
              ## Add Device Count
              key = self.config_row['Arg2']
              value = self.config_row['Arg3'] 
              chassis.add_config(self.config_row['Name'] , key , value) 
              self.config_row["Parsed_size"] = 7
          case "fpc":
              fpc = self.config_row['Arg1']
              match self.config_row['Arg2']:
                  case 'pic':
                      pic = self.config_row['Arg3']
                      self.config_row["Parsed_size"] = 7
                      match self.config_row['Arg4']:
                          case 'port':
                              port = self.config_row['Arg5']
                              speed = self.config_row['Arg7']
                              chassis.add_port(fpc, pic, port, speed = speed)
                              self.config_row["Parsed_size"] += 4
                          case 'tunnel-services': 
                              # Set tunnel Service True
                              chassis.add_pic(fpc, pic, tunnel_services='True')
                              self.config_row["Parsed_size"] = 8
                              # if Bandwidth is defied set it
                              bandwidth = self.config_row['Arg6']
                              if self.config_row['Arg5']=='bandwidth':
                                  chassis.add_pic_tunnel_services(fpc, pic, bandwidth)
                                  self.config_row["Parsed_size"] = 10
                  case 'apply-groups':
                      applygroups = self.config_row['Arg3']
                      chassis.add_fpc( fpc, apply_groups = applygroups)
                      self.config_row["Parsed_size"] = 7
                      
          case 'network-services':
              key = self.config_row['Name']
              value = self.config_row['Arg1']
              chassis.add_config(self.config_row['Name'] , key , value) 
              self.config_row["Parsed_size"] = 5
          case 'redundancy':
              key = self.config_row['Name']
              value = self.config_row['Arg1']
              chassis.add_config(self.config_row['Name'] , key , value) 
              self.config_row["Parsed_size"] = 5
          case 'redundancy-group':
              key = self.config_row['Name']
              value = self.config_row['Arg1']
              chassis.add_config(self.config_row['Name'] , key , value) 
              self.config_row["Parsed_size"] = 5
              if self.config_row['Arg2'] == 'redundant-logical-tunnel':
                  key = self.config_row['Arg2']
                  value = 'True'
                  chassis.add_config(self.config_row['Name'] , key , value) 
                  self.config_row["Parsed_size"] += 1
              if self.config_row['Arg3'] == 'device-count':
                  key = self.config_row['Arg3']
                  value = self.config_row['Arg4']
                  chassis.add_config(self.config_row['Name'] , key , value) 
                  self.config_row["Parsed_size"] += 2
          case 'pseudowire-service':
              match self.config_row['Arg1']:
                  case 'device-count':
                      key = self.config_row['Arg1']
                      value = self.config_row['Arg2']
                      chassis.add_config(self.config_row['Name'], key , value) 
                      self.config_row["Parsed_size"] = 6
        return chassis
              
    def _parse_interfaces(self, interface):
        interface_name = self.config_row['Name']
        channel = self.get_interface_channel(interface_name)
        interface_id, fpc, pic, port =  self.get_interface_fpc_pic_port(interface_name)
        unit = '-'
        ## Interface_name parsing for interfaces in unit will be added in unit section
        if self.config_row['Arg1'] != 'unit':
            interface.add_unit(interface_name, unit,  ignore_duplicates=True,  interface_id = interface_id)
            if not pd.isnull(fpc):
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  fpc = fpc)
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  pic = pic)
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  port = port)
            if not pd.isnull(channel):
                interface.add_unit(interface_name, unit,  ignore_duplicates=True,  channel = channel)
            
        match self.config_row['Arg1']:
            case 'apply-groups':                
                if  self.config_row['Arg2'] == "[":
                    ## The functions returns column no of closing bracket
                    apply_groups, self.config_row["Parsed_size"] = self.get_columns_data_as_list(self.config_row)
                    interface.add_unit(interface_name, unit, ignore_duplicates=True, apply_groups = apply_groups)
                else:
                    apply_groups = self.config_row['Arg2']
                    interface.add_unit(interface_name, unit, ignore_duplicates=True, apply_groups = apply_groups)
                    self.config_row["Parsed_size"] = 6
            case 'number-of-sub-ports':
                number_of_sub_ports = self.config_row['Arg2']
                interface.add_unit(interface_name, unit, ignore_duplicates=True, number_of_sub_ports = number_of_sub_ports)
                self.config_row["Parsed_size"] = 6                 
            case 'redundancy-group':
                redundancy_group = 'True'
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  redundancy_group = redundancy_group)
                self.config_row["Parsed_size"] = 5
                if self.config_row['Arg2'] == 'member-interface':
                    member_interface = self.config_row['Arg3']
                    interface.add_unit(interface_name, unit, ignore_duplicates=True,  member_interface = member_interface)
                    self.config_row["Parsed_size"] = 7
            case 'speed':
                speed = self.config_row['Arg2']
                interface.add_unit(interface_name, unit,  ignore_duplicates=True, speed = speed)
                self.config_row["Parsed_size"] = 6                 
            case 'ether-options':
                ether_options = self.config_row['Arg2']
                interface.add_unit(interface_name, unit,  ignore_duplicates=True, ether_options = ether_options)
                self.config_row["Parsed_size"] = 6                 
                ether_options_interface = self.config_row['Arg3']
                interface.add_unit(interface_name, unit,  ignore_duplicates=True, interface = ether_options_interface)
                self.config_row["Parsed_size"] = 7                
            case 'anchor-point':
                anchor_point = self.config_row['Arg2']
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  anchor_point = anchor_point)
                self.config_row["Parsed_size"] = 6                 
            case 'aggregated-ether-options':
                match self.config_row['Arg2']:
                    case 'load-balance':
                        load_balance = self.config_row['Arg3']
                        interface.add_unit(interface_name, unit, ignore_duplicates=True,  load_balance = load_balance)
                        self.config_row["Parsed_size"] = 7   
                        if self.config_row['Arg4'] == 'tolerance':
                            tolerance = self.config_row['Arg5']
                            interface.add_unit(interface_name, unit, ignore_duplicates=True,  tolerance = tolerance)
                            self.config_row["Parsed_size"] +=2                       
                    case 'minimum-links':
                        minimum_links = self.config_row['Arg3']
                        interface.add_unit(interface_name, unit, ignore_duplicates=True,  minimum_links = minimum_links)
                        self.config_row["Parsed_size"] = 7   
                    case 'lacp':
                        match self.config_row['Arg3']:
                            case 'active':
                                lacp_mode = self.config_row['Arg3'] 
                                interface.add_unit(interface_name, unit, ignore_duplicates=True,  lacp_mode = lacp_mode)
                                self.config_row["Parsed_size"] = 7                               
                            case 'periodic':
                                lacp_transmission_rate = self.config_row['Arg4']
                                interface.add_unit(interface_name, unit, ignore_duplicates=True,  lacp_transmission_rate = lacp_transmission_rate)
                                self.config_row["Parsed_size"] = 8
                            case 'system-id':
                                system_id = self.config_row['Arg4']
                                interface.add_unit(interface_name, unit, ignore_duplicates=True,  system_id = system_id)
                                self.config_row["Parsed_size"] = 8                               
            case 'gigether-options':
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  gigether_options = 'True')
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  lacp = self.config_row['Arg2'])
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  lag_name = self.config_row['Arg3'])
                self.config_row["Parsed_size"] = 7
            case 'flexible-vlan-tagging':
                value = 'True'
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  flexible_vlan_tagging = value)
                self.config_row["Parsed_size"] = 5                                                             
            case "encapsulation":
                interface.add_unit(interface_name, unit, ignore_duplicates=True,  encapsulation = self.config_row['Arg2'])
                self.config_row["Parsed_size"] = 6                                                             
            case 'unit':
                unit = self.config_row['Arg2']
                # key is identified, lets add channel if it there
                if not pd.isnull(channel):
                    interface.add_unit(interface_name, unit,  ignore_duplicates=True,  channel = channel)
                interface.add_unit(interface_name, unit,  ignore_duplicates=True,  interface_id = interface_id)
                if not pd.isnull(fpc):
                    interface.add_unit(interface_name, unit, ignore_duplicates=True,  fpc = fpc)
                    interface.add_unit(interface_name, unit, ignore_duplicates=True,  pic = pic)
                    interface.add_unit(interface_name, unit, ignore_duplicates=True,  port = port)
                match self.config_row['Arg3']:
                    case 'tunnel':
                        interface.add_unit(interface_name, unit, ignore_duplicates=True,  tunnel = 'True')
                        match self.config_row['Arg4']:
                            case 'source':
                                unit_source = self.config_row['Arg5']
                                interface.add_unit(interface_name, unit, ignore_duplicates=True,  source = unit_source)
                                self.config_row["Parsed_size"] = 9                                                             
                            case "destination":
                                unit_destination = self.config_row['Arg5']
                                interface.add_unit(interface_name, unit, ignore_duplicates=True,  destination = unit_destination)
                                self.config_row["Parsed_size"] = 9                                                             
                            case "routing-instance":
                                match self.config_row['Arg5']:
                                    case 'destination':
                                        routing_instance_destination = self.config_row['Arg6']
                                        interface.add_unit(interface_name, unit,  ignore_duplicates=True, routing_instance = routing_instance_destination)
                                        self.config_row["Parsed_size"] = 10
                    case "family":
                        ## Every family has a column that is set to True as there can be multiple families configured for a unit
                        match self.config_row['Arg4']:
                            case 'inet':
                                interface.add_unit(interface_name, unit, family_inet = 'True')
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'address':
                                        ipv4_address = self.config_row['Arg6']
                                        interface.add_unit(interface_name, unit, inet_address = ipv4_address)
                                        self.config_row["Parsed_size"] = 10
                                        if self.config_row['Arg7'] == 'primary':
                                            interface.add_unit(interface_name, unit, inet_primary = 'True')
                                            self.config_row["Parsed_size"] +=1
                                        if self.config_row['Arg7'] =='vrrp-group':
                                            vrrp_group = self.config_row['Arg8']
                                            interface.add_unit(interface_name, unit, vrrp_group = vrrp_group)
                                            self.config_row["Parsed_size"] +=2
                                            match self.config_row['Arg9']:
                                                case 'virtual-address':
                                                    virtual_ipv4 = self.config_row['Arg10']
                                                    interface.add_unit(interface_name, unit, virtual_address = virtual_ipv4)
                                                    self.config_row["Parsed_size"] +=2
                                                case 'priority':
                                                    priority = self.config_row['Arg10']
                                                    interface.add_unit(interface_name, unit, priority = priority)
                                                    self.config_row["Parsed_size"] +=2
                                                case 'accept-data':
                                                    accept_data = 'True'
                                                    interface.add_unit(interface_name, unit, accept_data = accept_data)
                                                    self.config_row["Parsed_size"] +=1
                                                case 'track':                                                    
                                                    track = 'True'
                                                    interface.add_unit(interface_name, unit, track = track)
                                                    self.config_row["Parsed_size"] +=1
                                                    if self.config_row['Arg10'] == 'interface':
                                                        track_interface = self.config_row['Arg11']
                                                        interface.add_unit(interface_name, unit, track_interface = track_interface )
                                                        self.config_row["Parsed_size"] +=2
                                                        if self.config_row['Arg12'] == 'priority-cost':
                                                            priority_cost = self.config_row['Arg13']
                                                            interface.add_unit(interface_name, unit, priority_cost = priority_cost)
                                                            self.config_row["Parsed_size"] +=2 
                                    case 'rpf-check':
                                        interface.add_unit(interface_name, unit, rfp_check = 'True')
                                        self.config_row["Parsed_size"] +=1
                                        match self.config_row['Arg6']:
                                            case 'fail-filter':
                                                fail_filter = self.config_row['Arg7']
                                                interface.add_unit(interface_name, unit, fail_filter = fail_filter)
                                                self.config_row["Parsed_size"] +=2
                                            case 'mode':
                                                mode = self.config_row['Arg7']
                                                interface.add_unit(interface_name, unit, mode = mode)
                                                self.config_row["Parsed_size"] +=2
                                    case 'filter':
                                        self.config_row["Parsed_size"] +=1
                                        if self.config_row['Arg6'] == 'input':
                                            filter_input = self.config_row['Arg7']
                                            interface.add_unit(interface_name, unit, input = filter_input)
                                            self.config_row["Parsed_size"] +=2
                            case 'inet6':
                                interface.add_unit(interface_name, unit, family_inet6 = 'True')
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'address':
                                        ipv6_address = self.config_row['Arg6']
                                        interface.add_unit(interface_name, unit, inet6_address = ipv6_address)
                                        self.config_row["Parsed_size"] = 10
                                        if self.config_row['Arg7'] == 'primary':
                                            interface.add_unit(interface_name, unit, inet6_primary = 'True')
                                            self.config_row["Parsed_size"] +=1
                                        if self.config_row['Arg7'] =='vrrp-inet6-group':
                                            vrrp_inet6_group = self.config_row['Arg8']
                                            interface.add_unit(interface_name, unit, vrrp_inet6_group = vrrp_inet6_group)
                                            self.config_row["Parsed_size"] +=2
                                            match self.config_row['Arg9']:
                                                case 'virtual-inet6-address':
                                                    virtual_ipv6 = self.config_row['Arg10']
                                                    interface.add_unit(interface_name, unit, virtual_inet6_address = virtual_ipv6)
                                                    self.config_row["Parsed_size"] +=2
                                                case 'priority':
                                                    priority = self.config_row['Arg10']
                                                    interface.add_unit(interface_name, unit, priority = priority)
                                                    self.config_row["Parsed_size"] +=2
                                                case 'accept-data':
                                                    accept_data = 'True'
                                                    interface.add_unit(interface_name, unit, accept_data = accept_data)
                                                    self.config_row["Parsed_size"] +=1                   
                                                case 'track':
                                                    track = 'True'
                                                    interface.add_unit(interface_name, unit, track = track)
                                                    self.config_row["Parsed_size"] +=1
                                                    if self.config_row['Arg10'] == 'interface':
                                                        track_interface = self.config_row['Arg11']
                                                        interface.add_unit(interface_name, unit, track_interface = track_interface )
                                                        self.config_row["Parsed_size"] +=2
                                                        if self.config_row['Arg12'] == 'priority-cost':
                                                            priority_cost = self.config_row['Arg13']
                                                            interface.add_unit(interface_name, unit, priority_cost = priority_cost)
                                                            self.config_row["Parsed_size"] +=2                                                        
                                    case 'rpf-check':
                                        interface.add_unit(interface_name, unit, rfp_check = 'True')
                                        self.config_row["Parsed_size"] +=1
                                        match self.config_row['Arg6']:
                                            case 'fail-filter':
                                                fail_filter = self.config_row['Arg7']
                                                interface.add_unit(interface_name, unit, fail_filter = fail_filter)
                                                self.config_row["Parsed_size"] +=2
                                            case 'mode':
                                                mode = self.config_row['Arg7']
                                                interface.add_unit(interface_name, unit, mode = mode)
                                                self.config_row["Parsed_size"] +=2
                                    case 'filter':
                                        self.config_row["Parsed_size"] +=1
                                        if self.config_row['Arg6'] == 'input':
                                            filter_input = self.config_row['Arg7']
                                            interface.add_unit(interface_name, unit, input = filter_input)
                                            self.config_row["Parsed_size"] +=2
                            case 'iso':
                                protocols = self.config_row['Arg4']
                                interface.add_unit(interface_name, unit, protocols = protocols)
                                self.config_row["Parsed_size"] = 8
                                match self.config_row['Arg5']:
                                    case 'address':
                                        iso_address = self.config_row['Arg6']
                                        interface.add_unit(interface_name, unit, iso_address = iso_address)
                                        self.config_row["Parsed_size"] = 10
                            case 'ccc':
                                interface.add_unit(interface_name, unit, family_ccc = 'True')
                                self.config_row["Parsed_size"] = 8
                                if self.config_row['Arg5'] =='filter':
                                    interface.add_unit(interface_name, unit, filter = 'True')
                                    self.config_row["Parsed_size"] += 1
                                    match self.config_row['Arg6']:
                                        case 'input-list':
                                            input_list = self.config_row['Arg7']
                                            interface.add_unit(interface_name, unit, input_list = input_list)
                                            self.config_row["Parsed_size"] += 2
                                        case 'output-list':
                                            output_list = self.config_row['Arg7']
                                            interface.add_unit(interface_name, unit, output_list = output_list)
                                            self.config_row["Parsed_size"] += 2
                            case 'mpls':
                                self.config_row["Parsed_size"] = 8
                                interface.add_unit(interface_name, unit, family_mpls = 'True')
                                if self.config_row['Arg5'] == 'maximum-labels':
                                    maximum_labels = self.config_row['Arg6']
                                    interface.add_unit(interface_name, unit, maximum_labels = maximum_labels)
                                    self.config_row["Parsed_size"] += 2
                    case "encapsulation":
                        encapsulation = self.config_row['Arg4']
                        interface.add_unit(interface_name, unit, encapsulation = encapsulation)
                        self.config_row["Parsed_size"] = 8                                                             
                    case 'vlan-id':
                        vlanid = self.config_row['Arg4']
                        interface.add_unit(interface_name, unit, vlan_id = vlanid)
                        self.config_row["Parsed_size"] = 8                                                             
                    case 'esi':
                        esi = self.config_row['Arg3']
                        interface.add_unit(interface_name, unit, esi = esi)
                        self.config_row["Parsed_size"] = 7
                        if  self.config_row['Arg4'].count(':') > 2:
                            esi_id =  self.config_row['Arg4']
                            interface.add_unit(interface_name, unit, esi_id = esi_id)
                            self.config_row["Parsed_size"] += 1
                        else:
                            esi_mode = self.config_row['Arg4']
                            interface.add_unit(interface_name, unit, esi_mode = esi_mode)                                                  
                            self.config_row["Parsed_size"] += 1
                    case 'vlan-id-list':
                        vlan_id_list = self.config_row['Arg4']
                        interface.add_unit(interface_name, unit, vlan_id_list = vlan_id_list)
                        self.config_row["Parsed_size"] = 8
                    case 'vlan-tags':
                        interface.add_unit(interface_name, unit, vlan_tags = 'True')
                        self.config_row["Parsed_size"] = 7
                        if self.config_row['Arg4']=='outer':
                            outer = self.config_row['Arg5']
                            interface.add_unit(interface_name, unit, outer = outer)
                            self.config_row["Parsed_size"] += 2
                        if self.config_row['Arg6']=='inner':
                            inner = self.config_row['Arg7']
                            interface.add_unit(interface_name, unit, inner = inner)
                            self.config_row["Parsed_size"] += 2
        return interface

    def get_network_config(self):
        return self.network_config
    
    def get_router_config(self, name):
        return self.network_config.get_router_config(name)


    def __repr__(self):
        return f"NetworkConfigParser(config_file={self.config_file}, network_config={self.network_config})"
    
key_columns = pd.DataFrame(columns=['dataframe_name', 'column_name', 'position', 'count'])
key_columns.set_index(['dataframe_name', 'column_name', 'position'], inplace=True)

def add_key_columns(dataframe_name):
    df = globals().get(dataframe_name)
    index_columns = list(df.index.names)
    position = 0
    for column in index_columns:
        position += 1
        key_columns_index = (dataframe_name, column, position)
        record_exist = key_columns_index in key_columns.index
        if record_exist:
            key_columns.at[key_columns_index, "count"] += 1
        else:
            key_columns.at[key_columns_index, "count"] = 1

def process_network_config():

    now = datetime.datetime.now()
    print("Processing Start Time :", now)
    start_time = time.process_time()

    parser = NetworkConfigParser(r'data/combined_data.csv', r'data/dataframe_columns.csv')
    parser.parse()
    print("Total Processing Time :", time.process_time() - start_time)

    for file in parser.files:
        print(file)
        # Chassis DataFrames
        process_data_frames(parser, file, 'fpcs', 'chassis')
        process_data_frames(parser, file, 'configs', 'chassis')

        # Interface DataFrames
        process_data_frames(parser, file, 'interfaces', 'interface', update=True)

        # Firewall DataFrames
        process_data_frames(parser, file, 'filters', 'firewall')
        process_data_frames(parser, file, 'policers', 'firewall')
        process_data_frames(parser, file, 'families', 'firewall')

        # Protocols DataFrames
        process_data_frames(parser, file, 'protocols', 'protocol', update=True)
        process_data_frames(parser, file, 'protocol_config_kv', 'protocol')

        # Routing Instances DataFrames
        process_data_frames(parser, file, 'routing_instances', 'routing_instance')
        process_data_frames(parser, file, 'routing_instances_config_kv', 'routing_instance')

        # Service DataFrames
        process_data_frames(parser, file, 'service', 'service')

        # BridgeDomain DataFrames
        process_data_frames(parser, file, 'bridgedomain', 'bridgedomain')

        # Policy Options DataFrames
        process_data_frames(parser, file, 'policy_options', 'policy_option')
        process_data_frames(parser, file, 'policy_options_config_kv', 'policy_option')

        # Class of Service DataFrames
        process_data_frames(parser, file, 'class_of_services', 'class_of_service')
        process_data_frames(parser, file, 'class_of_services_config_kv', 'class_of_service')

        # Routing Option DataFrames
        process_data_frames(parser, file, 'routing_options', 'routing_option')
        process_data_frames(parser, file, 'routing_options_config_kv', 'routing_option')
        process_data_frames(parser, file, 'forwarding_options', 'forwarding_option')
        process_data_frames(parser, file, 'forwarding_options_config_kv', 'forwarding_option')

    # Write indexes to a file
    filename = r"data/key_columns.csv"
    if key_columns.shape[0] > 0:
        key_columns.to_csv(filename)

    print("Total Processing + file creation Time :", time.process_time() - start_time)

def process_data_frames(parser, file, frame, section, update=False):
    if update:
        start_time_update_data = time.process_time()
        getattr(parser.get_router_config(file), section).update_data()
        print(f"Total Processing Time {section} Update Data:", time.process_time() - start_time_update_data)

    data_frame = getattr(parser.get_router_config(file), section).__dict__[frame]
    add_key_columns(frame)
    filename = f"data/{file}_{section}_{frame}.csv"
    if data_frame.shape[0] > 0:
        data_frame.to_csv(filename)
