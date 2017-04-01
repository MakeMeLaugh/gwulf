#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#  __author__ = 'MakeMeLaugh'
"""
Just a helper for MongoDB aggregate functions
"""

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
docs = collection.aggregate(  # more here: https://docs.mongodb.org/manual/reference/operator/aggregation/group/
    [
        # {"$project": {"_id": 0}},  # which fields will be sent to the next pipe ("_id": 0 - removes _id from results)
        {"$match": {}},  # find() alias in aggregate
        # {"$limit": 10},  # how much documents from $match step will be sent to the next pipe
        # {"$skip": 5},  # how much documents to skip from the start of $match step results
        # {"$unwind": "$arrayField"},  # flattens array fields
        {"$group": {"_id": "$test_key",
                    # "test": {"$push": "$test_key_2"},  # Add custom field 'test' in results with 'test_key_2' value
                    # "avg": {"$avg": "$test_key_2"},  # Average of field 'test_key_2' values
                    # "max": {"$max": "test_key_2"},  # Max value of 'test_key_2' field
                    # "min": {"$min": "test_key_2"},  # Min value of 'test_key_2' field
                    "total": {"$sum": 1}  # Total number of matched documents
                    }
         },
        {"$sort": {"total": -1}},  # Sort field
        {"$out": "statistics"}  # Export results to 'statistics' collection in the same database
    ]
)
