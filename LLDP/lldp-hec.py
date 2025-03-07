from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor
from getpass import getpass
import csv
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_neighbor_output(output, command_type, originating_device):
    """Parse the neighbor output into a list of dictionaries based on the protocol."""
    entries = []
    current_entry = {}
    for line in output.splitlines():
        if command_type == "cdp":
            if "Device ID:" in line:
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    'Originating Device': originating_device,
                    'Device ID': line.split("Device ID:")[1].strip()
                }
            elif "IP address:" in line:
                current_entry['IP address'] = line.split("IP address:")[1].strip()
            elif "Platform:" in line:
                current_entry['Platform'] = line.split("Platform:")[1].strip().split(',')[0]
            elif "Interface:" in line:
                current_entry['Local Interface'] = line.split("Interface:")[1].split(',')[0].strip()
                current_entry['Port ID'] = line.split("Port ID (outgoing port):")[1].strip()
        elif command_type == "lldp":
            if "Chassis id:" in line:
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    'Originating Device': originating_device,
                    'Chassis ID': line.split("Chassis id:")[1].strip()
                }
            elif "Port id:" in line:
                current_entry['Port ID'] = line.split("Port id:")[1].strip()
            elif "Port Description:" in line:
                current_entry['Port Description'] = line.split("Port Description:")[1].strip()
            elif "System Name:" in line:
                current_entry['System Name'] = line.split("System Name:")[1].strip()
            elif "System Description:" in line:
                current_entry['System Description'] = line.split("System Description:")[1].strip()
            elif "Local Intf:" in line:
                current_entry['Local Intf'] = line.split("Local Intf:")[1].strip()
    if current_entry:
        entries.append(current_entry)
    return entries


def connect_and_retrieve(ip, username, password):
    """Connect to a network device via SSH and retrieve CDP and LLDP details."""
    try:
        # Define the device parameters
        device = {
            'device_type': 'cisco_ios',
            'host': ip,
            'username': username,
            'password': password,
        }


        # Connect to the device
        logger.info(f"Connecting to {ip}")
        connection = ConnectHandler(**device)


        # CDP command
        cdp_command = "show cdp neighbors detail"
        logger.info(f"Sending CDP command to {ip}: {cdp_command}")
        cdp_output = connection.send_command(cdp_command)
        cdp_data = parse_neighbor_output(cdp_output, "cdp", ip)
        
        # LLDP command
        lldp_command = "show lldp neighbors detail"
        logger.info(f"Sending LLDP command to {ip}: {lldp_command}")
        lldp_output = connection.send_command(lldp_command)
        lldp_data = parse_neighbor_output(lldp_output, "lldp", ip)


        # Save CDP data to CSV
        cdp_csv_filename = f'cdp_neighbors.csv'
        with open(cdp_csv_filename, 'a', newline='') as csvfile:
            fieldnames = ['Originating Device', 'Device ID', 'IP address', 'Platform', 'Local Interface', 'Port ID']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for entry in cdp_data:
                writer.writerow(entry)


        # Save LLDP data to CSV
        lldp_csv_filename = f'lldp_neighbors.csv'
        with open(lldp_csv_filename, 'a', newline='') as csvfile:
            fieldnames = ['Originating Device', 'Chassis ID', 'Port ID', 'Port Description', 'System Name', 'System Description', 'Local Intf']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for entry in lldp_data:
                writer.writerow(entry)


        logger.info(f"CDP data from {ip} saved to {cdp_csv_filename}")
        logger.info(f"LLDP data from {ip} saved to {lldp_csv_filename}")


        # Disconnect from the device
        connection.disconnect()


    except Exception as e:
        logger.error(f"Failed to connect or retrieve data from {ip}: {e}")


def main():
    """Read IP addresses from a file and connect to them concurrently."""
    try:
        # Prompt user for SSH credentials
        username = input("Enter your SSH username: ")
        password = getpass("Enter your SSH password: ")


        # Read IP addresses from file
        with open('ips.txt', 'r') as file:
            ip_list = [line.strip() for line in file if line.strip()]


        # Use ThreadPoolExecutor to connect to IPs concurrently
        with ThreadPoolExecutor() as executor:
            executor.map(lambda ip: connect_and_retrieve(ip, username, password), ip_list)


    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == '__main__':
    main()