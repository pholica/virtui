#!/bin/env python2

from . import logger
import threading
import libvirt

class Event(object):
    def __init__(self, event_type, *args, **kwargs):
        if event_type != "tick":
            logger.debug("Event created: '%s' with args: '%s' and kwargs: '%s'",
                         event_type, repr(args), repr(kwargs))
        self.event_type = event_type
        self.args = args
        self.kwargs = kwargs

class LibvirtEventThread(threading.Thread):
    def __init__(self, events):
        super(LibvirtEventThread, self).__init__()
        self.event = events
        self.daemon = True
        self.ended = False
        libvirt.virEventRegisterDefaultImpl()

    def register_for_connection(self, connection):
        connection.registerCloseHandler(self.close_event, None)
        connection.registerDomainEventHandler(self.handle_event, None)
        connection.setKeepAlive(5, 3)        
        
    def run(self):
        logger.debug("LibvirtEvent Thread started")
        while not self.ended:
            if libvirt.virEventRunDefaultImpl() < 0:
                logger.error("virEventRunDefaultImpl failed")
        logger.debug("LibvirtEvent Thread finished")

    def stop(self):
        self.ended = True

    def close_event(self, conn, reason, opaque):
        logger.error("Libvirt connection closed!")
        
    def handle_event(self, conn, dom, event, detail, opaque):
        logger.debug("Libvirt event: '%s' for domain: '%s' detail: %s",
                     event, dom, detail)
