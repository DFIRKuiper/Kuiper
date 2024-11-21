# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#
"""A module containing a collection of plugins that produce data typically
found in Linux's /proc file system."""

from typing import List

from volatility.framework import renderers, interfaces
from volatility.framework.configuration import requirements
from volatility.framework.interfaces import plugins
from volatility.framework.objects import utility
from volatility.framework.renderers import format_hints
from volatility.plugins.linux import pslist


class Elfs(plugins.PluginInterface):
    """Lists all memory mapped ELF files for all processes."""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "vmlinux", description = "Linux kernel symbols"),
            requirements.PluginRequirement(name = 'pslist', plugin = pslist.PsList, version = (1, 0, 0)),
            requirements.ListRequirement(name = 'pid',
                                         description = 'Filter on specific process IDs',
                                         element_type = int,
                                         optional = True)
        ]

    def _generator(self, tasks):
        for task in tasks:
            proc_layer_name = task.add_process_layer()
            if not proc_layer_name:
                continue

            proc_layer = self.context.layers[proc_layer_name]

            name = utility.array_to_string(task.comm)

            for vma in task.mm.get_mmap_iter():
                hdr = proc_layer.read(vma.vm_start, 4, pad = True)
                if not (hdr[0] == 0x7f and hdr[1] == 0x45 and hdr[2] == 0x4c and hdr[3] == 0x46):
                    continue

                path = vma.get_name(self.context, task)

                yield (0, (task.pid, name, format_hints.Hex(vma.vm_start), format_hints.Hex(vma.vm_end), path))

    def run(self):
        filter_func = pslist.PsList.create_pid_filter(self.config.get('pid', None))

        return renderers.TreeGrid([("PID", int), ("Process", str), ("Start", format_hints.Hex),
                                   ("End", format_hints.Hex), ("File Path", str)],
                                  self._generator(
                                      pslist.PsList.list_tasks(self.context,
                                                               self.config['primary'],
                                                               self.config['vmlinux'],
                                                               filter_func = filter_func)))
