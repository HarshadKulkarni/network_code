import os
import sys
import argparse
import datetime
import json
import csv
from netmiko import ConnectHandler
import textfsm
from getpass import getpass as gp
 
def get_credentials():
    username = input("Enter your username: ")
    password = gp("Enter your password: ")
    hostname = input("Enter the hostname or IP address: ")
    return username, password, hostname
 
def ssh_connect(username, password, hostname):
    try:
        # Define the device parameters
        device = {
            'device_type': 'cisco_ios',
            'host': hostname,
            'username': username,
            'password': password,
        }
       
        # Establish an SSH connection
        connection = ConnectHandler(**device)
       
        # Send the command and receive the output
        output = connection.send_command("show lldp neighbor details")
       
        # Close the connection
        connection.disconnect()
       
        return output
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
   
# Parse output using textfsm
def parse_output(filepath, template_path):
    with open(template_path) as template_file:
        fsm = textfsm.TextFSM(template_file)
        with open(filepath) as output_file:
            parsed_results = fsm.ParseText(output_file.read())
        return [dict(zip(fsm.header, result)) for result in parsed_results]
   
# Load all parsed files into a dictionary
def load_parsed_outputs(parsed_folder):
    parsed_output_dict = {}
    for filename in os.listdir(parsed_folder):
        if filename.endswith(".json"):
            ip_or_hostname = filename.replace("parsed-", "").replace(".json", "")
            with open(os.path.join(parsed_folder, filename), 'r') as file:
                neighbor_list = json.load(file)
            parsed_output_dict[ip_or_hostname] = {
                'neighbor_list': neighbor_list
            }
    return parsed_output_dict
 
# Main SW search function
def search_sw(parsed_output_dict, sw_name):
    final_output = []
    for switch, data in parsed_output_dict.items():
        for neighbor in data['neighbor_list']:
            if "-sw" in neighbor['NEIGHBOR_NAME'].lower():
                final_output.append({
                    'sw_device': neighbor['NEIGHBOR_NAME'],
                    'uplink_switch': switch.replace(".txt", ""),
                    'uplink_interface': neighbor['LOCAL_INTERFACE'],
                    'sw_ip': neighbor['MGMT_ADDRESS']
                })
    return final_output
 
# Save the final output to a CSV file
def save_to_csv(final_output, output_folder):
    csv_filename = os.path.join(output_folder, "fin-out.csv")
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['sw_device', 'uplink_switch', 'uplink_interface', 'sw_ip']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in final_output:
            writer.writerow(entry)
    print(f"Final output saved to {csv_filename}")
 
def create_timestamped_folder(base_folder):
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = os.path.join(base_folder, timestamp)
    os.makedirs(folder, exist_ok=True)
    return folder
 
def execute_command(target, command, output_folder, username, password):
    try:
        # Define the device parameters
        device = {
            'device_type': 'cisco_ios',
            'host': target,
            'username': username,
            'password': password,
        }
       
        # Establish an SSH connection
        connection = ConnectHandler(**device)
       
        # Send the command and receive the output
        output = connection.send_command(command)
       
        # Close the connection
        connection.disconnect()
       
        # Save the raw output to a file
        raw_filename = f"out-{target}.txt"
        raw_filepath = os.path.join(output_folder, raw_filename)
        with open(raw_filepath, 'w') as raw_file:
            raw_file.write(output)
       
        return raw_filepath
    except Exception as e:
        print(f"An error occurred while executing command on {target}: {e}")
        return None
 
def main(target_file):
    username, password, hostname = get_credentials()
    output = ssh_connect(username, password, hostname)
 
    # Path to the textfsm template
    template_file = os.path.join(os.path.dirname(__file__), 'cisco_ios_show_lldp_neighbors_detail.txt')
 
    # Create output folders if they don't exist
    raw_output_base = "z-out-raw"
    parsed_output_base = "z-out-parsed"
    final_output_base = "z-out-fin"
    os.makedirs(raw_output_base, exist_ok=True)
    os.makedirs(parsed_output_base, exist_ok=True)
    os.makedirs(final_output_base, exist_ok=True)
 
    # Create timestamped folders for this run
    raw_output_folder = create_timestamped_folder(raw_output_base)
    parsed_output_folder = create_timestamped_folder(parsed_output_base)
    final_output_folder = create_timestamped_folder(final_output_base)
 
    # Open target.txt file
    with open(target_file, 'r') as file:
        targets = [line.strip() for line in file.readlines()]
   
    # Execute show lldp command
    command = "show lldp neighbors detail"
    for target in targets:
        raw_filepath = execute_command(target, command, raw_output_folder, username, password)
        if raw_filepath:
            parsed_data = parse_output(raw_filepath, template_file)
 
            # Output to a JSON file
            parsed_filename = f"parsed-{os.path.basename(raw_filepath).replace('out-', '')}.json"
            parsed_filepath = os.path.join(parsed_output_folder, parsed_filename)
            with open(parsed_filepath, 'w') as parsed_file:
                json.dump(parsed_data, parsed_file, indent=4)
            print(f"Parsed output saved to {parsed_filepath}")
 
    # Load all parsed outputs into a dictionary
    parsed_output_dict = load_parsed_outputs(parsed_output_folder)
   
    # Search for IE/APs in the parsed output
    final_output = search_sw(parsed_output_dict, "-sw")
 
    # Save the final output to a CSV file
    save_to_csv(final_output, final_output_folder)
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and parse APs on Cisco Switches")
    parser.add_argument('--target', required=True, help='Path to target.txt file')
    args = parser.parse_args()
    main(args.target)