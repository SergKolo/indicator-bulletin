from gi.repository import Gtk,Gdk,GLib

class clip(object):
    def __init__(self,*args):
        self.clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        #self.clip.request_uris(self.uri_callback,None)
        #self.clip.request_targets(self.callback,None)
        #self.sel = self.clip.wait_for_contents()
        #print(ddself.clip.wait_for_targets())

    def __iter__(self):
        return self

    def __next__(self):
            yield ( self.clip.wait_for_uris(),
                    self.clip.wait_for_text(),
                    self.clip.wait_for_image() )



#    def uri_callback(self,*args):
#        print("URICALLBACK",args)
#
#
#    def img_callback(self,*args):
#        print("IMGCALLBACK",args)
#
#    def __enter__(self,*args):
#        print("Enter:",args)
#        return self
#    #def callback(self,clipboard,atoms,*data):
#    def callback(self,clipboard,sel_data,*data):
#        print("callback")
#        #print(sel_data.get_data_type(),sel_data.get_data())
#        print("/************/")
#
#
##    def poll(self):
##        print("Polling")
##        self.clip.request_image(self.img_callback,None)
##        self.clip.request_uris(self.uri_callback,None)
#    def poll(self):
#        print(self.clip.wait_for_contents(Gdk.TARGET_DRAWABLE))
#        print("URI:",self.clip.wait_for_uris())
#        print("TEXT:",self.clip.wait_for_text())
#        print("IMG:",self.clip.wait_for_image(),self.clip.wait_is_image_available())
#
#        img = self.clip.wait_for_image()
#        if img:
#           print(img.get_options())
#        #self.clip.request_targets(self.printstuff,None)
#        
#    def write(self,text):
#        self.clip.set_text(text,-1)
#        # keeps the text after application exits
#        self.clip.store()
#    def __exit__(self,*args):
#        pass

class testwindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self,title="clip")
        self.add(Gtk.Label("foobar label"))

#        self.clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
#        self.clip.connect('owner-change',self.handler)
#        #self.poll()
#   
#    def handler(self,clip,event):
#        print("Handler:",event)
#   
#    def poll(self):
#        while True:
#            self.clip.request_uris(self.uri_callback,None)
#
#    def uri_callback(self,*args):
#        print("I'm callback:",args)
#

#    def poll(self,*args):
#        from time import sleep
#        while True:
#            with clip("FOOBAR") as c:
#                 c.poll()
#                 sleep(2)
            #c.write("HELLO WORLD")

t = testwindow()
t.show_all()
#t.poll()
# make glib, then wire it up

def consume():
    while True:
        data = yield
        print("Consumed:",data)

consumer = consume()
consumer.send(None)
producer = clip()
while True:
    val = next(producer)
    print(val)
    consumer.send(val)
    
#clipgen = clip()
#for i in clipgen:
#    print(next(i))

ml = GLib.MainLoop()
t.connect("destroy",lambda x: ml.quit())
ml.run()
