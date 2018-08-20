# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import collections
import json
import logging
import os

import ida_idp
import ida_kernwin
import ida_netnode

from ..module import Module
from ..shared.commands import Subscribe, Unsubscribe
from ..utilities.misc import local_resource
from .hooks import Hooks, IDBHooks, IDPHooks, HexRaysHooks, ViewHooks, UIHooks

logger = logging.getLogger('IDArling.Core')


class Core(Module):
    """
    The core module, responsible for all interactions with the IDA kernel.
    """
    NETNODE_NAME = '$ idarling'

    def __init__(self, plugin):
        super(Core, self).__init__(plugin)

        self._idbHooks = None
        self._idpHooks = None
        self._hxeHooks = None
        self._viewHooks = None
        self._uiHooks = None

        self._uiHooksCore = None
        self._idbHooksCore = None

        # Database members
        self._repo = None
        self._branch = None
        self._tick = 0

        # Instance members
        self._config = {"servers": []}

    def _install(self):
        logger.debug("Installing hooks")
        core = self
        self.load_state()

        self._idbHooks = IDBHooks(self._plugin)
        self._idpHooks = IDPHooks(self._plugin)
        self._hxeHooks = HexRaysHooks(self._plugin)
        self._viewHooks = ViewHooks(self._plugin)
        self._uiHooks = UIHooks(self._plugin)

        class UIHooksCore(Hooks, ida_kernwin.UI_Hooks):
            """
            The concrete class for all core UI-related events.
            """

            def __init__(self, plugin):
                ida_kernwin.UI_Hooks.__init__(self)
                Hooks.__init__(self, plugin)

            def ready_to_run(self, *_):
                core.load_netnode()

                # Subscribe to the events stream if needed
                if core.repo and core.branch:
                    self._plugin.network.send_packet(Subscribe(
                        core.repo, core.branch, core.tick,
                        self._plugin.interface.painter.color))
                    core.hook_all()

        self._uiHooksCore = UIHooksCore(self._plugin)
        self._uiHooksCore.hook()

        class IDBHooksCore(Hooks, ida_idp.IDB_Hooks):
            """
            The concrete class for all core IDB-related events.
            """

            def __init__(self, plugin):
                ida_idp.IDB_Hooks.__init__(self)
                Hooks.__init__(self, plugin)

            def closebase(self):
                color = self._plugin.interface.painter.color
                self._plugin.network.send_packet(Unsubscribe(color))
                logger.debug("Sending unsubscribe packet")
                core.unhook_all()
                core.repo = None
                core.branch = None
                core.ticks = 0
                return 0

        self._idbHooksCore = IDBHooksCore(self._plugin)
        self._idbHooksCore.hook()
        return True

    def _uninstall(self):
        logger.debug("Uninstalling hooks")
        self._idbHooksCore.unhook()
        self._uiHooksCore.unhook()

        self.unhook_all()
        self.save_state()
        return True

    def hook_all(self):
        """
        Add the hooks to be notified of incoming IDA events.
        """
        self._idbHooks.hook()
        self._idpHooks.hook()
        self._hxeHooks.hook()
        self._viewHooks.hook()
        self._uiHooks.hook()

    def unhook_all(self):
        """
        Remove the hooks to not be notified of incoming IDA events.
        """
        self._idbHooks.unhook()
        self._idpHooks.unhook()
        self._hxeHooks.unhook()
        self._viewHooks.unhook()
        self._uiHooks.unhook()

    @property
    def repo(self):
        """
        Get the current repository.

        :return: the repo name
        """
        return self._repo

    @repo.setter
    def repo(self, name):
        """
        Set the the current repository.

        :param name: the repo name
        """
        self._repo = name
        self.save_netnode()

    @property
    def branch(self):
        """
        Get the current branch.

        :return: the branch name
        """
        return self._branch

    @branch.setter
    def branch(self, name):
        """
        Set the current branch.

        :param name: the branch name
        """
        self._branch = name
        self.save_netnode()

    @property
    def tick(self):
        """
        Get the current tick.

        :return: the tick
        """
        return self._tick

    @tick.setter
    def tick(self, tick):
        """
        Set the current tick.

        :param tick: the tick
        """
        self._tick = tick
        self.save_netnode()

    def load_netnode(self):
        """
        Load members from the custom netnode.
        """
        node = ida_netnode.netnode(Core.NETNODE_NAME, 0, True)
        self._repo = node.hashval('repo') or None
        if self._repo:
            self._repo = self._repo.decode('utf-8')

        self._branch = node.hashval('branch') or None
        if self._branch:
            self._branch = self._branch.decode('utf-8')

        self._tick = int(node.hashval('tick') or '0')

        logger.debug("Loaded netnode: repo=%s, branch=%s, tick=%d"
                     % (self._repo, self._branch, self._tick))

    def save_netnode(self):
        """
        Save members to the custom netnode.
        """
        node = ida_netnode.netnode(Core.NETNODE_NAME, 0, True)
        if self._repo:
            node.hashset('repo', self._repo.encode('utf-8'))
        if self._branch:
            node.hashset('branch', self._branch.encode('utf-8'))
        if self._tick:
            node.hashset('tick', str(self._tick))

        logger.debug("Saved netnode: repo=%s, branch=%s, tick=%d"
                     % (self._repo, self._branch, self._tick))

    @property
    def servers(self):
        """
        Get the list of servers.

        :return: the servers
        """
        return self._config["servers"]

    @servers.setter
    def servers(self, servers):
        """
        Set the list of servers.

        :param servers: the list of server
        """
        self._config["servers"] = servers
        self.save_state()

    def load_state(self):
        """
        Load the state file.

        The state file is now a json file in the form like this:
        { "servers" : [
            { "host": "127.0.0.1", "port": 3389, "no_ssl": True },
            { "host": "127.0.0.2", "port": 3389, "no_ssl": True }
            ]
        }
        """
        statePath = local_resource('files', 'config.json')
        if not os.path.isfile(statePath):
            return
        with open(statePath, 'rb') as stateFile:
            try:
                self._config = json.loads(stateFile.read())
            except ValueError:
                logger.warning("Couldn't load state file")
                return
            logger.debug("Loaded state: %s" % self._config)

    def save_state(self):
        """
        Save the state file.
        """
        statePath = local_resource('files', 'config.json')
        with open(statePath, 'wb') as stateFile:
            logger.debug("Saved state: %s" % self._config)
            stateFile.write(json.dumps(self._config))

    def notify_connected(self):
        if self._repo and self._branch:
            color = self._plugin.interface.painter.color
            self._plugin.network.send_packet(
                Subscribe(self._repo, self._branch, self._tick, color))
            self.hook_all()
