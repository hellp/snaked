import gtk
import weakref
from gobject import timeout_add

class FeedbackPopup(object):
    def __init__(self, view):
        self.view = weakref.ref(view)

        self.bar = gtk.EventBox()

        box = gtk.EventBox()
        box.set_border_width(5)
        
        self.label = gtk.Label()
        box.add(self.label)
        box.show_all()
        
        self.bar.add(box)
    
        view.add_child_in_window(self.bar, gtk.TEXT_WINDOW_TEXT, 0, 0)
    
    def show(self, text, timeout=1500):
        self.label.set_text(u'  '+ text + u'  ')
        
        x, y, w, h, d = self.view().get_window(gtk.TEXT_WINDOW_TEXT).get_geometry()
        sw, sh = self.bar.size_request()
        x, y = w - sw, h - sh        
        self.view().move_child(self.bar, x, y) 
        self.bar.show()
        
        timeout_add(timeout, self.hide)

    def hide(self):
        self.bar.hide()
        return False