#USAGE: python3 inv_discover.py --inventory "cdp_table.csv"
import re
import csv
import sys
import json
import getpass
import argparse
import openpyxl
from netmiko import ConnectHandler

parser = argparse.ArgumentParser(description='Connect to a cisco device using SSH and execute a command')
parser.add_argument('--inventory', type=str, help='Path to inventory CSV file')
args = parser.parse_args()

def ssh_comm(device_list, command, password, username):
    results = {}
    pattern = r"(sw|gw)"
    for device_key, device_val in device_list.items():
        if re.search(pattern, device_val['Hostname'], re.IGNORECASE):
            hostname, ip_address = device_val['Hostname'], device_val['Ip_address']
            device_key = f"{hostname}_{ip_address}"
            device_key = f"{hostname}"
            try:
                connection = ConnectHandler(
                    device_type='cisco_ios',
                    ip=ip_address,
                    username=username,
                    password=password
                    )
                output = connection.send_command(command, use_textfsm=True)
                results[device_key] = {
                    "success": True,
                    "output": output
                }
                connection.disconnect()
                print(f"Successfully connected to {device_key}")
            except Exception as e:
                print(f"Failed to connect to {device_key}")
                results[device_key] = {
                    "success": False,
                    "output": str(e)
                }
        else:
            print(f"Skipping {device_val['Hostname']} - hostname check condition failed")
            continue
    return results

def read_inventory(inventory_path):
    device_list = {}
    with open(inventory_path, mode='r') as file:
        devices = csv.DictReader(file)
        for device in devices:
            device_list.update(
                {
                    f"{device['Hostname']}": {}
                }

            )
            device_list[f"{device['Hostname']}"].update(
                {
                    'Hostname': f"{device['Hostname']}",
                    'Ip_address': f"{device['Ip_address']}"
                }
            )
        return device_list

def count_items(lst):
   counts = {
    "Description": "Total"
   }
   for item in lst:
       if item in counts:
           counts[item] += 1
       else:
           counts[item] = 1
   return counts

def generate_excel(data1, data2):
    workbook = openpyxl.Workbook()
    first_sheet = True
    sheet = workbook.active
    sheet.title = "Summary"
    for k,v in data1.items():
        sheet.append([k,v])
    for switch, entries in data2.items():
        sheet = workbook.create_sheet(title=switch)
        for entry in entries:
            sheet.append(entry.split(","))
    workbook.save("network_switch_data.xlsx")

def main():
    username = input("Enter username: ")
    password = getpass.getpass(prompt="Enter your device password: ")
    inventory_path = args.inventory
    devices = read_inventory(inventory_path)
    all_inv = []
    all_inv_descr = []
    device_tab = {}
    # Connect to device
    inv_table = ssh_comm(devices, "show inventory", password, username)
    with open('j_inv.json', 'w') as file:
        json.dump(inv_table, file, indent=4)
    # Use saved json file
    # with open('j_inv.json', 'r') as file:
    #     inv_table = json.load(file)
    print(json.dumps(all_inv, indent=2))

    for device, value in inv_table.items():
        if value['success']:
            device_tab.update({device: []})
            all_inv.extend(value['output'])
            for inv in value['output']:
                all_inv_descr.append(inv['descr'])
                device_tab[device].append(
                    f"NAME:,{inv['name']},DESCR:,{inv['descr']},PID:,{inv['pid']},SN:,{inv['sn']}"
                )

    print(json.dumps(all_inv, indent=2))
    print(json.dumps(all_inv_descr, indent=2))
    result = count_items(all_inv_descr)
    print(json.dumps(result, indent=2))
    print(json.dumps(device_tab, indent=2))
    generate_excel(result, device_tab)

if __name__ == "__main__":
    main()