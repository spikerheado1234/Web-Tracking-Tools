import subprocess
import json
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Define queries that we will use repeatedly over here.

def insert_link_query(write_api, website, bucket_name, active_time, inactive_time):
    one = Point("measurement").tag("website", website).field("active_time", active_time).field("inactive_time", inactive_time)
    write_api.write(bucket=bucket_name, record=[one])

def load_config():
    try:
        with open('config.json', 'r') as f:
            config_json = json.load(f)
        return config_json
    except:
        print('config file does not exist')

def parse_url(url):
    # Can be either http or https, depending on ssl certification.
    if len(url) > 12 and url[:12] == "https://www.":
        return url[12:].split(".")[0]
    elif len(url) > 11 and url[:11] == "http://www.":
        return url[11:].split(".")[0]
    elif url[:8] == "https://":
        return url[8:].split(".")[0]
    elif url[:7] == "http://":
        return url[7:].split(".")[0]

def main():
    # Main logic resides here.

    # Connect to local influx db container.
    config_json = load_config()
    client = InfluxDBClient(url='http://localhost:8086', token=config_json['token'], org=config_json['org'])

    try:
        while True:
            is_chrome_open = False
            list_procs = ""
            output = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
            list_procs = output.stdout.read()
            if 'Google Chrome'.encode('utf-8') in list_procs:
                is_chrome_open = True

            if is_chrome_open:
                all_tabs = subprocess.Popen(["chrome-cli", "list", "links"], stdout=subprocess.PIPE)
                active_tab = subprocess.Popen(["chrome-cli", "info"], stdout=subprocess.PIPE)
                all_tabs = all_tabs.stdout.read()
                active_tab = active_tab.stdout.read()
                all_tabs = all_tabs.split()
                active_tab = active_tab.decode('utf-8').split('\n')[2]

                parsed_links = set()
                for link in all_tabs:
                    string_form = link.decode('utf-8')
                    if string_form[0] != '[':
                        parsed_url = parse_url(string_form)
                        parsed_links.add(parsed_url)

                parsed_active_link = parse_url(active_tab[5:])

                write_api = client.write_api(write_options=SYNCHRONOUS)
                query_api = client.query_api()

                for link in parsed_links:
                    active_time = 0 if parsed_active_link != link else 1
                    inactive_time = 1 if parsed_active_link != link else 0
                    insert_link_query(write_api, link, config_json['bucket_name'], active_time, inactive_time)

            time.sleep(1)

    except:
        client.close()
