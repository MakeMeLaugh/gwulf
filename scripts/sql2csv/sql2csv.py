#!/usr/bin/env python2
#  -*- coding: utf-8 -*-
from __future__ import print_function
from csv import writer, QUOTE_NONNUMERIC
from os.path import dirname, realpath
from time import strftime, localtime
from subprocess import Popen, PIPE
from mysql import connector
from sys import argv
from ConfigParser import SafeConfigParser

config = SafeConfigParser()
CONFIG_PATH = dirname(realpath(__file__)) + '/sql.ini'
config.read(CONFIG_PATH)
CONFIG = argv[1]
save_path = config.get(CONFIG, 'save_path')
if save_path.find('user'):
    # get user name to create directory path
    user = Popen(['whoami'], stdout=PIPE, stderr=PIPE).communicate()[0].strip()
    save_path = save_path.replace('user', user)

db = connector.connect(host=config.get(CONFIG, 'host'), user=config.get(CONFIG, 'user'),
                       passwd=config.get(CONFIG, 'passwd'), db=config.get(CONFIG, 'database'))

query = config.get(CONFIG, 'query')
cursor = db.cursor(dictionary=True)
cursor.execute("SET NAMES utf8")  # For non-latin chars
cursor.execute(query)
res = cursor.fetchall()

output_file = save_path + strftime("%Y_%b_%d_%H%M", localtime()) + '_' + CONFIG + '.csv'
print("Output in:", output_file)

with open(output_file, 'wb') as csvfile:
    data_writer = writer(csvfile, delimiter=',', quotechar='"', quoting=QUOTE_NONNUMERIC)
    data_writer.writerow(res[0].keys())
    for row in res:
        data_writer.writerow(row.values())

csvfile.close()
cursor.close()
db.close()
