#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os
import sys
import syslog
import logging
import requests
import killer
from subprocess import call
from ConfigParser import SafeConfigParser


config = SafeConfigParser()
CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + '/application.ini'
config.read(CONFIG_PATH)

LOG_LVL = eval(config.get('Local', 'log_level'))
APPLICATION_PATH = os.path.dirname(__file__)
OK_ICON = APPLICATION_PATH + '/pb_ok.png'
FAIL_ICON = APPLICATION_PATH + '/pb_red.png'
PID = config.get('Local', 'pid_file')
LOG_FORMAT = config.get('Local', 'log_format', raw=True)
logging.basicConfig(filename=config.get('Local', 'log_file'),
                    format=LOG_FORMAT,
                    level=LOG_LVL)
SYSLOG_IDENT = config.get('Local', 'syslog_ident')
url = config.get('Pushbullet', 'url')
headers = {'Authorization': 'Bearer ' + config.get('Pushbullet', 'token')}


def logger(message, level):
    if level == 'debug':
        logging.debug(message)
    elif level == 'info':
        logging.info(message)
    elif level == 'warn':
        logging.warning(message)
    elif level == 'err':
        logging.error(message)
    elif level == 'crit':
        logging.critical(message)

logger("Starting...", 'info')

if os.path.exists(PID):
    pid = open(PID)
    old_pid = pid.read()
    logger('Checking if process is running...', 'info')
    running = call(['cat',
                    '/proc/' + old_pid + '/cmdline'],
                   stdout=open(os.devnull, 'w'),
                   stderr=open(os.devnull, 'w'))
    if running == 1:
        logger('Process is not running (Maybe it was killed by `-9`?). Creating PID file in ' + PID + ' PID: ' + str(os.getpid()), 'info')
        syslog.openlog(SYSLOG_IDENT,
                       logoption=syslog.LOG_PID)
        syslog.syslog('Process is not running. Creating PID file in ' + PID)
        fp = open(PID, 'w')
        fp.write(str(os.getpid()))
        fp.close()
    else:
        hours = int(time.strftime('%H', time.localtime()))
        minutes = int(time.strftime('%M', time.localtime())) + 1
        logger('Process already running. PID: ' + old_pid + '. Next try at: ' + str(hours) + ':' + str(minutes), 'info')
        syslog.openlog(SYSLOG_IDENT,
                       logoption=syslog.LOG_PID)
        syslog.syslog('Process already running. Next try at: ' + str(hours) + ':' + str(minutes))
        sys.exit(1)
else:
    logger('Process is not running. Creating PID file in ' + PID, 'info')
    syslog.openlog(SYSLOG_IDENT,
                   logoption=syslog.LOG_PID)
    syslog.syslog('Process is not running. Creating PID file in ' + PID)
    os.mknod(PID)
    fp = open(PID, 'w')
    fp.write(str(os.getpid()))
    fp.close()


def _request():
    t = str(int(time.time()) - config.get('Pushbullet', 'update_step'))
    try:
        r = requests.get(url + t,
                         headers=headers,
                         timeout=config.get('Pushbullet', 'timeout'))
        json = r.json()
        return json
    except:
        logger('No internet connection or api.pushbullet.com is unreachable', 'crit')
        time.sleep(60)
        _request()


kill = killer.GracefulKiller()

if __name__ == '__main__':
    while True:

        j = _request()

        if not j:
            hours = int(time.strftime('%H', time.localtime()))
            minutes = int(time.strftime('%M', time.localtime())) + 1
            logger('Connection established. Restarting the daemon at ' + str(hours) + ':' + str(minutes), 'info')
            break

        length = len(j['pushes'])

        if not j['pushes']:
            logger('Nothing new. My watch continues', 'info')
        else:
            for l in range(0, length):
                try:
                    title = j['pushes'][l]['title']
                except:
                    title = 'Push without title'

                if j['pushes'][l]['active'] == bool(True):
                    try:
                        ok = title.split(':')[0].lower()
                    except:
                        ok = 'push'
                    if title.split(':')[0].lower() not in ['ok', 'push without title']:
                        notify_body = j['pushes'][l]['body'] + '\r\n\nCreated:\n' + time.ctime(
                            j['pushes'][l]['created'])
                        call(['notify-send',
                              '-i',
                              str(FAIL_ICON),
                              title,
                              notify_body])
                        logger('Notified with: \r\n' + title, 'info')
                    else:
                        notify_body = j['pushes'][l]['body'] + '\r\n\nCreated:\n' + time.ctime(
                            j['pushes'][l]['created'])
                        call(['notify-send',
                              '-i',
                              str(OK_ICON),
                              title,
                              notify_body])
                        logger('Notified with: ' + title, 'info')
                else:
                    logger('Dismissed push found: ' + title, 'info')
        logger('Finished checking pushes. It\'s time to have a nap', 'debug')
        time.sleep(20)
        if kill.kill_now:
            logger("Killed...", 'err')
            syslog.openlog(SYSLOG_IDENT,
                           logoption=syslog.LOG_PID)
            syslog.syslog('Killed...')
            os.remove(PID)
            break
