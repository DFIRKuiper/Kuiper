# This file is Copyright 2020 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#
import logging
from typing import List

from volatility.framework import exceptions, interfaces
from volatility.framework import renderers, contexts
from volatility.framework.configuration import requirements
from volatility.framework.interfaces import plugins
from volatility.framework.objects import utility
from volatility.framework.renderers import format_hints
from volatility.framework.symbols import mac
from volatility.plugins.mac import lsmod

vollog = logging.getLogger(__name__)


class Socket_filters(plugins.PluginInterface):
    """Enumerates kernel socket filters."""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "darwin", description = "Mac kernel symbols"),
            requirements.VersionRequirement(name = 'macutils', component = mac.MacUtilities, version = (1, 0, 0)),
            requirements.PluginRequirement(name = 'lsmod', plugin = lsmod.Lsmod, version = (1, 0, 0))
        ]

    def _generator(self):
        kernel = contexts.Module(self._context, self.config['darwin'], self.config['primary'], 0)

        mods = lsmod.Lsmod.list_modules(self.context, self.config['primary'], self.config['darwin'])

        handlers = mac.MacUtilities.generate_kernel_handler_info(self.context, self.config['primary'], kernel, mods)

        members_to_check = ["sf_unregistered", "sf_attach", "sf_detach", "sf_notify", "sf_getpeername",
                            "sf_getsockname",
                            "sf_data_in", "sf_data_out", "sf_connect_in", "sf_connect_out", "sf_bind", "sf_setoption",
                            "sf_getoption", "sf_listen", "sf_ioctl"]

        filter_list = kernel.object_from_symbol(symbol_name = "sock_filter_head")

        for filter_container in mac.MacUtilities.walk_tailq(filter_list, "sf_global_next"):
            current_filter = filter_container.sf_filter

            filter_name = utility.pointer_to_string(current_filter.sf_name, count = 128)

            try:
                filter_socket = filter_container.sf_entry_head.sfe_socket.vol.offset
            except exceptions.InvalidAddressException:
                filter_socket = 0

            for member in members_to_check:
                check_addr = current_filter.member(attr = member)
                if check_addr == 0:
                    continue

                module_name, symbol_name = mac.MacUtilities.lookup_module_address(self.context, handlers, check_addr)

                yield (0, (format_hints.Hex(current_filter.vol.offset), filter_name, member, \
                           format_hints.Hex(filter_socket), format_hints.Hex(check_addr), module_name, symbol_name))

    def run(self):
        return renderers.TreeGrid([("Filter", format_hints.Hex), ("Name", str), ("Member", str),
                                   ("Socket", format_hints.Hex), ("Handler", format_hints.Hex), ("Module", str),
                                   ("Symbol", str)], self._generator())
