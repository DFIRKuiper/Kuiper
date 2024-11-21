# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#
from volatility.framework import exceptions, renderers, contexts
from volatility.framework.configuration import requirements
from volatility.framework.interfaces import plugins
from volatility.framework.objects import utility
from volatility.framework.symbols import mac


class Ifconfig(plugins.PluginInterface):
    """Lists loaded kernel modules"""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls):
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "darwin", description = "Mac kernel symbols"),
            requirements.VersionRequirement(name = 'macutils', component = mac.MacUtilities, version = (1, 0, 0))
        ]

    def _generator(self):
        kernel = contexts.Module(self._context, self.config['darwin'], self.config['primary'], 0)

        try:
            list_head = kernel.object_from_symbol(symbol_name = "ifnet_head")
        except exceptions.SymbolError:
            list_head = kernel.object_from_symbol(symbol_name = "dlil_ifnet_head")

        for ifnet in mac.MacUtilities.walk_tailq(list_head, "if_link"):
            name = utility.pointer_to_string(ifnet.if_name, 32)
            unit = ifnet.if_unit
            prom = ifnet.if_flags & 0x100 == 0x100  # IFF_PROMISC

            sock_addr_dl = ifnet.sockaddr_dl()
            if sock_addr_dl is None:
                mac_addr = renderers.UnreadableValue()
            else:
                mac_addr = str(sock_addr_dl)

            for ifaddr in mac.MacUtilities.walk_tailq(ifnet.if_addrhead, "ifa_link"):
                ip = ifaddr.ifa_addr.get_address()

                yield (0, ("{0}{1}".format(name, unit), ip, mac_addr, prom))

    def run(self):
        return renderers.TreeGrid([("Interface", str), ("IP Address", str), ("Mac Address", str),
                                   ("Promiscuous", bool)], self._generator())
