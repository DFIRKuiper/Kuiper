# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#
"""A module containing a collection of plugins that produce data typically
found in Linux's /proc file system."""
import logging
from typing import List

from volatility.framework import renderers, interfaces, constants
from volatility.framework.configuration import requirements
from volatility.framework.interfaces import plugins
from volatility.framework.objects import utility
from volatility.framework.symbols import linux
from volatility.plugins.linux import pslist

vollog = logging.getLogger(__name__)


class Lsof(plugins.PluginInterface):
    """Lists all memory maps for all processes."""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "vmlinux", description = "Linux kernel symbols"),
            requirements.PluginRequirement(name = 'pslist', plugin = pslist.PsList, version = (1, 0, 0)),
            requirements.VersionRequirement(name = 'linuxutils', component = linux.LinuxUtilities, version = (1, 0, 0)),
            requirements.ListRequirement(name = 'pid',
                                         description = 'Filter on specific process IDs',
                                         element_type = int,
                                         optional = True)
        ]

    def _generator(self, tasks):
        symbol_table = None
        for task in tasks:
            if symbol_table is None:
                if constants.BANG not in task.vol.type_name:
                    raise ValueError("Task is not part of a symbol table")
                symbol_table = task.vol.type_name.split(constants.BANG)[0]

            name = utility.array_to_string(task.comm)
            pid = int(task.pid)

            for fd_num, _, full_path in linux.LinuxUtilities.files_descriptors_for_process(
                    self.context, symbol_table, task):
                yield (0, (pid, name, fd_num, full_path))

    def run(self):
        filter_func = pslist.PsList.create_pid_filter(self.config.get('pid', None))

        return renderers.TreeGrid([("PID", int), ("Process", str), ("FD", int), ("Path", str)],
                                  self._generator(
                                      pslist.PsList.list_tasks(self.context,
                                                               self.config['primary'],
                                                               self.config['vmlinux'],
                                                               filter_func = filter_func)))
