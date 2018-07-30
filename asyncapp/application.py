import warnings
import collections

from aiohttp.signals import Signal


class BaseApplication(collections.MutableMapping):

    def __init__(self):
        self._state = {}
        self._frozen = False

        self._on_startup = Signal(self)
        self._on_shutdown = Signal(self)
        self._on_cleanup = Signal(self)

    @property
    def frozen(self):
        return self._frozen

    def freeze(self):
        if self._frozen:
            return

        self._frozen = True
        self._on_startup.freeze()
        self._on_shutdown.freeze()
        self._on_cleanup.freeze()

    @property
    def on_startup(self):
        return self._on_startup

    @property
    def on_shutdown(self):
        return self._on_shutdown

    @property
    def on_cleanup(self):
        return self._on_cleanup

    async def startup(self):
        """Causes on_startup signal
        Should be called in the event loop along with the request handler.
        """
        await self.on_startup.send(self)

    async def shutdown(self):
        """Causes on_shutdown signal
        Should be called before cleanup()
        """
        await self.on_shutdown.send(self)

    async def cleanup(self):
        """Causes on_cleanup signal
        Should be called after shutdown()
        """
        await self.on_cleanup.send(self)

    # MutableMapping API
    def __eq__(self, other):
        return self is other

    def __getitem__(self, key):
        return self._state[key]

    def _check_frozen(self):
        if self._frozen:
            warnings.warn("Changing state of started or joined "
                          "application is deprecated",
                          DeprecationWarning,
                          stacklevel=3)

    def __setitem__(self, key, value):
        self._check_frozen()
        self._state[key] = value

    def __delitem__(self, key):
        self._check_frozen()
        del self._state[key]

    def __len__(self):
        return len(self._state)

    def __iter__(self):
        return iter(self._state)
    ######################

    def __repr__(self):
        return "<Application 0x{:x}>".format(id(self))
