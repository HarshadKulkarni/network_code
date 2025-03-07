import csv
from netmiko import ConnectHandler

def capture_cdp_neighbors(ip, username, password):
    device = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': username,
        'password': password,
    }

    connection = ConnectHandler(**device)
    output = connection.send_command("show cdp neighbors")
    connection.disconnect()

    return output

def parse_cdp_output(output):
    neighbors = []
    lines = output.splitlines()[5:]  # Skip the header lines

    for line in lines:
        parts = line.split()
        if len(parts) < 8:
            continue
        local_interface = parts[1] + parts[2]
        neighbor_device = parts[0]
        neighbor_interface = parts[-2] + parts[-1]
        neighbors.append([local_interface, neighbor_device, neighbor_interface])

    return neighbors

def store_as_csv(neighbors, hostname):
    filename = f"{hostname}_neighbors.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Local Interface", "Neighbor Device", "Neighbor Interface"])
        writer.writerows(neighbors)
    print(f"Stored parsed output to {filename}")

def main():
    ip = 'your_switch_ip'
    username = 'your_username'
    password = 'your_password'
    hostname = 'your_switch_hostname'

    output = capture_cdp_neighbors(ip, username, password)
    neighbors = parse_cdp_output(output)
    store_as_csv(neighbors, hostname)

if __name__ == "__main__":
    main()
