#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#  __author__ = 'MakeMeLaugh'
from redis import Redis
from logging import getLogger
from application.handlers import cfgHandler


class RedisHelper(Redis):

    def __init__(self):
        self.cfg = None
        self.config = self.init_config()
        super(RedisHelper, self).__init__(self.config['host'], self.config['port'])
        self.logger = getLogger('TGRedisModel')

    def init_config(self):
        self.cfg = cfgHandler.CfgHandler(self)
        return self.cfg.config['redis']
