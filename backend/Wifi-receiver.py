#import machine
#machine.reset()

import network
import socket
import time

# WiFi credentials
ssid = "Redmi"
password = "12345678"

# Network configuration
static_ip = '192.168.47.100'
subnet_mask = '255.255.255.0'
gateway = '192.168.47.100'
dns_server = '192.168.47.100'

# File path to store data
csv_file_path = 'sensor_data.csv'

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        for _ in range(20):  # Wait for 20 seconds maximum
            if wlan.isconnected():
                break
            time.sleep(1)
    if wlan.isconnected():
        print('Connected to WiFi')
        print('Network config:', wlan.ifconfig())
    else:
        print('Failed to connect to WiFi')
    return wlan

def set_static_ip(wlan):
    if wlan.isconnected():
        try:
            wlan.ifconfig((static_ip, subnet_mask, gateway, dns_server))
            print('Static IP set:', wlan.ifconfig())
        except Exception as e:
            print('Error setting static IP:', e)

def start_server(ip, port):
    addr = socket.getaddrinfo(ip, port)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print(f'Server started. Listening on {ip}:{port}')
    return s

def get_last_index():
    """Gets the last used index from the CSV file."""
    last_index = -1  # Initialize with -1 in case the file is empty or doesn't exist
    try:
        with open(csv_file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) > 1:  # Ensure the file has data beyond the header
                last_line = lines[-1]
                last_index = int(last_line.split(',')[0])  # Get the index from the last line
    except OSError:
        print(f"{csv_file_path} does not exist, initializing new file.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return last_index

def get_unix_millis():
    """Get the current Unix timestamp in milliseconds."""
    return int(time.time() * 1000)  # Convert seconds to milliseconds

def write_to_file(data, index):
    """Append the incoming data to the file in CSV format with the provided index."""
    try:
        with open(csv_file_path, 'a') as file:
            file.write(f"{index},{data[1]},{data[2]},{data[3]}\n")
        print(f"Data written to {csv_file_path}: {index},{data[1]},{data[2]},{data[3]}")
    except OSError as e:
        print(f"Error writing to file: {e}")

def main():
    wlan = connect_wifi()
    if not wlan.isconnected():
        print('WiFi connection failed. Exiting.')
        return
    set_static_ip(wlan)
    
    port = 8080
    try:
        s = start_server(static_ip, port)
    except Exception as e:
        print(f'Error starting server: {e}')
        return
    print('Waiting for connections...')
    
    # Initialize the file with headers if it doesn't exist
    try:
        with open(csv_file_path, 'r'):
            pass  # File exists
    except OSError:
        # File does not exist, so create it and add headers
        with open(csv_file_path, 'w') as file:
            file.write("Index,Distance (cm),MAC Address,Unix Timestamp (ms)\n")
    
    # Get the last index from the file
    last_index = get_last_index()

    while True:
        try:
            cl, addr = s.accept()
            print(f'New connection from {addr}')
            
            received_data = cl.recv(1024)
            if received_data:
                received_data = received_data.decode('utf-8')
                print(f"Received Data from {addr}: {received_data}")
                
                # Expected format: "Distance:50.00cm,MAC:xx:xx:xx:xx:xx:xx"
                data_parts = received_data.split(',')
                # Increment the index manually
                last_index += 1
                distance = data_parts[0].split(':')[1].replace('cm', '').strip()
                mac = ':'.join(data_parts[1].split(':')[1:]).strip()  # Concatenate the MAC address properly
                
                # Get the current Unix timestamp in milliseconds
                unix_millis = get_unix_millis()
                
                # Write data to the file with a unique index and Unix timestamp
                write_to_file([last_index, distance, mac, unix_millis], last_index)
            else:
                print(f"No data received from {addr}")
                
            cl.close()
            print(f"Connection closed with {addr}")
        except Exception as e:
            print(f'Error handling client: {e}')

if __name__ == '__main__':
    main()
