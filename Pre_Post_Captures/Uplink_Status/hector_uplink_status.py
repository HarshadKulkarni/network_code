import os
import csv
import logging
from netmiko import ConnectHandler
from getpass import getpass

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_command_output(connection, command):
    """Execute a command on the device and return the output."""
    try:
        logger.debug(f"Sending command: {command}")
        output = connection.send_command(command)
        logger.debug(f"Output for command '{command}': {output}")
        return output
    except Exception as e:
        logger.error(f"Failed to execute command '{command}': {e}")
        return ""

def parse_port_channel_details(output):
    """Parse the number of port channels and aggregators from the command output."""
    logger.debug(f"Parsing Port Channel Details from Output: {output}")
    channel_groups = 0
    aggregators = 0
    ports_bundled = 0
    for line in output.splitlines():
        if 'Number of channel-groups in use' in line:
            channel_groups = int(line.split(':')[-1].strip())
        elif 'Number of aggregators' in line:
            aggregators = int(line.split(':')[-1].strip())
        elif '(P)' in line:
            ports_bundled += line.count('(P)')
    logger.debug(f"Parsed Port Channel Details - Channel Groups: {channel_groups}, Aggregators: {aggregators}, Ports Bundled: {ports_bundled}")
    return channel_groups, aggregators, ports_bundled

def parse_isis_neighbors_count(output):
    """Parse the number of ISIS neighbors from the command output."""
    logger.debug(f"Parsing ISIS Neighbors Count from Output: {output}")
    count = 0
    for line in output.splitlines():
        if 'Number of lines which match regexp' in line:
            count = int(line.split('=')[-1].strip())
    logger.debug(f"Parsed ISIS Neighbors Count: {count}")
    return count

def save_device_data_to_csv(ip, hostname, channel_groups, aggregators, ports_bundled, isis_neighbors_count, csv_filename='device_data.csv'):
    """Save the parsed data to a CSV file."""
    logger.debug(f"Saving data to CSV for hostname: {hostname}")
    with open(csv_filename, 'a', newline='') as csvfile:
        fieldnames = ['IP Address', 'Hostname', 'Channel Groups', 'Aggregators', 'Ports Bundled', 'ISIS Neighbors Count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if csvfile.tell() == 0:
            writer.writeheader()
        writer.writerow({
            'IP Address': ip,
            'Hostname': hostname,
            'Channel Groups': channel_groups,
            'Aggregators': aggregators,
            'Ports Bundled': ports_bundled,
            'ISIS Neighbors Count': isis_neighbors_count
        })
    logger.info(f"Data for {hostname} saved to CSV.")

def connect_and_collect_data(ip, username, password):
    """Connect to the device, execute commands, and collect the output."""
    device = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': username,
        'password': password,
    }

    try:
        logger.info(f"Connecting to {ip}")
        connection = ConnectHandler(**device)
        
        hostname_command = "show running-config | include hostname"
        port_channel_command = "show etherchannel summary"
        isis_neighbors_command = "show isis neighbors | count UP"
        
        hostname_output = get_command_output(connection, hostname_command)
        port_channel_output = get_command_output(connection, port_channel_command)
        isis_neighbors_output = get_command_output(connection, isis_neighbors_command)
        
        # Extract hostname from output
        hostname = hostname_output.split()[1] if 'hostname' in hostname_output else ip
        
        # Check if outputs are received
        if not port_channel_output:
            logger.warning(f"No Port Channel output received for {ip}.")
        if not isis_neighbors_output:
            logger.warning(f"No ISIS Neighbors output received for {ip}.")
        
        connection.disconnect()

        return hostname, port_channel_output, isis_neighbors_output
         
    except Exception as e:
        logger.error(f"Failed to connect to {ip}: {e}")
        return None, None, None

def main():
    """Main function to connect to devices, collect data, and save to CSV."""
    try:
        # Prompt user for SSH credentials
        username = input("Enter your SSH username: ")
        password = getpass("Enter your SSH password: ")

        # Read IP addresses from the 'ips.txt' file
        with open('ips.txt', 'r') as ip_file:
            ip_list = [line.strip() for line in ip_file if line.strip()]

        if not ip_list:
            logger.warning("No IP addresses found in ips.txt.")
            return
        
        csv_filename = 'device_data.csv'
        
        # Ensure the CSV file is created and header is written
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = ['IP Address', 'Hostname', 'Channel Groups', 'Aggregators', 'Ports Bundled', 'ISIS Neighbors Count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        # Connect to each device and collect data
        for device_ip in ip_list:
            hostname, port_channel_output, isis_neighbors_output = connect_and_collect_data(device_ip, username, password)
            if hostname and port_channel_output and isis_neighbors_output:
                channel_groups, aggregators, ports_bundled = parse_port_channel_details(port_channel_output)
                isis_neighbors_count = parse_isis_neighbors_count(isis_neighbors_output)
                save_device_data_to_csv(device_ip, hostname, channel_groups, aggregators, ports_bundled, isis_neighbors_count, csv_filename)
            else:
                logger.error(f"Failed to collect data for device {device_ip}.")
        
        logger.info("Processing complete, data saved to CSV.")
        
    except FileNotFoundError:
        logger.error("The file 'ips.txt' was not found. Please ensure it exists in the current directory.")
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
