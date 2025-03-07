# ++++++++++++Author: Harshad Kulkarni +++++++++++
# Steps 
# Read Hostname from switches.csv file
# Login to switch
# Run "Show Version"
# Store Output in Buffer memory
# Parse Output into YML
# Save parsed Output into YML file with Switch hostname as filename

import csv
import yaml
from ntc_templates.parse import parse_output
from netmiko import ConnectHandler

# Function to read Hostnames from CSV
def read_hostnames(filename):
    with open(filename, newline='') as csvfile:
        hostname = csv.reader(csvfile)
        return [row[0] for row in hostname]
    
# Function to run "show version"  command and store output
def run_command(hostname, username, password):
    device = {
        'device_type': 'cisco_ios',
        'host': hostname,
        'username': username,
        'password': password,
    }

    connection = ConnectHandler(**device)
    output = connection.send_command("show version")
    connection.disconnect()

    return output

#Function to parser output and store in yml file
def parse_output_using_ntc(output):
    parsed_output = parse_output(platform="cisco_ios", command="show version", data=output)
    return parsed_output

def store_as_yaml(parsed_output, hostname):
    filename = f"{hostname}.yml"
    with open(filename, "w") as f:
        yaml.dump(parsed_output, f)
    print(f"Stored parsed output to {filename}")


# Define Main
def main():
    hostname = read_hostnames('switches.csv')
    username = input("Enter username: ")
    password = input("Enter password: ")

    for hostname in hostname:
        try:
            output = run_command(hostname, username, password)
            parsed_output = parse_output_using_ntc(output)
            store_as_yaml(hostname, output)
        except Exception as e:
            print(f"Failed to connect to {hostname}: {e}")

if __name__ == "__main__":
    main()