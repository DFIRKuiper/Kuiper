# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

from volatility.framework import constants
from volatility.framework import interfaces
from volatility.framework import renderers
from volatility.framework.configuration import requirements
from volatility.framework.objects import utility
from volatility.framework.renderers import format_hints
from volatility.plugins.mac import pslist


class Malfind(interfaces.plugins.PluginInterface):
    """Lists process memory ranges that potentially contain injected code."""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls):
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "darwin", description = "Mac kernel"),
            requirements.PluginRequirement(name = 'pslist', plugin = pslist.PsList, version = (2, 0, 0)),
            requirements.ListRequirement(name = 'pid',
                                         description = 'Filter on specific process IDs',
                                         element_type = int,
                                         optional = True)
        ]

    def _list_injections(self, task):
        """Generate memory regions for a process that may contain injected
        code."""

        proc_layer_name = task.add_process_layer()
        if proc_layer_name is None:
            return

        proc_layer = self.context.layers[proc_layer_name]

        for vma in task.get_map_iter():
            if not vma.is_suspicious(self.context, self.config['darwin']):
                data = proc_layer.read(vma.links.start, 64, pad = True)
                yield vma, data

    def _generator(self, tasks):
        # determine if we're on a 32 or 64 bit kernel
        if self.context.symbol_space.get_type(self.config["darwin"] + constants.BANG + "pointer").size == 4:
            is_32bit_arch = True
        else:
            is_32bit_arch = False

        for task in tasks:
            process_name = utility.array_to_string(task.p_comm)

            for vma, data in self._list_injections(task):
                if is_32bit_arch:
                    architecture = "intel"
                else:
                    architecture = "intel64"

                disasm = interfaces.renderers.Disassembly(data, vma.links.start, architecture)

                yield (0, (task.p_pid, process_name, format_hints.Hex(vma.links.start), format_hints.Hex(vma.links.end),
                           vma.get_perms(), format_hints.HexBytes(data), disasm))

    def run(self):
        filter_func = pslist.PsList.create_pid_filter(self.config.get('pid', None))
        list_tasks = pslist.PsList.get_list_tasks(self.config.get('pslist_method', pslist.PsList.pslist_methods[0]))

        return renderers.TreeGrid([("PID", int), ("Process", str), ("Start", format_hints.Hex),
                                   ("End", format_hints.Hex), ("Protection", str), ("Hexdump", format_hints.HexBytes),
                                   ("Disasm", interfaces.renderers.Disassembly)],
                                  self._generator(
                                      list_tasks(self.context,
                                                 self.config['primary'],
                                                 self.config['darwin'],
                                                 filter_func = filter_func)))
