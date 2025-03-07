# Usage: python3 Nexus_Health_Config_Check_v2.py ips.csv
import csv
from netmiko import ConnectHandler
from getpass import getpass

# Function to connect to the device
def connect_device(device):
    connection = ConnectHandler(**device)
    connection.enable()
    return connection

# Function to run commands on the device
def run_commands(connection, commands):
    output = {}
    for command in commands:
        output[command] = connection.send_command(command)
    return output

# Function to write output to a file
def write_output_to_file(output, ip):
    output_file = f"{ip.strip()}.txt"
    with open(output_file, 'w') as file:
        for command, result in output.items():
            file.write(f"==== {command.upper()} OUTPUT ====\n")
            file.write(result)
            file.write("\n\n")
    print(f"Output stored in {output_file}")

# Main function
def main():
    username = input("Enter your username: ")
    password = getpass("Enter your password: ")

    commands = ['show version', 'show inventory', 'show module']

    with open('ips.csv', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            ip = row[0]
            device = {
                'device_type': 'cisco_ios',
                'ip': ip.strip(),
                'username': username,
                'password': password,
            }

            try:
                connection = connect_device(device)
                output = run_commands(connection, commands)
                write_output_to_file(output, ip)
                connection.disconnect()
            except Exception as e:
                print(f"Failed to connect to {ip}: {e}")

if __name__ == "__main__":
    main()
