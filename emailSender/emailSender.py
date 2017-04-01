#!/usr/bin/env python22
# -*- coding: utf-8 -*-
"""
Simple command-line tool to send email messages.
Compatible with Python 2.7.12. Not tested on other versions.
bash_completion supported
Important note: bash_completion package is required for this to work (browse your OS repository.
1. Make a symbolic link to this file somewhere on your PATH
e.g.: ln -snivf /path/to/emailSender.py /usr/local/bin/emailSend
2. Make a symbolic link to emailsend_completion.sh file
e.g.: ln -snivf emailsend_completion.sh /etc/bash_completion.d/emailSend
Important note: Link in /etc/bash_completion.d/ should have same name as your executable
"""

from __future__ import print_function
from sys import argv
from os import unlink
from os.path import dirname, realpath, basename
from time import strftime, localtime
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ConfigParser import SafeConfigParser, NoOptionError
from smtplib import SMTP, SMTPConnectError, SMTPResponseException, SMTPException, SMTPServerDisconnected, SMTPDataError
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.encoders import encode_base64
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
# TODO::Change print calls to logging module


def parse_args():
    """Parses command line arguments"""

    _parser = ArgumentParser(
        prog=basename(realpath(argv[0])).replace('.py', ''),
        usage="%(prog)s [OPTIONS]...",
        add_help=True,
        formatter_class=ArgumentDefaultsHelpFormatter,
        epilog=u"'Screw\'em all! May the cow force be with you!'",
        description=u"Sends email messages from command line"
    )

    _parser.add_argument('-t', '--to', dest='to', action='append', help=u"Email receivers ('To:' field)")
    _parser.add_argument('-c', '--cc', dest='cc', action='append', default=[],
                         help=u"Email receivers ('Cc:' field)")
    _parser.add_argument('-s', '--subject', dest='subject',
                         help=u"Email subject ('Subject:' field)")
    _parser.add_argument('-b', '--body', dest='body', help=u"Email body (HTML is supported)")
    _parser.add_argument('-a', '--attachment', dest='attachment', action='append', help=u"Path to attachment file")
    _parser.add_argument('-z', '--zip', dest='zip', action='store_true', help=u"Zip attachment file(-s)")
    _parser.add_argument('-Z', '--zip-name', dest='zip_name', default='attachments.zip',
                         help=u"Name of zip-archive")
    _parser.add_argument('--config', dest='config', default='MailServer', help=u"Section name in config file")
    _parser.add_argument('--list-config', dest='list_config', action='store_true',
                         help=u"List config sections and exit")
    _parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                         help=u"Enable SMTP debug output")

    opts = _parser.parse_args()

    return_opts = {
        'to': opts.to, 'cc': opts.cc, 'subject': opts.subject, 'body': opts.body, 'attachment': opts.attachment,
        'debug': opts.debug, 'zip': opts.zip, 'zip_name': opts.zip_name,
        'config': opts.config, 'list_config': opts.list_config
    }

    return return_opts, _parser


def zip_attachments(files, archive_name):
    """Zip email attachments into archive"""

    global compression
    global MAIL_ATTACHMENTS
    print("\033[92m{0}\t[INFO]\tCreating zip archive with attachments.\033[0m".format(
        strftime("%Y-%b-%d %H:%M:%S", localtime())
    ))
    with ZipFile(archive_name, mode='a') as zf:
        for f in files:
            zf.write(basename(f), compress_type=compression)

    return [realpath(archive_name)]


def attach_file(file_name, file_path):
    """Construct MIMEBase object for attachment file"""

    if not file_name and not file_path:
        return None
    part = MIMEBase('application', "octet-stream")
    try:
        part.set_payload(open(file_path, "rb").read())
    except OSError as err:
        print("\033[91m{0}\t[ERROR]\t{1}\033[0m".format(strftime("%Y-%b-%d %H:%M:%S", localtime()), err.strerror))
        return None
    encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=file_name)

    return part


def send_mail(smtp_obj, mail_from, recipients, message, _iter):
    """Sends email message via passed SMTP object"""

    global USER
    global PASSWD
    global DEBUG
    if smtp_obj.__module__ != 'smtplib':
        print("\033[91m{}\t[ERROR]\tsmtp_obj.__module__ != 'smtplib'\033[0m".format(
            strftime("%Y-%b-%d %H:%M:%S", localtime())))
        exit(2)
    else:
        try:
            smtp_obj.set_debuglevel(DEBUG)
            smtp_obj.starttls()
            smtp_obj.login(USER, PASSWD)
            try:
                # TODO::Check SMTP sendmail function response
                smtp_obj.sendmail(mail_from, recipients, message.as_string())
                return True
            except SMTPDataError as er:
                print("\033[91m{0}\t[ERROR]\t{1}\033[0m".format(
                    strftime("%Y-%b-%d %H:%M:%S", localtime()),
                    er.smtp_error if er.smtp_error else er.message
                ))
                exit(er.smtp_code)
        except SMTPResponseException as er:
            print("\033[91m{0}\t[ERROR]\t{1} Message not sent. Retries left: {2}\033[0m".format(
                strftime("%Y-%b-%d %H:%M:%S", localtime()),
                er.smtp_error if er.smtp_error else er.message, (10 - _iter)
            ))
            return False
        except SMTPException as er:
            print("\033[91m{0}\t[ERROR]\t{1} Message not sent. Retries left: {2}\033[0m".format(
                strftime("%Y-%b-%d %H:%M:%S", localtime()), er.message, (10 - _iter)
            ))
            return False
        except RuntimeError as er:
            print("\033[91m{0}\t[ERROR]\t{1} Message not sent. Exiting...\033[0m".format(
                strftime("%Y-%b-%d %H:%M:%S", localtime()), er.message))
            exit(2)

# Read config file
config = SafeConfigParser()
CONFIG_PATH = dirname(realpath(__file__)) + '/email.ini'
config.read(CONFIG_PATH)

arguments, parser = parse_args()

if arguments['list_config']:
    print("\033[92mAvailable configs:\033[0m", ' '.join(config.sections()))
    exit(0)

mandatory_args = ['to', 'subject', 'body']
filtered_args_keys = dict((a, b) for (a, b) in arguments.iteritems() if b is not None).keys()
fully_filtered_args_keys = dict((a, b) for (a, b) in arguments.iteritems() if b not in
                                [None, False, [], 'MailServer', 'attachments.zip']).keys()

if not fully_filtered_args_keys:
    print("\033[91m{0}\t[ERROR]\tAt least '{1}' must be passed as arguments\033[0m".format(
        strftime("%Y-%b-%d %H:%M:%S", localtime()), ', '.join(mandatory_args)))
    parser.print_help()
    exit(1)

for arg in mandatory_args:
    if arg not in filtered_args_keys:
        print("\033[91m{0}\t[ERROR]\t{1} must be passed as argument\033[0m".format(
            strftime("%Y-%b-%d %H:%M:%S", localtime()), arg.capitalize()))
        parser.print_help()
        exit(1)

# Defining the constants
MAIL_TO = arguments['to']
MAIL_COPY = arguments['cc']
MAIL_SUBJECT = arguments['subject']
MAIL_BODY = arguments['body']
MAIL_ATTACHMENTS = [realpath(attach) for attach in arguments['attachment']] if arguments['attachment'] else []
FILE_NAMES = []
DEBUG = arguments['debug']  # use -d/--debug to turn the debug on.
CONFIG = arguments['config']  # Define the default config you will use from config file
compress = arguments['zip']
archive = arguments['zip_name']

# Define constants with the values from config file
USER = config.get(CONFIG, 'login')
PASSWD = config.get(CONFIG, 'password')
MAIL_SERVER = config.get(CONFIG, 'host')
MAIL_PORT = config.get(CONFIG, 'port')
MAIL_FROM = config.get(CONFIG, 'from')
try:
    max_iterations = config.get(CONFIG, 'max_iterations')
except NoOptionError:
    max_iterations = 10

# Start to build email message
msg = MIMEMultipart()
msg['Subject'] = MAIL_SUBJECT
msg['From'] = MAIL_FROM
msg['To'] = ', '.join(MAIL_TO)
msg['Cc'] = ', '.join(MAIL_COPY)
RECIPIENTS = MAIL_TO + MAIL_COPY

if compress:
    try:
        __import__('zlib')
        compression = ZIP_DEFLATED
        MAIL_ATTACHMENTS = zip_attachments(MAIL_ATTACHMENTS, archive)
    except ImportError as e:
        print("\033[91m{0}\t[WARNING]\t{1}. Archive will be made without compression\033[0m".format(
                    strftime("%Y-%b-%d %H:%M:%S", localtime()), e.message))
        compression = ZIP_STORED
        MAIL_ATTACHMENTS = zip_attachments(MAIL_ATTACHMENTS, archive)

# Parse passed files
if MAIL_ATTACHMENTS:
    FILE_NAMES = [basename(path_) for path_ in MAIL_ATTACHMENTS]

# Prepare attachments
attachments = []
for _file, _path in zip(FILE_NAMES, MAIL_ATTACHMENTS):
    p = attach_file(_file, _path)
    if p:
        attachments.append(p)

body_part = MIMEBase('text', "html")
body_part.set_payload(MAIL_BODY)
encode_base64(body_part)

if attachments:
    for a in attachments:
        msg.attach(a)

msg.attach(body_part)

iteration = 0
server = False
# Try to auth on SMTP server
while not server:
    if iteration == max_iterations:
        print(
            "\03391m{0}\t[ERROR]\tFailed to connect to SMTP server. Maximum number of iterations reached ({1})".format(
                strftime("%Y-%b-%d %H:%M:%S", localtime()), max_iterations
            ))
        exit(2)
    try:
        iteration += 1
        server = SMTP(MAIL_SERVER, MAIL_PORT)
        print("\033[92m{0}\t[INFO]\tConnected to SMTP server.\033[0m".format(
            strftime("%Y-%b-%d %H:%M:%S", localtime())
        ))
    except SMTPConnectError as e:
        print("\033[91m{0}\t[ERROR]\t{1} Failed to auth on SMTP server. Retries left: {2}\033[0m".format(
            strftime("%Y-%b-%d %H:%M:%S", localtime()), e.smtp_error, (max_iterations - iteration)))
    except SMTPServerDisconnected as e:
        print("\033[91m{0}\t[ERROR]\t{1} Failed to auth on SMTP server. Retries left: {2}\033[0m".format(
            strftime("%Y-%b-%d %H:%M:%S", localtime()), e.message, (max_iterations - iteration)))

iteration = 1
send = False
# Try to send email message
while not send:
    if iteration == max_iterations:
        print("\03391m{0}\t[ERROR]\tFailed to send message. Maximum number of iterations reached ({1})".format(
            strftime("%Y-%b-%d %H:%M:%S", localtime()), max_iterations
        ))
        exit(2)
    send = send_mail(server, MAIL_FROM, RECIPIENTS, msg, iteration)
    iteration += 1
server.quit()

if compress:
    print("\033[92m{0}\t[INFO]\tRemoving attached archive: {1}\033[0m".format(
        strftime("%Y-%b-%d %H:%M:%S", localtime()), realpath(MAIL_ATTACHMENTS[0])
    ))
    unlink(MAIL_ATTACHMENTS[0])

print("\033[92m{0}\t[INFO]\tMessage successfully sent to: {1}\033[0m".format(
    strftime("%Y-%b-%d %H:%M:%S", localtime()), ', '.join(RECIPIENTS),
))
