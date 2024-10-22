import network
import socket
import time

# WiFi credentials
ssid = "Redmi"
password = "12345678"

# Network configuration
static_ip = '192.168.160.100'
subnet_mask = '255.255.255.0'
gateway = '192.168.160.100'
dns_server = '192.168.160.100'

# File path to store data
csv_file_path = 'keccak_hash.csv'

# Keccak constants
KECCAK_RATE = 136  # Rate for Keccak-256 in bytes
KECCAK_CAPACITY = 64  # Capacity for Keccak-256 in bytes
STATE_SIZE = 200  # Size of the state in bytes

# Energy consumption constants
IDLE_CURRENT = 0.070  # in Amps (70 mA when idle)
ACTIVE_CURRENT = 0.120  # in Amps (120 mA when processing)
VOLTAGE = 3.3  # Voltage for Pico W in Volts

def keccak_f1600(state):
    """Perform the Keccak-f[1600] permutation on the state."""
    # Placeholder for the actual Keccak-f implementation
    for round in range(24):
        pass  # Full implementation needed here
    return state

def keccak_256(data):
    """Perform Keccak-256 hashing."""
    state = bytearray(STATE_SIZE)
    byte_data = bytearray(data.encode('utf-8'))
    for i in range(0, len(byte_data), KECCAK_RATE):
        chunk = byte_data[i:i + KECCAK_RATE]
        for j in range(len(chunk)):
            state[j] ^= chunk[j]
        state = keccak_f1600(state)
    state[len(byte_data) % KECCAK_RATE] ^= 0x01
    state[KECCAK_RATE - 1] ^= 0x80
    state = keccak_f1600(state)
    output = bytearray()
    while len(output) < 32:
        state = keccak_f1600(state)
        output.extend(state[:KECCAK_RATE])
    return ''.join(f'{b:02x}' for b in output[:32])

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        for _ in range(20):
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
    last_index = -1
    try:
        with open(csv_file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) > 1:
                last_line = lines[-1]
                last_index = int(last_line.split(',')[0])
    except OSError:
        print(f"{csv_file_path} does not exist, initializing new file.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return last_index

def get_unix_millis():
    return int(time.time() * 1000)

def write_to_file(index, hashed_data, unix_millis):
    try:
        with open(csv_file_path, 'a') as file:
            file.write(f"{index},{hashed_data},{unix_millis}\n")
        print(f"Data written to {csv_file_path}: {index},{hashed_data},{unix_millis}")
    except OSError as e:
        print(f"Error writing to file: {e}")

# Energy calculation functions
def calculate_power(current):
    return VOLTAGE * current

def calculate_energy(power, duration):
    return power * duration * 1000  # Convert Wh to mWh

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
            pass
    except OSError:
        with open(csv_file_path, 'w') as file:
            file.write("Index,Keccak-256 Hash,Unix Timestamp (ms)\n")
    
    last_index = get_last_index()

    # Energy consumption tracking variables
    start_time = time.time()
    total_energy_consumed = 0
    try:
        while True:
            # Waiting for connection (idle state)
            idle_start_time = time.time()
            cl, addr = s.accept()  # Blocking call, will idle until connection
            idle_end_time = time.time()

            # Calculate energy consumed during idle
            idle_duration = idle_end_time - idle_start_time
            idle_power = calculate_power(IDLE_CURRENT)
            total_energy_consumed += calculate_energy(idle_power, idle_duration)

            print(f"Idle energy consumed: {total_energy_consumed:.2f} mWh")

            print(f'New connection from {addr}')
            received_data = cl.recv(1024)
            if received_data:
                active_start_time = time.time()

                received_data = received_data.decode('utf-8')
                print(f"Received Data from {addr}: {received_data}")
                
                data_parts = received_data.split(',')
                last_index += 1
                distance = data_parts[0].split(':')[1].replace('cm', '').strip()
                mac = ':'.join(data_parts[1].split(':')[1:]).strip()
                
                unix_millis = get_unix_millis()
                data_string = f"{last_index},{distance},{mac},{unix_millis}"
                
                hashed_data = keccak_256(data_string)
                print(f"Keccak-256 Hash: {hashed_data}")
                
                write_to_file(last_index, hashed_data, unix_millis)
                
                active_end_time = time.time()

                # Calculate energy consumed during active processing
                active_duration = active_end_time - active_start_time
                active_power = calculate_power(ACTIVE_CURRENT)
                total_energy_consumed += calculate_energy(active_power, active_duration)

                print(f"Active energy consumed: {total_energy_consumed:.2f} mWh")

            cl.close()
            print(f"Connection closed with {addr}")

    except KeyboardInterrupt:
        print(f"Total energy consumed: {total_energy_consumed:.2f} mWh")

if __name__ == "__main__":
    main()