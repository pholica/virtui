#!/bin/env python2

from .domain import Domain
from . import logger
import libvirt

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

    def registerDomainEventHandler(self, cb, opaque):
        logger.error('Registered Domain event Handler')
        return self._conn.domainEventRegister(cb, opaque)

    def registerCloseHandler(self, cb, opaque):
        return self._conn.registerCloseCallback(cb, opaque)

    def registerAnyEventHandler(self, fd, events, cb, opaque):
        return self._conn.domainEventRegisterAny(fd, events, cb, opaque)

    def setKeepAlive(self, interval, count):
        return self._conn.setKeepAlive(interval, count)

    # virEventRegisterDefaultImpl
    # virEventRunDefaultImpl
