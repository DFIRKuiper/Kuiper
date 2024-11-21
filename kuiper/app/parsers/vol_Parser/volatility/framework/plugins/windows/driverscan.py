# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

from typing import Iterable

from volatility.framework import renderers, interfaces, exceptions
from volatility.framework.configuration import requirements
from volatility.framework.renderers import format_hints
from volatility.plugins.windows import poolscanner


class DriverScan(interfaces.plugins.PluginInterface):
    """Scans for drivers present in a particular windows memory image."""

    _required_framework_version = (2, 0, 0)
    _version = (1, 0, 0)

    @classmethod
    def get_requirements(cls):
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "nt_symbols", description = "Windows kernel symbols"),
            requirements.PluginRequirement(name = 'poolscanner', plugin = poolscanner.PoolScanner, version = (1, 0, 0)),
        ]

    @classmethod
    def scan_drivers(cls,
                     context: interfaces.context.ContextInterface,
                     layer_name: str,
                     symbol_table: str) -> \
            Iterable[interfaces.objects.ObjectInterface]:
        """Scans for drivers using the poolscanner module and constraints.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            symbol_table: The name of the table containing the kernel symbols

        Returns:
            A list of Driver objects as found from the `layer_name` layer based on Driver pool signatures
        """

        constraints = poolscanner.PoolScanner.builtin_constraints(symbol_table, [b'Dri\xf6', b'Driv'])

        for result in poolscanner.PoolScanner.generate_pool_scan(context, layer_name, symbol_table, constraints):

            _constraint, mem_object, _header = result
            yield mem_object

    def _generator(self):
        for driver in self.scan_drivers(self.context, self.config['primary'], self.config['nt_symbols']):

            try:
                driver_name = driver.get_driver_name()
            except (ValueError, exceptions.InvalidAddressException):
                driver_name = renderers.NotApplicableValue()

            try:
                service_key = driver.DriverExtension.ServiceKeyName.String
            except exceptions.InvalidAddressException:
                service_key = renderers.NotApplicableValue()

            try:
                name = driver.DriverName.String
            except exceptions.InvalidAddressException:
                name = renderers.NotApplicableValue()

            yield (0, (format_hints.Hex(driver.vol.offset), format_hints.Hex(driver.DriverStart),
                       format_hints.Hex(driver.DriverSize), service_key, driver_name, name))

    def run(self):
        return renderers.TreeGrid([("Offset", format_hints.Hex),
                                   ("Start", format_hints.Hex), ("Size", format_hints.Hex), ("Service Key", str),
                                   ("Driver Name", str), ("Name", str)], self._generator())
