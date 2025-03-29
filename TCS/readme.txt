Update the Inventory.csv with the Switch details and credentials

precheck command:
python .\cisco_show.py -i .\Inventroy.csv -c .\cisco_show_commands.txt -o "precheck"

#Make sure precheck is completed before starting postcheck
postcheck command:
python .\cisco_show.py -i .\Inventroy.csv -c .\cisco_show_commands.txt -o "postcheck"