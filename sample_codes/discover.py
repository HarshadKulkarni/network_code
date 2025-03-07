#USAGE: python3 discover.py --username "username" --inventory "inventory-1.csv"
import re
import csv
import sys
import json
import socket
import getpass
import jmespath
import argparse
import datetime
from netmiko import ConnectHandler
from netaddr import IPNetwork, IPAddress
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException


parser = argparse.ArgumentParser(description='Connect to a cisco device using SSH and execute a command')
parser.add_argument('--username', type=str, help='Username')
parser.add_argument('--inventory', type=str, help='Path to inventory CSV file')
args = parser.parse_args()

def get_items_with_key_value(data, key, value):
   return [item for item in data if key in item and item[key] == value]

def dnslookup(hostname, default_value):
   try:
       # Attempt to resolve the hostname to an IP address
       ip_address = socket.gethostbyname(hostname)
       return {'ip': ip_address, 'dns_result': 'successful'}
   except Exception as e:
       # Catch any kind of exception and format the return value to include the default value and error message
       return {'ip': default_value, 'dns_result': str(e)}

def ssh_comm(device_list, command, password):
    results = {}
    pattern = r"(sw|gw)"
    for device_key, device_val in device_list.items():
        if re.search(pattern, device_val['HOSTNAME'], re.IGNORECASE):
            hostname, ip_address = device_val['HOSTNAME'], device_val['IP_ADDRESS']
            device_key = f"{hostname}_{ip_address}"
            device_key = f"{hostname}"
            try:
                connection = ConnectHandler(
                    device_type='cisco_ios',
                    ip=ip_address,
                    username=args.username,
                    password=password
                    )
                output = connection.send_command(command, use_textfsm=True)
                results[device_key] = {
                    "success": True,
                    "output": output
                }
                connection.disconnect()
                print(f"Successfully connected to {device_key}")
            # except (NetmikoAuthenticationException, NetmikoTimeoutException, TextFSMError) as e:
            except Exception as e:
                print(f"Failed to connect to {device_key}")
                results[device_key] = {
                    "success": False,
                    "output": str(e)
                }
        else:
            print(f"Skipping {device_val['HOSTNAME']} - hostname check condition failed")
            continue
    return results

def read_inventory(inventory_path):
    device_list = {}
    with open(inventory_path, mode='r') as file:
        devices = csv.DictReader(file)
        for device in devices:
            device_list.update(
                {
                    f"{device['HOSTNAME']}": device
                }

            )
            device_list[f"{device['HOSTNAME']}"].update(
                {
                    'csv_entry': f"{device['HOSTNAME']},{device['IP_ADDRESS']}",
                    'cdp_links': {}
                }
            )
        return device_list

def cdp_data_table(ssh_comm_cdp, new_inv_dict):
    for device, result in ssh_comm_cdp.items():
        # print(json.dumps(device, indent=2))
        # print(json.dumps(result, indent=2))
        if result["success"] and isinstance(result["output"], list):
            for neighbor in result["output"]:
                if f"{neighbor['destination_host']}" not in new_inv_dict:
                    ip_lookup = dnslookup(f"{neighbor['destination_host']}",f"{neighbor['management_ip']}")
                    new_inv_dict.update(
                        {
                            f"{neighbor['destination_host']}":{
                                "HOSTNAME": f"{neighbor['destination_host']}",
                                "IP_ADDRESS": ip_lookup['ip'],
                                "DNS_LOOKUP": ip_lookup['dns_result'],
                                "csv_entry": f"{neighbor['destination_host']},{neighbor['management_ip']}",
                                "cdp_detected_os": f"{neighbor['software_version']}",
                                "cdp_detected_platform": f"{neighbor['platform']}",
                                "cdp_detected_capabilities": f"{neighbor['capabilities']}",
                                "cdp_links": {}
                            }
                        }
                    )
                if f"{neighbor['destination_host']}" in new_inv_dict:
                    new_inv_dict[f"{neighbor['destination_host']}"]['cdp_links'].update(
                        {
                            f"{device}_port_{neighbor['local_port']}": {
                                "local_port": f"{neighbor['remote_port']}",
                                "remote_port": f"{device}, port {neighbor['local_port']}"
                            }
                        }
                    )
                    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{args.inventory.split('.')[0]}_{timestamp}.csv"
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['HOSTNAME', 'IP_ADDRESS'])
        for entry in new_inv_dict:
            writer.writerow(entry.split(', '))
    print(json.dumps(new_inv_dict, indent=2))
    sys.exit()
    new_inv_len = len(new_inv_dict.items())
    return new_inv_dict

def vlan_frame(ssh_comm_vlan_br):
    device_vlan_dict = {}
    for device, result in ssh_comm_vlan_br.items():
        device_vlan_dict.update(
            {
                device: {
                    "vlan_dict": {}
                }
            }
        )
        if result["success"] and isinstance(result["output"], list):
            for vlan in result["output"]:
                device_vlan_dict[device]['vlan_dict'].update(
                    {
                        f"vlan_{vlan['vlan_id']}": {
                            "vlan_id": vlan['vlan_id'],
                            "vlan_name": vlan['name'],
                            "vlan_status": vlan['status']
                        }
                    }
                )
    return device_vlan_dict

def main():
    password = getpass.getpass(prompt="Enter your device password: ")
    inventory_path = args.inventory
    devices = read_inventory(inventory_path)
    print(json.dumps(devices, indent=2))
    sys.exit()

    new_inv_dict = {}
    comm_list = [
        "show cdp neighbors detail",
        "show version",
        "show vlan brief",
        "show ip interface"
    ]
    vlan_dict = {
    }

    # for command in comm_list[0:1]:
    # for command in comm_list[0:2]:
    for command in comm_list:
        with open('j_devices.json', 'r') as file:
            devices = json.load(file)
        with open('j_version.json', 'r') as file:
            command_show_version_results = json.load(file)
        with open('j_vlan.json', 'r') as file:
            command_show_vlan_brief_results = json.load(file)
        with open('j_ipint.json', 'r') as file:
            command_show_ip_interface_results = json.load(file)
        '''
        if command == "show cdp neighbors detail":
            print("#################################################################### NEW show cdp neighbors detail ####################################################################")
            new_inv_dict = devices
            print(" INSIDE IF")
            cdp_comm = True
            while cdp_comm:
                if len(new_inv_dict.items()) == 0:
                    cdp_comm = False
                print("     INSIDE WHILE")
                print("     ################# devices #################")
                print(json.dumps(devices, indent=2))
                print(len(devices))
                print("     ################# OLD new_inv_dict #################")
                print(json.dumps(new_inv_dict, indent=2))
                print(len(new_inv_dict))
                command_results = ssh_comm(new_inv_dict, command, password)
                print("     ################# command_results #################")
                print(json.dumps(command_results, indent=2))
                new_inv_dict = {}
                new_inv_dict.update(cdp_data_table(command_results, new_inv_dict))
                new_inv_dict_2 = {}
                print("     ################# new_inv_dict - 1ST #################")
                print(json.dumps(new_inv_dict, indent=2))
                for device, device_val in new_inv_dict.items():
                    print("         ################# CHECK new_inv_dict #################")
                    print(device)
                    print(json.dumps(devices.get(device, None), indent=2))
                    item_dict = {
                        f"{device_val['HOSTNAME']}" : device_val
                    }
                    print(json.dumps(item_dict, indent=2))
                    if f"{device_val['HOSTNAME']}" not in devices:
                        devices.update(item_dict)
                        new_inv_dict_2.update(item_dict)
                        print("         INSIDE IF2A")
                        print(json.dumps(devices, indent=2))
                        print(json.dumps(new_inv_dict_2, indent=2))

                    if f"{device_val['HOSTNAME']}" in devices:
                        print("         INSIDE IF2B")
                        print(json.dumps(devices[f"{device_val['HOSTNAME']}"], indent=2))
                        print(json.dumps(item_dict[f"{device_val['HOSTNAME']}"], indent=2))
                        # sys.exit()
                        for remote, local in item_dict[f"{device_val['HOSTNAME']}"]["cdp_links"].items():
                            print("             INSIDE IF2B-FOR")
                            print(json.dumps(remote, indent=2))
                            print(json.dumps(local, indent=2))
                            devices[f"{device_val['HOSTNAME']}"]['cdp_links'].update(
                                {
                                    f"{remote}": local
                                }
                            )
                print("     ################# NEW new_inv_dict #################")
                new_inv_dict = new_inv_dict_2
                print(json.dumps(new_inv_dict, indent=2))
                print(len(new_inv_dict))
                # sys.exit()
            with open('j_devices.json', 'w') as file:
                json.dump(devices, file, indent=4)
                
        if command == "show version":
            print("#################################################################### NEW show version ####################################################################")
            command_show_version_results = ssh_comm(devices, command, password)
            print(json.dumps(command_show_version_results, indent=2))
            with open('j_version.json', 'w') as file:
                json.dump(command_show_version_results, file, indent=4)

        if command == "show vlan brief":
            print("#################################################################### NEW show vlan_brief ####################################################################")
            command_show_vlan_brief_results = ssh_comm(devices, command, password)
            print(json.dumps(command_show_vlan_brief_results, indent=2))
            with open('j_vlan.json', 'w') as file:
                json.dump(command_show_vlan_brief_results, file, indent=4)

        if command == "show ip interface":
            print("#################################################################### NEW show ip_interface ####################################################################")
            command_show_ip_interface_results = ssh_comm(devices, command, password)
            print(json.dumps(command_show_ip_interface_results, indent=2))
            with open('j_ipint.json', 'w') as file:
                json.dump(command_show_ip_interface_results, file, indent=4)

        # '''
    print("################# DEVICES #################")
    # print(json.dumps(new_inv_dict, indent=2))
    print(json.dumps(devices, indent=2))
    print(len(devices))
    print(json.dumps(command_show_version_results, indent=2))
    print(len(command_show_version_results))


    device_table = [
        [
            "Hostname",
            "OS",
            "SN",
            "Platform",
            "CDP_links",
            "CDP_links_platform"
        ]
    ]

    for device, value in command_show_version_results.items():
        print(json.dumps(devices[device], indent=2))
        links_query_1 = "cdp_links.*.local_port"
        links_query_2 = "cdp_links.*.remote_port"
        links_host = jmespath.search(links_query_2, devices[device])
        links_host_sub = [ re.sub('[,].+', '', host) for host in links_host ]
        links_platform = [ command_show_version_results[host]['output'][0]['hardware'] for host in links_host_sub ]
        print(json.dumps(links_platform, indent=2))
        if value['success']:
            dev_hostname = value['output'][0]['hostname']
            dev_os = value['output'][0]['version']
            dev_sn = value['output'][0]['serial']
            dev_platform = value['output'][0]['hardware']
            dev_cdp_links = jmespath.search(links_query_1, devices[device])
            dev_cdp_links_platform = links_platform
        else:
            dev_hostname = device
            dev_os = devices[device].get("cdp_detected_os", "No")
            dev_sn = "No"
            dev_platform = devices[device].get("cdp_detected_platform", "No")
            dev_cdp_links = jmespath.search(links_query_1, devices[device])
            dev_cdp_links_platform = jmespath.search(links_query_2, devices[device])
        device_table.append(
            [
                dev_hostname,
                dev_os,
                dev_sn,
                dev_platform,
                dev_cdp_links,
                dev_cdp_links_platform
            ]
        )
    output_filename = 'device_table.csv'
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(device_table)

    interface_table = [
        [
            "Hostname",
            "Vlan_id",
            "Vlan_name",
            "VRF",
            "SVI",
            "CIDR",
            "Prefix",
            "SEC_IP",
            "IP_Helper(s)",
            "Gateway"
        ]
    ]

    for device, value in command_show_ip_interface_results.items():
        print(device)
        # print(json.dumps(value, indent=2))
        dev_hostname = device
        if value['success']:
            for vlan in value['output']:
                if "Vlan" in vlan['interface']:
                    vlan_id = vlan['interface'].replace('Vlan','')
                    print(vlan_id)
                    select_vlan = get_items_with_key_value(command_show_vlan_brief_results[device]['output'], 'vlan_id', vlan_id)
                    if len(select_vlan) != 0:
                        vlan_name = select_vlan[0].get('vlan_name', "No")
                        print(vlan_name)
                    else:
                        vlan_name = "No"
                    if vlan['vrf'] == "":
                        vlan_vrf = "default"
                    else:
                        vlan_vrf = vlan['vrf']
                    if len(vlan['ip_address']) == 0:
                        vlan_svi = "No"
                        vlan_cidr = "No"
                        vlan_gw = "No"
                        vlan_prefix = "No"
                        vlan_secip = "No"
                    else:
                        vlan_svi = vlan['ip_address'][0]
                        vlan_cidr = str(IPNetwork(f"{vlan['ip_address'][0]}/{vlan['prefix_length'][0]}").cidr)
                        vlan_prefix = vlan['prefix_length'][0]
                        vlan_secip = "No"
                        vlan_gw = IPNetwork(f"{vlan['ip_address'][0]}/{vlan['prefix_length'][0]}").cidr[-2]
                    if len(vlan['ip_address']) == 2:
                        vlan_secip = vlan['ip_address'][1]
                    if len(vlan['ip_helper']) == 0:
                        vlan_iphelper = "No"
                    else:
                        vlan_iphelper = vlan['ip_helper']
                    
                    interface_table.append(
                        [
                            dev_hostname,
                            vlan_id,
                            vlan_name,
                            vlan_vrf,
                            vlan_svi,
                            vlan_cidr,
                            vlan_prefix,
                            vlan_secip,
                            vlan_iphelper,
                            vlan_gw
                        ]
                    )

    for device, value in command_show_vlan_brief_results.items():
        print(device)
        # print(json.dumps(value, indent=2))
        dev_hostname = device
        ipint_query_1 = '[*].interface'
        ipint_list = jmespath.search(ipint_query_1, command_show_ip_interface_results[device]['output'])
        print(ipint_list)
        if value['success']:
            for vlan in value['output']:
                print(vlan['vlan_id'])
                if ipint_list != None and f"Vlan{vlan['vlan_id']}" in ipint_list:
                    print(f"{vlan['vlan_id']} already added in interface table")
                else:
                    vlan_id = vlan['vlan_id']
                    vlan_name = vlan['vlan_name']
                    vlan_vrf = "No"
                    vlan_svi = "No"
                    vlan_cidr = "No"
                    vlan_prefix = "No"
                    vlan_secip = "No"
                    vlan_iphelper = "No"
                    vlan_gw = "No"
                    interface_table.append(
                        [
                            dev_hostname,
                            vlan_id,
                            vlan_name,
                            vlan_vrf,
                            vlan_svi,
                            vlan_cidr,
                            vlan_prefix,
                            vlan_secip,
                            vlan_iphelper,
                            vlan_gw
                        ]
                    )
                    print(f"{vlan['vlan_id']} Added!")

    output_filename = 'interface_table.csv'
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(interface_table)

    

    cdp_table = [
        [
            "Hostname",
            "Ip_address",
            "OS",
            "Platform",
            "Capabilities",
            "CDP_links",
            "DNS_lookup_remarks"
        ]
    ]

    for device, value in devices.items():
        # print(device)
        # print(json.dumps(value['cdp_links'], indent=2))
        links_query_3 = "cdp_links.*.{local_port: local_port, remote_port: remote_port}"
        links_host_2 = jmespath.search(links_query_3, value)
        dev_hostname = value.get('HOSTNAME', "No")
        dev_ip = value.get('IP_ADDRESS', "No")
        dev_os = value.get('cdp_detected_os', "No")
        dev_platform = value.get('cdp_detected_platform', "No")
        dev_capabilities = value.get('cdp_detected_capabilities', "No")
        dev_links = "\n".join(str(item) for item in links_host_2) 
        dns_remarks = value.get('DNS_LOOKUP', "N/A")
        cdp_table.append(
            [
                dev_hostname,
                dev_ip,
                dev_os,
                dev_platform,
                dev_capabilities,
                dev_links,
                dns_remarks
            ]
        )
    output_filename = 'cdp_table.csv'
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(cdp_table)

'''
Hostname
Vlan_id
Vlan_name
VRF
SVI
CIDR
Prefix
SEC_IP
IP_Helper(s)
Gateway
'''
if __name__ == "__main__":
    main()
