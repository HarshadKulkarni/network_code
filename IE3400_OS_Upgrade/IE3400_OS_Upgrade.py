from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor
from getpass import getpass
import logging
import time


# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Enable debug logging
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
        }


        # Connect to the device
        logger.info(f"Connecting to {ip}")
        connection = ConnectHandler(**device)


        # First validation: Check for the presence of the specific file
        check_command1 = 'dir | include 17.12.'
        check_output1 = connection.send_command_timing(check_command1)


        # Second validation: Ensure "sdflash" is not in the boot command output
        check_command2 = 'show boot | include flash'
        check_output2 = connection.send_command_timing(check_command2)


        # Check both conditions
        if 'ie3x00-universalk9.17.12.04.SPA.bin' in check_output1 and 'sdflash' not in check_output2:
            print(f"Valid conditions met on {ip}. Proceeding with commands.")


            # If both conditions are met, proceed with sending other commands
            full_output = ""
            for command in commands:
                if "install add file flash" in command:
                    print("Go for coffe rebooting now")
                    output = connection.send_command_timing(command)
                    time.sleep(999999)
                if "do wr" in command:
                    output = connection.send_command_timing(command)
                    print("Saving Config")
                    time.sleep(30)
                logger.info(f"Sending command to {ip}: {command}")
                output = connection.send_command_timing(command)
                full_output += f"Command: {command}\n{output}\n"


                # Wait 10 seconds between commands
                time.sleep(10)


            # Save the full output to a file
            with open(f'{ip}_output.txt', 'w') as file:
                file.write(full_output)


            print(f"Output from {ip} saved to {ip}_output.txt")
        else:
            if 'ie3x00-universalk9.17.12.04.SPA.bin' not in check_output1:
                print(f"File 'ie3x00-universalk9.17.12.04.SPA.bin' not found on {ip}, skipping commands.")
            if 'sdflash' in check_output2:
                print(f"'sdflash' found in boot configuration on {ip}, skipping commands.")


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
 