import os
import stat
import socket
import logging
import asyncio

from enum import Enum
from aiohttp.web_runner import BaseSite, TCPSite, UnixSite, SockSite

LOG = logging.getLogger(__name__)


class ProtocolType(Enum):
    STREAM = 1
    DATAGRAM = 2


TCPSite._protocol_type = ProtocolType.STREAM
UnixSite._protocol_type = ProtocolType.STREAM
SockSite._protocol_type = ProtocolType.STREAM


class DatagramServer:
    """
    Shim to present a unified server interface.
    """

    def __init__(self, transport):
        self.transport = transport

    def close(self):
        self.transport.close()

    async def wait_closed(self):
        pass


class UDPSite(BaseSite):
    def __init__(
        self,
        runner,
        host=None,
        port=None,
        *,
        shutdown_timeout=60.0,
        reuse_address=None,
        reuse_port=None,
    ):
        super().__init__(runner, shutdown_timeout=shutdown_timeout)

        if host is None:
            host = "0.0.0.0"
        self._host = host
        if port is None:
            port = 8443 if self._ssl_context else 8080
        self._port = port
        self._reuse_address = reuse_address
        self._reuse_port = reuse_port
        self._protocol_type = ProtocolType.DATAGRAM

    @property
    def name(self):
        return f"UDP://{self._host}:{self._port}"

    async def start(self):
        await super().start()
        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            self._runner.server,
            local_addr=(self._host, self._port),
            reuse_address=self._reuse_address,
            reuse_port=self._reuse_port,
        )
        self._server = DatagramServer(transport)


class DatagramUnixSite(BaseSite):
    def __init__(self, runner, path, *, shutdown_timeout=60.0):
        super().__init__(runner, shutdown_timeout=shutdown_timeout)
        self._path = path
        self._protocol_type = ProtocolType.DATAGRAM

    @property
    def name(self):
        return f"UDP://unix:{self._path}"

    async def start(self):
        await super().start()
        await self._clean_stale_unix_socket(self._path)

        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            self._runner.server, family=socket.AF_UNIX, local_addr=self._path
        )
        self._server = DatagramServer(transport)

    @staticmethod
    async def _clean_stale_unix_socket(path):
        if path[0] not in (0, "\x00"):
            try:
                if stat.S_ISSOCK(os.stat(path).st_mode):
                    os.remove(path)
            except FileNotFoundError:
                pass
            except OSError as err:
                # Directory may have permissions only to create socket.
                LOG.error(
                    "Unable to check or remove stale UNIX socket %r: %r", path, err
                )


class DatagramSockSite(BaseSite):
    def __init__(self, runner, sock, *, shutdown_timeout=60.0):
        super().__init__(runner, shutdown_timeout=shutdown_timeout)
        self._sock = sock

        if hasattr(socket, "AF_UNIX") and sock.family == socket.AF_UNIX:
            name = f"UDP://unix:{sock.getsockname()}"
        else:
            host, port = sock.getsockname()[:2]
            name = f"UDP://{host}:{port}"

        self._name = name
        self._protocol_type = ProtocolType.DATAGRAM

    @property
    def name(self):
        return self._name

    async def start(self):
        await super().start()
        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            self._runner.server, sock=self._sock
        )
        self._server = DatagramServer(transport)
