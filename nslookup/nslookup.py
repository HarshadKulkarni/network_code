import csv
import subprocess
import re

def run_nslookup(ip):
    try:
        result = subprocess.run(['nslookup', ip], capture_output=True, text=True, check=True)
        output_lines = result.stdout.splitlines()
        for line in output_lines:
            if 'Name:' in line:
                return line.split('Name:')[1].strip()
        for line in output_lines:
            match = re.search(r'name = ([\w.-]+)', line)
            if match:
                return match.group(1)
        return 'N/A'
    except subprocess.CalledProcessError as e:
        print(f"Error running nslookup for IP {ip}: {e}")
        return 'Error'

input_file = 'input_ips.csv'
output_file = 'output_ips_hostnames.csv'

try:
    with open(input_file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        ip_addresses = [row[0] for row in csvreader]
except FileNotFoundError:
    print(f"Input file {input_file} not found.")
    ip_addresses = []

if ip_addresses:
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['IP Address', 'Hostname'])

        for ip in ip_addresses:
            hostname = run_nslookup(ip)
            csvwriter.writerow([ip, hostname])

    print(f'Results saved to {output_file}')
else:
    print("No IP addresses to process.")
