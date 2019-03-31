#!/usr/bin/env python3
import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gio
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GLib

class ClipboardProducer(Gtk.Application):
    '''
    Producer class. Requires an instantiated consumer function object as parameter.
    Instantiate the producer, and begin producing via object.run() method
    '''
    def __init__(self,consumer):
        Gtk.Application.__init__(self,
                                 application_id="indicator-bulletin.sergkolo.com.github",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.clipboard = Gtk.Clipboard().get(Gdk.SELECTION_CLIPBOARD)
        self.clipboard.connect('owner-change', self.callback)

        # Prepare the consumer
        self.consumer = consumer
        self.consumer.send(None)
       
        self.last_data = None
    
    def do_activate(self):
        self.mainloop = GLib.MainLoop()
        self.mainloop.run()

    def callback(*args):
        print('>>> Callback:')
        print(args)
        args[0].__next__()

    def __next__(self):
        data = self.clipboard.wait_for_targets()
        self.consumer.send((self.clipboard, data))
