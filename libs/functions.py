from .config import VirtuiConfig

import sys, os
import shlex
import subprocess

def _null_file(mode='r'):
    return open('/dev/null', mode)

def _new_groupid():
    os.setpgid(os.getpid(), os.getpid())

def __join_command(command):
    return " ".join([
        "'%s'" % x.replace("\\", "\\\\").replace("'", "\\'") for x in command])

def run_command(command, terminal=False, terminal_title=''):
    if terminal:
        terminal_command = shlex.split(VirtuiConfig.general('terminal_command'))
        try:
            index = terminal_command.index('%(command_list)s')
            terminal_command[index:index+1] = command
            command = terminal_command
        except ValueError:
            pass
        final_substitutions = {
            'command' : __join_command(command),
            'title' : terminal_title,
        }
        try:
            command = [arg % final_substitutions for arg in command]
        except KeyError:
            print >>sys.stderr, "Failed to substitute some portions of command: %s" % str(command)

    subprocess.Popen(command,
                     stdin=_null_file(),
                     stdout=_null_file('w'),
                     stderr=_null_file('w'),
                     preexec_fn=_new_groupid)
