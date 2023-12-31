from session import Session
from messages import Colors
import requests
import json
from files import File
from menu import userMenu
import pandas as pd
import base64

class Device(Session, userMenu):
    all_devices = []
    messages = Colors()
    
    def __init__(self):
        self.ready_device = None
        self.device_prototype = None
        self.__port_resume = {}
        self.start_date = None
        self.end_date = None
        self.all_data = []
        self.test = {}
        
    def get_device(self):

        self.messages.prLightPurple('*' * 30)
        deveui = input('Type a deveui > ')
        input("Press enter to continue")
        self.messages.prLightPurple('...................')
        dynamic_url = Session.base_url + f'/devices/{deveui}?access_token={Session.token}'
        headers = {
            'Authorization': f'Bearer {Session.token}',
            'Cookie': f'session_token={Session.token}'
        }

        response = requests.request('GET', dynamic_url, headers=headers, data="")
        return self._check_request_status(response)

    def get_multi_devices(self):
        while True:
            try:
                offset = int(input('Offset (min number to get) > '))
                limit = int(input('Limit (max number to get) > '))
                dynamic_url = f'/devices?offset={offset}&limit={limit}'
                q_url = Session.base_url + dynamic_url
                headers = {
                'Authorization': f'Bearer {Session.token}',
                'Cookie': f'session_token={Session.token}'
                }

                response = requests.request('GET', url=q_url, headers=headers, data="")
                return self._check_request_status(response)
            except ValueError:
                self.messages.error('Type a valid integer!')
                self.messages.prPurple('*' * 25)
                continue
            except KeyboardInterrupt:
                self.messages.prLightPurple('\nThank you for use!\nQuitting the program...')
                exit()
    
    @staticmethod
    def decode_uplink_port(payload_base64):
        return base64.b64decode(payload_base64).hex()
    
    @staticmethod
    def get_payload_from_uplinks(uplinks=[]):
        """
            Returns the complete payload of each uplink from a list of uplinks,
            
            Parameters:
                    uplinks (list): a list of uplink messages
            Returns:
                (base64_payload, hex_payloads): base64 version of the payload, hexadecimal version of the payload
        """   
        hex_payloads = []
        base64_payload = []
        
        for uplink in uplinks:
            
            # checks the port number of the uplink
            if uplink['params']['port'] == 9:
                hex_payload = Device.decode_uplink_port(uplink['params']['payload'])
                hex_payloads.append(hex_payload)
                base64_payload.append(uplink['params']['payload'])
        return base64_payload, hex_payloads
    
    @staticmethod
    def extract_coord_bits_from_payload(hex_payloads, base):
        latitudes = []
        longitudes = []
        for payload in hex_payloads:
            latitudes.append(bin(int(payload[4:10], base)))
            longitudes.append(bin(int(payload[10:16], base)))
        return latitudes, longitudes
    
    def extract_coordinates(binaries):
        new_coordinates= []
        for binaries_of24bits in binaries:
            first_bit = binaries_of24bits[2]
            
            # checks if the binary is greater than 0b0
            if len(binaries_of24bits) > 3:
                if first_bit == '1':
                    decimal_value = -int(binaries_of24bits[3:], base=2)
                else:
                    decimal_value = int(binaries_of24bits[3:], base=2)
                new_coordinates.append(decimal_value/10**4) 
                
        return new_coordinates
    # @staticmethod
    # def extract_signal(payloads_in_bit):
    #     mask = int('100000000000000000000000', 2)
    #     results = []
    #     for payload in payloads_in_bit:
    #         results.append(bin(int(payload, 2) & mask))
    #     return results
        
    def get_uplink_message(self):
        while True:
            self.messages.prLightPurple('*' * 30)
            try:
                start_date = str(input('Type the start date (yyyymmdd) > '))
                #end_date = str(input('Type the end date (yyyymmdd) > '))
                end_date = '20230918'
                if all(len(date)==8 for date in [start_date, end_date]):
                    self.start_date = start_date + '000000'
                    self.end_date = end_date + '000000'
                    break
                else:
                    self.messages.warning('Check if dates are in the correct format (yyyymmdd)')
            except Exception as error:
                self.validate_option(error)
                continue
                
        deveui = input('Type a deveui > ')
        while True:
            try:
                limit = int(input('Messages limit > '))
                break
            except Exception as error:
                self.validate_option(error)
            
        input("Press enter to continue")
        dynamic_url = Session.base_url + f'/history/data.json?access_token={Session.token}&from={self.start_date}&to={self.end_date}' \
        f'&limit={limit}&devices={deveui}&types=uplink&duplicate=false'
        print(dynamic_url)
        response = requests.request('GET', dynamic_url, headers=self.header, data="")
        return self._check_request_status(response)
            
    @classmethod
    def display_devices(cls, data):
        counter = 0
        if data is not None:
            if len(data) > 1:
                for devices in data['devices']:
                    counter +=1
                    cls.messages.prLightPurple('=========================')
                    cls.messages.warning(f'Device {counter} ({devices["dev_eui"]})')
                    for key, value in devices.items():
                        cls.messages.prPurple(f'{key} -> ', endline=True)
                        print(value)
            else:
                print('Device ', end='')
                cls.messages.prLightPurple(data['device']['dev_eui'])
                for key, value in data['device'].items():
                        cls.messages.prPurple(f'{key} -> ', endline=True)
                        print(value)
    
    def __messages_resume(self, value):
        if 'Port ' + str(value['port']) not in self.__port_resume.keys():
            self.__port_resume[f'Port {value["port"]}'] = 0
        self.__port_resume[f'Port {value["port"]}'] += 1
        
    
    def __display_ports(self, ports):
        self.messages.warning('---------- Port Resume ----------')
        for key, value in ports.items():
            self.messages.prLightPurple(f'{key}: ', endline=True)
            print(value)
        
    def display_messages(self, data):
        counter = 0
        if data is not None:
            if len(data) > 1:          
                for message in data:
                    counter += 1
                    self.messages.prLightPurple('=========================')
                    self.messages.warning(f'Message {counter}')
                    for key, value in  message.items():
                        self.all_data.append((key, value))
                        if type(value) == dict:
                            print('Dicionário')
                        if key == 'params':
                            self.__messages_resume(value)
                        if key in ('params', 'meta'):
                            for keyx, valuex in value.items():
                                self.all_data.append([keyx, valuex])
                        self.messages.prPurple(f'{key} -> ', endline=True)
                        print(value)
                    
        self.messages.prLightPurple('=========================')
        port_df = pd.DataFrame(self.all_data)
        port_df.to_excel('Device_info.xlsx')
        self.__display_ports(self.__port_resume)
                                     

    def build_device(self, sheet:File = None, ask_default_values:bool = False):
        self.messages.prPurple('*' * 30)
        device = self.generate_empty_device()

        if not ask_default_values:
            device['tags'] = ['TV_2']
            device['activation'] = 'ABP'
            device['encryption'] = 'NS'
            device['dev_class'] = 'A'
            device['block_downlink'] = True
            device['adr'] = {
                # 30dBm
                'tx_power':0,
                'datarate':0,
                'mode':'static'
            }
            device['band'] = 'LA915-928A'
            device['counters_size'] = 4
        else:
            device['tags'] = input('\033[1;96mTags (separate by commas) > \033[00m').split(',')
            device['tags'] = [tags.strip(' ') for tags in device['tags']]
            device['activation'] = input('\033[1;96m Activation > \033[00m')
            device['encryption'] = 'NS'
            device['dev_class'] = 'A'
            device['block_downlink'] = True
            device['adr'] = {
                # 30dBm
                'tx_power':0,
                'datarate':0,
                'mode':'static'
            }
            device['band'] = 'LA915-928A'
            device['counters_size'] = 4
        
        # perguntas para o usuário dos valores não constantes, e caso não seja um upload de arquivo
        if sheet is None:
            device['dev_eui'] = input('\033[1;96mDeveui > \033[00m')
            device['app_eui'] = input('\033[1;96mAppeui > \033[00m')
            device['dev_addr'] = input('\033[1;96mDev address > \033[00m')
            device['nwkskey'] = input('\033[1;96mNetwork secret key > \033[00m')
            device['appskey'] = input('\033[1;96mApp secret key > \033[00m')
            device['block_downlink'] = True
            self.messages.prPurple('*' * 30)
        else:
            device['dev_eui'] = sheet.dev_eui
            device['app_eui'] = sheet.app_eui
            device['dev_addr'] = sheet.dev_addr
            device['nwkskey'] = sheet.nwkskey
            device['appskey'] = sheet.appskey
            device['block_downlink'] = True
            
        # prototype: versão dicionário
        self.device_prototype = device
        
        #ready_device: versão json
        self.ready_device = json.dumps(device)
        
        self.all_devices.append(self.device_prototype)
    
    def create_multiple_devices_mannualy(self):
        print('\033[1;96m====================\033[00m')
        while True:
            keep_creating = ""
            self.build_device()
            device_created = self.create_single_device()
            if device_created is not None:
                self.messages.prGreen(f'{self.device_prototype["dev_eui"]} has been created!')
                
            print('\033[1;96m====================\033[00m')
            while keep_creating not in ('Y', 'y', 'n', 'N'):
                keep_creating = input('Create more devices: Y/n > ')
            if keep_creating in ('Y','y'):
                continue
            else:
                return
    
    def manage_excelfile(self, file:File):
        file._check_columns()
        file._check_size()
        if file.is_able_to_use:
            file.adjust_content()
            options = ""
            self.messages.prGreen('It is possible to use the sheet!')
            self.messages.prLightPurple('File content previous')
            print(file.content.head(5))
            while options not in ('Y', 'y', 'n', 'N'):
                confirmation = input('\033[1;93mAre you sure you want to create these devices: Y/n > \033[00m')
                if confirmation in ('Y', 'y'):
                    print('Creating devices!')
                    for row in file.content.itertuples():
                        self.build_device(sheet=row)
                        device_created = self.create_single_device()
                        if device_created is not None:
                            self.messages.prGreen(f'{self.device_prototype["dev_eui"]} has been created!')
                    return
                else:
                    return
        else:
            self.messages.error('It is not possible to use the sheet!')
            return

    def manage_jsonfile(self, file: File):
        self.messages.warning('This feature is not implemented yet!')
        return

    def create_via_file(self, file_type:str):
        file_path = input(f'Type the \033[1;92m{file_type}\033[00m absolute path > ')
        file_instancy = File(file_path)
        print()
        match file_instancy.extension:
            case '.xlsx' | '.csv':
                self.manage_excelfile(file_instancy)
            case '.json':
                self.manage_jsonfile(file_instancy)

        
    def create_multiple_devices(self):
        print('To create multiple devices, choose one of the options below ')
        file_menu = userMenu(['Manually', 'JSON file', 'CSV file', 'XLSX file', 'Back main menu'], key='file_menu')
        file_menu.show()
        
        opc = file_menu.ask_option()
        match opc:
            case 1:
                self.create_multiple_devices_mannualy()
            case 2 | 3 | 4:
                self.create_via_file(file_type=file_menu.menu_options[opc-1])
            case 5:
                print('returning')
                return

    def create_single_device(self, method='POST'):
        dynamic_url = f"/devices"
        q_url = self.base_url + dynamic_url
        
        payload = self.ready_device
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {Session.token}',
            'Cookie': f'session_token={Session.token}'
        }
        response = requests.request(method=method, url=q_url, headers=headers, data=payload)
        return self._check_request_status(response, code=201)
    
    def edit_single_device(self):
        self.build_device(ask_default_values=input('Ask default values > '))
        self.create_single_device(method='PATCH')
    
    def ask_for_sure(self):
        sure = ""
        while sure not in ('Yes', 'Y', 'y', 'yes', 'No', 'n', 'N', 'NO'):
            sure = input('\033[1;93mAre you sure you want to proceed: (Y/n)\033[00m ')
        if sure in ('Y', 'y', 'Yes', 'yes'):
            return True
        return False
            
    def delete_single_device(self):
        self.messages.prLightPurple('*' * 30)
        deveui = input('Type a deveui > ')
        self.messages.prLightPurple('...................')
        dynamic_url = Session.base_url + f'/devices/{deveui}?access_token={Session.token}'
        headers = {'Cookie': self.token}
        
        if self.ask_for_sure():
            print('Deleting device!')
            return
        else:
            print('Returning')
            return
        #     response = requests.request('DELETE', dynamic_url, headers=headers, data="")
        #     return self._check_request_status(response, code=204)
        # return