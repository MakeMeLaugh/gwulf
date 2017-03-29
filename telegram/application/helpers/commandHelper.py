#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#  __author__ = 'MakeMeLaugh'

class CommandHelper(object):

    @staticmethod
    def ping_cmd(message, *args, **kwargs):
        return u"pong!\nOur chat id is: {cid}".format(cid=message['chat_id'])

    @staticmethod
    def default_cmd(*args, **kwargs):
        return u"I'm stupido, I don't understand you"

    @staticmethod
    def test_cmd(*args, **kwargs):
        cmd_args = list(kwargs['command'][1:])
        return_str = ""
        if len(cmd_args) == 0:
            return u"I haven't received any arguments for the command."
        else:
            for arg in cmd_args:
                a = {}
                arg_str = u"Key: {}; Value: {}\n"
                if arg.find("="):
                    if arg.partition("=")[0] != "" and arg.partition("=")[2] != "":
                        a['key'] = arg.partition("=")[0].strip('"')
                        a['value'] = arg.partition("=")[2].strip('"')
                        arg_str = arg_str.format(a['key'], a['value'])
                        return_str += arg_str
                    else:
                        return_str += arg
                else:
                    return_str += ', '.join(cmd_args)
            return u"I have received some arguments for this command: {args}".format(
                args=return_str
            )

    @staticmethod
    def err_cmd():
        return u"Something went wrong with your last message. Telegram API has lost it"

    @staticmethod
    def not_authorized_user_cmd():
        return u"Please ask one of my masters to approve your chat"
