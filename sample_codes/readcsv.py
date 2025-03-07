import csv
import netmiko

def run_show_command(device_ip, username, password, command):
    """Connects to the device and runs the specified show command."""

    try:
        with netmiko.ConnectHandler(
            device_type='cisco_ios',  # Adjust device type as needed
            ip=device_ip,
            username=username,
            password=password,
        ) as netdev:
            output = netdev.send_command(command)
            return output

    except Exception as e:
        return f"Error: {e}"

def main():
    """Reads device IPs from CSV, runs the command, and stores output in a new CSV."""

    csv_file = 'devices.csv'  # Replace with your CSV file
    output_file = 'output.csv'

    with open(csv_file, 'r') as f, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(f)
        writer = csv.writer(outfile)
        writer.writerow(['Device IP', 'Command Output'])

        for row in reader:
            device_ip = row['IP']  # Assuming the column name is 'IP'
            username = row['Username']
            password = row['Password']
            command = 'show int Vlan1021 | i Hardware'  # Replace with your desired command

            output = run_show_command(device_ip, username, password, command)

            writer.writerow([device_ip, output])

if __name__ == '__main__':
    main()