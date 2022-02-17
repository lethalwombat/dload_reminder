#! /usr/bin/python3

import configparser
from imaplib import IMAP4_SSL
import email
import os
import re

# get parameters from the config file
configfile = configparser.ConfigParser()
configfile.read(os.path.join(os.getcwd(), 'dload_reminder', 'config.cfg'))

# assing parameters to strings from configfile
imap_host = configfile['connection']['host']
imap_user = configfile['connection']['user']
imap_pass = configfile['connection']['password']

folder = configfile['email']['folder']
from_addr = configfile['email']['from'].lower()
email_buffer = int(configfile['email']['buffer'])

# only purge if a specific email is set
if from_addr == 'all':
    purge = 'no'
else:
    purge = configfile['email']['purge']

# function to parse email using regex
def parse_email(input_str: str):
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    _ = re.findall(email_regex, input_str)
    if len(_) == 0:
        return ''
    else:
        return _[0]


def read_dloads(imap_host, imap_user, imap_pass, email_buffer, folder, from_addr, purge: str) -> list:

    _results = {}

    conn = IMAP4_SSL(imap_host)
    try:
        conn.login(imap_user, imap_pass)
    except IMAP4_SSL.error as e:
        print(e)
    if conn.state == 'AUTH':
        status, messages = conn.select(folder)
        n_messages = int(messages[0])
        print('Total number of emails: {}'.format(n_messages))
        print('Searching last {}'.format(email_buffer))

        for i in range(n_messages, n_messages-email_buffer, -1):
            _, data = conn.fetch(str(i), '(RFC822)')
            _, bytes_data = data[0]
            email_message = email.message_from_bytes(bytes_data)

            # if searching all emails
            parsed_email = parse_email(email_message['from']).lower()
            if from_addr == 'all':
                print('Found this: {}'.format(email_message['subject']))
                if parsed_email not in _results:
                    _results[parsed_email] = 0
                _results[parsed_email] += 1
            
            # if searching for a specific address
            else:
                if parsed_email == from_addr:
                    print('Found this: {}'.format(email_message['subject']))
                    if parsed_email not in _results:
                        _results[parsed_email] = 0
                    _results[parsed_email] += 1

            if purge == 'yes':
                conn.store(str(i), "+FLAGS", "\\Deleted")
            
    if conn.state == 'SELECTED':
        conn.expunge()
        conn.close()
    conn.logout()

    return _results
        

def main():
    print('Searching for emails from {} in {}:{}'.format(from_addr, folder, imap_user))

    # read in download reminders from email
    dload_list = read_dloads(imap_host, imap_user, imap_pass, email_buffer, folder, from_addr, purge)

    # output results into a .csv file
    with open('result.csv', 'w') as f:
        for k, v in dload_list.items():
            f.write('{},{}\n'.format(k, v))  

if __name__ == '__main__':
    main()  