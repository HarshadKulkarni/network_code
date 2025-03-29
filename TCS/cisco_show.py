from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor
import csv, os, time
import difflib
import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument('--inventory_file', '-i', type=str, required=True)
parser.add_argument('--commands_file', '-c', type=str, required=True)
parser.add_argument('--operation', '-o', choices=['precheck', 'postcheck'], type=str, required=True)
args = parser.parse_args()

inventory_file = args.inventory_file
commands_file = args.commands_file
operation = args.operation

def compare_outputs(source_file, target_file, host_name):
    
    with open(source_file,'r') as precheck:
        precheck_out = precheck.readlines()

    with open(target_file,'r') as postcheck:
        postcheck_out = postcheck.readlines()

    changes = difflib.HtmlDiff().make_file(precheck_out, postcheck_out, fromdesc='Precheck Values', todesc=' Postcheck Values', charset='utf-8')

    with open(f"./output/{host_name}/{host_name}_changes.html", 'w') as output:
        output.writelines(changes)

def create_summary_html():
    index_html = '''
    <!DOCTYPE html>
    <html>
		<head>
			<style>
                body {font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; justify-content: flex-start;}
                ol {background-color: #000000; color: #FFF; margin: 0; padding: 1;}
                p {padding: 10px; color: #EB0A1E; font-weight: bold; font-size: 20px;}
                li {padding: 3px; margin: 0;}
                li a {text-decoration: none; color: #FFF; padding: 15px 15px; }
                li a:hover {color: #EB0A1E; }
                #iframe { width: 100%; height: 100vh; border: none; }
            </style>
		</head>
    <body>
    <ol>
	<p>TMNA Switches</p>
    '''
    
    folder_path = Path('./output')
    html_files = folder_path.rglob('*.html')
    for html_file in html_files:
        index_html += f'<li><a href="{html_file.name.split("_changes")[0]}\{html_file.name}" target="iframe">{html_file.name.split("_changes")[0]}</a></li>'
    
    index_html +=  ' </ol><iframe name="iframe" id="iframe"></iframe></body></html>'

    with open(f"./output/Index.html", "w") as outfile:
        outfile.write(index_html)

def run_cisco_show_commands(host_name, host_ip, username, password, cisco_commands, operation):

    if not os.path.exists(f"./output/{host_name}"):
        os.makedirs(f"./output/{host_name}")

    cisco = {
        "device_type": "cisco_ios",
        "host": host_ip,
        "username": username,
        "password": password,
        "session_log": f"./output/{host_name}/{host_name}_log.txt",
    }

    try:
        # Create the Netmiko SSH connection
        ssh_conn = ConnectHandler(**cisco)
        print(f"Running commands on  : {host_name}")
        
        with open(f"./output/{host_name}/{host_name}_{operation}.txt", "a") as outfile:
            outfile.write(f"{host_name}\n")

            for command in cisco_commands:
                outfile.write(f"\n{'#'*100}\nExecuting command on {host_name} : {command} \n{'#'*100}\n")
                output = ssh_conn.send_command(command, read_timeout=300)
                outfile.write(output)

        if operation == "postcheck":
            try:
                source_precheck_file = f"./output/{host_name}/{host_name}_precheck.txt"
                target_postcheck_file = f"./output/{host_name}/{host_name}_postcheck.txt"
                compare_outputs(source_precheck_file, target_postcheck_file, host_name)
            except:
                print(f"File comparison failed for {host_name}.Source or Target file might be missing")


    except Exception as e:
        print(e)


switches = []
with open(inventory_file, 'r') as inventory:
    csvreader = csv.reader(inventory)
    header = next(csvreader)
    for row in csvreader:
        switches.append(row)

with open('cisco_show_commands.txt','r') as commands_file:
    cisco_commands = commands_file.read().splitlines()

with ThreadPoolExecutor(10) as executor:
    prechecks_threads = [executor.submit(run_cisco_show_commands, switch[0].strip(), switch[1].strip(), switch[2].strip(), switch[3].strip(), cisco_commands ,operation) for switch in switches]

if operation == "postcheck":
    print("Creating output summary inside /output/Index.html")
    create_summary_html()
