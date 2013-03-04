import subprocess
import shutil
import shlex
import os, os.path
import fcntl
from threading import Thread

class SubprocessError(Exception): pass
class SubProcess(object):
    def __init__(self, cmd, shell=False,
                 cwd=os.path.curdir,
                 stdin=subprocess.PIPE,
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,
                 post_exec=str,
                 post_exec_args=[],
                 **kwargs):
        self.stdout = ''
        self.stderr = ''
        self.alive = True
        self.post_exec = post_exec
        self.post_exec_args = post_exec_args

        if not cmd:
            raise SubprocessError('Command argument requred')

        if isinstance(cmd, str):
            self.cmd = shlex.split(cmd)
        elif isinstance(cmd, list) or isinstance(cmd, tuple):
            self.cmd = cmd
        else:
            raise SubprocessError('Command must be string or list')

        self.pipe = subprocess.Popen(self.cmd, stdin=stdin, stderr=stderr, stdout=stdout, shell=False, cwd=cwd, **kwargs)

        self.thread_stdout = Thread(target=self._stdout_stream_reader_worker)
        self.thread_stdout.daemon = True
        self.thread_stdout.start()

        self.thread_stderr = Thread(target=self._stderr_stream_reader_worker)
        self.thread_stderr.daemon = True
        self.thread_stderr.start()

        self.thread_exitWaiter = Thread(target=self._exit_waiter)
        self.thread_exitWaiter.daemon = True
        self.thread_exitWaiter.start()

    def _exit_waiter(self):
        self.pipe.wait()
        self.alive = False
        self.post_exec(*self.post_exec_args)
        self._del()

    def _stdout_stream_reader_worker(self):
        while self.alive:
            fd = self.pipe.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)

            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            try:
                self.stdout += self.pipe.stdout.read()
            except:
                pass

    def _stderr_stream_reader_worker(self):
        while self.alive:
            fd = self.pipe.stderr.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)

            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            try:
                self.stdout += self.pipe.stderr.read()
            except:
                pass

    def _del(self):
        self.alive = False
        try:
            self.pipe
        except:
            return

        if self.pipe.poll():
            try:
                self.pipe.kill()
            except Exception, e:
                print('Killing process failed: %s' % str(e))

    def __del__(self):
        return self._del()

class TestSubProcess(object):
    def setUp(self):
        self.multiplier = 1
    def test_01_null_argument(self):
        """ Testing None command """
        try:
            SubProcess(None)
        except SubprocessError:
            pass
    def test_02_converting_cmd(self):
        ''' Test "ls -alh" as string '''
        SubProcess('ls -alh .')
    def test_03_list_cmd(self):
        ''' Test ('ls', '-alh', '.') as tuple '''
        SubProcess(('ls', '-alh', '.'))
    def test_04_stdin(self):
        """ Test stgin and stdout with 'cat'"""
        prc = SubProcess('cat')
        test_text = [
            '123\n',
            'text\n',
            'ololo\n',
        ]
        prc.pipe.stdin.write(''.join(test_text))
        from time import sleep
        sleep(1)
        assert prc.stdout == ''.join(test_text)
