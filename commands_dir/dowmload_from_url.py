
import urllib.request
import gdown

def execute_dowmload_from_url(url):
        string = "drive.google.com"
        
        try:
            if string in url:
                 output = "my_file.zip"  # specify the name of the output file
                 gdown.download(url, output, quiet=False)  # download the file
            else:
                urllib.request.urlretrieve(url, "dowloaded")
                
            return f"Downloaded {url}  successfully"
        except Exception as e:
            return f"Error downloading {url}: {str(e)}"