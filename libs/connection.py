#!/bin/env python2

from .domain import Domain
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
