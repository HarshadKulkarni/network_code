import paramiko
import csv

def run_show_command(ip, username, password, command):
    """Runs a show command on a Cisco switch and returns the output."""

    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)

        with ssh.invoke_shell() as channel:
            channel.send(command + "\n")
            output = ""
            while True:
                if channel.recv_ready():
                    output += channel.recv(1024).decode("utf-8")
                else:
                    break
    return output

def write_to_csv(data, filename):
    """Writes data to a CSV file."""

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)

if __name__ == "__main__":
    ip = "your_switch_ip"
    username = "your_username"
    password = "your_password"
    command = "show version"
    filename = "output.csv"

    output = run_show_command(ip, username, password, command)
    # Process output into rows for CSV
    rows = output.splitlines()
    write_to_csv(rows, filename)