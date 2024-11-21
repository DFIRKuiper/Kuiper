# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

from volatility.framework import renderers
from volatility.framework.configuration import requirements
from volatility.framework.interfaces import plugins
from volatility.framework.objects import utility
from volatility.plugins.mac import pslist


class PsTree(plugins.PluginInterface):
    """Plugin for listing processes in a tree based on their parent process
    ID."""

    _required_framework_version = (2, 0, 0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._processes = {}
        self._levels = {}
        self._children = {}

    @classmethod
    def get_requirements(cls):
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "darwin", description = "Mac kernel symbols"),
            requirements.PluginRequirement(name = 'pslist', plugin = pslist.PsList, version = (2, 0, 0))
        ]

    def _find_level(self, pid):
        """Finds how deep the pid is in the processes list."""
        seen = set([])
        seen.add(pid)
        level = 0
        proc = self._processes.get(pid, None)
        while proc is not None and proc.vol.offset != 0 and proc.p_ppid != 0 and proc.p_ppid not in seen:
            ppid = int(proc.p_ppid)
            child_list = self._children.get(ppid, set([]))
            child_list.add(proc.p_pid)
            self._children[ppid] = child_list
            proc = self._processes.get(ppid, None)
            level += 1
        self._levels[pid] = level

    def _generator(self):
        """Generates the tree list of processes"""
        list_tasks = pslist.PsList.get_list_tasks(self.config.get('pslist_method', pslist.PsList.pslist_methods[0]))

        for proc in list_tasks(self.context, self.config['primary'], self.config['darwin']):
            self._processes[proc.p_pid] = proc

        # Build the child/level maps
        for pid in self._processes:
            self._find_level(pid)

        def yield_processes(pid):
            proc = self._processes[pid]
            row = (proc.p_pid, proc.p_ppid, utility.array_to_string(proc.p_comm))

            yield (self._levels[pid] - 1, row)
            for child_pid in self._children.get(pid, []):
                yield from yield_processes(child_pid)

        for pid in self._levels:
            if self._levels[pid] == 1:
                yield from yield_processes(pid)

    def run(self):
        return renderers.TreeGrid([("PID", int), ("PPID", int), ("COMM", str)], self._generator())
