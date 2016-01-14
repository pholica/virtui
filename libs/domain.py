#!/bin/env python2

import libvirt
import libxml2

def _first_or_None(l):
    try:
        return l[0]
    except IndexError:
        return None

class Domain(object):
    _domain = None
    _name = None

    def __init__(self, domain):
        super(Domain, self).__init__()
        self._domain = domain
        self._name = domain.name()

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return not self.__ne__(other)

    def __ne__(self, other):
        if type(self) != type(other):
            return False
        return self._domain == other._domain

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
            if self.isActive():
                self._domain.updateDeviceFlags(xml, libvirt.VIR_DOMAIN_DEVICE_MODIFY_LIVE)
            else:
                self._domain.updateDeviceFlags(xml)
            return True
        except libvirt.libvirtError as e:
            print "Couldn't change/eject CD. Libvirt error: %s" % e.get_error_message()
            return False

    def remove(self):
        self._domain.undefine()
        self._domain = None
        self._name = None

    def short_status(self):
        # REMOVE IN FUTURE
        pass

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
