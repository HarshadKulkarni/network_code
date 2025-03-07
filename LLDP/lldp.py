from netmiko import ConnectHandler
import csv
import getpass
import re

def get_device_ips(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        return [row['IP'] for row in reader]

def parse_output(output):
    parsed_data = []
    lines = output.strip().split('\n')
    for line in lines[5:]:  # Skip the header lines
        columns = re.split(r'\s{2,}', line)  # Split by 2 or more spaces
        if len(columns) >= 5:
            parsed_data.append({
                'Local Interface': columns[0],
                'Remote Interface': columns[-1],
                'Remote Device': columns[1],
                'Remote Port': columns[-2]
            })
    return parsed_data

def run_command_on_device(ip, username, password):
    command = 'show lldp neighbors'
    output = ''
    try:
        device = {
            'device_type': 'cisco_ios',
            'host': ip,
            'username': username,
            'password': password,
        }
        connection = ConnectHandler(**device)
        output = connection.send_command(command)
        connection.disconnect()
    except Exception as e:
        print(f"Failed to connect to {ip}: {e}")
    return output

def main():
    input_file = 'input_ips.csv'  # Change this to the path of your input CSV file
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    device_ips = get_device_ips(input_file)
    all_results = []

    for ip in device_ips:
        output = run_command_on_device(ip, username, password)
        parsed_output = parse_output(output)
        for entry in parsed_output:
            entry['Device IP'] = ip  # Add IP address to each entry
            all_results.append(entry)

    output_file = 'lldp_neighbors_output.csv'
    keys = all_results[0].keys()
    with open(output_file, 'w', newline='') as csvfile:
        dict_writer = csv.DictWriter(csvfile, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_results)
    
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
