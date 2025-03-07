import csv
import logging
from netmiko import ConnectHandler
from getpass import getpass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Prompt for username and password
username = input("Enter your SSH username: ")
password = getpass("Enter your SSH password: ")  # Password will be hidden as you type

# Define a function to get port status via SSH
def get_port_status(switch_name, port, username, password):
    try:
        # Device connection parameters (customize as needed)
        device = {
            'device_type': 'cisco_ios',  # Adjust based on your switch type
            'host': switch_name,
            'username': username,
            'password': password,
        }
        logger.info(f"Connecting to switch: {switch_name}")
        # Establish SSH connection
        with ConnectHandler(**device) as ssh_conn:
            logger.info(f"Connected to {switch_name}. Retrieving status for port: {port}")
            # Send a command to check port status (modify command as needed)
            command = f"show interface {port} status"
            output = ssh_conn.send_command(command)
            # Extract status from the output (adjust parsing logic as needed)
            if "connected" in output:
                logger.info(f"Port {port} on {switch_name} is connected.")
                return "connected"
            elif "notconnect" in output:
                logger.info(f"Port {port} on {switch_name} is not connected.")
                return "notconnect"
            else:
                logger.warning(f"Port status for {port} on {switch_name} is unknown.")
                return "unknown"
    except Exception as e:
        logger.error(f"Error connecting to {switch_name}: {e}")
        return f"Error: {e}"

# Process the CSV file
def process_csv(file_path):
    logger.info(f"Reading CSV file: {file_path}")
    with open(file_path, mode='r') as csv_file:
        reader = csv.reader(csv_file)
        rows = list(reader)

    # Assuming the first row is a header
    header = rows[0]
    header.append("Status")  # Add a new column for status

    # Process each switch and port
    for row in rows[1:]:
        switch_name, port = row[0], row[1]
        logger.info(f"Processing switch: {switch_name}, port: {port}")
        status = get_port_status(switch_name, port, username, password)
        row.append(status)

    # Write updated data back to the CSV file
    with open(file_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(rows)
    logger.info(f"Updated CSV file saved: {file_path}")

# Example usage
input_csv_file = "input.csv"  # Replace with your CSV file name
process_csv(input_csv_file)
