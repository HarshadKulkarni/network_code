#Usage: python3 get_vlan_int_ip_mac.py ips.csv
import csv
from netmiko import ConnectHandler
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to read IPs from CSV
def read_ips(filename):
    with open(filename, newline='') as csvfile:
        ipreader = csv.reader(csvfile)
        return [row[0] for row in ipreader]

# Function for Encoding    
def read_ips(filename):
    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        ipreader = csv.reader(csvfile)
        return [row[0] for row in ipreader]

# Function to run commands and store output
def run_commands(ip, username, password):
    device = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': username,
        'password': password,
    }

    # Connect to the device
    logger.info(f"Connecting to {ip}")
    connection = ConnectHandler(**device)

    connection = ConnectHandler(**device)
    output1 = connection.send_command("sh run | i hostname TBMNC")
    output2 = connection.send_command("show int Vlan1021 | i Internet")
    output3 = connection.send_command("show int Vlan1021 | i Hardware")
    connection.disconnect()

    return output1, output2, output3

# Function to store output in CSV
def store_output(filename, data):
    with open(filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Hostname", "Internet_Add", "Hardware_Add"])
        for row in data:
            writer.writerow(row)

# Main function to tie it all together
def main():
    ips = read_ips('ips.csv')
    username = input("Enter username: ")
    password = input("Enter password: ")
    results = []

    for ip in ips:
        try:
            output1, output2, output3 = run_commands(ip, username, password)
            results.append([output1, output2, output3])
        except Exception as e:
            print(f"Failed to connect to {ip}: {e}")

    store_output('output.csv', results)

if __name__ == "__main__":
    main()