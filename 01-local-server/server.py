# This is a server with a similar functionality of logging as https://2minlog.com.
#
# Tutorial: https://doc.2minlog.com/tutorials/local-server/
#
# You can run this script to set the server. You can log the values in the same format as described here:
# https://doc.2minlog.com/technical-docs/data-logging. It will create the data.csv file, which you can plot
# with the same code, as you do in 2minlog.
#
# Example of data logging:
# curl "http://localhost:8000?datasetSecret=SEC-d811574a-b61e-4844-b61b-e06da34c6ef7&temperature=451&humidity=80"
# curl -X POST --user "2minlog:SEC-d811574a-b61e-4844-b61b-e06da34c6ef7" http://localhost:8000/ -d "{\"temperature\":\"451\", \"humidity\":\"8017x1\"}"
# Both comments work in Windows command.com and Linux shell.

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import json
from datetime import datetime

PORT = 8000
HOSTNAME = 'localhost' # 'localhost' or e.g. '10.0.0.10'

CSVFILE = 'data.csv'
RAWDATAFILE = 'raw_data.log'


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

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        print(f'{query_params=}')
        par = {pp: values[0] for pp, values in query_params.items()}
        handle_data(par)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        post_data = post_data.decode('utf-8')
        post_data = json.loads(post_data)
        print(f'{post_data=}')
        handle_data(post_data)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


if __name__ == '__main__':
    httpd = HTTPServer((HOSTNAME, PORT), SimpleHTTPRequestHandler)
    print(f"Server started at http://{HOSTNAME}:{PORT}")
    httpd.serve_forever()
