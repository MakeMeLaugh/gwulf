#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# __author__ = 'wulf'
# FIXME::Optimize imports
import logging
import sys
from os.path import abspath, dirname
from requests import post, exceptions
from syslog import *
from time import sleep
from json import dumps
from helpers import mysqlHelper
from helpers import commandHelper
from helpers import redisHelper
from handlers import cfgHandler
from handlers import signalHandler

APPLICATION_PATH = abspath(dirname(__file__))
APPLICATION_NAME = __name__
sys.path.append(dirname(APPLICATION_PATH))
openlog(APPLICATION_NAME, logoption=LOG_PID, facility=LOG_USER)


class TelegramWorker(object):
    """Class for handling messages sent by users to the bot"""

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}
        self.update_id = self.prev_update_id = 0
        self.worker = self.cmd_helper = self.logger = self.log_lvl = self.api_url = self.config = self.cfg = None

        try:
            self.sig_handler = signalHandler.SignalHandler(self)
            self.init_log()
            openlog(self.config['log']['syslog_ident'], logoption=LOG_PID, facility=LOG_USER)
            self.db = mysqlHelper.MysqlHelper()
            self.redis = redisHelper.RedisHelper()
            self.sig_handler.handle_signals()
        except IOError as e:
            syslog(LOG_ERR, u"Failed to load config for telegram bot")
            self.logger.error(u"Failed to load config: {err}".format(err=e.strerror))

        syslog(LOG_INFO, u"Initialized telegram daemon")
        self.logger.info(u"Started telegram daemon")

    def init_config(self):
        """Initialise config"""
        self.cfg = cfgHandler.CfgHandler(self)
        return self.cfg.config

    def reload_config(self):
        """Reload config from file on disk"""
        if self.config:
            self.logger.info(u"Reloading config from disk: {}".format(self.cfg.conf_file))
            self.config = self.cfg.reload_config()
            self.init_log()
        return self.config

    def init_log(self):
        """Initialise logging"""
        self.config = self.init_config()
        logging.basicConfig(
            filename=self.config['log']['file'],
            format=self.config['log']['format'],
            level=(self.config['log']['level'] if self.config['bot']['debug'] > 0 else None)
        )
        # TODO::Restart loggers in external modules on reload signal?
        self.logger = logging.getLogger("TGWorker")
        self.logger.setLevel(self.config['log']['level'])
        self.log('info', u"Loaded config for telegram bot: {}".format(dumps(self.config)))

    def api_call(self, method, params):
        """
        Send request to Telegram API
        :param method: Method name
        :param params: Request dictionary
        :return: dict
        """
        self.api_url = self.config['bot']['api_url'] + self.config['bot']['token'] + '/'
        api_call_url = self.api_url + method
        try:
            if params:
                params = dumps(params)
                self.log('debug', u"Request params: {params}".format(params=dumps(params)))
                request = post(api_call_url, headers=self.headers, data=params)
            else:
                request = post(api_call_url, headers=self.headers)
            response = request.json()
        except exceptions.RequestException as e:
            self.log("error", u"Failed to call TG API: {err}".format(err=e.message))
            return {}
        self.log('debug', u"API response: {resp}".format(resp=dumps(response)))
        if "error_code" in response:
            self.log('warning', u"Error while calling TG API: {err}".format(err=response['description']))
        return response

    @staticmethod
    def __has_key(obj, key):
        """Check if dict has a specified key"""
        try:
            if key in obj:
                return True
        except KeyError:
            return False

    def get_updates(self):
        """Received updates from Telegram API"""
        if self.update_id > 0:
            self.log('debug', u"Last handled update_id={}".format(str(self.update_id)))
            return self.api_call('getUpdates', {'offset': self.update_id + 1})
        else:
            self.log('debug', u"Last handled update_id={}".format(str(self.update_id)))
            return self.api_call('getUpdates', {})

    def handle_messages(self, new_msgs):
        """
        Handle messages received from Telegram API
        :param new_msgs: Raw messages received from Telegram API
        :return: list(msg)
        """
        msgs = []
        if new_msgs:
            for msg in new_msgs['result']:
                self.get_update_id(msg)
                self.log('debug', "Message: " + dumps(msg))
                msgs.append(self.parse_msg(msg))
        if msgs:
            self.log('debug', u"Messages: {0}".format(dumps(msgs)))
        return msgs

    def get_update_id(self, m):
        """
        Get update id of current message
        :param m: Message being handled
        """
        self.update_id = m[u"update_id"]

    def parse_msg(self, msg):
        """
        Parse message received from Telegram API for later handling
        :param msg: Message being handled
        :return: dict
        """
        f_msg = dict.fromkeys(['chat_id', 'update_id', 'text', 'type'])
        if u'message' not in msg.keys():
            msg[u'message'] = msg[u'edited_message']
            del (msg[u'edited_message'])
        if type(msg[u'message'][u'chat']) is dict:
            f_msg[u'chat_id'] = msg[u'message'][u'chat'][u'id']
        else:
            f_msg[u'chat_id'] = msg[u'message'][u'chat']
        f_msg[u'update_id'] = msg[u'update_id']

        try:
            f_msg[u'text'] = msg[u'message'][u'text']
        except KeyError as e:
            self.log('debug', u"No text in received message. {err}".format(err=e.message))
            f_msg[u'text'] = u''

        if u'entities' in msg[u'message']:
            self.log(u'debug', u'Entities: {0}'.format(dumps(msg[u'message'][u'entities'])))
            f_msg[u'type'] = msg[u'message'][u'entities'][0][u'type']
        else:
            f_msg[u'type'] = u''

        return f_msg

    def get_msg_text(self, message):
        """Return message text to send to user"""
        msg_text = ""
        command_args = message['text'].split()
        try:
            msg_text = getattr(self.cmd_helper, command_args[0][1:] + '_cmd')(message,
                                                                              command=command_args)
            return msg_text
        except AttributeError:
            self.log('warning', u"Received unknown command: {cmd}".format(cmd=command_args[0]))
            msg_text = self.cmd_helper.default_cmd()
            return msg_text
        finally:
            return msg_text

    def send_message(self, msg, msg_params):
        """
        Send message to user
        :param msg: message object from TG API
        :param msg_params: Request object
        """
        try:
            self.api_call("sendMessage", msg_params)
            self.log('info', u"Send message to: {cid}, message: {msg}".format(cid=msg['chat_id'],
                                                                              msg=msg_params['text']))
        except IOError:
            msg_params['text'] = self.cmd_helper.err_cmd()
            self.api_call("sendMessage", msg_params)
        self.db.save_last_update_id(msg['update_id'], self.prev_update_id)
        self.update_id = self.prev_update_id = msg['update_id']

    def log(self, priority, msg):
        """
        Log to syslog and log-file from config
        :param priority: Severity
        :param msg: Message to log
        """
        # TODO::Refactor this **** logging to use logging.handlers?
        msg = str(msg.encode('utf-8').replace('\n', ' '))
        if priority in ['debug', 10]:
            self.logger.debug(msg)
            syslog(LOG_DEBUG, msg)
        elif priority in ['info', 20]:
            self.logger.info(msg)
            syslog(LOG_INFO, msg)
        elif priority in ['warning', 30]:
            self.logger.warning(msg)
            syslog(LOG_WARNING, msg)
        elif priority in ['error', 40]:
            self.logger.error(msg)
            syslog(LOG_ERR, msg)
        elif priority in ['critical', 50]:
            self.logger.critical(msg)
            syslog(LOG_CRIT, msg)

    def do_work(self):
        """Main daemon loop"""
        self.cmd_helper = commandHelper.CommandHelper()
        self.update_id = self.prev_update_id = self.db.get_last_msg_id(False)
        while not self.sig_handler.stop:
            self.on_iterate()
            sleep(self.config['bot']['sleep'])

    def on_iterate(self):
        """Main logic of daemon"""
        updates = self.get_updates()
        if not self.__has_key(updates, 'result') or not updates['result']:
            self.log('debug', u"No updates found after last handled update: {0}".format(str(self.update_id)))
            return False
        else:
            formatted_message = self.handle_messages(updates)
            if not formatted_message:
                self.log('warning', u"Failed to format new updates")
                return False
            for message in formatted_message:
                if self.db.check_auth(message['chat_id']):
                    if message['type'] == u"bot_command" and message['text'].startswith('/'):
                        msg_text = self.get_msg_text(message)
                        msg_params = {"chat_id": message['chat_id'], "text": msg_text}
                        self.send_message(message, msg_params)
                    else:
                        msg_params = {"chat_id": message['chat_id'], "text": self.cmd_helper.default_cmd()}
                        self.send_message(message, msg_params)
                else:
                    self.db.save_user_chat_id(message['chat_id'])
                    msg_params = {"chat_id": message['chat_id'], "text": self.cmd_helper.not_authorized_user_cmd()}
                    self.send_message(message, msg_params)
            return True
