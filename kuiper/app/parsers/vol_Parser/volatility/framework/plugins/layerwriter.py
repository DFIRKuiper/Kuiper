# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

import logging
from typing import List, Optional, Type

from volatility.framework import renderers, interfaces, constants, exceptions
from volatility.framework.configuration import requirements
from volatility.framework.interfaces import plugins

vollog = logging.getLogger(__name__)


class LayerWriter(plugins.PluginInterface):
    """Runs the automagics and writes out the primary layer produced by the stacker."""

    default_block_size = 0x500000

    _required_framework_version = (2, 0, 0)
    _version = (2, 0, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.IntRequirement(name = 'block_size',
                                        description = "Size of blocks to copy over",
                                        default = cls.default_block_size,
                                        optional = True),
            requirements.BooleanRequirement(name = 'list',
                                            description = 'List available layers',
                                            default = False,
                                            optional = True),
            requirements.ListRequirement(name = 'layers',
                                         element_type = str,
                                         description = 'Names of layer to write',
                                         default = None,
                                         optional = True)
        ]

    @classmethod
    def write_layer(
            cls,
            context: interfaces.context.ContextInterface,
            layer_name: str,
            preferred_name: str,
            open_method: Type[plugins.FileHandlerInterface],
            chunk_size: Optional[int] = None,
            progress_callback: Optional[constants.ProgressCallback] = None) -> Optional[plugins.FileHandlerInterface]:
        """Produces a FileHandler from the named layer in the provided context or None on failure

        Args:
            context: the context from which to read the memory layer
            layer_name: the name of the layer to write out
            preferred_name: a string with the preferred filename for hte file
            chunk_size: an optional size for the chunks that should be written (defaults to 0x500000)
            open_method: class for creating FileHandler context managers
            progress_callback: an optional function that takes a percentage and a string that displays output
        """

        if layer_name not in context.layers:
            raise exceptions.LayerException("Layer not found")
        layer = context.layers[layer_name]

        if chunk_size is None:
            chunk_size = cls.default_block_size

        file_handle = open_method(preferred_name)
        for i in range(0, layer.maximum_address, chunk_size):
            current_chunk_size = min(chunk_size, layer.maximum_address - i)
            data = layer.read(i, current_chunk_size, pad = True)
            file_handle.write(data)
            if progress_callback:
                progress_callback((i / layer.maximum_address) * 100, 'Writing layer {}'.format(layer_name))
        return file_handle

    def _generator(self):
        if self.config['list']:
            for name in self.context.layers:
                yield 0, (name,)
        else:
            import pdb
            pdb.set_trace()
            # Choose the most recently added layer that isn't virtual
            if self.config['layers'] is None:
                self.config['layers'] = []
                for name in self.context.layers:
                    if not self.context.layers[name].metadata.get('mapped', False):
                        self.config['layers'] = [name]

            for name in self.config['layers']:
                # Check the layer exists and validate the output file
                if name not in self.context.layers:
                    yield 0, ('Layer Name {} does not exist'.format(name),)
                else:
                    output_name = self.config.get('output', ".".join([name, "raw"]))
                    try:
                        file_handle = self.write_layer(self.context,
                                                       name,
                                                       output_name,
                                                       self.open,
                                                       self.config.get('block_size', self.default_block_size),
                                                       progress_callback = self._progress_callback)
                        file_handle.close()
                    except IOError as excp:
                        yield 0, ('Layer cannot be written to {}: {}'.format(self.config['output_name'], excp),)

                    yield 0, ('Layer has been written to {}'.format(output_name),)

    def _generate_layers(self):
        """List layer names from this run"""
        for name in self.context.layers:
            yield (0, (name,))

    def run(self):
        if self.config['list']:
            return renderers.TreeGrid([("Layer name", str)], self._generate_layers())
        return renderers.TreeGrid([("Status", str)], self._generator())
