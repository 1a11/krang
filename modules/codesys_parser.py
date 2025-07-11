import os
import uuid
import random
import re
import json
from typing import Optional

"""
// Define initial addresses, some pre-assigned to devices
                mockAddresses = [
                    { id: 'addr_001', name: 'Motor Speed', modbusAddress: 'IR40001', type: 'MODBUS', deviceId: 'device_A', deviceName: 'Production Line A' },
                    { id: 'addr_002', name: 'Temperature Sensor', modbusAddress: 'HR40002', type: 'MODBUS', deviceId: 'device_A', deviceName: 'Production Line A' },
                    { id: 'addr_003', name: 'Emergency Stop Button', modbusAddress: 'C00001', type: 'MODBUS', deviceId: null, deviceName: null }, // Unassigned
                    { id: 'addr_004', name: 'Pressure Gauge Reading', modbusAddress: 'IS10001', type: 'MODBUS', deviceId: 'device_B', deviceName: 'HVAC System' },
                    { id: 'addr_005', name: 'Flow Rate', modbusAddress: 'HR40003', type: 'MODBUS', deviceId: null, deviceName: null }, // Unassigned
                    { id: 'addr_006', name: 'Valve Status', modbusAddress: 'C00002', type: 'MODBUS', deviceId: 'device_C', deviceName: 'Water Treatment Unit' },
                    // Expression with suggested name
                    {
                        id: 'addr_expr_001',
                        name: 'RH3 COLD2 Scale', // User-friendly name
                        modbusAddress: '%MW38', // PLC address
                        type: 'Expression',
                        fullExpression: '%MW38 := SCALE_T(RH3_COLD2, 0, 98); (* RH3 COLD2 *)',
                        functionName: 'SCALE_T',
                        suggestedName: 'RH3 COLD2',
                        deviceId: 'device_B', deviceName: 'HVAC System'
                    },
                    // Expression without suggested name
                    {
                        id: 'addr_expr_002',
                        name: 'Analog Input Processing', // User-friendly name
                        modbusAddress: '%IW100', // PLC address
                        type: 'Expression',
                        fullExpression: '%IW100 := ANALOG_IN_PROCESS(AI_RAW, 0, 1000);',
                        functionName: 'ANALOG_IN_PROCESS',
                        suggestedName: null, // No suggested name
                        deviceId: null, deviceName: null // Unassigned
                    },
"""

class CodesysParser:
    def __init__(self, file_path: Optional[str] = None, raw_content: Optional[str] = None):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path) if file_path else "unknown.cdc"
        self.file_uuid = str(uuid.uuid4())
        self.file_content = ""
        self.parsed_data = []
        self.devices = []
        self.raw_content = raw_content
        self.device_colors = ['blue', 'green', 'purple', 'orange', 'red']

    def read(self):
        #check if raw content is provided
        if self.file_path is None and self.raw_content is not None:
            self.file_content = self.raw_content
            return True
        if self.file_path is not None:
            with open(self.file_path, 'r') as file:
                self.file_content = file.read()

    def get_file_name(self):
        return self.file_name

    def get_file_uuid(self):
        return self.file_uuid

    def get_file_content(self):
        return self.file_content
    
    def check_if_codesys_code_is_valid(self):
        if not self.file_content:
            raise ValueError("File content is not loaded. Call read() method first.")
        # Check for basic structure of CODESYS code
        # if line starts with %(MW|IW|QW|DB|QX|QD|MX|IX) or (*, it is valid
        # no regex, just check if the first 3 characters contain %MW, %IW, %QW, %DB, %QX, %QD, %MX, %IX or (* for comments
        lines = self.file_content.splitlines()
        # print(lines)  # Debug: Uncomment for troubleshooting
        valid_start_patterns = ('%MW', '%IW', '%QW', '%DB', '%QX', '%QD', '%MX', '%IX', '%MD', '(* ', '(*', 'VAR', 'END_VAR', 'PROGRAM', 'END_PROGRAM', 'IF', 'THEN', 'ELSE', 'END_IF')
        # Check if each line starts with one of the valid patterns
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith(valid_start_patterns):
                print(f"Invalid line found: {stripped_line}")  # Debug: Uncomment for troubleshooting
                # If a line does not start with any of the valid patterns, return False
                return False
        return True

    def parse_file_content(self):
        if not self.file_content:
            raise ValueError("File content is not loaded. Call read() method first.")
        
        # Example parsing logic (to be replaced with actual parsing logic)
        parsed_data = {}
        lines = self.file_content.splitlines()
        for line in lines:
            if line.strip():
                if not line.strip().startswith("(*"):
                    address, value = line.split(':=')
                    self.parsed_data.append({
                        'id': str(uuid.uuid4()),
                        'name': None,
                        'modbusAddress': address.strip(),
                        'type': None,
                        'deviceId': None,
                        'deviceName': None,
                        'value': value.strip(),
                        'fullExpression': None,
                    })
                    if self.parsed_data[-1]['value'].startswith('MBCFG_'):
                        self.parsed_data[-1]['type'] = 'MODBUS'
                        self.parsed_data[-1]['name'] = self.parsed_data[-1]['value'].split('.')[1].strip()
                        #{ id: 'device_A', name: 'Production Line A', description: 'Main PLC for Line A', color: 'blue' },
                        #Look if a device with this name does not already exist
                        device_name = self.parsed_data[-1]['value'].split('.')[0].strip()
                        existing_device = next((device for device in self.devices if device['name'] == device_name), None)
                        if not existing_device:
                            device_id = str(uuid.uuid4())
                            self.devices.append({
                                'id': device_id,
                                'name': device_name,
                                'description': "",
                                'color': random.choice(self.device_colors),
                            })
                        else:
                            device_id = existing_device['id']
                        self.parsed_data[-1]['deviceId'] = device_id
                        self.parsed_data[-1]['deviceName'] = device_name
                    else:
                        self.parsed_data[-1]['type'] = 'Expression'
                        #string.maketrans("\n\t\r", "   ") to get rid of newlines, tabs, and carriage returns
                        self.parsed_data[-1]['fullExpression'] = self.parsed_data[-1]['modbusAddress'] +":="+ self.parsed_data[-1]['value'].translate(str.maketrans("\n\t\r", "   "))
                        self.parsed_data[-1]['name'] = self.parsed_data[-1]['value'].split(':=')[0].strip()
                        self.parsed_data[-1]['functionName'] = self.parsed_data[-1]['value'].split('(')[0].strip()
                        device_name = "Expressions"
                        existing_device = next((device for device in self.devices if device['name'] == device_name), None)

                        if not existing_device:
                            device_id = str(uuid.uuid4())
                            self.devices.append({
                                'id': device_id,
                                'name': device_name,
                                'description': "",
                                'color': random.choice(self.device_colors),
                            })
                        else:
                            device_id = existing_device['id']
                        self.parsed_data[-1]['deviceId'] = device_id
                        self.parsed_data[-1]['deviceName'] = device_name

        # Convert parsed data to webpage format

        return self.parsed_data, self.devices
    



"""parser = CodesysParser("./data/test.cdc")
parser.read()

parsed_data, devices = parser.parse_file_content()

def python_to_js(obj):
    # Convert Python None to JS null, keep keys unquoted, and use : not =
    if isinstance(obj, dict):
        items = []
        for k, v in obj.items():
            js_v = python_to_js(v)
            items.append(f"{k}: {js_v}")
        return "{" + ", ".join(items) + "}"
    elif isinstance(obj, list):
        return "[" + ", ".join([python_to_js(i) for i in obj]) + "]"
    elif obj is None:
        return "null"
    elif isinstance(obj, str):
        # Escape backslashes and double quotes for JS string
        return f'"{obj.replace("\\", "\\\\").replace("\"", "\\\"")}"'
    else:
        return str(obj)

print("mockAddresses = [")
for data in parsed_data:
    print(python_to_js(data) + ",")
print("];\n")

print("devices = [")
for device in devices:
    print(python_to_js(device) + ",")
print("];")
"""