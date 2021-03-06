import gtk
import glib

from snaked.util import refresh_gui

console_widget = []

class Escape(object): pass

def get_console_widget(editor):
    try:
        return console_widget[0]
    except IndexError:
        pass

    w = create_console_widget()
    console_widget.append(w)

    editor.add_widget_to_stack(w, on_console_popup)
    return w

def create_console_widget():
    panel = gtk.ScrolledWindow()
    panel.set_border_width(5)
    panel.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

    panel.view = gtk.TextView()
    panel.view.set_editable(False)
    panel.view.set_buffer(gtk.TextBuffer())
    panel.add(panel.view)
    panel.view.show()

    return panel

def toggle_console(editor):
    console = get_console_widget(editor)

    if console.props.visible:
        console.hide()
        editor.view.grab_focus()
    else:
        editor.popup_widget(console)

def hide(editor, widget, escape):
    widget.hide()
    editor.view.grab_focus()

def on_console_popup(widget, editor):
    widget.escape = Escape()
    editor.push_escape(hide, widget, widget.escape)

def unblock_fd(fd):
    import fcntl, os
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

def consume_output(editor, proc, on_finish):
    console = get_console_widget(editor)
    buf = console.view.get_buffer()
    buf.delete(*buf.get_bounds())
    unblock_fd(proc.stdout)
    unblock_fd(proc.stderr)
    glib.io_add_watch(proc.stdout, glib.IO_IN|glib.IO_ERR|glib.IO_HUP,
        consume_io, editor, console, proc, on_finish)
    glib.io_add_watch(proc.stderr, glib.IO_IN|glib.IO_ERR|glib.IO_HUP,
        consume_io, editor, console, proc, on_finish)

def consume_io(f, cond, editor, console, proc, on_finish):
    data = f.read()
    if data:
        if not console.props.visible:
            editor.popup_widget(console)

        buf = console.view.get_buffer()
        iter = buf.get_bounds()[1]
        buf.insert(iter, data)
        buf.place_cursor(buf.get_bounds()[1])
        console.view.scroll_mark_onscreen(buf.get_insert())

    if proc.poll() is not None:
        if not getattr(proc, 'consume_done', False):
            proc.consume_done = True
            on_finish()
        return False

    return True