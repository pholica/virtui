#!/bin/env python2

import logging

__all__  = ["config", "connection", "domain", "events"]

logger = logging.getLogger("virtui_curses")
logger.addHandler(logging.NullHandler())
