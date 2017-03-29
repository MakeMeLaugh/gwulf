#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#  __author__ = 'MakeMeLaugh'
from mysql import connector
from mysql.connector.errors import Error
from logging import getLogger
from application.handlers import cfgHandler
from redisHelper import RedisHelper

AUTH_CHECK_SQL = "SELECT chat_id FROM auth_users WHERE chat_id = %d AND approved = 1"
INSERT_CHAT_ID_SQL = "INSERT INTO auth_users (chat_id) VALUES (%d)"
UPDATE_UPD_ID_SQL = "UPDATE telegram_bot.msg_updates SET update_id = %d WHERE update_id = %d"
INSERT_UPD_ID_SQL = "INSERT INTO telegram_bot.msg_updates (update_id) VALUES (%d)"
GET_LAST_UPD_ID_SQL = "SELECT update_id as id FROM telegram_bot.msg_updates"


class MysqlHelper:
    def __init__(self):
        self.db_cfg = cfgHandler.CfgHandler(self).config['database']
        self.db = None
        self.curr = None
        self.redis = RedisHelper()
        self.logger = getLogger('TGmysqlHelper')

    def get_db_connection(self):
        """Return database connection object"""
        try:
            self.db = connector.connect(**self.db_cfg)
        except Error as e:
            self.logger.error("Database interaction error: {}".format(e.msg))
            exit(1)
        return self.db

    def get_cursor(self, dictionary=None):
        """Return database cursor object"""
        if not dictionary:
            self.curr = self.get_db_connection().cursor()
        else:
            self.curr = self.get_db_connection().cursor(dictionary=True)
        return self.curr

    def check_auth(self, cid):
        """
        Authorise user to receive messages from bot
        :return: boolean
        """
        if self.redis.get("{}.{}.{}".format(self.redis.config['prefix'], self.check_auth.__name__, str(cid))) > 0:
            return True
        curr = self.get_cursor(True)
        try:
            curr.execute(AUTH_CHECK_SQL % cid)
            result = curr.fetchall()
            if result:
                self.redis.set("{}.{}.{}".format(self.redis.config['prefix'], self.check_auth.__name__, str(cid)),
                               1,
                               self.redis.config['ttl'])
                self.logger.info("Saved info for chat_id: {} in redis for: {}".format(cid, self.redis.config['ttl']))
                return True
            else:
                return False
        except Error as e:
            self.db.rollback()
            self.logger.error(u"Failed to check user's authorization. Error: {}".format(e.msg))

    def save_user_chat_id(self, cid):
        curr = self.get_cursor(True)
        sql = INSERT_CHAT_ID_SQL
        sql %= cid
        try:
            curr.execute(sql)
            self.db.commit()
            self.logger.info(u"Save new user (chat_id={}) to database".format(cid))
            return True
        except Error as e:
            self.db.rollback()
            self.logger.error(u"Failed to save new user to database. Error: {}".format(e.msg))
            return False

    def get_last_msg_id(self, redis=True):
        """
        Return last handled message id
        :return: int
        """
        if redis:
            if self.redis.get("{}.{}".format(self.redis.config['prefix'], self.get_last_msg_id.__name__)):
                return int(self.redis.get("{}.{}".format(self.redis.config['prefix'], self.get_last_msg_id.__name__)))
        self.logger.debug(u"Retrieving last handled update")
        sql = GET_LAST_UPD_ID_SQL
        curr = self.get_cursor(True)
        try:
            curr.execute(sql)
            last_id = curr.fetchone()
            self.logger.debug("ID: {}".format(last_id))
            if last_id and 'id' in last_id:
                _id = int(last_id['id'])
            else:
                _id = 0
            self.redis.set("{}.{}".format(self.redis.config['prefix'], self.get_last_msg_id.__name__), _id)
            self.logger.debug("Received last_msg_id from redis: {}".format(_id))
            return _id
        except Error as e:
            self.db.rollback()
            self.logger.error(u"Failed to get last handled message id in database. Error: {}".format(e.msg))
            return False

    def save_last_update_id(self, upd_id, prev_upd_id, redis=True):
        """
        Save last handled message id to database
        :return: bool
        """
        if prev_upd_id == 0:
            sql = INSERT_UPD_ID_SQL
            sql %= upd_id
        else:
            if redis:
                self.redis.set("{}.{}".format(self.redis.config['prefix'], self.save_last_update_id.__name__), upd_id)
                self.logger.debug("Saved last update_id ({}) in redis".format(upd_id))
                return True
            sql = UPDATE_UPD_ID_SQL
            sql %= (upd_id, prev_upd_id)
        curr = self.get_cursor()
        try:
            curr.execute(sql)
            self.db.commit()
            self.logger.debug(u"Updated message id in database")
            self.logger.debug(u"{}".format(sql))
            return True
        except Error as e:
            self.db.rollback()
            self.logger.error(u"Failed to update message id in database. Error: {}".format(e.msg))
            return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db or self.curr:
            try:
                self.curr.close()
            except AttributeError:
                pass
            try:
                self.db.close()
            except AttributeError:
                pass
