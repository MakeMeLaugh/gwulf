#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  __author__ = 'wulf'

import mysql.connector as mysql

conn = mysql.connect(user='root', password='123321', database='db_test')

cursor = conn.cursor()
query = "SELECT * FROM test LIMIT 3"

cursor.execute(query)

fields = [field[0] for field in cursor.description]

result = list()

for row in cursor:
    result.append(row)

print("%s\t%s\t%s" % (fields[0], fields[1], fields[2]))
for i in result:
    print("%s\t%s\t%s" % (i[0], i[1], i[2]))
