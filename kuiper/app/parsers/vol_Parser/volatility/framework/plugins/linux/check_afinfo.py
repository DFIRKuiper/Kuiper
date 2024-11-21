# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#
"""A module containing a collection of plugins that produce data typically
found in Linux's /proc file system."""
import logging
from typing import List

from volatility.framework import exceptions, interfaces, contexts
from volatility.framework import renderers
from volatility.framework.configuration import requirements
from volatility.framework.interfaces import plugins
from volatility.framework.renderers import format_hints

vollog = logging.getLogger(__name__)


class Check_afinfo(plugins.PluginInterface):
    """Verifies the operation function pointers of network protocols."""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "vmlinux", description = "Linux kernel symbols")
        ]

    # returns whether the symbol is found within the kernel (system.map) or not
    def _is_known_address(self, handler_addr):
        symbols = list(self.context.symbol_space.get_symbols_by_location(handler_addr))

        return len(symbols) > 0

    def _check_members(self, var_ops, var_name, members):
        for check in members:
            # redhat-specific garbage
            if check.startswith("__UNIQUE_ID_rh_kabi_hide"):
                continue

            if check == "write":
                addr = var_ops.member(attr = 'write')
            else:
                addr = getattr(var_ops, check)

            if addr and addr != 0 and not self._is_known_address(addr):
                yield check, addr

    def _check_afinfo(self, var_name, var, op_members, seq_members):
        for hooked_member, hook_address in self._check_members(var.seq_fops, var_name, op_members):
            yield var_name, hooked_member, hook_address

        # newer kernels
        if var.has_member("seq_ops"):
            for hooked_member, hook_address in self._check_members(var.seq_ops, var_name, seq_members):
                yield var_name, hooked_member, hook_address

        # this is the most commonly hooked member by rootkits, so a force a check on it
        elif not self._is_known_address(var.seq_show):
            yield var_name, "show", var.seq_show

    def _generator(self):
        vmlinux = contexts.Module(self.context, self.config['vmlinux'], self.config['primary'], 0)

        op_members = vmlinux.get_type('file_operations').members
        seq_members = vmlinux.get_type('seq_operations').members

        tcp = ("tcp_seq_afinfo", ["tcp6_seq_afinfo", "tcp4_seq_afinfo"])
        udp = ("udp_seq_afinfo", ["udplite6_seq_afinfo", "udp6_seq_afinfo", "udplite4_seq_afinfo", "udp4_seq_afinfo"])
        protocols = [tcp, udp]

        for (struct_type, global_vars) in protocols:
            for global_var_name in global_vars:
                # this will lookup fail for the IPv6 protocols on kernels without IPv6 support
                try:
                    global_var = vmlinux.get_symbol(global_var_name)
                except exceptions.SymbolError:
                    continue

                global_var = vmlinux.object(object_type = struct_type, offset = global_var.address)

                for name, member, address in self._check_afinfo(global_var_name, global_var, op_members, seq_members):
                    yield 0, (name, member, format_hints.Hex(address))

    def run(self):

        return renderers.TreeGrid([("Symbol Name", str), ("Member", str), ("Handler Address", format_hints.Hex)],
                                  self._generator())
