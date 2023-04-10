# Command and Control Application
## Summary of the application structure:
### Server side:
1. The server always listens to clients that want to connect and accepts them.
2. At the same time, the server manages a refresh CLI that:
    - Displays the status of the connected clients
    - Updated every "interval" time
    - Displayed when the operator does not perform any operation - so that it does not overrun the menu and distrub
     - (The desire was to open another separate terminal from the terminal on which the operations are done, but it was not done because of time...)
3. At the same time, the server performs operations on the clients that are already connected
    - The menu operations are:
      -  send a command
      -  kill clients
      -  display results of operation 
      -  exit the server -> close it
    - Each action can be sent to a selected client or broadcast to all clients
    - When sending a command:
      - The server creates a command message - which is built from:
      - The payload of the command -> which it creates from the payloads that exist in "commands_dir"
      - arguments -> are taken as input from the server operator
      - command_id and command_type of the command
> Note The port_scan and screenshot payloads do not work - I left them to show thinking...
### Client side:
1. The client takes data from the predefined configuration file - "coinfig_client_file.py"
2. Trying to connect to the server
3. Always sends "keep alive" messages to the server
4. At the same time always waiting for a message from the server
5. When a message arrives:
    - Decodes and breaks down the message
    - If it is an "exit" message, close the connection
    - If this is a command message:
      - Creates a file with the payload of the command
      - Executes the command - runs it
      - Deletes the file after runinng it  and receiving the output
      - Sends back to the server a result message composed of:
        - command_result -> the output from running the payload
        - command_status -> if successful returns Finished otherwise Error
        - command_id and command_type of the executed command

## The application include the following files:
### Server files:
> 1. server.py
> 2. command_dir dirctory
>    - dowmload_from_url.py
>    - file_upload.py
>    - port_scan.py
>    - screenshot.py
>    - shell_exec.py
### Client files:
> 1. client.py
> 2. config_client_file.py
### Packages 
> requirements.txt

## To test this C2 Appliacation:
 Clone the repository:
```
https://github.com/hadasa324/Development_Exercise.git
```
Install the required python dependencies on both attacker and victim machines:
```
pip install -r requirements.txt
```
First run the server:
```
python server.py
```
 Then run num of clients:
```
python client.py
```
