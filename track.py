import subprocess
import mysql.connector
import json
import time

# Define queries that we will use repeatedly over here.

def insert_new_link_query(table_name):
    return  (
            "INSERT INTO " + table_name + " (link_name, active_time, inactive_time) "
            "VALUES (%s, %s, %s);"
            )

def update_old_link_query(table_name):
    return (
            "UPDATE " + table_name + " "
            "SET active_time = %s, inactive_time = %s "
            "WHERE link_name = %s;"
            )

def get_link_query(table_name):
    return (
            "SELECT link_name, active_time, inactive_time "
            "FROM " + table_name + " "
            "WHERE link_name = %s;"
            )

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

            config_json = load_config()
            cnct = mysql.connector.connect(host="127.0.0.1:33060", user=config_json['user'], database=config_json['database'], password=config_json['password'])
            get_link_buffer = cnct.cursor(buffered=True)
            update_link_buffer = cnct.cursor(buffered=True)
            insert_link_buffer = cnct.cursor(buffered=True)

            for link in parsed_links:
                get_link_buffer.execute(get_link_query(config_json['table']), (link,))
                if get_link_buffer.rowcount > 0:
                    assert get_link_buffer.rowcount == 1
                    new_active_time = 0
                    new_inactive_time = 0
                    for (link_name, active_time, inactive_time) in get_link_buffer:
                        new_active_time = active_time if parsed_active_link != link else active_time + 1
                        new_inactive_time = inactive_time if parsed_active_link == link else inactive_time + 1

                    update_link_buffer.execute(update_old_link_query(config_json['table']), (new_active_time, new_inactive_time, link))
                else: # Persist new link to the database.
                    active_time = 0 if parsed_active_link != link else 1
                    inactive_time = 1 if parsed_active_link != link else 0

                    insert_link_buffer.execute(insert_new_link_query(config_json['table']), (link, active_time, inactive_time))

                cnct.commit()

        print('a')
        time.sleep(1)
