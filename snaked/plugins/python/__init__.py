langs = ['python']

handlers = {}
outline_dialog = None

def init(manager):
    manager.add_shortcut('python-goto-definition', 'F3', 'Python',
        'Navigates to python definition', goto_definition)

    manager.add_shortcut('python-outline', '<ctrl>o', 'Python',
        'Opens outline dialog', open_outline)

def editor_created(editor):
    editor.connect('get-title', on_editor_get_title)
    
def editor_opened(editor):
    from plugin import Plugin    
    h = Plugin(editor)
    handlers[editor] = h

def editor_closed(editor):
    handlers[editor].close()
    del handlers[editor]

def quit():
    global outline_dialog
    if outline_dialog:
        outline_dialog.window.destroy()
        del outline_dialog

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

def open_outline(editor):
    global outline_dialog
    if not outline_dialog:
        from outline import OutlineDialog
        outline_dialog = OutlineDialog()
    
    outline_dialog.show(editor)