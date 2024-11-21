from typing import List

from volatility import framework
from volatility.framework import interfaces, renderers
from volatility.framework.interfaces import plugins


class FrameworkInfo(plugins.PluginInterface):
    """Plugin to list the various modular components of Volatility"""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls) -> List[interfaces.configuration.RequirementInterface]:
        return []

    def _generator(self):
        categories = {
            'Automagic': interfaces.automagic.AutomagicInterface,
            'Requirement': interfaces.configuration.RequirementInterface,
            'Layer': interfaces.layers.DataLayerInterface,
            'LayerStacker': interfaces.automagic.StackerLayerInterface,
            'Object': interfaces.objects.ObjectInterface,
            'Plugin': interfaces.plugins.PluginInterface,
            'Renderer': interfaces.renderers.Renderer
        }

        for category, module_interface in categories.items():
            yield (0, (category, ))
            for clazz in framework.class_subclasses(module_interface):
                yield (1, (clazz.__name__, ))

    def run(self):
        return renderers.TreeGrid([("Data", str)], self._generator())
