#!/bin/env python2

import Queue
import threading
import collections
import curses

import logging

from math import ceil

from libs import connection

logger = logging.getLogger("virtui_curses")
logger.addHandler(logging.NullHandler())

class Event(object):
    def __init__(self, event_type, *args, **kwargs):
        if event_type != "tick":
            logger.debug("Event created: '%s' with args: '%s' and kwargs: '%s'",
                         event_type, repr(args), repr(kwargs))
        self.event_type = event_type
        self.args = args
        self.kwargs = kwargs

class Ticker(threading.Thread):
    def __init__(self, interval, events):
        super(Ticker, self).__init__()
        self.interval = interval
        self.events = events
        self.daemon = True

    def run(self):
        from time import sleep
        while True:
            sleep(self.interval)
            self.events.put(Event("tick"))
        
class UI(object):
    def __init__(self, events, stdscr, log = False):
        super(UI, self).__init__()
        self.ended = False
        self.events = events
        self.stdscr = stdscr
        self.log = log
        self.items = []
        self.current = None
        self.__handlers = {}
        self.__connection = connection.Connection()

        curses.curs_set(0)
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i, i, -1)
        self.stdscr.clear()
        self.stdscr.nodelay(1)
        self.windows = {
            "left" : stdscr.subwin(1, 1, 0, 0),
            "right" : stdscr.subwin(1, 1, 0, 0),
        }
        if self.log:
            self.windows["bottom"] = stdscr.subwin(1, 1, 0, 0)

        self.add_handlers()
        if self.log:
            logger.addHandler(self.loggingHandler(logging.WARN))
        self.events.put(Event("window resized"))
        self.events.put(Event("add", self.__connection.domains(True)))

    def __register_handler(self, event_type, func):
        self.__handlers[event_type] = func

    def __handle_event(self, event):
        events = None
        try:
            handler = self.__handlers[event.event_type]
        except KeyError:
            if event.event_type != "tick":
                logger.warn("Unhandled event: '%s', ignoring", event.event_type)
            return
        try:
            events = handler(*event.args, **event.kwargs)
        except TypeError as e:
            logger.error("Wrong event '%s' for handler: %s", event.event_type, e)
        if events is None:
            return
        if not isinstance(events, collections.Iterable):
            events = [events]
        for event in events:
            self.__handle_event(event)

    def loggingHandler(self, *args, **kwargs):
        ui = self
        events = self.events
        class LoggingHandler(logging.Handler):
            def __init__(self, level=None):
                if level is None:
                    super(LoggingHandler, self).__init__()
                else:
                    super(LoggingHandler, self).__init__(level)

            def emit(self, record):
                events.put(Event("log message", self.format(record)))

        return LoggingHandler(*args, **kwargs)

    def resize(self, event = None):
        height, width = self.stdscr.getmaxyx()
        self.stdscr.clear()
        if self.log:
            height -= 1
            self.windows["bottom"].resize(1, width)
            self.windows["bottom"].mvwin(height, 0)
        self.windows["left"].resize(height, width/2)
        self.windows["right"].resize(height, int(ceil(width/2.0)))
        self.windows["right"].mvwin(0, width/2)
        self.draw_items()

    def key_press(self, keycode):
        if keycode == ord('q'):
            return Event("quit")
        if keycode == curses.KEY_RESIZE:
            return Event("window resized")
        if keycode == curses.KEY_UP:
            return Event("select previous")
        if keycode == curses.KEY_DOWN:
            return Event("select next")
        if keycode >= ord('0') and keycode <= ord('9'):
            return Event("select", keycode - ord('0') - 1)
        try:
            logger.debug("Unhandled key press: '%d': '%s'", keycode, chr(keycode))
        except ValueError:
            logger.debug("Unhandled key press: '%d'", keycode)

    def show_message(self, message):
        window = self.windows["bottom"]
        window.clear()
        window.addnstr(0, 0, "LOG: " + message, window.getmaxyx()[1]-1)
        window.refresh()

    def add_handlers(self):
        self.__register_handler("quit", self.quit)
        self.__register_handler("select", self.select)
        self.__register_handler("select next", self.select_next)
        self.__register_handler("select previous", self.select_previous)
        self.__register_handler("selection changed", self.selection_changed)
        self.__register_handler("window resized", self.resize)
        self.__register_handler("log message", self.show_message)
        self.__register_handler("key press", self.key_press)
        self.__register_handler("add", self.add)
        
    def add(self, items):
        if not isinstance(items, collections.Iterable):
            items = [items]
        if len(items) == 0:
            return
        self.items += items
        self.draw_items()
        if self.current is None:
            self.current = 0
            self.events.put(Event("selection changed"))

    def remove(self, items):
        old = None
        if not isinstance(items, collections.Iterable):
            items = [items]
        for item in items:
            if self.current == self.items.index(item):
                if len(self.items) == 1:
                    if old is None:
                        old = self.current
                    self.current = None
                elif self.current == len(self.items) - 1:
                    if old is None:
                        old = self.current
                    self.current -= 1
            self.items.remove(item)
        if old is not None:
            self.events.put(Event("selection changed", old))

    def select(self, index):
        if index < 0 or index >= len(self.items):
            return
        if index == self.current:
            return
        old = self.current
        self.current = index
        self.events.put(Event("selection changed", old))

    def select_next(self):
        if self.current is None:
            return
        self.select(index=self.current+1)

    def select_previous(self):
        if self.current is None:
            return
        self.select(index=self.current-1)

    def selection_changed(self, old = None):
        if old is None:
            logger.debug("Set selection to %d", self.current)
        else:
            logger.debug("Changed selection from %d to %d", old, self.current)
            self.draw_item(old)
        self.draw_item(self.current)

    def quit(self):
        self.ended = True
        
    def draw_item(self, index):
        window = self.windows["left"]
        _, width = window.getmaxyx()
        format_string = "%%-2s %%-%ds" % (width - 5)
        attrs = curses.A_NORMAL
        if index == self.current:
            attrs = curses.A_REVERSE
        window.addstr(index+1, 1,
                      format_string % (index+1, str(self.items[index])),
                      attrs + curses.color_pair(curses.COLOR_CYAN))
        window.noutrefresh()

    def draw_items(self):
        window = self.windows["left"]
        window.erase()
        window.border()
        for i in range(len(self.items)):
            self.draw_item(i)

    def __readkeys(self):
        while True:
            char = self.stdscr.getch()
            if char == -1:
                break
            self.events.put(Event("key press", char))        

    def mainloop(self):
        Ticker(0.1, self.events).start()
        while not self.ended:
            self.__readkeys()
            try:
                event = self.events.get()
            except Queue.Empty:
                continue
            self.__handle_event(event)
            curses.doupdate()
            self.events.task_done()
        return 0
            
def main(stdscr):
    file_handler = logging.FileHandler("/tmp/watcher_debug", "w")
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    events = Queue.Queue()
    ui = UI(events, stdscr, True)
    return ui.mainloop()

if __name__ == "__main__":
    import sys
    sys.exit(curses.wrapper(main, *sys.argv[1:]))
