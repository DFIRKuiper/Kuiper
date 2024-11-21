# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#
import logging
from typing import List, Iterable, Generator

from volatility.framework import constants
from volatility.framework import exceptions, interfaces
from volatility.framework import renderers
from volatility.framework.configuration import requirements
from volatility.framework.renderers import format_hints
from volatility.framework.symbols import intermed
from volatility.framework.symbols.windows.extensions import pe
from volatility.plugins.windows import pslist, dlllist

vollog = logging.getLogger(__name__)


class Modules(interfaces.plugins.PluginInterface):
    """Lists the loaded kernel modules."""

    _required_framework_version = (2, 0, 0)
    _version = (1, 1, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "nt_symbols", description = "Windows kernel symbols"),
            requirements.VersionRequirement(name = 'pslist', component = pslist.PsList, version = (2, 0, 0)),
            requirements.VersionRequirement(name = 'dlllist', component = dlllist.DllList, version = (2, 0, 0)),
            requirements.BooleanRequirement(name = 'dump',
                                            description = "Extract listed modules",
                                            default = False,
                                            optional = True)
        ]

    def _generator(self):
        pe_table_name = intermed.IntermediateSymbolTable.create(self.context,
                                                                self.config_path,
                                                                "windows",
                                                                "pe",
                                                                class_types = pe.class_types)

        for mod in self.list_modules(self.context, self.config['primary'], self.config['nt_symbols']):

            try:
                BaseDllName = mod.BaseDllName.get_string()
            except exceptions.InvalidAddressException:
                BaseDllName = ""

            try:
                FullDllName = mod.FullDllName.get_string()
            except exceptions.InvalidAddressException:
                FullDllName = ""

            file_output = "Disabled"
            if self.config['dump']:
                file_handle = dlllist.DllList.dump_pe(self.context, pe_table_name, mod, self.open)
                file_output = "Error outputting file"
                if file_handle:
                    file_handle.close()
                    file_output = file_handle.preferred_filename

            yield (0, (format_hints.Hex(mod.vol.offset), format_hints.Hex(mod.DllBase),
                       format_hints.Hex(mod.SizeOfImage), BaseDllName, FullDllName, file_output))

    @classmethod
    def get_session_layers(cls,
                           context: interfaces.context.ContextInterface,
                           layer_name: str,
                           symbol_table: str,
                           pids: List[int] = None) -> Generator[str, None, None]:
        """Build a cache of possible virtual layers, in priority starting with
        the primary/kernel layer. Then keep one layer per session by cycling
        through the process list.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            symbol_table: The name of the table containing the kernel symbols
            pids: A list of process identifiers to include exclusively or None for no filter

        Returns:
            A list of session layer names
        """
        seen_ids = []  # type: List[interfaces.objects.ObjectInterface]
        filter_func = pslist.PsList.create_pid_filter(pids or [])

        for proc in pslist.PsList.list_processes(context = context,
                                                 layer_name = layer_name,
                                                 symbol_table = symbol_table,
                                                 filter_func = filter_func):
            proc_id = "Unknown"
            try:
                proc_id = proc.UniqueProcessId
                proc_layer_name = proc.add_process_layer()

                # create the session space object in the process' own layer.
                # not all processes have a valid session pointer.
                session_space = context.object(symbol_table + constants.BANG + "_MM_SESSION_SPACE",
                                               layer_name = layer_name,
                                               offset = proc.Session)

                if session_space.SessionId in seen_ids:
                    continue

            except exceptions.InvalidAddressException:
                vollog.log(
                    constants.LOGLEVEL_VVV,
                    "Process {} does not have a valid Session or a layer could not be constructed for it".format(
                        proc_id))
                continue

            # save the layer if we haven't seen the session yet
            seen_ids.append(session_space.SessionId)
            yield proc_layer_name

    @classmethod
    def find_session_layer(cls, context: interfaces.context.ContextInterface, session_layers: Iterable[str],
                           base_address: int):
        """Given a base address and a list of layer names, find a layer that
        can access the specified address.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            symbol_table: The name of the table containing the kernel symbols
            session_layers: A list of session layer names
            base_address: The base address to identify the layers that can access it

        Returns:
            Layer name or None if no layers that contain the base address can be found
        """

        for layer_name in session_layers:
            if context.layers[layer_name].is_valid(base_address):
                return layer_name

        return None

    @classmethod
    def list_modules(cls, context: interfaces.context.ContextInterface, layer_name: str,
                     symbol_table: str) -> Iterable[interfaces.objects.ObjectInterface]:
        """Lists all the modules in the primary layer.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            symbol_table: The name of the table containing the kernel symbols

        Returns:
            A list of Modules as retrieved from PsLoadedModuleList
        """

        kvo = context.layers[layer_name].config['kernel_virtual_offset']
        ntkrnlmp = context.module(symbol_table, layer_name = layer_name, offset = kvo)

        try:
            # use this type if its available (starting with windows 10)
            ldr_entry_type = ntkrnlmp.get_type("_KLDR_DATA_TABLE_ENTRY")
        except exceptions.SymbolError:
            ldr_entry_type = ntkrnlmp.get_type("_LDR_DATA_TABLE_ENTRY")

        type_name = ldr_entry_type.type_name.split(constants.BANG)[1]

        list_head = ntkrnlmp.get_symbol("PsLoadedModuleList").address
        list_entry = ntkrnlmp.object(object_type = "_LIST_ENTRY", offset = list_head)
        reloff = ldr_entry_type.relative_child_offset("InLoadOrderLinks")
        module = ntkrnlmp.object(object_type = type_name, offset = list_entry.vol.offset - reloff, absolute = True)

        for mod in module.InLoadOrderLinks:
            yield mod

    def run(self):
        return renderers.TreeGrid([("Offset", format_hints.Hex), ("Base", format_hints.Hex), ("Size", format_hints.Hex),
                                   ("Name", str), ("Path", str), ("File output", str)], self._generator())
