# helper to load url
# runs webserver and loads url with webbrowswer module
import sys


def load_url(path):
    """
    Load a web server.

    Args:
        path: (str): write your description
    """
    PORT = 8000
    httpd = StoppableHTTPServer(("127.0.0.1", PORT), handler)
    thread.start_new_thread(httpd.serve, ())
    webbrowser.open_new('http://localhost:%s/%s' % (PORT, path))
    input("Press <RETURN> to stop server\n")
    httpd.stop()
    print("To restart server run: \n%s" % server)


if sys.version_info[0] == 2:
    import SimpleHTTPServer
    import BaseHTTPServer
    import socket
    import thread
    import webbrowser

    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
#    input = raw_input
    server = "python -m SimpleHTTPServer 8000"


    class StoppableHTTPServer(BaseHTTPServer.HTTPServer):

        def server_bind(self):
            """
            Binds a server.

            Args:
                self: (todo): write your description
            """
            BaseHTTPServer.HTTPServer.server_bind(self)
            self.socket.settimeout(1)
            self.run = True

        def get_request(self):
            """
            Get a request.

            Args:
                self: (todo): write your description
            """
            while self.run:
                try:
                    sock, addr = self.socket.accept()
                    sock.settimeout(None)
                    return (sock, addr)
                except socket.timeout:
                    pass

        def stop(self):
            """
            Stop the manager

            Args:
                self: (todo): write your description
            """
            self.run = False

        def serve(self):
            """
            Starts a thread.

            Args:
                self: (todo): write your description
            """
            while self.run:
                self.handle_request()


else:
    import http.server
    import http.server
    import socket
    import _thread as thread
    import webbrowser

    handler = http.server.SimpleHTTPRequestHandler
    server = "python -m http.server 8000"


    class StoppableHTTPServer(http.server.HTTPServer):

        def server_bind(self):
            """
            Binds a socket.

            Args:
                self: (todo): write your description
            """
            http.server.HTTPServer.server_bind(self)
            self.socket.settimeout(1)
            self.run = True

        def get_request(self):
            """
            Get a request.

            Args:
                self: (todo): write your description
            """
            while self.run:
                try:
                    sock, addr = self.socket.accept()
                    sock.settimeout(None)
                    return (sock, addr)
                except socket.timeout:
                    pass

        def stop(self):
            """
            Stop the manager

            Args:
                self: (todo): write your description
            """
            self.run = False

        def serve(self):
            """
            Starts a thread.

            Args:
                self: (todo): write your description
            """
            while self.run:
                self.handle_request()
