import csv
import getpass
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import yaml
import pandas as pd

def capture_lldp_neighbors(device):
    connection = ConnectHandler(**device)
    output = connection.send_command("show lldp neighbors")
    connection.disconnect()
    return output

def parse_lldp_neighbors(output, template_path):
    parsed_data = parse_output(output, template_path)
    return parsed_data

def save_to_yaml(data, filename):
    with open(filename, 'w') as yaml_file:
        yaml.dump(data, yaml_file, default_flow_style=False)

if __name__ == "__main__":
    # Ask for username and password
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    #secret = getpass.getpass("Enter your enable/secret password: ")

    # Read switch IP addresses from CSV
    switch_df = pd.read_csv('input_switch_ips.csv')
    switch_ips = switch_df['ip_address'].tolist()

    template_path = "ntc_templates/templates/cisco_ios_show_lldp_neighbors.textfsm"
    
    all_parsed_data = []

    for ip in switch_ips:
        device = {
            'device_type': 'cisco_ios',
            'host': ip,
            'username': username,
            'password': password,
        }

        # Capture the output from the device
        command_output = capture_lldp_neighbors(device)

        # Parse the output using NTC template
        parsed_data = parse_lldp_neighbors(command_output, template_path)
        all_parsed_data.append({
            'ip_address': ip,
            'lldp_neighbors': parsed_data
        })

    # Save the parsed data to a YAML file
    save_to_yaml(all_parsed_data, "lldp_neighbors.yaml")

    print("Parsed LLDP neighbors data saved to lldp_neighbors.yaml")
