import network
import socket
import time
import uhashlib  # MicroPython's hashlib for SHA-256

# WiFi credentials
ssid = "Redmi"
password = "12345678"

# Network configuration
static_ip = '192.168.47.100'
subnet_mask = '255.255.255.0'
gateway = '192.168.47.100'
dns_server = '192.168.47.100'

# File path to store data
csv_file_path = 'sha-256.csv'

def sha256_hash(data):
    """Hashes the given data using SHA-256."""
    sha256 = uhashlib.sha256()
    sha256.update(data.encode('utf-8'))
    return sha256.digest().hex()  # Use .digest() and convert to hex string

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

def write_to_file(index, hashed_data, unix_millis):
    """Append the index, hashed data, and Unix timestamp to the CSV file."""
    try:
        with open(csv_file_path, 'a') as file:
            file.write(f"{index},{hashed_data},{unix_millis}\n")
        print(f"Data written to {csv_file_path}: {index},{hashed_data},{unix_millis}")
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
            file.write("Index,SHA-256 Hash,Unix Timestamp (ms)\n")
    
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

                # Concatenate data into a single string to be hashed
                data_string = f"{last_index},{distance},{mac},{unix_millis}"
                
                # Apply SHA-256 hash
                hashed_data = sha256_hash(data_string)
                print(f"SHA-256 Hash: {hashed_data}")
                
                # Write index, hashed data, and timestamp to the CSV
                write_to_file(last_index, hashed_data, unix_millis)

                # Print the index, distance, MAC address, hash, and timestamp to terminal for reference
                print(f"Reference Data - Index: {last_index}, Distance: {distance} cm, MAC: {mac}, Hash: {hashed_data}, Unix Timestamp: {unix_millis}")
            else:
                print(f"No data received from {addr}")
                
            cl.close()
            print(f"Connection closed with {addr}")
        except Exception as e:
            print(f'Error handling client: {e}')

if __name__ == '__main__':
    main()
