#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from subprocess import call, check_output
from sys import argv
from os import path
import syslog

from redmine import Redmine, exceptions as e

FILENAME = str(argv[0]).split('/')[len(str(argv[0]).split('/')) - 1]
APPLICATION_PATH = str(path.dirname(check_output(['readlink', '-e', argv[0]])))
API_KEY = ''  # Redmine API-key (Check your Redmine profile page)
RM_URL = ''  # Redmine URL
ICON = APPLICATION_PATH + '/rm.png'  # Path to Redmine icon
RM = Redmine(RM_URL, key=API_KEY)
TASKS = RM.issue  # Redmine.Issue object - list of tasks
USAGE = """
    USAGE: %s [OPTIONS] ...
    \t-n\tget today tasks assigned to you
    \t-g\tget specified task

    Example calls:
    \t%s -n
    \t%s -g 6667
    """ % (FILENAME, FILENAME, FILENAME)

syslog.openlog(ident='rm_tasks', logoption=syslog.LOG_PID)


def notify(title, body):
    run = call(['notify-send',
                '-i',
                ICON,
                title,
                body])

    return run


def today_tasks():
    # project_id='-' - Id of the root project (to able to search all subprojects)
    # query_id - Id of custom search query
    my_tasks = TASKS.filter(project_id='-', query_id=69)
    if len(my_tasks) == 0:
        return notify(":)", "No tasks for today")
    else:
        for task in my_tasks:
            title = str(task['id']) + "  " + \
                str(task['start_date']) + " " + \
                str(task['status'])

            body = task['subject'] + "\n" + \
                unicode(task['description']) + \
                "\n\nURL: " + RM_URL + "/issues/" + \
                str(task['id'])

            notify(title, body)

        return True


def get_task():
    task_num = str(check_output(['xsel', '-o']))
    try:
        task = TASKS.get(task_num, include='journals')
    except e.ResourceNotFoundError as err:
        syslog.syslog(syslog.LOG_ERR, "#" + task_num, err.message)
        return notify("#" + task_num, err.message)
    except e.ForbiddenError as err:
        syslog.syslog(syslog.LOG_ERR, "#" + task_num, err.message)
        return notify("#" + task_num, err.message)

    notes = task['journals']

    # Validate missing attributes
    try:
        unicode(notes[(len(task['journals']) - 1)]['notes'])
        last_comment = u"-"
    except e.ResourceAttrError:
        last_comment = unicode(notes[(len(task['journals']) - 1)]['notes'])

    try:
        last_comment_author = unicode(task['journals'][(len(task['journals']) - 1)]['user']['name'])
    except e.ResourceAttrError as err:
        syslog.syslog(syslog.LOG_INFO, "#" + task_num, err.message)
        last_comment_author = err.message

    try:
        start_date = str(task['start_date'])
    except e.ResourceAttrError as err:
        syslog.syslog(syslog.LOG_INFO, "#" + task_num, err.message)
        start_date = err.message

    # Set title and body of notification
    title = "#" + str(task['id']) + '  ' + str(task['created_on']) + " " + str(task['status'])
    body = task['subject'] + "\n" +\
        u'Start date: ' + start_date + "\n" + u'Description: ' +\
        unicode(task['description']) +\
        "\n\nURL: " + RM_URL + "/issues/" +\
        str(task['id']) + u'\n\nLast comment:\n' +\
        u'Author: ' + last_comment_author + "\n" + last_comment

    return notify(title, body)


if len(argv) != 2:
    print(USAGE)
    exit(1)

if argv[1] == '-n':
    today_tasks()
elif argv[1] == '-g':
    get_task()

exit(0)
