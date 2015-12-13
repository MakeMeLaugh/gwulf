#!/usr/bin/python
# -*- coding: utf-8 -*-
# __author__ = 'wulf' (originally by: http://stackoverflow.com/users/578989/mayank-jaiswal
# found this at (http://stackoverflow.com/a/31464349)

# Usage: create an instance of GracefulKiller class in your app
# e.g. kill = killer.GracefulKiller()
# If you want put some logic or break your cycle just use this code:
# `if kill.kill_now: break`
# If you want to add some logic before breaking - you are welcome to do that :)
# Your app will keep running to the end of the cycle and exit with exit code 0

import signal


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT,
                      self.exit_gracefully)
        signal.signal(signal.SIGTERM,
                      self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
