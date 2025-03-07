import csv
import netmiko
from getpass import getpass
from sys import exit

# username = input('Enter username: ')
# password = getpass('Enter password: ')


# Define the function to read IPs from the CSV file
def read_ips(filename):
    with open(filename, newline='') as csvfile:
        ipreader = csv.reader(csvfile)
        return [row[0] for row in ipreader]
    
def read_ips(filename):
    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        ipreader = csv.reader(csvfile)
        return [row[0] for row in ipreader]

# host = '10.113.64.6'
    
# devices = {
#     'device_type': 'cisco_ios',
#     'host': host,
#     'username': username,
#     'password': password,
#           }
    
conn = netmiko.ConnectHandler(**devices)

command = 'show int Vlan1021 | i Hardware'
command2 = 'show int Vlan1021 | i Internet'

print(f'Processing for {host}')

output = conn.send_command(command, delay_factor=10)
output2 = conn.send_command(command2, delay_factor=10)

conn.disconnect()

with open('Results.txt', 'a') as file:
    file.write(output)
    file.write(output2)
        
input('Complete, press any key to close')

exit(0)
