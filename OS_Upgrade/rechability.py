import subprocess
import concurrent.futures
import re
import time
from colorama import init, Fore, Style
import threading
from tabulate import tabulate


# Initialize colorama
init(autoreset=True)


# Create a lock object for synchronized printing
print_lock = threading.Lock()


def ping_host(ip, results):
    """Ping a host and calculate packet loss percentage."""
    try:
        # Execute the ping command
        #result = subprocess.run(['ping', '-c', '3', ip], capture_output=True, text=True, check=True) ## for MAC
        result = subprocess.run(['ping ', '-n', '3', ip], capture_output=True, text=True, check=True) ## for windos
        
        # Extract the packet loss percentage using regex
        match = re.search(r'(\d+\.?\d*)% loss', result.stdout)
        if match:
            loss_percentage = float(match.group(1))
        else:
            loss_percentage = 100.0  # Assume 100% loss if parsing fails
        
        # Determine the color based on loss percentage
        if loss_percentage == 100.0:
            color = Fore.RED
        elif loss_percentage == 0.0:
            color = Fore.GREEN
        else:
            color = Fore.YELLOW


        # Append the result with color formatting
        results.append([ip, f"{color}{loss_percentage}%{Style.RESET_ALL}"])
        
    except subprocess.CalledProcessError:
        results.append([ip, f"{Fore.RED}100% (host unreachable){Style.RESET_ALL}"])
    except Exception as e:
        results.append([ip, f"Error: {e}"])


def main():
    """Read IP addresses from a file and ping them concurrently."""
    try:
        # Read IP addresses from file
        with open('ips.txt', 'r') as file:
            ip_list = [line.strip() for line in file if line.strip()]
        
        while True:
            # List to store ping results
            results = []


            # Use ThreadPoolExecutor to ping IPs concurrently
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(lambda ip: ping_host(ip, results), ip_list)
            
            # Use the lock to ensure thread-safe printing of the table
            with print_lock:
                print(tabulate(results, headers=['IP Address', 'Packet Loss'], tablefmt='pretty'))
            
            # Wait for a specified time before the next round of pings
            time.sleep(10)  # Adjust the sleep duration as needed
            
    except FileNotFoundError:
        print("The file ips.txt was not found.")
    except KeyboardInterrupt:
        print("\nPing process interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
