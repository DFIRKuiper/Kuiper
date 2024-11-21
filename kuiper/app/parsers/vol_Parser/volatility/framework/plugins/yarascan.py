# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

import logging
from typing import Iterable, Tuple, List, Dict, Any

from volatility.framework import interfaces, renderers
from volatility.framework.configuration import requirements
from volatility.framework.interfaces import plugins
from volatility.framework.layers import resources
from volatility.framework.renderers import format_hints

vollog = logging.getLogger(__name__)

try:
    import yara
except ImportError:
    vollog.info("Python Yara module not found, plugin (and dependent plugins) not available")
    raise


class YaraScanner(interfaces.layers.ScannerInterface):
    _version = (2, 0, 0)

    # yara.Rules isn't exposed, so we can't type this properly
    def __init__(self, rules) -> None:
        super().__init__()
        self._rules = rules

    def __call__(self, data: bytes, data_offset: int) -> Iterable[Tuple[int, str, str, bytes]]:
        for match in self._rules.match(data = data):
            for offset, name, value in match.strings:
                yield (offset + data_offset, match.rule, name, value)


class YaraScan(plugins.PluginInterface):
    """Scans kernel memory using yara rules (string or file)."""

    _required_framework_version = (2, 0, 0)
    _version = (1, 0, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = "Memory layer for the kernel",
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.BooleanRequirement(name = "insensitive",
                                            description = "Makes the search case insensitive",
                                            default = False,
                                            optional = True),
            requirements.BooleanRequirement(name = "wide",
                                            description = "Match wide (unicode) strings",
                                            default = False,
                                            optional = True),
            requirements.StringRequirement(name = "yara_rules",
                                           description = "Yara rules (as a string)",
                                           optional = True),
            requirements.URIRequirement(name = "yara_file", description = "Yara rules (as a file)", optional = True),
            requirements.IntRequirement(name = "max_size",
                                        default = 0x40000000,
                                        description = "Set the maximum size (default is 1GB)",
                                        optional = True)
        ]

    @classmethod
    def process_yara_options(cls, config: Dict[str, Any]):
        rules = None
        if config.get('yara_rules', None) is not None:
            rule = config['yara_rules']
            if rule[0] not in ["{", "/"]:
                rule = '"{}"'.format(rule)
            if config.get('case', False):
                rule += " nocase"
            if config.get('wide', False):
                rule += " wide ascii"
            rules = yara.compile(sources = {'n': 'rule r1 {{strings: $a = {} condition: $a}}'.format(rule)})
        elif config.get('yara_file', None) is not None:
            rules = yara.compile(file = resources.ResourceAccessor().open(config['yara_file'], "rb"))
        else:
            vollog.error("No yara rules, nor yara rules file were specified")
        return rules

    def _generator(self):
        rules = self.process_yara_options(dict(self.config))

        layer = self.context.layers[self.config['primary']]
        for offset, rule_name, name, value in layer.scan(context = self.context, scanner = YaraScanner(rules = rules)):
            yield 0, (format_hints.Hex(offset), rule_name, name, value)

    def run(self):
        return renderers.TreeGrid([('Offset', format_hints.Hex), ('Rule', str), ('Component', str), ('Value', bytes)],
                                  self._generator())
