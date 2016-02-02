#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  __author__ = 'wulf'

import mysql.connector as mysql
import csv

output_file = './file.xlsx'


conn = mysql.connect(user='root', password='123321', database='db_test')

cursor = conn.cursor()
query = "SELECT * FROM test LIMIT 3"

cursor.execute(query)

fields = [field[0] for field in cursor.description]

result = list()

for row in cursor:
    result.append(row)

with open(output_file, 'wb') as csvfile:
    data_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    data_writer.writerow(fields)
    for row in result:
        data_writer.writerow(row)
csvfile.close()

cursor.close()
conn.close()
