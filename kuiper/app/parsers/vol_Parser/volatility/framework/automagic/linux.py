# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

import logging
from typing import Optional, Tuple, Type

from volatility.framework import interfaces, constants
from volatility.framework.automagic import symbol_cache, symbol_finder
from volatility.framework.layers import intel, scanners
from volatility.framework.symbols import linux

vollog = logging.getLogger(__name__)


class LinuxIntelStacker(interfaces.automagic.StackerLayerInterface):
    stack_order = 45
    exclusion_list = ['mac', 'windows']

    @classmethod
    def stack(cls,
              context: interfaces.context.ContextInterface,
              layer_name: str,
              progress_callback: constants.ProgressCallback = None) -> Optional[interfaces.layers.DataLayerInterface]:
        """Attempts to identify linux within this layer."""
        # Bail out by default unless we can stack properly
        layer = context.layers[layer_name]
        join = interfaces.configuration.path_join

        # Never stack on top of an intel layer
        # FIXME: Find a way to improve this check
        if isinstance(layer, intel.Intel):
            return None

        linux_banners = LinuxBannerCache.load_banners()
        # If we have no banners, don't bother scanning
        if not linux_banners:
            vollog.info("No Linux banners found - if this is a linux plugin, please check your symbol files location")
            return None

        mss = scanners.MultiStringScanner([x for x in linux_banners if x is not None])
        for _, banner in layer.scan(context = context, scanner = mss, progress_callback = progress_callback):
            dtb = None
            vollog.debug("Identified banner: {}".format(repr(banner)))

            symbol_files = linux_banners.get(banner, None)
            if symbol_files:
                isf_path = symbol_files[0]
                table_name = context.symbol_space.free_table_name('LintelStacker')
                table = linux.LinuxKernelIntermedSymbols(context,
                                                         'temporary.' + table_name,
                                                         name = table_name,
                                                         isf_url = isf_path)
                context.symbol_space.append(table)
                kaslr_shift, aslr_shift = cls.find_aslr(context,
                                                        table_name,
                                                        layer_name,
                                                        progress_callback = progress_callback)

                layer_class = intel.Intel  # type: Type
                if 'init_top_pgt' in table.symbols:
                    layer_class = intel.Intel32e
                    dtb_symbol_name = 'init_top_pgt'
                elif 'init_level4_pgt' in table.symbols:
                    layer_class = intel.Intel32e
                    dtb_symbol_name = 'init_level4_pgt'
                else:
                    dtb_symbol_name = 'swapper_pg_dir'

                dtb = cls.virtual_to_physical_address(table.get_symbol(dtb_symbol_name).address + kaslr_shift)

                # Build the new layer
                new_layer_name = context.layers.free_layer_name("IntelLayer")
                config_path = join("IntelHelper", new_layer_name)
                context.config[join(config_path, "memory_layer")] = layer_name
                context.config[join(config_path, "page_map_offset")] = dtb
                context.config[join(config_path, LinuxSymbolFinder.banner_config_key)] = str(banner, 'latin-1')

                layer = layer_class(context,
                                    config_path = config_path,
                                    name = new_layer_name,
                                    metadata = {'kaslr_value': aslr_shift})

            if layer and dtb:
                vollog.debug("DTB was found at: 0x{:0x}".format(dtb))
                return layer
        return None

    @classmethod
    def find_aslr(cls,
                  context: interfaces.context.ContextInterface,
                  symbol_table: str,
                  layer_name: str,
                  progress_callback: constants.ProgressCallback = None) \
            -> Tuple[int, int]:
        """Determines the offset of the actual DTB in physical space and its
        symbol offset."""
        init_task_symbol = symbol_table + constants.BANG + 'init_task'
        init_task_json_address = context.symbol_space.get_symbol(init_task_symbol).address
        swapper_signature = rb"swapper(\/0|\x00\x00)\x00\x00\x00\x00\x00\x00"
        module = context.module(symbol_table, layer_name, 0)
        address_mask = context.symbol_space[symbol_table].config.get('symbol_mask', None)

        task_symbol = module.get_type('task_struct')
        comm_child_offset = task_symbol.relative_child_offset('comm')

        for offset in context.layers[layer_name].scan(scanner = scanners.RegExScanner(swapper_signature),
                                                      context = context,
                                                      progress_callback = progress_callback):
            init_task_address = offset - comm_child_offset
            init_task = module.object(object_type = 'task_struct', offset = init_task_address, absolute = True)
            if init_task.pid != 0:
                continue
            elif init_task.has_member('state') and init_task.state.cast('unsigned int') != 0:
                continue

            # This we get for free
            aslr_shift = init_task.files.cast('long unsigned int') - module.get_symbol('init_files').address
            kaslr_shift = init_task_address - cls.virtual_to_physical_address(init_task_json_address)
            if address_mask:
                aslr_shift = aslr_shift & address_mask

            if aslr_shift & 0xfff != 0 or kaslr_shift & 0xfff != 0:
                continue
            vollog.debug("Linux ASLR shift values determined: physical {:0x} virtual {:0x}".format(
                kaslr_shift, aslr_shift))
            return kaslr_shift, aslr_shift

        # We don't throw an exception, because we may legitimately not have an ASLR shift, but we report it
        vollog.debug("Scanners could not determine any ASLR shifts, using 0 for both")
        return 0, 0

    @classmethod
    def virtual_to_physical_address(cls, addr: int) -> int:
        """Converts a virtual linux address to a physical one (does not account
        of ASLR)"""
        if addr > 0xffffffff80000000:
            return addr - 0xffffffff80000000
        return addr - 0xc0000000


class LinuxBannerCache(symbol_cache.SymbolBannerCache):
    """Caches the banners found in the Linux symbol files."""

    os = "linux"
    symbol_name = "linux_banner"
    banner_path = constants.LINUX_BANNERS_PATH


class LinuxSymbolFinder(symbol_finder.SymbolFinder):
    """Linux symbol loader based on uname signature strings."""

    banner_config_key = "kernel_banner"
    banner_cache = LinuxBannerCache
    symbol_class = "volatility.framework.symbols.linux.LinuxKernelIntermedSymbols"
    find_aslr = lambda cls, *args: LinuxIntelStacker.find_aslr(*args)[1]
