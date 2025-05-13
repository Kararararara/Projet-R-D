#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
File: blescanner.py
Date: 20240104
Description:
Scan for BLE devices and return a JSON object (array) holding the list of devices found with address, name and optional advertised data.

Run:
python3 blescanner.py arguments
Arguments
-t, timeout seconds		- Scanning duration in seconds. Minimum is 5 seconds.
-a, advdata 0=Off, 1=On	- Flag to add advertised data to the result.
-m, mac - MAC address   - MAC address for single device only.
-d, debug 0=Off, 1=On 	- Debug flag. 

python3 blescanner.py -t 5 -a 1
Output Example:
[
{"address": "70:2A:D5:7E:23:26", "name": null, "advertisementdata": {"manufacturer_data": true, "0X75": "4204018060702AD57E2326722AD57E232501000000000000", "rssi": -90}}, 
{"address": "A4:C1:38:52:74:C2", "name": "ATC_5274C2", "local_name": "ATC_5274C2", "advertisementdata": {"service_data": true, "0000181A-0000-1000-8000-00805F9B34FB": "C2745238C1A4A406F81759091B410E", "rssi": -46}}, 
{"address": "F7:6F:D8:27:B7:8D", "name": "Ruuvi B78D", "local_name": "Ruuvi B78D", "advertisementdata": {"manufacturer_data": true, "0X499": "050D255DB8CAFEFFE4006C03F8AB761CAFC6F76FD827B78D", "rssi": -59}}, 
{"address": "76:73:5D:F9:74:96", "name": null, "advertisementdata": {"service_data": true, "0000FEF3-0000-1000-8000-00805F9B34FB": "4A17234D52584A1132D1308AC746ECB6A1393FF8102BFDAB6BC685", "rssi": -63}}, 
{"address": "A4:C1:38:38:A9:0C", "name": "ATC_38A90C", "local_name": "ATC_38A90C", "advertisementdata": {"service_data": true, "0000181A-0000-1000-8000-00805F9B34FB": "0CA93838C1A48C068017270B5DA40E", "rssi": -52}}
]

Data for single device, i.e. Raspberry Pi Pico W in this example
python3 blescanner.py -t 5 -a 1 -m 28:CD:C1:09:05:98
[
{"address": "28:CD:C1:09:05:98", "name": "PICOW", "local_name": "PICOW", "advertisementdata": {"manufacturer_data": true, "0X4C52": "32383930", "rssi": -74}}
]
"""

import argparse
import sys
import json
import asyncio
from bleak import BleakScanner

_VERSION = 'BLE Scanner v20240104'

# Minumum discover time in seconds
_TIMEOUT_MIN = 5

class BLEScanner():
    """Scan for BLE devices"""
    
    def __init__(self, timeout=10, advdata=0, mac=None, debug=0):
        """Init the ble scanner with options."""
        self._timeout = int(timeout) 
        self._timeout = self._timeout if self._timeout >= _TIMEOUT_MIN else _TIMEOUT_MIN
        self._advdata = False if advdata == 0 else True
        if mac != None:
            mac = mac.strip()
        self._mac = mac
        self._debug = False if debug == 0 else True
        return

    async def scanning(self):
        """Scan for sensors"""

        if self._debug:
            print(f'[DEBUG scanning] running for {self._timeout} seconds, mac={self._mac}')

        devices = await BleakScanner.discover(
            timeout = self._timeout,
            return_adv = self._advdata
            # cb=dict(use_bdaddr=True)
        )

        if self._debug:
            print('[DEBUG scanning] scanning completed.')
            print(f'[DEBUG scanning] {len(devices)} sensors found.')

        if not self._advdata:
            # property BleakScanner.discovered_devices: List[BLEDevice]
            # Gets list of the devices that the scanner has discovered during the scanning. 
            result = []
            for device in devices:
                if self._debug:
                    print(f'[DEBUG scanning] {device}')
                newdevice = {}
                newdevice['address'] = device.address
                newdevice['name'] = device.name
                # print(newdevice, _mac)
                if self._mac == None:
                    result.append(newdevice)
                elif self._mac == device.address:
                    result.append(newdevice)
            if self._debug:
                print('[DEBUG scanning] result')
            print(json.dumps(result))
           
        else:
            #property BleakScanner.discovered_devices_and_advertisement_data: Dict[str, Tuple[BLEDevice, AdvertisementData]]
            #Gets a map of device address to tuples of devices and the most recently received advertisement data for that device.
            # platform_data not used as not stable
            result = []
            for device, advdata in devices.values():
                if self._debug:
                    print(advdata)

                newdevice = {}
                newdevice['address'] = device.address
                newdevice['name'] = device.name
                
                newadvdata = {}
                # AdvertisementData(local_name: Optional[str], manufacturer_data: Dict[int, bytes], service_data: Dict[str, bytes], service_uuids: List[str], tx_power: Optional[int], rssi: int, platform_data: Tuple)
                if advdata.local_name:
                    newdevice['local_name'] = advdata.local_name
                if advdata.manufacturer_data:
                    newadvdata['manufacturer_data'] = True
                    for key, value in advdata.manufacturer_data.items():
                        newadvdata[hex(key).upper()] = value.hex().upper()
                if advdata.service_data:
                    newadvdata['service_data'] = True
                    for key, value in advdata.service_data.items():
                        newadvdata[key.upper()] = value.hex().upper()
                if advdata.tx_power:
                    newadvdata ['tx_power']=advdata.tx_power
                if advdata.rssi:
                    newadvdata['rssi'] = advdata.rssi
                newdevice['advertisementdata'] = newadvdata

                if self._mac == None:
                    result.append(newdevice)
                    if self._debug:
                        print(f'[DEBUG scanning] newdevice={newdevice}')            
                elif self._mac == device.address:
                    result.append(newdevice)
                    if self._debug:
                        print(f'[DEBUG scanning] newdevice={newdevice}')            
            if self._debug:
                print("[DEBUG scanning] result")
            print(json.dumps(result))
        
if __name__ == "__main__":
    """Scan for BLE sensors"""
    
    # python3 blescanner.py -t 5 -a 1 -m 28:CD:C1:09:05:98
    parser = argparse.ArgumentParser()        
    parser.add_argument("-t", "--timeout", default=10, type=int)   
    parser.add_argument("-a", "--advdata", default=0, type=int)    
    parser.add_argument("-m", "--mac", default=None, type=str)    
    parser.add_argument("-d", "--debug", default=0, type=int)    

    # Parse the arguments and assign to global
    args = parser.parse_args()
    # Create blescanner object
    blescanner = BLEScanner(args.timeout, args.advdata, args.mac, args.debug)

    # Run
    if args.debug == 1:
        print(f'[DEBUG main] {_VERSION}, Python {sys.version}')
        print(f'[DEBUG main] arguments: timeout={args.timeout}, advdata={args.advdata}, mac={args.mac}, debug={args.debug}')
    asyncio.run(blescanner.scanning())
