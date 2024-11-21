# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

import logging
from typing import List, Tuple, Dict, Generator

from volatility.framework import interfaces, renderers, exceptions
from volatility.framework.configuration import requirements
from volatility.framework.layers import intel
from volatility.framework.renderers import format_hints

vollog = logging.getLogger(__name__)


class VirtMap(interfaces.plugins.PluginInterface):
    """Lists virtual mapped sections."""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        # Since we're calling the plugin, make sure we have the plugin's requirements
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "nt_symbols", description = "Windows kernel symbols")
        ]

    def _generator(self, map):
        for entry in sorted(map):
            for (start, end) in map[entry]:
                yield (0, (entry, format_hints.Hex(start), format_hints.Hex(end)))

    @classmethod
    def determine_map(cls, module: interfaces.context.ModuleInterface) -> \
            Dict[str, List[Tuple[int, int]]]:
        """Returns the virtual map from a windows kernel module."""
        layer = module.context.layers[module.layer_name]
        if not isinstance(layer, intel.Intel):
            raise

        result = {}  # type: Dict[str, List[Tuple[int, int]]]
        system_va_type = module.get_enumeration('_MI_SYSTEM_VA_TYPE')
        large_page_size = (layer.page_size ** 2) // module.get_type("_MMPTE").size

        if module.has_symbol('MiVisibleState'):
            symbol = module.get_symbol('MiVisibleState')
            visible_state = module.object(object_type = 'pointer',
                                          offset = symbol.address,
                                          subtype = module.get_type('_MI_VISIBLE_STATE')).dereference()
            if hasattr(visible_state, 'SystemVaRegions'):
                for i in range(visible_state.SystemVaRegions.count):
                    lookup = system_va_type.lookup(i)
                    region_range = result.get(lookup, [])
                    region_range.append(
                        (visible_state.SystemVaRegions[i].BaseAddress, visible_state.SystemVaRegions[i].NumberOfBytes))
                    result[lookup] = region_range
            elif hasattr(visible_state, 'SystemVaType'):
                system_range_start = module.object(object_type = "pointer",
                                                   offset = module.get_symbol("MmSystemRangeStart").address)
                result = cls._enumerate_system_va_type(large_page_size, system_range_start, module,
                                                       visible_state.SystemVaType)
            else:
                raise exceptions.SymbolError(None, module.name, "Required structures not found")
        elif module.has_symbol('MiSystemVaType'):
            system_range_start = module.object(object_type = "pointer",
                                               offset = module.get_symbol("MmSystemRangeStart").address)
            symbol = module.get_symbol('MiSystemVaType')
            array_count = (0xFFFFFFFF + 1 - system_range_start) // large_page_size
            type_array = module.object(object_type = 'array',
                                       offset = symbol.address,
                                       count = array_count,
                                       subtype = module.get_type('char'))

            result = cls._enumerate_system_va_type(large_page_size, system_range_start, module, type_array)
        else:
            raise exceptions.SymbolError(None, module.name, "Required structures not found")

        return result

    @classmethod
    def _enumerate_system_va_type(cls, large_page_size: int, system_range_start: int,
                                  module: interfaces.context.ModuleInterface,
                                  type_array: interfaces.objects.ObjectInterface) -> Dict[str, List[Tuple[int, int]]]:
        result = {}  # type: Dict[str, List[Tuple[int, int]]]
        system_va_type = module.get_enumeration('_MI_SYSTEM_VA_TYPE')
        start = system_range_start
        prev_entry = -1
        cur_size = large_page_size
        for entry in type_array:
            entry = system_va_type.lookup(entry)
            if entry != prev_entry:
                region_range = result.get(entry, [])
                region_range.append((start, cur_size))
                result[entry] = region_range
                start = start + cur_size
                cur_size = large_page_size
            else:
                cur_size += large_page_size
            prev_entry = entry

        return result

    @classmethod
    def scannable_sections(cls, module: interfaces.context.ModuleInterface) -> Generator[Tuple[int, int], None, None]:
        mapping = cls.determine_map(module)
        for entry in mapping:
            if 'Unused' not in entry:
                for value in mapping[entry]:
                    yield value

    def run(self):
        layer = self.context.layers[self.config['primary']]
        module = self.context.module(self.config['nt_symbols'],
                                     layer_name = layer.name,
                                     offset = layer.config['kernel_virtual_offset'])

        return renderers.TreeGrid([("Region", str), ("Start offset", format_hints.Hex),
                                   ("End offset", format_hints.Hex)],
                                  self._generator(self.determine_map(module = module)))
