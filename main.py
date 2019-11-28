import socket

import tornado.httpclient
import tornado.ioloop
import tornado.iostream
import tornado.web


class MainRequestHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = tornado.web.RequestHandler.SUPPORTED_METHODS + ('CONNECT', )

    async def get(self):
        client = tornado.httpclient.AsyncHTTPClient()
        request = self.build_request()
        response = await client.fetch(request)
        self.set_status(response.code)
        self.rewrite_header(response.headers)

    def rewrite_header(self, headers):
        for header in ("Date", "Cache-Control", "Server", "Content-Type", "Location"):
            v = headers.get(header)
            if v:
                self.set_header(header, v)
        self.set_header("Connection", "close")
        v = headers.get_list("Set-Cookie")
        if v:
            for i in v:
                self.add_header("Set-Cookie", i)
        self.add_header("VIA", "Proxy")

    def build_request(self):
        request = tornado.httpclient.HTTPRequest(
            url=self.request.uri,
            method=self.request.method,
            headers=self.request.headers,
            body=self.request.body,
            follow_redirects=False,
            streaming_callback=self.streaming_callback,
            allow_nonstandard_methods=True,
        )
        return request

    def streaming_callback(self, chunk):
        self.write(chunk)

    async def connect(self):
        downstream = self.request.connection.stream
        host, port = self.request.uri.split(":", 1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(sock)
        # todo: TCPClient
        await upstream.connect((host, int(port)))


class HelloRequestHandler(tornado.web.RequestHandler):
    def get(self):
        self.write({"hello": "world"})


def make_app():
    app = tornado.web.Application(
        [(r"/hello", HelloRequestHandler), (r".*", MainRequestHandler)]
    )
    return app


if __name__ == "__main__":
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
