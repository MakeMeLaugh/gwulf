#!/usr/bin/env python2
from os import fork, chdir, setsid, umask, dup2, \
    getpid, remove, kill, path, mkdir, mknod
from sys import stderr, stdin, stdout, exit, argv
from psutil import Process, NoSuchProcess
from datetime import datetime
from collections import namedtuple
from signal import SIGTERM
from atexit import register
from time import sleep


class Daemon(object):
    """
    A generic daemon class.
    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def _test_pid_file(self):
        """Test if directory for pidfile is writable"""

        self._check_process_on_startup()
        if not path.isdir(path.dirname(self.pidfile)):
            try:
                mkdir(path.dirname(self.pidfile))
            except OSError as e:
                stderr.write("Startup failed: {errno} ({errmsg})\n".format(errno=e.errno, errmsg=e.strerror))
                exit(e.errno)
        else:
            try:
                mknod(self.pidfile)
                remove(self.pidfile)
            except OSError as e:
                stderr.write("Startup failed: {errno} ({errmsg})\n".format(errno=e.errno, errmsg=e.strerror))
                exit(e.errno)

    def _check_process_on_startup(self):
        """Check whether process with PID from pidfile exists in the system"""

        try:
            Process(self.get_pid()).is_running()
        except NoSuchProcess:
            self.delpid()

    def daemonize(self):
        """
        Do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """

        try:
            pid = fork()
            if pid > 0:
                # exit first parent
                exit(0)
        except OSError as e:
            stderr.write("fork #1 failed: {errno} ({errmsg})\n".format(errno=e.errno, errmsg=e.strerror))
            exit(e.errno)

        # decouple from parent environment
        chdir("/")
        setsid()
        umask(0)

        # do second fork
        try:
            pid = fork()
            if pid > 0:
                # exit from second parent
                exit(0)
        except OSError as e:
            stderr.write("fork #2 failed: {errno} ({errmsg})\n".format(errno=e.errno, errmsg=e.strerror))
            exit(e.errno)

        # redirect standard file descriptors
        stdout.flush()
        stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)

        dup2(si.fileno(), stdin.fileno())
        dup2(so.fileno(), stdout.fileno())
        dup2(se.fileno(), stderr.fileno())

        # write pidfile
        register(self.delpid)
        pid = str(getpid())

        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        """Delete pidfile"""

        remove(self.pidfile)

    def start(self):
        """Start the daemon"""

        # Check for a pidfile to see if the daemon already runs
        self._test_pid_file()
        pid = self.get_pid()

        if pid:
            message = "pidfile {pid} already exist. Daemon already running?\n"
            stderr.write(message.format(pid=self.pidfile))
            self._check_process_on_startup()
            exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon"""

        # Get the pid from the pidfile
        pid = self.get_pid()

        if not pid:
            message = "pidfile {pid} does not exist. Daemon not running?\n"
            stderr.write(message.format(pid=self.pidfile))
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                kill(pid, SIGTERM)
                sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if path.exists(self.pidfile):
                    remove(self.pidfile)
            else:
                stderr.write(str(err))
                exit(1)

    def restart(self):
        """Restart the daemon"""

        pid = self.get_pid()
        if pid:
            stdout.write("Restarting process with pid: {}\n".format(pid))
        self.stop()
        self.start()

    def reload(self):
        """Reload daemon's config
        You need to implement reload config function on your own
        This function actually just send SIGHUP (kill -1) to a process
        with PID from pidfile
        """

        pid = self.get_pid()
        if not pid:
            message = "pidfile {pid} does not exist. Daemon not running?\n"
            stderr.write(message.format(pid=self.pidfile))
            exit(1)  # Nothing to reload. Exiting

        try:
            if pid > 0:
                stdout.write("Reloading process with pid: {} with sending SIGHUP signal\n".format(pid))
                kill(pid, 1)
        except OSError as err:
            print(err.strerror)
            exit(1)

    def get_pid(self):
        """Return pid of the running process"""

        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        return pid

    @staticmethod
    def get_info_template():
        return {"pid": "", "start_time": "", "binary": "", "status": "",
                "cpu_times": namedtuple('pcputimes', ['user', 'system']),
                "memory_info": namedtuple('pmem', ['rss', 'vms']), "cpu_percent": ""}

    def get_proc_info(self):
        """Return info about the daemon process for status method"""

        info = self.get_info_template()
        info['cpu_times'].user = 0.0
        info['cpu_times'].system = 0.0
        info['memory_info'].rss = 0
        info['memory_info'].vms = 0
        info['pid'] = self.get_pid()

        if info['pid']:
            try:
                proc = Process(info['pid'])
                proc_info = proc.as_dict(attrs=[
                    'status',
                    'exe',
                    'username',
                    'create_time',
                    'cmdline',
                    'cpu_times',
                    'cpu_percent',
                    'memory_info'
                ])
                info['start_time'] = datetime.fromtimestamp(
                    proc_info['create_time']).strftime("%Y-%m-%d %H:%M:%S")
                info['binary'] = proc_info['exe']
                info['status'] = "Running/" + proc_info['status'].capitalize()
                info['cpu_times'] = proc_info['cpu_times']
                info['memory_info'] = proc_info['memory_info']
                info['cpu_percent'] = proc_info['cpu_percent']
            except NoSuchProcess:
                info['pid'] = ""
                info['status'] = "Stopped/Not running"
                pass
            except KeyError:
                pass
        else:
            info['pid'] = ""
            info['status'] = "Stopped/Not running"

        return info

    def status(self):
        """Get the daemon status info string"""

        proc_info = self.get_proc_info()

        status_info = """
        SCRIPT:\t\t{name}
        BINARY:\t\t{bin}
        PID:\t\t{pid}
        PID_FILE:\t{pid_file}
        STDOUT:\t\t{out}
        STDERR:\t\t{err}
        STATE:\t\t{state}
        CPU_TIMES:\tuser: {user}/system: {system}
        CPU_PERCENT:\t{percent}
        MEMORY USAGE:\tresident: {resident} kB/virtual: {virtual} kB
        STARTED AT:\t{start_time}
        """.format(name=path.realpath(argv[0]),
                   bin=proc_info['binary'],
                   pid=proc_info['pid'],
                   pid_file=self.pidfile,
                   out=self.stdout,
                   err=self.stderr,
                   state=proc_info['status'],
                   user=proc_info['cpu_times'].user,
                   system=proc_info['cpu_times'].system,
                   percent=proc_info['cpu_percent'],
                   resident=proc_info['memory_info'].rss/1024,
                   virtual=proc_info['memory_info'].vms/1024,
                   start_time=proc_info['start_time'])
        return status_info

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been daemonized by start() or restart().
        """
