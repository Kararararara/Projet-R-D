import asyncio
from bleak import BleakScanner
import math

def calculate_distance(rssi, tx_power=-59):
    """
    Calcule la distance estimée entre le périphérique et le beacon.
    
    :param rssi: Puissance reçue en dBm.
    :param tx_power: Puissance d'émission (valeur par défaut -59 dBm pour BLE).
    :return: Distance en mètres.
    """
    if rssi == 0:
        return None  # Impossible de déterminer la distance
    
    # Modèle de calcul de la distance basé sur RSSI
    ratio = rssi / tx_power
    if ratio < 1.0:
        return math.pow(ratio, 10)
    else:
        return 0.89976 * math.pow(ratio, 7.7095) + 0.111

# Initialize a global variable to track consecutive detections
consecutive_within_1m = 0

async def scan_ble():
    """
    Scans for nearby BLE devices and displays their information.
    """
    global consecutive_within_1m
    devices = await BleakScanner.discover(return_adv=True)    
    for address, adv_data in devices.items():
        # Unpack tuple if needed
        if isinstance(adv_data, tuple):
            adv_data = adv_data[1]  # Assuming advertisement data is in the second position
        
        # Extract data safely
        local_name = getattr(adv_data, 'local_name', 'Unknown')
        rssi = getattr(adv_data, 'rssi', None)
        
        if local_name in ["airport1", "airport2"]:
            print(f"Device: {local_name} (Address: {address})")
            print(f"RSSI: {rssi} dBm")
            
            distance = calculate_distance(rssi) if rssi else None
            consecutive_within_1m += 1 
            print(f"Estimated Distance: {distance:.2f} meters")
            # Track consecutive detections within 1 meter
            if distance < 1.25:
                consecutive_within_1m += 1 
                print("Device detected within 1 meter.")
                if consecutive_within_1m > 4:
                    print("Vous êtes arrivé.")
                    exit()
            else:
                consecutive_within_1m = 0
         

if __name__ == "__main__":
    try:
        while True:
            asyncio.run(scan_ble())

    except KeyboardInterrupt:
        print("\nScan stopped by user.")
