#!/bin/env python2

import logging
import os
import curses

from ConfigParser import RawConfigParser

logger = logging.getLogger("virtui_curses")

def _config_init(method):
    def wrapped(*args, **kwargs):
        if VirtuiConfig._options == None:
            VirtuiConfig.loadconfig()
        return method(*args, **kwargs)
    return wrapped

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
                'helpers_path' : os.path.join(os.path.dirname(__file__), 'helpers'),
            },
            'helpers' : {
            },
            'key bindings' : {
                'q' : "quit",
                'KEY_RESIZE' : "window resized",
                'KEY_UP' : "select previous",
                'KEY_DOWN' : "select next",
                'u' : "power on",
                'd' : "power off",
                'r' : "reset",
                'c' : "open console",
                'v' : "open viewer",
                # 0-9 - don't know how to handle this
            },
            'colors' : {
                'foreground' : 'COLOR_CYAN',
                'domain_active' : 'COLOR_GREEN',
                'domain_inactive' : 'COLOR_RED',
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
        new_key_bindings = {}
        for key, value in VirtuiConfig._options['key bindings'].iteritems():
            if len(key) == 1:
                new_key_bindings[ord(key)] = value
            elif key.startswith("KEY_"):
                try:
                    new_key_bindings[getattr(curses, key)] = value
                except:
                    logger.warn("Wrong name of key in config: %s", key)
            else:
                logger.warn("Unknown name of key in config: %s", key)
        VirtuiConfig._options['key bindings'] = new_key_bindings
        new_colors = {}
        for key, value in VirtuiConfig._options['colors'].iteritems():
            if value.startswith('COLOR_'):
                try:
                    new_colors[key] = getattr(curses, value)
                except:
                    logger.warn("Wrong name of color in config: %s", value)
            else:
                try:
                    new_colors[key] = int(value)
                except ValueError:
                    logger.warn("Unknown name of color in config: %s", value)
        VirtuiConfig._options['colors'] = new_colors

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
    def key_bindings(name):
        try:
            return VirtuiConfig._options['key bindings'][name]
        except KeyError:
            pass

    @staticmethod
    @_config_init
    def colors(name):
        try:
            return VirtuiConfig._options['colors'][name]
        except KeyError:
            pass

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
