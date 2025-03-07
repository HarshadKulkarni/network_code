from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor
from getpass import getpass
import logging

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_and_retrieve(ip, username, password, commands):
    """Connect to a network device via SSH and retrieve command output."""
    try:
        # Define the device parameters
        device = {
            'device_type': 'cisco_ios',  # Adjust this for your specific device type
            'host': ip,
            'username': username,
            'password': password,
            'timeout': 100,  # Increase timeout for long-running commands
            'blocking_timeout': 100,
        }

        # Connect to the device
        logger.info(f"Connecting to {ip}")
        connection = ConnectHandler(**device)

        # Set terminal length to 0 to disable paging
        connection.send_command('terminal length 0')

        # Retrieve the hostname
        hostname_output = connection.send_command("show run | include hostname")
        hostname = hostname_output.split()[1] if "hostname" in hostname_output else ip

        # Execute commands and collect output
        full_output = ""
        for command in commands:
            logger.info(f"Sending command to {ip}: {command}")
            output = connection.send_command_timing(command, delay_factor=2)
            full_output += f"{hostname}# {command}\n{output}\n"

        # Save the full output to a file
        with open(f'{ip}_output.txt', 'w') as file:
            file.write(full_output)

        logger.info(f"Output from {ip} saved to {ip}_output.txt")

        # Disconnect from the device
        connection.disconnect()

    except Exception as e:
        logger.error(f"Failed to connect or retrieve data from {ip}: {e}")

def main():
    """Read IP addresses and commands from files and connect to them concurrently."""
    try:
        # Prompt user for SSH credentials
        username = input("Enter your SSH username: ")
        password = getpass("Enter your SSH password: ")

        # Read IP addresses from file
        with open('ips.txt', 'r') as file:
            ip_list = [line.strip() for line in file if line.strip()]

        # Read commands from file
        with open('commands.txt', 'r') as file:
            commands = [line.strip() for line in file if line.strip()]

        # Use ThreadPoolExecutor to connect to IPs concurrently
        with ThreadPoolExecutor() as executor:
            executor.map(lambda ip: connect_and_retrieve(ip, username, password, commands), ip_list)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
