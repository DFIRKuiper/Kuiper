# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

import datetime
import logging
from typing import Iterable, Callable

from volatility.framework import renderers, interfaces
from volatility.framework.configuration import requirements
from volatility.framework.renderers import format_hints
from volatility.framework.symbols import intermed
from volatility.framework.symbols.windows.extensions import pe
from volatility.plugins import timeliner
from volatility.plugins.windows import info
from volatility.plugins.windows import poolscanner
from volatility.plugins.windows import pslist

vollog = logging.getLogger(__name__)


class PsScan(interfaces.plugins.PluginInterface, timeliner.TimeLinerInterface):
    """Scans for processes present in a particular windows memory image."""

    _required_framework_version = (2, 0, 0)
    _version = (1, 1, 0)

    @classmethod
    def get_requirements(cls):
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "nt_symbols", description = "Windows kernel symbols"),
            requirements.PluginRequirement(name = 'pslist', plugin = pslist.PsList, version = (2, 0, 0)),
            requirements.VersionRequirement(name = 'info', component = info.Info, version = (1, 0, 0)),
            requirements.ListRequirement(name = 'pid',
                                         element_type = int,
                                         description = "Process ID to include (all other processes are excluded)",
                                         optional = True),
            requirements.BooleanRequirement(name = 'dump',
                                            description = "Extract listed processes",
                                            default = False,
                                            optional = True)
        ]

    @classmethod
    def scan_processes(cls,
                       context: interfaces.context.ContextInterface,
                       layer_name: str,
                       symbol_table: str,
                       filter_func: Callable[[interfaces.objects.ObjectInterface], bool] = lambda _: False) -> \
            Iterable[interfaces.objects.ObjectInterface]:
        """Scans for processes using the poolscanner module and constraints.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            symbol_table: The name of the table containing the kernel symbols

        Returns:
            A list of processes found by scanning the `layer_name` layer for process pool signatures
        """

        constraints = poolscanner.PoolScanner.builtin_constraints(symbol_table, [b'Pro\xe3', b'Proc'])

        for result in poolscanner.PoolScanner.generate_pool_scan(context, layer_name, symbol_table, constraints):

            _constraint, mem_object, _header = result
            if not filter_func(mem_object):
                yield mem_object

    @classmethod
    def virtual_process_from_physical(cls,
                                      context: interfaces.context.ContextInterface,
                                      layer_name: str,
                                      symbol_table: str,
                                      proc: interfaces.objects.ObjectInterface) -> \
            Iterable[interfaces.objects.ObjectInterface]:
        """ Returns a virtual process from a physical addressed one

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            symbol_table: The name of the table containing the kernel symbols
            proc: the process object with phisical address

        Returns:
            A process object on virtual address layer

        """

        # We'll use the first thread to bounce back to the virtual process
        kvo = context.layers[layer_name].config['kernel_virtual_offset']
        ntkrnlmp = context.module(symbol_table, layer_name = layer_name, offset = kvo)

        tleoffset = ntkrnlmp.get_type("_ETHREAD").relative_child_offset("ThreadListEntry")
        # Start out with the member offset
        offsets = [tleoffset]

        # If (and only if) we're dealing with 64-bit Windows 7 SP1
        # then add the other commonly seen member offset to the list
        kuser = info.Info.get_kuser_structure(context, layer_name, symbol_table)
        nt_major_version = int(kuser.NtMajorVersion)
        nt_minor_version = int(kuser.NtMinorVersion)
        vers = info.Info.get_version_structure(context, layer_name, symbol_table)
        build = vers.MinorVersion
        bits = context.layers[layer_name].bits_per_register
        version = (nt_major_version, nt_minor_version, build)
        if version == (6, 1, 7601) and bits == 64:
            offsets.append(tleoffset + 8)

        # Now we can try to bounce back
        for ofs in offsets:
            ethread = ntkrnlmp.object(object_type = "_ETHREAD",
                                      offset = proc.ThreadListHead.Flink - ofs,
                                      absolute = True)

            # Ask for the thread's process to get an _EPROCESS with a virtual address layer
            virtual_process = ethread.owning_process()
            # Sanity check the bounce.
            # This compares the original offset with the new one (translated from virtual layer)
            (_, _, ph_offset, _, _) = list(context.layers[layer_name].mapping(offset = virtual_process.vol.offset,
                                                                              length = 0))[0]
            if virtual_process and \
                    proc.vol.offset == ph_offset:
                return virtual_process

    def _generator(self):
        pe_table_name = intermed.IntermediateSymbolTable.create(self.context,
                                                                self.config_path,
                                                                "windows",
                                                                "pe",
                                                                class_types = pe.class_types)
        for proc in self.scan_processes(self.context,
                                        self.config['primary'],
                                        self.config['nt_symbols'],
                                        filter_func = pslist.PsList.create_pid_filter(self.config.get('pid', None))):

            file_output = "Disabled"
            if self.config['dump']:
                vproc = self.virtual_process_from_physical(self.context, self.config['primary'],
                                                           self.config['nt_symbols'], proc)

                file_handle = pslist.PsList.process_dump(self.context, self.config['nt_symbols'], pe_table_name,
                                                         vproc, self.open)
                file_output = "Error outputting file"
                if file_handle:
                    file_output = file_handle.preferred_filename

            yield (0, (proc.UniqueProcessId, proc.InheritedFromUniqueProcessId,
                       proc.ImageFileName.cast("string", max_length = proc.ImageFileName.vol.count,
                                               errors = 'replace'), format_hints.Hex(proc.vol.offset),
                       proc.ActiveThreads, proc.get_handle_count(), proc.get_session_id(), proc.get_is_wow64(),
                       proc.get_create_time(), proc.get_exit_time(), file_output))

    def generate_timeline(self):
        for row in self._generator():
            _depth, row_data = row
            description = "Process: {} {} ({})".format(row_data[0], row_data[2], row_data[3])
            yield (description, timeliner.TimeLinerType.CREATED, row_data[8])
            yield (description, timeliner.TimeLinerType.MODIFIED, row_data[9])

    def run(self):
        return renderers.TreeGrid([("PID", int), ("PPID", int), ("ImageFileName", str), ("Offset", format_hints.Hex),
                                   ("Threads", int), ("Handles", int), ("SessionId", int), ("Wow64", bool),
                                   ("CreateTime", datetime.datetime), ("ExitTime", datetime.datetime),
                                   ("File output", str)], self._generator())
