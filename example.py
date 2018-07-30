import asyncio
import logging
import asyncapp
import aiohttp.web

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


async def start(http_runner, custom_app_runner):

    await asyncio.gather(http_runner.setup(), custom_app_runner.setup())

    http_tcp_site = asyncapp.sites.TCPSite(http_runner, 'localhost', 8080)
    http_unix_site = asyncapp.sites.UnixSite(http_runner, 'http_unix_site_socket')
    custom_app_tcp_site = asyncapp.sites.TCPSite(custom_app_runner, 'localhost', 8081)
    custom_app_udp_site = asyncapp.sites.UDPSite(custom_app_runner, 'localhost', 8081)

    await asyncio.gather(http_tcp_site.start(), http_unix_site.start(), custom_app_tcp_site.start(), custom_app_udp_site.start())


async def cleanup(http_runner, custom_app_runner):
    await asyncio.gather(http_runner.cleanup(), custom_app_runner.cleanup())


async def ping(request):
    return aiohttp.web.Response(text='pong')


class CustomApplication(asyncapp.BaseApplication):

    async def _handler(self, msg, address):
        LOG.debug(msg)
        LOG.debug(address)


class CustomAppRunner(aiohttp.web.BaseRunner):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

    async def shutdown(self):
        await self._app.shutdown()

    async def _make_server(self):
        self._app.on_startup.freeze()
        await self._app.startup()
        self._app.freeze()
        return CustomAppServer(self._app._handler)

    async def _cleanup_server(self):
        await self._app.cleanup()


class CustomAppServer:
    def __init__(self, handler):
        self._handler = handler

    def __call__(self):
        return CustomProtocol(handler=self._handler)

    async def shutdown(self, timeout):
        pass


class CustomProtocol(asyncio.Protocol, asyncio.DatagramProtocol):
    def __init__(self, handler):
        self._handler = handler
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        asyncio.ensure_future(
            self._handler(data, self.transport.get_extra_info("peername"))
        )

    def datagram_received(self, data, addr):
        asyncio.ensure_future(self._handler(data, addr))


if __name__ == "__main__":
    http = aiohttp.web.Application()
    http.router.add_route('GET', '/ping', ping)
    http_runner = aiohttp.web.AppRunner(http)

    custom_app = CustomApplication()
    custom_app_runner = CustomAppRunner(custom_app)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start(http_runner, custom_app_runner))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(cleanup(http_runner, custom_app_runner))
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
