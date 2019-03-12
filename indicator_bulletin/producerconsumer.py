from gi.repository import Gtk,Gio,GLib,Gdk
from hashlib import md5

def produce(consumer):
    clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    while True:
       img = clip.wait_for_image()
       img_ret = None
       if img:
          img_ret = md5(img.get_pixels()).digest()
       data = ( clip.wait_for_uris(),
                clip.wait_for_text(),
                 img_ret)
       print("Producing")
       consumer.send(data)
       yield

def consume():
    cache = None
    while True:
        data = yield
        if cache != data:
            print('Consumed:',data,cache)
        cache = data
        yield

def poll():
    from time import sleep
    cons = consume()
    cons.send(None)
    prod = produce(cons)
    while True:
        next(prod)
        sleep(1)

if __name__ == '__main__':        
    poll()
    ml = GLib.MainLoop()
    ml.run()
