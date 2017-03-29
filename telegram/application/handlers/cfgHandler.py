#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#  __author__ = 'MakeMeLaugh'
from __future__ import print_function
from __future__ import unicode_literals
from ConfigParser import SafeConfigParser
from os.path import dirname, abspath
from logging import getLogger

APPLICATION_PATH = dirname(abspath(dirname(__file__)))
CONFIGS_PATH = dirname(APPLICATION_PATH) + '/configs'


class CfgHandler(object):
    """
    Class for working with config files (in sectioned format)
    Provide a module object while creating CfgHandler object
    e.g.: config = CfgHandler(self)
    """

    def __init__(self, cls=None, config=CONFIGS_PATH + '/application.ini'):
        self.cls = cls
        self.conf_file = config
        self.config = self.read_config()
        self.logger = getLogger('TGconfigLogger')
        # TODO::Do something if handler is called not from class...
        if not self.cls:
            self.cls = self
            # raise IOError("Module instance has to be provided while constructing config object")
        self.sig_handler = None

    def read_config(self):
        """
        Return the config dict from config file
        :return: dict(conf)
        """
        cfg = SafeConfigParser()
        cfg.read(self.conf_file)
        conf = {}
        for section in cfg.sections():
            conf[section] = {}
            for item in cfg.items(section):
                conf[section][item[0]] = item[1]

        # Crutch >_<
        if conf['log']['level']:
            conf['log']['level'] = int(conf['log']['level'])
        if conf['database']['port']:
            conf['database']['port'] = int(conf['database']['port'])
        if conf['bot']['sleep']:
            conf['bot']['sleep'] = int(conf['bot']['sleep'])
        if conf['bot']['debug']:
            conf['bot']['debug'] = int(conf['bot']['debug'])
        if conf['redis']['port']:
            conf['redis']['port'] = int(conf['redis']['port'])
        if conf['redis']['ttl']:
            conf['redis']['ttl'] = int(conf['redis']['ttl'])

        return conf

    def reload_config(self):
        """
        Reload module's config from file on disk without stopping the daemon process
        :return: dict(conf)
        """
        try:
            self.logger.info(u"Reloading config")
            self.cls.config = None
            return self.read_config()
        except AttributeError:
            self.logger.error("Caller class config is not loaded. Class: {}".format(self.cls.__class__.__name__))

    def increase_log(self):
        """
        Increase logging level without modifying config file
        :return: dict(conf)
        """
        try:
            self.logger.info("Increasing log level")
            if self.cls.config['log']['level'] < 50:
                self.cls.config['log']['level'] += 10
                self.cls.logger.setLevel(self.cls.config['log']['level'])
                return self.cls.config
            else:
                self.logger.warning("Log level already at max priority")
                return self.cls.config
        except AttributeError:
            self.logger.error("Caller class config is not loaded. Class: {}".format(self.cls.__class__.__name__))

    def decrease_log(self):
        """
        Decrease logging level without modifying config file
        :return: dict(conf)
        """
        try:
            self.logger.info("Decreasing log level")
            if self.cls.config['log']['level'] > 10:
                self.cls.config['log']['level'] -= 10
                self.cls.logger.setLevel(self.cls.config['log']['level'])
                return self.cls.config
            else:
                self.logger.warning("Log level already at min priority")
                return self.cls.config
        except AttributeError:
            self.logger.error("Caller class config is not loaded. Class: {}".format(self.cls.__class__.__name__))
