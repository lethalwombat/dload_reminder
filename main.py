import configparser

from imaplib import IMAP4_SSL
import email
from email.header import decode_header
from select import select

import os


# get parameters from the config file
configfile = configparser.ConfigParser()
configfile.read('config.cfg')

# assing parameters to strings from configfile
print(configfile.sections())


# temporary parameters
# imap_host = 'imap.outlook.com'
# imap_user = 'korean_6_golf_golf@outlook.com'
# imap_pass = 'nV9,sRdhE[VPV,uKc'
# folder = 'inbox'
# subj = 'dload'
# purge = 0

def read_dloads(imap_host, imap_user, imap_pass, folder, subj: str, purge: int) -> list:

    _results = []

    conn = IMAP4_SSL(imap_host)
    try:
        conn.login(imap_user, imap_pass)
    except IMAP4_SSL.error as e:
        print(e)
    if conn.state == 'AUTH':
        status, messages = conn.select(folder)
        _, selected_messages = conn.search(None, 'ALL')

        for m in selected_messages[0].split():
            _, data = conn.fetch(m, '(RFC822)')
            _, bytes_data = data[0]

            email_message = email.message_from_bytes(bytes_data)
            _one_result = {'id' : int(m)}

            if email_message['subject'].lower().startswith(subj.lower()):

                _one_result['subject'] = email_message['subject']

                for part in email_message.walk():
                    if part.get_content_type() == 'text/plain':
                        _one_result['body'] = part.get_payload(decode=True).decode()

                _results.append(_one_result)


    if purge == 1:
        conn.store(m, "+FLAGS", "\\Deleted")
            
    if conn.state == 'SELECTED':
        conn.expunge()
        conn.close()
    conn.logout()

    print(_results)

    return _results

def main():
    # dload_list = read_dloads()
    print('main function')

if __name__ == '__main__':
    main()