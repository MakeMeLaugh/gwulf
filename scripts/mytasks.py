#!/usr/bin/python
# -*- coding: utf-8 -*-
from subprocess import call, check_output
from sys import argv
from os import path
import syslog

from redmine import Redmine, exceptions as e

FILENAME = str(argv[0]).split('/')[len(str(argv[0]).split('/')) - 1]
APPLICATION_PATH = str(path.dirname(check_output(['readlink', '-e', argv[0]])))
API_KEY = ''  # API-ключ редмайна (см. свой профиль в RM)
RM_URL = ''  # URL редмайна
ICON = APPLICATION_PATH + '/rm.png'  # Иконка RM
RM = Redmine(RM_URL, key=API_KEY)
TASKS = RM.issue  # Объект Redmine.Issue - список задач
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
    # project_id='-' - идентификатор корневого проекта (для просмотра задач по всем подпроектам)
    # query_id - идентификатор сохраненного запроса в RM
    my_tasks = TASKS.filter(project_id='-', query_id=69)
    if len(my_tasks) == 0:
        return notify(":)", "Задач на сегодня нет")
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
    except e.ResourceNotFoundError:
        syslog.syslog(syslog.LOG_ERR, "#" + task_num, u'Задача не существует или удалена')
        return notify("#" + task_num, u'Задача не существует или удалена')
    except e.ForbiddenError:
        syslog.syslog(syslog.LOG_ERR, "#" + task_num, u'У вас нет прав на просмотр данной страницы')
        return notify("#" + task_num, u'У вас нет прав на просмотр данной страницы')

    notes = task['journals']

    # Валидируем отсутствующие свойства
    try:
        unicode(notes[(len(task['journals']) - 1)]['notes'])
        last_comment = u"-"
    except e.ResourceAttrError:
        last_comment = unicode(notes[(len(task['journals']) - 1)]['notes'])

    try:
        last_comment_author = unicode(task['journals'][(len(task['journals']) - 1)]['user']['name'])
    except e.ResourceAttrError:
        syslog.syslog(syslog.LOG_INFO, "#" + task_num, u"Без автора О_о")
        last_comment_author = u"Без автора О_о"

    try:
        start_date = str(task['start_date'])
    except e.ResourceAttrError:
        syslog.syslog(syslog.LOG_INFO, "#" + task_num, u'Дата начала не была установлена')
        start_date = u'Дата начала не была установлена'

    # Устанавливаем тему и тело нотификации
    title = "#" + str(task['id']) + '  ' + str(task['created_on']) + " " + str(task['status'])
    body = task['subject'] + "\n" +\
        u'Дата начала: ' + start_date + "\n" + u'Описание: ' +\
        unicode(task['description']) +\
        "\n\nURL: " + RM_URL + "/issues/" +\
        str(task['id']) + u'\n\nПоследний комментарий:\n' +\
        u'Автор: ' + last_comment_author + "\n" + last_comment

    return notify(title, body)


if len(argv) != 2:
    print(USAGE)
    exit(1)

if argv[1] == '-n':
    today_tasks()
elif argv[1] == '-g':
    get_task()

exit(0)
