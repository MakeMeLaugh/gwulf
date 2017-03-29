#!/usr/bin/env python2
#  -*- coding: utf-8 -*-
import MySQLdb, csv, sys, os, time
from ConfigParser import SafeConfigParser


#read config file
config = SafeConfigParser()
CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + '/sql.ini'
config.read(CONFIG_PATH)
CONFIG = sys.argv[1]

db = MySQLdb.connect(host=config.get(CONFIG, 'host'), user=config.get(CONFIG, 'user'), passwd=config.get(CONFIG, 'passwd'), db=config.get(CONFIG, 'database'))

query = config.get(CONFIG, 'query')

#Для динамического написания заголовка (первого ряда)
tbl = config.get(CONFIG, 'tbl_full')
tbl_fields = "SHOW COLUMNS FROM " + tbl

cursor = db.cursor()
cursor.execute("SET NAMES utf8") #Для кириллицы
cursor.execute(tbl_fields)
cursor.execute(query)
res = cursor.fetchall()

output_file = config.get(CONFIG, 'save_path') + time.strftime("%Y_%b_%d_%H%M", time.localtime()) + '_' + CONFIG + '.csv'

with open(output_file, 'wb') as csvfile:
    data_writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
    field_names = [field[0] for field in cursor.description]
    data_writer.writerow(field_names)
    for row in res:
        data_writer.writerow(row)
csvfile.close()

cursor.close()
db.close()
