# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

from volatility.framework import renderers, interfaces
from volatility.framework.configuration import requirements
from volatility.framework.objects import utility
from volatility.framework.renderers import format_hints
from volatility.plugins.mac import pslist


class Maps(interfaces.plugins.PluginInterface):
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

    def _generator(self, tasks):
        for task in tasks:
            process_name = utility.array_to_string(task.p_comm)
            process_pid = task.p_pid

            for vma in task.get_map_iter():
                path = vma.get_path(self.context, self.config['darwin'])
                if path == "":
                    path = vma.get_special_path()

                yield (0, (process_pid, process_name, format_hints.Hex(vma.links.start),
                           format_hints.Hex(vma.links.end), vma.get_perms(), path))

    def run(self):
        filter_func = pslist.PsList.create_pid_filter(self.config.get('pid', None))
        list_tasks = pslist.PsList.get_list_tasks(self.config.get('pslist_method', pslist.PsList.pslist_methods[0]))

        return renderers.TreeGrid([("PID", int), ("Process", str), ("Start", format_hints.Hex),
                                   ("End", format_hints.Hex), ("Protection", str), ("Map Name", str)],
                                  self._generator(
                                      list_tasks(self.context,
                                                 self.config['primary'],
                                                 self.config['darwin'],
                                                 filter_func = filter_func)))
