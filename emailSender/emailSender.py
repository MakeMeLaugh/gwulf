#!/usr/bin/env python
import smtplib
import sys
import getopt
import optparse
import os
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.encoders import encode_base64
from optparse import SUPPRESS_HELP
from ConfigParser import SafeConfigParser

# Something is messed up in the USAGE, but i'm too lazy to fix it
USAGE = "\r\n" \
        "-t / --to\t\trecipients in double quotes, comma-separated (""mail@example.com,example@mail.com,foo@bar.com"")\r\n" \
        "-c / --cc\t\tcopy recipients in double quotes, comma-separated (""mail@example.com,example@mail.com,foo@bar.com"")\r\n" \
        "-s / --subj\t\tmessage subject\r\n" \
        "-b / --body\t\tmessage body (supports HTML)\r\n" \
        "-a / --attachment\tfile to attach (repeat -a to attach multiple files)\r\n" \
        "-d / --debug\t\tturn debug on\r\n" \
        "--config\t\t\tspecify config section\r\n\n" \
        "Example call: \r\n\n" \
        """python email_send.py """ \
        """-t "Recepient 1<recepient_1@email.ru>,Recepient 2<recepient_2@email.ru>,Recepient 3<recepient_3@email.com """ \
        """-c "Copy Recepient 1<copy_recepient_1@email.com>,Copy Recepient 2<copy_recepient_2@email.ru> """ \
        """-s "this is mail subject" -b "this is mail body" -a "/home/user/files/data/mail.log -d --config MailConfig"""

# add options
parser = optparse.OptionParser(prog='email sender', usage=USAGE)
parser.add_option('-t', '--to', help=SUPPRESS_HELP)
parser.add_option('-c', '--cc', help=SUPPRESS_HELP)
parser.add_option('-s', '--subj', help=SUPPRESS_HELP)
parser.add_option('-b', '--body', help=SUPPRESS_HELP)
parser.add_option('-a', '--attachment', action='append', help=SUPPRESS_HELP)
parser.add_option('-d', '--debug', action="store_true", help=SUPPRESS_HELP)
parser.add_option('--config', help=SUPPRESS_HELP)

# read config file
config = SafeConfigParser()
CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + '/email.ini'
config.read(CONFIG_PATH)

arguments = parser.parse_args()

try:
    opts, args = getopt.getopt(sys.argv[1:], "t:c:s:b:a:dh",
                               ["to=", "cc=", "subj=", "body=", "attachment=", "debug", "config="])
except getopt.GetoptError as err:
    print str(err)
    parser.print_help()
    exit(2)

# Defining the constants
MAIL_TO = []
MAIL_COPY = []
MAIL_SUBJECT = ""
MAIL_BODY = ""
MAIL_ATTACHMENT = []
DEBUG = False  # use -d/--debug to turn the debug on.
CONFIG = 'MailServer'  # Define the default config you will use from email.ini

# parse command line arguments
for o, a in opts:
    if o in ("-t", "--to"):
        MAIL_TO = a.split(',')
    elif o in ("-c", "--cc"):
        MAIL_COPY = a.split(',')
    elif o in ("-s", "--subj"):
        MAIL_SUBJECT = a
    elif o in ("-b", "--body"):    # You can provide files as message body (e.g. html-based)
        if os.path.isfile(a):
            MAIL_BODY = open(a).read()
        else:
            MAIL_BODY = a
    elif o in ("-a", "--attachment"):
        MAIL_ATTACHMENT.append(a)
    elif o in ("-d", "--debug"):
        DEBUG = True
    elif o == "--config":
        CONFIG = a
    else:
        print parser.print_help()
        exit(2)

# Redefine constants with the values from config file
USER = config.get(CONFIG, 'login')
PASSWD = config.get(CONFIG, 'password')
MAIL_SERVER = config.get(CONFIG, 'host')
MAIL_PORT = config.get(CONFIG, 'port')
FILE_NAMES = []
MAIL_FROM = config.get(CONFIG, 'from')

for f in MAIL_ATTACHMENT:
    _name = f.split('/')[len(f.split('/')) - 1]
    FILE_NAMES.append(_name)

# Starting to build the message
msg = MIMEMultipart()
msg['Subject'] = MAIL_SUBJECT
msg['From'] = MAIL_FROM
msg['To'] = ', '.join(MAIL_TO)
msg['Cc'] = ', '.join(MAIL_COPY)

RECIPIENTS = MAIL_TO + MAIL_COPY

if FILE_NAMES:
    for _file, _name in zip(MAIL_ATTACHMENT, FILE_NAMES):
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(_file, "rb").read())
        encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=_name)
        msg.attach(part)

part2 = MIMEBase('text', "html")
part2.set_payload(MAIL_BODY)
encode_base64(part2)

msg.attach(part2)

# Start the SMTP session and send the message
server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
server.set_debuglevel(DEBUG)
server.starttls()
server.login(USER, PASSWD)
server.sendmail(MAIL_FROM, RECIPIENTS, msg.as_string())
server.quit()
