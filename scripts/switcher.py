# !/usr/bin/python
# -*- coding: utf-8 -*-
# __author__ = 'wulf'

from subprocess import Popen, PIPE


def switch():
    import sys

    alphabet = {u'й': 'q', u'ц': 'w', u'у': 'e', u'к': 'r', u'е': 't', u'н': 'y',
                u'г': 'u', u'ш': 'i', u'щ': 'o', u'з': 'p', u'х': '[', u'ъ': ']',
                u'ф': 'a', u'ы': 's', u'в': 'd', u'а': 'f', u'п': 'g', u'р': 'h',
                u'о': 'j', u'л': 'k', u'д': 'l', u'ж': ';', u'э': '\'', u'я': 'z',
                u'ч': 'x', u'с': 'c', u'м': 'v', u'и': 'b', u'т': 'n', u'ь': 'm',
                u'б': ',', u'ю': '.', u'.': '/', u'ё': '`', u'Ё': '~',
                u'Й': 'Q', u'Ц': 'W', u'У': 'E', u'К': 'R', u'Е': 'T', u'Н': 'Y',
                u'Г': 'U', u'Ш': 'I', u'Щ': 'O', u'З': 'P', u'Х': '{', u'Ъ': '}',
                u'Ф': 'A', u'Ы': 'S', u'В': 'D', u'А': 'F', u'П': 'G', u'Р': 'H',
                u'О': 'J', u'Л': 'K', u'Д': 'L', u'Ж': ':', u'Э': '"', u'Я': 'Z',
                u'Ч': 'X', u'С': 'C', u'М': 'V', u'И': 'B', u'Т': 'N', u'Ь': 'M',
                u'Б': '<', u'Ю': '>', u',': '?', u' ': ' ',
                '!': '!', '"': '@', '№': '#', ';': '$', '%': '%', ':': '^', '?': '&',
                '*': '*', '(': '(', ')': ')', '-': '-', '=': '=', '_': '_', '+': '+'
                }

    out = str
    args = sys.argv[2:]

    command = out.join(' ', [arg.decode('utf-8') for arg in args])

    phrase = command

    new_phrase = []

    for i in phrase:
        if i in alphabet:
            new_phrase.append(alphabet.get(i))
        else:
            new_phrase.append(i)

    c = str
    d = c.join('', new_phrase)

    return d


def get_tty():

    terminal = None

    try:
        p = Popen(['tty'], stdout=PIPE, stderr=PIPE)
        terminal, err = p.communicate()
    except OSError as e:
        print 'ErrorMessage: ' + str(e.strerror), '\nErrorCode: ' + str(e.errno)
        exit(1)

    return terminal.strip("\n")


def execute(pts=None, command=None):
    try:
        p = Popen(command.split(), stdin=open(pts, 'r'), stdout=open(pts, 'w'), stderr=open(pts, 'w'))
        out, err = p.communicate()
        return out, err
    except OSError as e:
        print("Command %s not found\nPython subprocess module error message: %s" % (command, e.strerror))
        exit(1)


def get_input(choice):
    import getpass

    _input = getpass.getpass(choice)
    return _input


def run():
    pts = get_tty()
    command = switch()
    choice = ("Execute command:\n\n%s\n" % command)
    _input = get_input(choice)
    if _input == 'y':
        _exec = execute(pts=pts, command=command)
        return _exec
    else:
        print('Command %s not found' % command)

if __name__ == '__main__':
    run()
