#!/bin/env python2

import sys, os
import copy
import libvirt
import libxml2
import subprocess, shlex
from ConfigParser import RawConfigParser

def _config_init(method):
    def wrapped(*args, **kwargs):
        if VirtuiConfig._options == None:
            VirtuiConfig.loadconfig()
        return method(*args, **kwargs)
    return wrapped

def _none_to_empty(value):
    if value is None:
        return ''
    return value

def _enable_helper(helper_name):
    # FIXME: Create documentation for helpers
    # Basic idea is, that user data is on stdout and data for virtui are passed
    # via stderr.
    def helper_decorator(funct):
        def wrapped(*args, **kwargs):
            helper = VirtuiConfig.helper(helper_name)
            if helper == None:
                return funct(*args, **kwargs)
            env = copy.copy(os.environ)
            for (key, value) in kwargs.iteritems():
                env["VIRUTI_%s" % key] = _none_to_empty(value)
            # Change all None arguments to empty strings
            args = map(_none_to_empty, args)
            # FIXME: Command may not be executed, check!
            proc = subprocess.Popen([helper] + list(args), stderr=subprocess.PIPE, env=env)
            stdout, stderr = proc.communicate()
            if proc.returncode == 0:
                return stderr
            return None
        return wrapped
    return helper_decorator

def _first_or_None(l):
    try:
        return l[0]
    except IndexError:
        return None

def _new_groupid():
    os.setpgid(os.getpid(), os.getpid())

def _change_terminal_title(title):
    sys.stdout.write("\033]0;%s\007" % title)
    sys.stdout.flush()

class VirtuiConfig(object):
    _options = None

    @staticmethod
    def _default():
        return {
            'general' : {
                'virtui_terminal_title' : 'virtui',
                'LIBVIRT_URI' : "qemu:///system",
                'viewer' : 'virt-viewer --connect %(LIBVIRT_URI)s %(domain_name)s',
                'viewer_terminal' : False,
                'vnc' : 'vncviewer %(hostname)s:%(port)d',
                'vnc_terminal' : False,
                'ssh' : 'ssh %(user)s@%(hostname)s',
                'ssh_terminal' : True,
                'console' : 'virsh --connect %(LIBVIRT_URI)s console %(domain_name)s',
                'console_terminal' : True,
                'terminal_command' : 'xterm -T %(title)s -e %(command_list)s',
                'domain_list_format' : '{name}\t{on} {ips}',
                'domain_on_format' : '[ON] ',
                'domain_off_format' : '[OFF]',
            },
            'helpers' : {
            },
            'template-simple' : {
                'virt-type' : 'kvm',
                'arch' : None,
                'machine' : None,
                'vcpus' : '1',
                'cpu' : 'host',
                'name' : 'template-test',
                'memory' : '2G',
                'display0_type' : 'spice', # none, spice, vnc
                'display0_listen' : None, # vnc
                'display0_port' : None, # spice, vnc
                'display0_password' : None, # vnc
                'serial0' : 'pty', # pty, dev, file, pipe, tcp, udp, unix
                'serial0_path' : None, # dev, file, pipe, unix
                'serial0_host' : None, # tcp, udp
                'serial0_port' : None, # tcp, udp
                'serial0_mode' : None, # tcp, unix
                'serial0_protocol' : None, # tcp
                'serial0_bind_host' : None, # udp
                'serial0_bind_port' : None, # udp
                'channel' : None, # TODO
                # redirdev, tpm, rng, panic
                'disk0_size' : '10G',
                'disk0_name' : 'template-test.img',
                'disk0_format' : 'qcow2',
                'disk0_driver' : 'virtio',
                'disk0_serial' : None,
                'disk0_readonly' : 'False',
                'cdrom0' : 'empty',
                'nic0_model' : 'virtio',
                'nic0_network' : 'default',
                'nic0_mac' : None,
                'install' : 'url', # url, pxe, cdrom, none
                'install_url' : 'http://download.fedoraproject.org/pub/fedora/linux/releases/20/Fedora/x86_64/os/',
                'install_commandline' : None, # url
                'initrd_inject' : None, # url: puts file from path to obtained initrd
                'os-variant' : 'none',
                'boot' : 'cdrom,network,hd,menu=on,useserial=on',
                'reboot' : 'False',
                'wait' : None,
                'helper' : None,
            }
        }


    @staticmethod
    def _configfile(configfile):
        parser = RawConfigParser()
        parser.read(os.path.expanduser(configfile))
        # make two dimentional dict from config file
        return dict([(section, dict(parser.items(section))) for section in parser.sections()])

    @staticmethod
    def _env():
        overrides = {}
        for key in VirtuiConfig._options['general'].keys():
            if key.upper() in os.environ:
                overrides[key] = os.environ[key.upper()]
        return {'general' : overrides}

    @staticmethod
    def _options_update(updates):
        for (key, section) in updates.iteritems():
            for (name, value) in section.iteritems():
                VirtuiConfig._options[key][name] = value

    @staticmethod
    def loadconfig(configfile=None, overrides=None, load_env=False):
        if overrides is None:
            overrides = {}
        VirtuiConfig._options = VirtuiConfig._default()
        if configfile is not None:
            VirtuiConfig._options_update(VirtuiConfig._configfile(configfile))
        if load_env:
            VirtuiConfig._options_update(VirtuiConfig._env())
        VirtuiConfig._options_update(overrides)

    @staticmethod
    @_config_init
    def general(option, overrides=None):
        # FIXME: Need cleanup together with helper
        try:
            value = VirtuiConfig._options['general'][option]
        except KeyError:
            return None
        try:
            if isinstance(value, str):
                replacements = dict()
                replacements.update(VirtuiConfig._options['general'])
                if overrides is not None:
                    replacements.update(overrides)
                value %= replacements
        except KeyError:
            pass
        return value

    @staticmethod
    @_config_init
    def helper(name, overrides=None):
        # FIXME: Need cleanup together with general
        try:
            value = VirtuiConfig._options['helpers'][name]
        except KeyError:
            return None
        try:
            if isinstance(value, str):
                replacements = dict()
                replacements.update(VirtuiConfig._options['general'])
                if overrides is not None:
                    replacements.update(overrides)
                value %= replacements
        except KeyError:
            pass
        return value

    @staticmethod
    @_config_init
    def templates():
        for key in VirtuiConfig._options.keys():
            if key.startswith('template-'):
                yield key.replace('template-', '', 1)

    @staticmethod
    @_config_init
    def template(name):
        return VirtuiConfig._options['template-%s' % name]

class Connection(object):
    _conn = None

    def __init__(self, URI="qemu:///system"):
        super(Connection, self).__init__()
        self._conn = libvirt.open(URI)

    def domains(self, inactive=False):
        domains = [Domain(dom) for dom in self._conn.listAllDomains()]
        if not inactive:
            domains = [dom for dom in  domains if dom.isActive()]
        return domains


class Domain(object):
    _domain = None
    _name = None

    def __init__(self, domain):
        super(Domain, self).__init__()
        self._domain = domain
        self._name = domain.name()

    def isActive(self):
        return bool(self._domain.isActive())

    def isOnline(self):
        if not self.isActive():
            return False
        for nic in self.nics:
            if nic[1] != None:
                return True
        return False

    def actions(self):
        if self.isActive():
            return [
                ('shutdown', self.shutdown),
                ('kill', self.stop),
                ('reboot', self.reboot),
                ('reset', self.reset),
            ]
        else:
            return [
                ('start', self.start),
            ]

    # power button or wakeup
    def start(self):
        self._domain.create()

    # force stop
    def stop(self):
        self._domain.destroy()

    # ACPI reset signal
    def reboot(self):
        self._domain.reboot()

    # reset button
    def reset(self):
        self._domain.reset()

    # suspend - memory remains on host
    def suspend(self):
        self._domain.suspend()

    # wakeup
    def resume(self):
        self._domain.resume()

    # power button
    def shutdown(self):
        self._domain.shutdown()

    def cdrom_image(self, device):
        medias = "//devices/disk[target/@dev='%s']/source/@dev" % device
        return _first_or_None(self._query_xml(medias))

    def change_cdrom(self, device, image):
        if image is None:
            xml = """<disk type='block' device='cdrom'>
  <driver name='qemu' type='raw' />
  <target dev='%s' bus='ide' />
  <readonly />
</disk>""" % device
        else:
            xml = """<disk type='block' device='cdrom'>
  <driver name='qemu' type='raw' />
  <target dev='%s' bus='ide' />
  <source dev='%s' />
  <readonly />
</disk>""" % (device, image)
        try:
            self._domain.updateDeviceFlags(xml, libvirt.VIR_DOMAIN_DEVICE_MODIFY_LIVE)
            return True
        except libvirt.libvirtError:
            return False

    def remove(self):
        self._domain.undefine()
        self._domain = None
        self._name = None

    def short_status(self):
        """Function that returns status string that is appended in menu."""
        # variables containing status strings
        power = VirtuiConfig.general('domain_on_format') \
                if self.isActive() else VirtuiConfig.general('domain_off_format')
        iplist = ','.join([nic[1] for nic in self.nics if nic[1] != None])

        sts = VirtuiConfig.general('domain_list_format').format(name=self.name,
                                                                on=power,
                                                                ips=iplist)
        return sts

    @property
    def name(self):
        return self._name

    @property
    def macs(self):
        return self._query_xml("//devices/interface[@type='network']/mac/@address")

    @property
    def nics(self):
        retval = []
        arpcache = open('/proc/net/arp', 'r')
        for mac in self.macs:
            arpcache.seek(0)
            IP = None
            for line in arpcache:
                # 0x0 here means outdated entry, so don't use it
                if line.split()[3] == mac and line.split()[2] != "0x0":
                    IP = line.split()[0]
                    break
            retval.append((mac, IP))
        arpcache.close()
        return retval

    @property
    def cdroms(self):
        devices = "//devices/disk[@device='cdrom']/target/@dev"
        return [
            (dev, self.cdrom_image(dev))
            for dev in self._query_xml(devices)
        ]

    @property
    def xml(self):
        return self._domain.XMLDesc()

    def _query_xml(self, xpath):
        ctxt = libxml2.parseDoc(self.xml).xpathNewContext()
        return [x.content for x in ctxt.xpathEval(xpath)]

################################################################################

def main(args):
    ended = False
    VirtuiConfig.loadconfig('~/.virtui.conf')
    _change_terminal_title(VirtuiConfig.general('virtui_terminal_title'))
    conn = Connection(VirtuiConfig.general('LIBVIRT_URI'))
    while not ended:
        domain = select_domain(conn)
        if domain == None:
            ended = True
            break
        manage_domain(domain)

def __generate_options(options):
    """If options is dict object, transform to list of (key, value).
    If options is iterable of strings, return list containing (item, item).
    In other cases, return options unmodified (expecting, that options was
    already in correct form).
    """
    if isinstance(options, dict):
        return options.viewitems()
    if isinstance(options[0], str):
        return [(option, option) for option in options]
    return options

def select_option(options, header="Select option:", prompt="#? ", other_options=None):
    """Print options and prompt asking user to select one.
    options can be either list of strings or list of tuples.
    When options is list of strings, value of option is returned.
    When options is list of tuples, first item returned.
    When options is dict, key is returned.
    Can also specify other_options as tuples where first item is returned,
    and second item needs to be one-character long and can be selected by user.

    One can enter number => option of such index is selected.
    One can enter one character => other_option of such shortcut is selected.
    One can enter start of option => option itself is selected if there is only one option starting with it.
    """
    while True:
        num = 0
        print
        print header
        if other_options is not None:
            for (description, key) in other_options:
                print "{0}] {1}".format(key, description)
            print
        options = __generate_options(options)
        for (_, option) in options:
            num += 1
            print "{0}) {1}".format(num, option)
        try:
            input_data = raw_input(prompt)
            if input_data.isdigit():
                return options[int(input_data)-1][0]
            elif len(input_data) == 1 and other_options is not None:
                return [opt[0] for opt in other_options if opt[1] == input_data][0]
            else:
                candidates = [opt[1] 
                              for opt in options
                              if opt[1].startswith(input_data)]
                if len(candidates) > 1:
                    print "Possible candidates: %s" % candidates
                elif len(candidates) == 1:
                    return candidates[0]
                else:
                    print "No option beginning with '%s' found" % input_data

        except (IndexError, ValueError):
            pass
        except (EOFError, KeyboardInterrupt):
            print
            return None

@_enable_helper('select_file')
def select_file(header="Select file.", preset=None, prompt="path: "):
    """Print prompt asking user to select file.
    When user doesn't enter any file path, preset is returned.
    Keep asking until path of existing file is entered or EOF or SIGINT is
    received.
    """
    while True:
        print
        print header
        try:
            filepath = raw_input(prompt)
        except (EOFError, KeyboardInterrupt):
            print
            return None
        if filepath == "":
            return preset
        if os.path.exists(filepath):
            return filepath
        print "File not found!"

def select_domain(conn):
    domains = conn.domains(inactive=True)
    menuitems = sorted([(dom.name, dom.short_status()) for dom in domains])
    selected = select_option(
        menuitems,
        "Select domain:",
        other_options=(('reload', 'r'),),
    )
    if selected == None:
        return None
    if selected == 'reload':
        return select_domain(conn)
    return [dom for dom in domains if dom.name == selected][0]

def select_cdrom(domain):
    if len(domain.cdroms) == 0:
        return None
    if len(domain.cdroms) == 1:
        return domain.cdroms[0][0]
    else:
        options = [
            (dev, '%s (%s)' % (dev, path))
            for dev, path in domain.cdroms
        ]
        return select_option(options, "Select cdrom:")

def manage_domain(domain):
    actions = []
    info = domain_info(domain)
    if domain.isActive():
        actions += [
            ('console', lambda: start_console(domain)),
            ('viewer', lambda: start_viewer(domain)),
        ]
        if domain.cdroms:
            actions += [
                ('change CD/DVD', lambda: manage_cdrom(domain)),
            ]
        if domain.isOnline():
            actions += [
                ('ssh', lambda: start_ssh(domain)),
                ('vnc', lambda: start_vnc(domain)),
            ]
    actions += domain.actions()
    print """Domain: {name}
Online: {online}
Running: {active}
Nics and IPs:""".format(**info)
    for (mac, IP) in domain.nics:
        if IP is None:
            IP = 'N/A'
        print "%s\t%s" % (mac, IP)
    action = select_option([a[0] for a in actions],
                           "%s actions:" % domain.name)
    actions = dict(actions) # we don't care about order anymore
    if action is None:
        return
    elif actions[action] != None:
        actions[action]()
    else:
        print 'Unhandled action: %s' % action

def manage_cdrom(domain):
    cdrom = select_cdrom(domain)
    header = '%s cdrom %s (%s) action:' % (
        domain.name,
        cdrom,
        domain.cdrom_image(cdrom)
    )
    action = select_option(['eject', 'change'], header)
    if action == None:
        return
    elif action == 'eject':
        domain.change_cdrom(cdrom, None)
    else:
        image = select_file("Select image for %s cdrom %s" %
                            (domain.name, cdrom), domain.cdrom_image(cdrom))
        if image is None:
            return
        domain.change_cdrom(cdrom, image)

def domain_info(domain):
    return {
        "name" : domain.name,
        "active" : domain.isActive(),
        "online" : domain.isOnline(),
        "macs" : domain.macs,
        }

def __join_command(command):
    return " ".join(
        [
        "'%s'" % x.replace("\\", "\\\\").replace("'", "\\'") for x in command
        ]
    )

def _run_command(command, terminal=False, terminal_title=''):
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
                     preexec_fn=_new_groupid,
    )


def start_console(domain):
    replacement = {'domain_name' : domain.name}
    cmd = shlex.split(VirtuiConfig.general('console', replacement))
    _run_command(cmd, VirtuiConfig.general('console_terminal'), 'Console %s' % domain.name)

def start_viewer(domain):
    replacement = {'domain_name' : domain.name}
    cmd = shlex.split(VirtuiConfig.general('viewer', replacement))
    _run_command(cmd, VirtuiConfig.general('viewer_terminal'), 'Viewer %s' % domain.name)

def start_ssh(domain):
    IPs = [IP[1] for IP in domain.nics]
    if len(IPs) == 0:
        print "No network connection on host %s" % domain.name
        return
    if len(IPs) > 1:
        IP = select_option(IPs)
    else:
        IP = IPs[0]
    replacement = {
        'user' : 'root',
        'hostname' : IP,
    }
    cmd = shlex.split(VirtuiConfig.general('ssh', replacement))
    _run_command(cmd, VirtuiConfig.general('ssh_terminal'), 'SSH %s' % domain.name,)

def start_vnc(domain):
    IPs = [IP[1] for IP in domain.nics]
    if len(IPs) == 0:
        print "No network connection on host %s" % domain.name
        return
    if len(IPs) > 1:
        IP = select_option(IPs)
    else:
        IP = IPs[0]
    replacement = {
        'hostname' : IP,
        'port' : 1,
    }
    cmd = shlex.split(VirtuiConfig.general('vnc', replacement))
    _run_command(cmd, VirtuiConfig.general('vnc_terminal'), 'Vncviewer %s' % domain.name)

def _null_file(mode='r'):
    return file('/dev/null', mode)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
