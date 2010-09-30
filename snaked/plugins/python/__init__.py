langs = ['python']

import gtk

from snaked.util import idle, refresh_gui
from snaked.signals import connect_external, connect_all

handlers = {}

def init(manager):
    manager.add_shortcut('python-goto-definition', 'F3', 'Python',
        'Navigates to python definition', goto_definition)

def editor_opened(editor):
    editor.connect('get-title', on_editor_get_title)
    idle(editor.update_title)
    
    h = EditorHandler(editor)
    handlers[editor] = h

def editor_closed(editor):
    try:
        handlers[editor].close()
        del handlers[editor]
    except KeyError:
        pass

def goto_definition(editor):
    try:
        h = handlers[editor]
    except KeyError:
        return
        
    h.goto_definition()

def on_editor_get_title(editor):
    if editor.uri.endswith('.py'):
        return get_python_title(editor.uri)
    
    return None

    
class EditorHandler(object):
    def __init__(self, editor):
        self.editor = editor
        idle(connect_all, self, view=editor.view)
        idle(self.init_completion) 

    def init_completion(self):
        provider = self.completion_provider
        self.editor.view.get_completion().add_provider(provider)
        
    def close(self):
        if hasattr(self, '__project'):
            self.__project.close()
        
    @property
    def project(self):
        try:
            return self.__project
        except AttributeError:
            root = self.editor.project_root
            if root:
                from rope.base.project import Project
                self.__project = Project(root)
            else:
                self.__project = None
                
            return self.__project
    
    @property
    def completion_provider(self):
        try:
            return self.__completion_provider
        except AttributeError:
            import complete
            self.__completion_provider = complete.RopeCompletionProvider(self)
            return self.__completion_provider

    def get_rope_resource(self, project, uri=None):
        from rope.base import libutils    
        uri = uri or self.editor.uri
        return libutils.path_to_resource(project, uri)

    def get_source_and_offset(self):
        offset = self.editor.cursor.get_offset()
        source = self.editor.text
        
        if not isinstance(source, unicode):
            source = source.decode('utf8')
        
        return source, offset

    def goto_line(self, editor, line):
        refresh_gui()
        edit = editor.buffer
        iterator = edit.get_iter_at_line(line - 1)
        edit.place_cursor(iterator)
        editor.view.scroll_to_iter(iterator, 0.001, use_align=True, xalign=1.0)

    def goto_definition(self):
        project = self.project
        if not project:
            project = getattr(self.editor, 'ropeproject', None)
            if not project:
                print "Can't find project path"
                return
        
        project.validate()
                 
        current_resource = self.get_rope_resource(project) 
        
        from rope.contrib import codeassist

        try:
            resource, line = codeassist.get_definition_location(
                project, *self.get_source_and_offset(),
                resource=current_resource)
        except Exception, e:
            import traceback
            traceback.print_exc()
            return
        
        if resource and resource.real_path == current_resource.real_path:
            resource = None
            
        if resource:
            uri = resource.real_path
            editor = self.editor.open_file(uri)
            editor.ropeproject = project 
            self.goto_line(editor, line)
        else:
            if line:
                self.goto_line(self.editor, line)
            else:
                print "Unknown definition"


    @connect_external('view', 'key-press-event')
    def on_textview_key_press_event(self, sender, event):
        if event.keyval != gtk.keysyms.Return:
            return False
            
        cursor = self.editor.cursor
        line_start = cursor.copy()
        line_start.set_line(line_start.get_line())
        
        text = line_start.get_text(cursor).strip()
        if text and text[-1] == ':':
            end = line_start.copy()
            end.forward_word_end()
            end.backward_word_start()
            ws = line_start.get_text(end)

            if self.editor.view.get_insert_spaces_instead_of_tabs():
                tab = u' ' * self.editor.view.get_tab_width()
            else:
                tab = u'\t'
                
            self.editor.buffer.begin_user_action()
            self.editor.buffer.insert(cursor, u'\n' + ws + tab)
            self.editor.buffer.end_user_action()
            return True
        
        return False

    @connect_external('view', 'backspace')
    def on_textview_backspace(self, *args):
        cursor = self.editor.cursor
        
        if cursor.starts_line():
            return False
        
        start = cursor.copy()
        start.set_line(start.get_line())
            
        text = start.get_text(cursor)
        
        if text.strip():
            return False
            
        delete_from = cursor.copy()
        if text[-1] == u'\t': 
            delete_from.backward_char()
        else:
            delete_from.backward_chars(self.editor.view.get_tab_width() - 1)
        
        if delete_from.get_line() != start.get_line():
            delete_from = start

        if delete_from.equal(start):
            delete_from.forward_char()

        self.editor.buffer.begin_user_action()
        self.editor.buffer.delete(delete_from, cursor)
        self.editor.buffer.end_user_action()

        return True

def get_python_title(uri):
    from os.path import dirname, basename, exists, join
    
    title = basename(uri)
    packages = []
    while True:
        path = dirname(uri)
        if path == uri:
            break
        
        uri = path
        
        if exists(join(uri, '__init__.py')):
            packages.append(basename(uri))
        else:
            break
            
    if packages:
        if title != '__init__.py':
            packages.insert(0, title.partition('.py')[0])
            
        return '.'.join(reversed(packages))
    else:
        return None
