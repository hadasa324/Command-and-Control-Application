import subprocess
import os
from termcolor import colored

def decode_bytes(data):
    encodings = ['utf-8', 'Windows-1255', 'cp1252']
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise UnicodeDecodeError(colored('Failed to decode data with any of the specified encodings' , "red"))



def execute_shell_command(args):
        cmd =args[0]
        if cmd[:2] == "cd" and len(cmd) > 2:
            try:
                # Use subprocess library to execute shell command
                output = os.chdir(cmd[3:])
                return decode_bytes(output)
            except Exception as e:
                 return colored("Error running command "+cmd+": " +str(e) , "red")
        else:
            try:
                # Use subprocess library to execute shell command
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                return decode_bytes(output)
            except Exception as e:
                return colored("Error running command "+cmd+": " +str(e) , "red")