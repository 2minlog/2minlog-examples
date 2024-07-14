# This is a server with a logging functionality similar to https://2minlog.com.
#
# Tutorial: https://doc.2minlog.com/tutorials/local-server/
#
# You can run this script to set the server. You can log the values in the same format as described here:
# https://doc.2minlog.com/technical-docs/data-logging. It will create the data.csv file, which you can plot
# with the same code as you do in 2minlog.
#
# To start over, delete raw_data.log and data.csv files
#
# Logging:
# - path /log, e.g. http://localhost:8000/log
# - Creates internal data file RAWDATAFILE and cvs file CSVFILE
# - It ignores datasetSecret parameter
# - If TWO_MINLOG_SCRIPT if non-empty, it runs the script and creates the graph defined in the script. It does not
#   pass any parameters - you need to set the correct intput csv and output jpg file names in the script. For a start,
#   you can upload https://raw.githubusercontent.com/2minlog/2minlog-examples/main/00-default_code/00_hello_world.py
#   script.
#
# Display image:
# - path /img, e.g. http://localhost:8000/img
# - Ignores all the parameters, returns the FILE_TO_SERVE
#
#
# Example of data logging:
# curl "http://localhost:8000/log?datasetSecret=SEC-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx&temperature=451&humidity=80"
# or via post HTTP command:
# Power Shell:
# curl.exe -X POST --user "2minlog:SEC-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" http://localhost:8000/log -d '{\"temperature\":\"451\", \"humidity\":\"80\"}'
# Windows CMD:
# curl -X POST --user "2minlog:SEC-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" http://localhost:8000/log -d "{\"temperature\":\"451\", \"humidity\":\"80\"}"
# Linux bash:
# curl -X POST --user "2minlog:SEC-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" http://localhost:8000/log -d "{\"temperature\":\"451\", \"humidity\":\"80\"}"
#


from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import json
from datetime import datetime
import subprocess

PORT = 8000
HOSTNAME = 'localhost' # 'localhost' or e.g. '10.0.0.10'

CSVFILE = 'example_dataset.csv'
RAWDATAFILE = 'raw_example_dataset.log'
TWO_MINLOG_SCRIPT = '00_hello_world.py' # e.g., '' or '00_hello_world.py'
FILE_TO_SERVE = 'output.jpg'

def to_csv(data):
    lines = data.strip().split('\n')
    records = []

    for line in lines:
        try:
            record = json.loads(line.strip())
            records.append(record)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e.msg} in line: {line}")
            pass

    header = sorted(set().union(*(d.keys() for d in records)))
    csv_data = [header]
    for row in records:
        csv_data.append([row.get(key, '') for key in header])

    csv_string = ""
    for row in csv_data:
        csv_string += ", ".join(row) + "\n"

    return csv_string


def handle_data(content):
    content.pop('datasetSecret', None)
    print(f'{content=}')
    timestamp = datetime.now()
    timestamp = timestamp.isoformat()
    content["timestamp"] = timestamp
    with open(RAWDATAFILE, "a") as f:
        f.write(json.dumps(content) + '\n')

    with open(RAWDATAFILE, "r") as f:
        data = f.read()
        csv = to_csv(data)
        with open(CSVFILE, "w") as ff:
            ff.write(csv)
            print('Updated', CSVFILE)

def generate_image():
    if TWO_MINLOG_SCRIPT == '':
        return

    try:
        result = subprocess.run(['python', TWO_MINLOG_SCRIPT], capture_output=True, text=True, check=True)
        print("Script output:")
        print(30*"*")
        print(result.stdout)
        print(30*"*")
        print("Successfully completed script.")
    except subprocess.CalledProcessError as e:
        print("An error occurred while trying to run the script:", e)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        print(f'{query_params=}')
        par = {pp: values[0] for pp, values in query_params.items()}

        if parsed_path.path == "/log":
            handle_data(par)
            generate_image()

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        elif parsed_path.path == "/img":
            try:
                # Open the image file
                with open(FILE_TO_SERVE, 'rb') as file:
                    image_data = file.read()

                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.end_headers()

                # Send the image data
                self.wfile.write(image_data)

            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Image not found")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Path not found")
        return

    def do_POST(self):

        try:
            parsed_path = urllib.parse.urlparse(self.path)
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = post_data.decode('utf-8')
            post_data = json.loads(post_data)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e.msg}, {post_data=}")
            post_data = json.loads('{}')
            pass

        if parsed_path.path == "/log":
            print(f'{post_data=}')
            handle_data(post_data)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Path not found")
        return


if __name__ == '__main__':
    httpd = HTTPServer((HOSTNAME, PORT), SimpleHTTPRequestHandler)
    print(f"Server started at http://{HOSTNAME}:{PORT}")
    httpd.serve_forever()
