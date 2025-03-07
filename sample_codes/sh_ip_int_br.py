import paramiko
import getpass
import time
 
def get_credentials():
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    hostname = input("Enter the hostname or IP address: ")
    return username, password, hostname
 
def ssh_connect(username, password, hostname):
    try:
        # Create an SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
       
        # Connect to the device
        ssh.connect(hostname, username=username, password=password, look_for_keys=False, allow_agent=False)
       
        # Create a shell session
        shell = ssh.invoke_shell()
       
        # Wait for the device to be ready (skip banners/messages)
        time.sleep(2)
        while not shell.recv_ready():
            time.sleep(2)
       
        # Clear any initial output (banners/messages)
        shell.recv(1024)
       
        # Send the command
        shell.send("show ip interface brief\n")
       
        # Wait for the command to execute and receive the output
        output = ""
        while not shell.recv_ready():
            time.sleep(2)
        while shell.recv_ready():
            output += shell.recv(1024).decode('utf-8')
       
        # Close the connection
        ssh.close()
        
        print (output)
        return output
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
 
def parse_output(output):
    lines = output.splitlines()
    interfaces = []
   
    # Skip the header lines and parse the interfaces
    for line in lines:
        if "Interface" in line and "IP-Address" in line:
            continue  # Skip the header line
        if line.strip() == "":
            continue  # Skip empty lines
        parts = line.split()
        if len(parts) >= 2:
            interface = parts[0]
            ip_address = parts[1]
            status = parts[2] if len(parts) >= 3 else "N/A"
            protocol = parts[3] if len(parts) >= 4 else "N/A"
            interfaces.append((interface, ip_address, status, protocol))
   
    print (interfaces)
    return interfaces
 
def save_to_file(filename, interfaces):
    with open(filename, 'w') as file:
        # Write the table header
        file.write(f"{'Interface':<20} {'IP Address':<15} {'Status':<10} {'Protocol':<10}\n")
        file.write("-" * 60 + "\n")
       
        # Write the interface details
        for interface, ip_address, status, protocol in interfaces:
            file.write(f"{interface:<20} {ip_address:<15} {status:<10} {protocol:<10}\n")
 
def main():
    username, password, hostname = get_credentials()
    output = ssh_connect(username, password, hostname)
   
    if output:
        # Parse the output
        interfaces = parse_output(output)
       
        # Save the output to a file
        filename = "interface_table.txt"
        save_to_file(filename, interfaces)
        print(f"Output saved to {filename}")
       
        # Print the output to the console
        print("\nInterface Table:")
        print(f"{'Interface':<20} {'IP Address':<15} {'Status':<10} {'Protocol':<10}")
        print("-" * 60)
        for interface, ip_address, status, protocol in interfaces:
            print(f"{interface:<20} {ip_address:<15} {status:<10} {protocol:<10}")
    else:
        print("No output received from the device.")
 
if __name__ == "__main__":
    main()