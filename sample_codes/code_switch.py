import csv
import paramiko
import re
import logging
import time

# Define the function to read IPs from the CSV file
def read_ips(filename):
    with open(filename, newline='') as csvfile:
        ipreader = csv.reader(csvfile)
        return [row[0] for row in ipreader]
    
def read_ips(filename):
    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        ipreader = csv.reader(csvfile)
        return [row[0] for row in ipreader]

# Define the function to execute show command and get output
def get_show_output(ip, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password)
    # transport = ssh.get_transport()
    # session = transport.open_session()
    # session.set_combine_stderr(True)
    # session.get_pty()
    time.sleep(10)   # wait 10 seconds for the session to be ready
    commands = ["show int Vlan1021 | i Hardware", "show int Vlan1021 | i Internet"]
    output = []
    for cmd in commands:
        time.sleep(5)  # Wait for 2 seconds before running the next command
        stdin, stdout, stderr = ssh.exec_command(cmd)
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(9999).decode())
        output_1 = stdout.read().decode()
        output.append(output_1)
        print(output)
        # output_2 = stdout.read().decode()
    ssh.close()
        # output_1 = output_2.split('\n')
        # output = output_1[-2]
    return output

# Define the function to store output in CSV file
def store_output(filename, data):
    with open(filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["IP", "Output"])
        for row in data:
            writer.writerow(row)

# Main function to tie it all together
def main():
    ips = read_ips('ips.csv')
    username = input("Enter username: ")
    password = input("Enter password: ")
    results = []

    for ip in ips:
        try:
            output = get_show_output(ip, username, password)
            results.append([ip, output])
        except Exception as e:
            print(f"Failed to connect to {ip}: {e}")

    store_output('output.csv', results)

if __name__ == "__main__":
    main()
