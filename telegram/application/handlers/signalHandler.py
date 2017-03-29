#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#  __author__ = 'MakeMeLaugh'
from __future__ import print_function
from __future__ import unicode_literals
from logging import getLogger
import signal


class SignalHandler(object):
    """Class for handling signals in created daemon"""
    stop = False

    def __init__(self, cls):
        self.config = None
        self.cfg = None
        self.cls = cls
        self.logger = getLogger('TGsignalHandler')

    def sig_handler(self, signum, stack):
        """
        Handle received signal
        :param signum: signal number
        :param stack:
        :return: dict|boolean
        """
        try:
            if signum == 1:
                self.cfg = getattr(self.cls, 'reload_config')()
                return self.cfg
            elif signum == 10:
                return self.cls.cfg.increase_log()
            elif signum == 12:
                return self.cls.cfg.decrease_log()
            elif signum == 15:
                # Crutch...but don't know how to call this method properly...
                if self.cls.__class__.__name__ == 'TelegramWorker':
                    self.cls.db.save_last_update_id(self.cls.update_id, self.cls.db.get_last_msg_id(False), False)
                self.stop = True
        except BaseException as e:
            self.logger.error("Error while handling signal: {}".format(e.message))

    def handle_signals(self):
        """Configure signals to handle with appropriate handler method"""
        signal.signal(signal.SIGHUP, self.sig_handler)
        signal.signal(signal.SIGUSR1, self.sig_handler)
        signal.signal(signal.SIGUSR2, self.sig_handler)
        signal.signal(signal.SIGTERM, self.sig_handler)
