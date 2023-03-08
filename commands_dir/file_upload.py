from termcolor import colored
import base64

def execute_file_upload(args):
    file_to_upload = base64.b64decode(args[0].encode('utf-8'))
    file_name = args[1]
    try:
        with open(file_name, 'wb') as f:
            f.write(file_to_upload)
        return colored(f"File uploaded successfully" , "green")
    except Exception as e:
                return colored(f"Error running command upload: {str(e)}" , "red")

