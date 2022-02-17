#! /usr/bin/python3

import configparser
from imaplib import IMAP4_SSL
import email
import os


# get parameters from the config file
configfile = configparser.ConfigParser()
configfile.read(os.path.join(os.getcwd(), 'config.cfg'))

# assing parameters to strings from configfile
imap_host = configfile['connection']['host']
imap_user = configfile['connection']['user']
imap_pass = configfile['connection']['password']

folder = configfile['email']['folder']
subj = configfile['email']['subject']
purge = configfile['email']['purge']

outfile = configfile['output']['outfile']

def read_dloads(imap_host, imap_user, imap_pass, folder, subj, purge: str) -> list:

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


    if purge == 'yes':
        conn.store(m, "+FLAGS", "\\Deleted")
            
    if conn.state == 'SELECTED':
        conn.expunge()
        conn.close()
    conn.logout()

    return _results

def dloads_to_file(dload_list: list, outfile: str) -> None:

    if len(dload_list) == 0:
        print('Nothing to add')
        return None

    else:
        # check what is already on the list 
        try:
            with open(outfile, 'r', encoding='utf-8') as r:
                on_the_list = [n.strip('\n') for n in r.readlines()]
        except FileNotFoundError:
            with open(outfile, 'w', encoding='utf-8') as r:
                on_the_list = []
            
        # add new entries to the list
        with open(outfile, 'a', encoding='utf-8') as f:        
            for e in dload_list:
                e_items = e['body'].strip('\n').split('\n')
                for e_item in e_items:
                    _ = e_item.strip('\r').lower()
                    if _ not in on_the_list:
                        on_the_list.append(_)
                        f.write('{}\n'.format(_))
        
        return None
        

def main():
    # read in download reminders from email
    dload_list = read_dloads(imap_host, imap_user, imap_pass, folder, subj, purge)
    
    # write results to the outputfile
    dloads_to_file(dload_list, outfile)


if __name__ == '__main__':
    main()
