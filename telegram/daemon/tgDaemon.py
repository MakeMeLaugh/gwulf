#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function
import baseDaemon
from sys import path
from os.path import dirname, abspath

path.append(dirname(abspath(dirname(__file__))))

from application.handlers import cfgHandler
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import application.bot as bot

description = """TelegramBotDaemon for handling incoming messages and doing stuff with received messages"""


class TelegramBot(baseDaemon.Daemon):
    __doc__ = description

    def __init__(self, **kwargs):
        super(TelegramBot, self).__init__(**kwargs)

    def run(self):
        """Overriding baseDaemon.Daemon run method with main bot logic"""
        bot.TelegramWorker().do_work()


class MyArgumentParser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(MyArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """
        Override ArgumentParser.error method to be able to catch errors
        :raises UserWarning
        """
        raise UserWarning(message)


def parse_arguments():
    global description
    cmds = ["start", "stop", "restart", "reload", "status"]
    parser = MyArgumentParser(prog="TelegramBotDaemon", usage="%(prog)s {}".format('|'.join(cmds)),
                              description=description, formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('cmd', choices=cmds, nargs='?', default="start")

    opts = None
    try:
        opts = parser.parse_args()
    except UserWarning:
        print(u"\033[91mInvalid arguments\033[0m")
        parser.print_help()
        exit(1)
    return opts


if __name__ == '__main__':
    command = parse_arguments().cmd
    config = cfgHandler.CfgHandler().config

    if not config['bot']['token'] or config['bot']['token'].find(':') < 0:
        print("\033[91mBot token is empty in config: {}\033[0m".format(cfgHandler.CfgHandler().conf_file))
        exit(1)

    c = TelegramBot(pidfile=config['bot']['pid_file'], stdin='/dev/null', stdout=config['log']['file'],
                    stderr=config['log']['file'])

    if command == "start":
        c.start()
    elif command == "stop":
        c.stop()
    elif command == "reload":
        c.reload()
    elif command == "restart":
        c.restart()
    elif command == "status":
        print(c.status())
