from paste.httpserver import serve
from paste.fileapp import DirectoryApp

from paste.urlmap import URLMap
from webob import Request, Response
import os
import simplejson as json

from optparse import OptionParser

def _main():
    parser = OptionParser()
    parser.add_option("-x", "--xinha-path", dest="xinha_path",
                      help="Filesystem path to Xinha code which we will serve")
    parser.add_option("-f", "--file-path", dest="file_path",
                      help="Filesystem path to static files which we will expose as Linker options")

    default = "/"
    parser.add_option("-u", "--xinha-url", dest="xinha_url",
                      help="URL to mount Xinha static files on (default: %s)" % default,
                      default=default)

    default="/linker_backend"
    parser.add_option("-l", "--linker-url", dest="linker_url",
                      help="URL to mount Linker backend on (default: %s)" % default,
                      default=default)

    default = "8080"
    parser.add_option("-p", "--port", dest="port",
                      help="Port to serve on (default: %s)" % default,
                      default=default)
    
    (options, args) = parser.parse_args()

    if options.xinha_path is None \
            or options.file_path is None:
        parser.print_help()
        return

    app = build_app(options.xinha_path, options.file_path,
                    options.xinha_url, options.linker_url)
    serve(app, port=options.port)

def build_app(xinha_path, file_path, xinha_url, linker_url):
    static_app = DirectoryApp(xinha_path)
    linker_app = LinkerApp(file_path)

    app = URLMap()
    app[linker_url] = linker_app
    app[xinha_url] = static_app
    
    return app


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

class LinkerApp(object):
    def __init__(self, file_path):
        self.file_path = file_path

    def __call__(self, environ, start_response):
        req = Request(environ)
        path = req.path_info
        path = path.split('/')
        path = self.file_path + path
        path = os.path.join(*path)
        assert os.path.exists(path)
        files = scan(req, path)
        return Response(json.dumps(files),
                        )(
            environ, start_response)

if __name__ == '__main__':
    _main()

