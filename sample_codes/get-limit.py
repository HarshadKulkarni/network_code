#!/usr/bin/python3

# This script takes as an input the branch name and then set's the environment variables with the limits
#
# Example: input: "NA"; output: [ "NA[1:679]", "NA[680:1359]", "NA[1360:2039]", "NA[2040:2719]",
#                       "NA[2720:3399]", "NA[3400:4079]", "NA[4080:4759]", "NA[4759:5434]"]
# It achieves that by grepping the catalyst.yml file and counting the number of matches

import sys
import subprocess

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print('all[1:10]')
        exit(0)
    branch = sys.argv[1]
    workspace = sys.argv[2]
    inventory_file = sys.argv[3]
    if   branch in "NA":
        region="NA"
        domain_match = "gw.na.xyz.com"
    elif branch in "LATAM":
        region="LATAM"
        domain_match = "gw.la.xyz.com"
    elif branch in "EMEA":
        region="EMEA"
        domain_match = "gw.eu.xyz.com"
    elif branch in "APAC":
        region="APAC"
        domain_match = "gw.sg.xyz.com"
    elif branch in "lab":
        region="lab"
        domain_match = "gw.lab.xyz.com"
    elif branch in "dev":
        region="dev"
        domain_match = "gw.dev.xyz.com"
    else:
        region="all"
        domain_match = "xyz.com"
    ## RUNS grep command
    cmd = 'grep %s %s/anshostfiles/%s | wc -l' %(domain_match, workspace, inventory_file)
    output = subprocess.check_output(cmd, shell=True)
    try:
        count = int(output)
    except:
        print('all[1:20]')
        exit(0)

    limits=[]
    jobTotal=4
    for i in range(0,jobTotal):
        lower_bound=str((i)*int(count/jobTotal))
        upper_bound=str((i+1)*int(count/jobTotal)-1)
        if (i+1)==jobTotal:
            upper_bound=""
        limits+=["%s[%s:%s]" % (region, lower_bound, upper_bound)]
    print(",".join(limits))