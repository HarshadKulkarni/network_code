import paramiko
import getpass
import sys
 
 
# main
username= ''
password= ''
hostname= ''

#print 'Params=', param_1, param_2, param_3
 
# Create an SSH client
 
client = paramiko.SSHClient()
 
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
 
 
 
# Connect to the switch
 
client.connect(hostname, username=username, password=password )
 
 
 
# Send a command to the switch and print the output
 
command = "show version"
 
stdin, stdout, stderr = client.exec_command(command)
 
output = stdout.read().decode()
 
print(output)
 
 
 
# Close the SSH connection
 
client.close()