#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  __author__ = 'wulf'

import datetime

import pymongo

client = pymongo.MongoClient()

db = client.get_database('test')
collection = db.get_collection('test')

data = {
    "test_key": "1",
    "test_key_2": "my test key",
    "create_time": datetime.datetime.utcnow(),
    "Data": {"Promotion": "TNA",
             "Champion": "Drew"},
    "update_time": None
}

# docs = collection.find({"create_time": {"$gt": datetime.datetime.utcfromtimestamp(1458262785)}})
docs = collection.aggregate(  # больше тут: https://docs.mongodb.org/manual/reference/operator/aggregation/group/
    [
        # {"$project": {"_id": 0}},  # какие поля передавать в следующий пайп ("_id": 0 - исключает поле _id из выдачи)
        {"$match": {}},  # что искать (аналог find())
        # {"$limit": 10},  # сколько документов передавать в следующий пайп
        # {"$skip": 5},  # оффсет
        # {"$unwind": "$arrayField"},  # раскрывает массив, возвращая кол-во документов, равное кол-ву документов
        {"$group": {"_id": "$test_key",
                    # "test": {"$push": "$test_key_2"},  # если нужно кастомно название поля. Возвращает массив.
                    # "avg": {"$avg": "$test_key_2"},  # среднее значение
                    # "max": {"$max": "test_key_2"},  # максимальное значение поля
                    # "min": {"$min": "test_key_2"},  # минимальное значение поля
                    "total": {"$sum": 1}  # поле с количеством
                    }
         },
        {"$sort": {"total": -1}},  # поле сортировки
        {"$out": "statistics"}  # для записи данных в выходную коллекцию
    ]
)