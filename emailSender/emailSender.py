#!/usr/bin/env python2
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
import logging
from logging import handlers
from smtplib import SMTP, SMTPConnectError, SMTPResponseException, SMTPException, SMTPServerDisconnected, SMTPDataError
from os.path import dirname, realpath, basename, isfile
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from ConfigParser import SafeConfigParser, NoOptionError
from sys import argv
from os import unlink
from time import sleep
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.encoders import encode_base64
from socket import gaierror


logger = logging.getLogger(basename(__file__).split('.')[0])
logger.setLevel(logging.WARNING)
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] [%(message)s]')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

syslog_handler = handlers.SysLogHandler()
syslog_handler.setFormatter(formatter)
logger.addHandler(syslog_handler)


def parse_args():
    """Parses command line arguments"""

    _parser = ArgumentParser(
        prog=basename(realpath(argv[0])).replace('.py', ''),
        usage="%(prog)s [OPTIONS]...",
        # add_help=True,
        formatter_class=ArgumentDefaultsHelpFormatter,
        epilog=u"'Screw\'em all! May the cow force be with you!'",
        description=u"Sends email messages from command line"
    )

    required_args = _parser.add_argument_group('required arguments')

    required_args.add_argument('-t', '--to', dest='to', action='append',
                                help=u"Email receivers ('To:' field)", required=True)
    required_args.add_argument('-s', '--subject', dest='subject',
                                help=u"Email subject ('Subject:' field)", required=True)
    required_args.add_argument('-b', '--body', dest='body',
                                help=u"Email body (HTML is supported)", required=True)
    # _parser.add_argument('-t', '--to', dest='to', action='append', help=u"Email receivers ('To:' field)")
    _parser.add_argument('-c', '--cc', dest='cc', action='append', default=[],
                         help=u"Email receivers ('Cc:' field)")
    _parser.add_argument('-B', '--bcc', dest='bcc', action='append', default=[],
                         help=u"Email receivers ('Cc:' field)")
    # _parser.add_argument('-s', '--subject', dest='subject',
                        #  help=u"Email subject ('Subject:' field)")
    # _parser.add_argument('-b', '--body', dest='body', help=u"Email body (HTML is supported)")
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
        'to': opts.to, 'cc': opts.cc, 'bcc': opts.bcc, 'subject': opts.subject, 'body': opts.body, 'attachment': opts.attachment,
        'debug': opts.debug, 'zip': opts.zip, 'zip_name': opts.zip_name,
        'config': opts.config, 'list_config': opts.list_config
    }

    return return_opts, _parser


def read_config():
    c = SafeConfigParser()
    c.read(dirname(realpath(__file__)) + '/email.ini')
    return c


def zip_attachments(_files, _archive_name, compression):
    """Zip email attachments into archive"""

    logger.info("Creating zip archive with attachments.")
    with ZipFile(_archive_name, mode='a') as zf:
        for f in _files:
            zf.write(basename(f), compress_type=compression)

    return [realpath(_archive_name)]


def archive_attachments(files, archive_name):
    try:
        __import__('zlib')
        compression = ZIP_DEFLATED
    except ImportError as e:
        logger.warning("{0}. Archive will be made without compression".format(e.message))
        compression = ZIP_STORED

    return zip_attachments(files, archive_name, compression)


def attach_file(file_name, file_path):
    """Construct MIMEBase object for attachment file"""

    if not file_name and not file_path:
        return None
    part = MIMEBase('application', "octet-stream")
    try:
        part.set_payload(open(file_path, "rb").read())
    except OSError as err:
        logger.error(err.strerror)
        return None
    encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=file_name)

    return part


def connect_to_relay(max_tries, host, port):
    _iteration = 0
    _server = False
    while not _server:
        if _iteration == max_tries:
            logger.error(
                "Failed to connect to SMTP server. Maximum number of iterations reached ({0})".format(max_tries)
            )
            exit(2)
        try:
            _iteration += 1
            _server = SMTP(host, port)
            logger.info("Connected to SMTP server.")
        except SMTPConnectError as e:
            logger.error("{0}. Failed to auth on SMTP server. Retries left: {1}".format(e.smtp_error,
                                                                                        (max_tries - _iteration)))
        except SMTPServerDisconnected as e:
            logger.error("{0}. Failed to auth on SMTP server. Retries left: {1}".format(e.message,
                                                                                        (max_tries - _iteration)))
        except gaierror as e:
            logger.error("{0}. Failed to resolve SMTP server hostname. Exiting...".format(e.strerror))
            exit(e.errno)

        sleep(5)

    return _server


def log_in_to_relay(smtp_obj, user, password, debug=False):
    try:
        smtp_obj.set_debuglevel(debug)
        smtp_obj.starttls()
        smtp_obj.login(user, password)
    except SMTPResponseException as er:
        logger.error("{0}. Message not sent. Retries left: {1}".format(
            er.smtp_error if er.smtp_error else er.message, (10 - _iter)
        ))
        return False
    except SMTPException as er:
        logger.error("{0}. Message not sent. Retries left: {1}".format(er.message, (10 - _iter)))
        return False
    except RuntimeError as er:
        logger.error("{0}. Message not sent. Exiting...".format(er.message))
        exit(2)
    return smtp_obj


def send_mail(smtp_obj, mail_from, recipients, message, _iter):
    """Sends email message via passed SMTP object"""

    if smtp_obj.__module__ != 'smtplib':
        logger.error("smtp_obj.__module__ != 'smtplib'")
        exit(2)
    else:
        try:
            # TODO::Check SMTP sendmail function response
            smtp_obj.sendmail(mail_from, recipients, message.as_string())
            return True
        except SMTPDataError as er:
            logger.error(er.smtp_error if er.smtp_error else er.message)
            exit(er.smtp_code)


# TODO::Add BCC

# Read config file
config = read_config()

arguments, parser = parse_args()

if arguments['list_config']:
    print("\033[92mAvailable configs:\033[0m", ' '.join(config.sections()))
    exit(0)

# Defining the constants
MAIL_TO = arguments['to']
MAIL_COPY = arguments['cc']
MAIL_SUBJECT = arguments['subject']
MAIL_BODY = arguments['body']
if isfile(MAIL_BODY):
    MAIL_BODY = open(MAIL_BODY, 'r').read()
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
    MAIL_ATTACHMENTS = archive_attachments(MAIL_ATTACHMENTS, archive)

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

# server = False
server = connect_to_relay(host=MAIL_SERVER, port=MAIL_PORT, max_tries=max_iterations)

iteration = 1
send = False
# Try to send email message
while not send:
    if iteration == max_iterations:
        logger.error("Failed to send message. Maximum number of iterations reached ({0})".format(max_iterations))
        exit(2)
    server = log_in_to_relay(server, USER, PASSWD, DEBUG)
    send = send_mail(server, MAIL_FROM, RECIPIENTS, msg, iteration)
    iteration += 1
server.quit()

if compress:
    logger.info("Removing attached archive: {0}".format(realpath(MAIL_ATTACHMENTS[0])))
    unlink(MAIL_ATTACHMENTS[0])

logger.info("Message successfully sent to: {0}".format(', '.join(RECIPIENTS)))
