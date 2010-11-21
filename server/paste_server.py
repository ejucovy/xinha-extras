from paste.httpserver import serve
from paste.fileapp import DirectoryApp

from paste.urlmap import URLMap
from webob import Request, Response
import os
import simplejson as json

static_app = DirectoryApp('.')

def scan(req, path):
    files = []
    for file in os.listdir(path):
        _file = file
        file = req.path_info.rstrip('/') + '/' + file
        data = {'url': file}
        filepath = os.path.join(path, _file)
        if os.path.isdir(filepath):
            _req = Request(req.environ.copy())
            _req.path_info = file
            subfiles = scan(_req, filepath)
            data['children'] = subfiles
        files.append(data)
    return files

def linker_app(environ, start_response):
    req = Request(environ)
    path = req.path_info
    path = path.split('/')
    path = [os.getcwd()] + path
    path = os.path.join(*path)
    assert os.path.exists(path)
    files = scan(req, path)
    return Response(json.dumps(files),
                    )(
        environ, start_response)

app = URLMap()
app['/linker_backend'] = linker_app
app['/'] = static_app

serve(app, port='8080')
