import csv
from netmiko import ConnectHandler

def read_ips_from_csv(input_csv):
    ips = []
    with open(input_csv, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ips.append(row['IP'])
    return ips

def check_uplinks(device):
    # Establish SSH connection to the switch
    connection = ConnectHandler(**device)
    
    # Get the hostname
    hostname_output = connection.send_command('show run | i hostname')
    hostname = hostname_output.split()[-1]
    
    # Determine uplink ports based on hostname
    if 'EDG' in hostname:
        uplinks = ['HundredGigE1/1/1', 'HundredGigE2/1/1']
    elif 'EXT' in hostname:
        uplinks