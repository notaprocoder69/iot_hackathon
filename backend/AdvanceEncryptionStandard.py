import network
import socket
import time
import ucryptolib
import os

# WiFi credentials
ssid = "Redmi"
password = "12345678"

# Network configuration
static_ip = '192.168.47.100'
subnet_mask = '255.255.255.0'
gateway = '192.168.47.100'
dns_server = '192.168.47.100'

# File path to store data
csv_file_path = 'aes_encryption.csv'

# Symmetric key for AES (must be 16, 24, or 32 bytes long)
symmetric_key = os.urandom(16)  # Generate a random 16-byte key

# AES padding function
def pad(data):
    block_size = 16
    padding_length = block_size - (len(data) % block_size)
    padding = bytes([padding_length] * padding_length)  # PKCS7 padding
    return data + padding

# AES encryption function
def aes_encrypt(data):
    padded_data = pad(data.encode('utf-8'))  # Pad the data
    aes = ucryptolib.aes(symmetric_key, 1, b'\0' * 16)  # AES in ECB mode
    encrypted_data = aes.encrypt(padded_data)
    return encrypted_data.hex()

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
    last_index = -1
    try:
        with open(csv_file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) > 1:
                last_line = lines[-1]
                last_index = int(last_line.split(',')[0])  # Get the index from the last line
    except OSError:
        print(f"{csv_file_path} does not exist, initializing new file.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return last_index

def get_unix_millis():
    """Get the current Unix timestamp in milliseconds."""
    return int(time.time() * 1000)

def write_to_file(index, encrypted_data, unix_millis):
    """Append the index, encrypted data, and Unix timestamp to the CSV file."""
    try:
        with open(csv_file_path, 'a') as file:
            file.write(f"{index},{encrypted_data},{unix_millis}\n")
        print(f"Data written to {csv_file_path}: {index},{encrypted_data},{unix_millis}")
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
    
    try:
        with open(csv_file_path, 'r'):
            pass  # File exists
    except OSError:
        with open(csv_file_path, 'w') as file:
            file.write("Index,Encrypted Data,Unix Timestamp (ms)\n")
    
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
                last_index += 1
                distance = data_parts[0].split(':')[1].replace('cm', '').strip()
                mac = ':'.join(data_parts[1].split(':')[1:]).strip()
                
                unix_millis = get_unix_millis()

                # Concatenate data into a single string to be encrypted
                data_string = f"{last_index},{distance},{mac},{unix_millis}"
                
                # Apply AES encryption
                encrypted_data = aes_encrypt(data_string)
                print(f"Encrypted Data: {encrypted_data}")
                
                # Write index, encrypted data, and timestamp to the CSV
                write_to_file(last_index, encrypted_data, unix_millis)

                # Print the index, distance, MAC address, encrypted data, and timestamp for reference
                print(f"Reference Data - Index: {last_index}, Distance: {distance} cm, MAC: {mac}, Encrypted Data: {encrypted_data}, Unix Timestamp: {unix_millis}")
            else:
                print(f"No data received from {addr}")
                
            cl.close()
            print(f"Connection closed with {addr}")
        except Exception as e:
            print(f'Error handling client: {e}')

if __name__ == '__main__':
    main()
