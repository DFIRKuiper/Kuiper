How to Write a Simple Plugin
============================

This guide will step through how to construct a simple plugin using Volatility 3.

The example plugin we'll use is :py:class:`~volatility.plugins.windows.dlllist.DllList`, which features the main traits
of a normal plugin, and reuses other plugins appropriately.

Inherit from PluginInterface
----------------------------

The first step is to define a class that inherits from :py:class:`~volatility.framework.interfaces.plugins.PluginInterface`.
Volatility automatically finds all plugins defined under the various plugin directories by importing them and then
making use of any classes that inherit from :py:class:`~volatility.framework.interfaces.plugins.PluginInterface`.

::

    from volatility.framework import interfaces

    class DllList(interfaces.plugins.PluginInterface):

The next step is to define the requirements of the plugin, these will be converted into options the user can provide
based on the User Interface.

Define the plugin requirements
------------------------------

These requirements are the names of variables that will need to be populated in the configuration tree for the plugin
to be able to run properly.  Any that are defined as optional need not necessarily be provided.

::

        @classmethod
        def get_requirements(cls):
            return [requirements.TranslationLayerRequirement(name = 'primary',
                                                             description = 'Memory layer for the kernel',
                                                             architectures = ["Intel32", "Intel64"]),
                    requirements.SymbolTableRequirement(name = "nt_symbols",
                                                        description = "Windows kernel symbols"),
                    requirements.PluginRequirement(name = 'pslist',
                                                   plugin = pslist.PsList,
                                                   version = (1, 0, 0)),
                    requirements.ListRequirement(name = 'pid',
                                                 element_type = int,
                                                 description = "Process IDs to include (all other processes are excluded)",
                                                 optional = True)]


This is a classmethod, because it is called before the specific plugin object has been instantiated (in order to know how
to instantiate the plugin).  At the moment these requirements are fairly straightforward:

::

    requirements.TranslationLayerRequirement(name = 'primary',
                                             description = 'Memory layer for the kernel',
                                             architectures = ["Intel32", "Intel64"]),

This requirement indicates that the plugin will operate on a single
:py:class:`TranslationLayer <volatility.framework.interfaces.layers.TranslationLayerInterface>`.  The name of the
loaded layer will appear in the plugin's configuration under the name ``primary``.    Requirement values can be
accessed within the plugin through the plugin's `config` attribute (for example ``self.config['pid']``).

.. note:: The name itself is dynamic depending on the other layers already present in the Context.  Always use the value
    from the configuration rather than attempting to guess what the layer will be called.

Finally, this defines that the translation layer must be on the Intel Architecture.  At the moment, this acts as a filter,
failing to be satisfied by memory images that do not match the architecture required.

Most plugins will only operate on a single layer, but it is entirely possible for a plugin to request two different
layers, for example a plugin that carries out some form of difference or statistics against multiple memory images.

This requirement (and the next two) are known as Complex Requirements, and user interfaces will likely not directly
request a value for this from a user.  The value stored in the configuration tree for a
:py:class:`~volatility.framework.configuration.requirements.TranslationLayerRequirement` is
the string name of a layer present in the context's memory that satisfies the requirement.

::

    requirements.SymbolTableRequirement(name = "nt_symbols",
                                        description = "Windows kernel symbols"),

This requirement specifies the need for a particular
:py:class:`SymbolTable <volatility.framework.interfaces.symbols.SymbolTableInterface>`
to be loaded.  This gets populated by various
:py:class:`Automagic <volatility.framework.interfaces.automagic.AutoMagicInterface>` as the nearest sibling to a particular
:py:class:`~volatility.framework.configuration.requirements.TranslationLayerRequirement`.
This means that if the :py:class:`~volatility.framework.configuration.requirements.TranslationLayerRequirement`
is satisfied and the :py:class:`Automagic <volatility.framework.interfaces.automagic.AutoMagicInterface>` can determine
the appropriate :py:class:`SymbolTable <volatility.framework.interfaces.symbols.SymbolTableInterface>`, the
name of the :py:class:`SymbolTable <volatility.framework.interfaces.symbols.SymbolTableInterface>` will be stored in the configuration.

This requirement is also a Complex Requirement and therefore will not be requested directly from the user.

::

    requirements.PluginRequirement(name = 'pslist',
                                   plugin = pslist.PsList,
                                   version = (1, 0, 0)),

This requirement indicates that the plugin will make use of another plugin's code, and specifies the version requirements
on that plugin.  The version is specified in terms of Semantic Versioning, meaning that to be compatible, the major
versions must be identical and the minor version must be equal to or higher than the one provided.  This requirement
does not make use of any data from the configuration, even if it were provided, it is merely a functional check before
running the plugin.

::

    requirements.ListRequirement(name = 'pid',
                                 description = 'Filter on specific process IDs',
                                 element_type = int,
                                 optional = True)

The final requirement is a List Requirement, populated by integers.  The description will be presented to the user to
describe what the value represents.  The optional flag indicates that the plugin can function without the ``pid`` value
being defined within the configuration tree at all.

Define the `run` method
-----------------------

The run method is the primary method called on a plugin.  It takes no parameters (these have been passed through the
context's configuration tree, and the context is provided at plugin initialization time) and returns an unpopulated
:py:class:`~volatility.framework.interfaces.renderers.TreeGrid` object.  These are typically constructed based on a
generator that carries out the bulk of the plugin's processing.  The
:py:class:`~volatility.framework.interfaces.renderers.TreeGrid` also specifies the column names and types
that will be output as part of the :py:class:`~volatility.framework.interfaces.renderers.TreeGrid`.

::

        def run(self):

            filter_func = pslist.PsList.create_pid_filter(self.config.get('pid', None))

            return renderers.TreeGrid([("PID", int),
                                       ("Process", str),
                                       ("Base", format_hints.Hex),
                                       ("Size", format_hints.Hex),
                                       ("Name", str),
                                       ("Path", str)],
                                      self._generator(pslist.PsList.list_processes(self.context,
                                                                                   self.config['primary'],
                                                                                   self.config['nt_symbols'],
                                                                                   filter_func = filter_func)))

In this instance, the plugin constructs a filter (using the PsList plugin's *classmethod* for creating filters).
It checks the plugin's configuration for the ``pid`` value, and passes it in as a list if it finds it, or None if
it does not.  The :py:func:`~volatility.plugins.windows.pslist.PsList.create_pid_filter` method accepts a list of process
identifiers that are included in the list. If the list is empty, all processes are returned.

The next line specifies the columns by their name and type.  The types are simple types (int, str, bytes, float, and bool)
but can also provide hints as to how the output should be displayed (such as a hexidecimal number, using
:py:class:`volatility.framework.renderers.format_hints.Hex`).
This indicates to user interfaces that the value should be displayed in a particular way, but does not guarantee that the value
will be displayed that way (for example, if it doesn't make sense to do so in a particular interface).

Finally, the generator is provided.  The generator accepts a list of processes, which is gathered using a different plugin,
the :py:class:`~volatility.plugins.windows.pslist.PsList` plugin.  That plugin features a *classmethod*,
so that other plugins can call it.  As such, it takes all the necessary parameters rather than accessing them
from a configuration.  Since it must be portable code, it takes a context, as well as the layer name,
symbol table and optionally a filter.  In this instance we unconditionally
pass it the values from the configuration for the ``primary`` and ``nt_symbols`` requirements.  This will generate a list
of :py:class:`~volatility.framework.symbols.windows.extensions.EPROCESS` objects, as provided by the :py:class:`~volatility.plugins.windows.pslist.PsList` plugin,
and is not covered here but is used as an example for how to share code across plugins
(both as the provider and the consumer of the shared code).

Define the generator
--------------------
The :py:class:`~volatility.framework.interfaces.renderers.TreeGrid` can be populated without a generator,
but it is quite a common model to use.  This is where the main processing for this plugin lives.

::

        def _generator(self, procs):

            for proc in procs:

                for entry in proc.load_order_modules():

                    BaseDllName = FullDllName = renderers.UnreadableValue()
                    try:
                        BaseDllName = entry.BaseDllName.get_string()
                        # We assume that if the BaseDllName points to an invalid buffer, so will FullDllName
                        FullDllName = entry.FullDllName.get_string()
                    except exceptions.InvalidAddressException:
                        pass

                    yield (0, (proc.UniqueProcessId,
                               proc.ImageFileName.cast("string", max_length = proc.ImageFileName.vol.count,
                                                       errors = 'replace'),
                               format_hints.Hex(entry.DllBase), format_hints.Hex(entry.SizeOfImage),
                               BaseDllName, FullDllName))

This iterates through the list of processes and for each one calls the :py:meth:`~volatility.framework.symbols.windows.extensions.EPROCESS.load_order_modules` method on it.  This provides
a list of the loaded modules within the process.

The plugin then defaults the ``BaseDllName`` and ``FullDllName`` variables to an :py:class:`~volatility.framework.renderers.UnreadableValue`,
which is a way of indicating to the user interface that the value couldn't be read for some reason (but that it isn't fatal).
There are currently four different reasons a value may be unreadable:

* **Unreadble**: values which are empty because the data cannot be read
* **Unparsable**: values which are empty because the data cannot be interpreted correctly
* **NotApplicable**: values which are empty because they don't make sense for this particular entry
* **NotAvailable**: values which cannot be provided now (but might in a future run, via new symbols or an updated plugin)

This is a safety provision to ensure that the data returned by the Volatility library is accurate and describes why
information may not be provided.

The plugin then takes the process's ``BaseDllName`` value, and calls :py:meth:`~volatility.framework.symbols.windows.extensions.UNICODE_STRING.get_string` on it.  All structure attributes,
as defined by the symbols, are directly accessible and use the case-style of the symbol library it came from (in Windows,
attributes are CamelCase), such as ``entry.BaseDllName`` in this instance.  Any attribtues not defined by the symbol but added
by Volatility extensions cannot be properties (in case they overlap with the attributes defined in the symbol libraries)
and are therefore always methods and prepended with ``get_``, in this example ``BaseDllName.get_string()``.

Finally, ``FullDllName`` is populated.  These operations read from memory, and as such, the memory image may be unable to
read the data at a particular offset.  This will cause an exception to be thrown.  In Volatility 3, exceptions are thrown
as a means of communicating when something exceptional happens.  It is the responsibility of the plugin developer to
appropriately catch and handle any non-fatal exceptions and otherwise allow the exception to be thrown by the user interface.

In this instance, the :py:class:`~volatility.framework.exceptions.InvalidAddressException` class is caught, which is thrown
by any layer which cannot access an offset requested of it.  Since we have already populated both values with ``UnreadableValue``
we do not need to write code for the exception handler.

Finally, we yield the record in the format required by the :py:class:`~volatility.framework.interfaces.renderers.TreeGrid`,
a tuple, listing the indentation level (for trees) and then the list of values for each column.
This plugin demonstrates casting a value ``ImageFileName`` to ensure it's returned
as a string with a specific maximum length, rather than its original type (potentially an array of characters, etc).
This is carried out using the :py:meth:`~volatility.framework.interfaces.objects.ObjectInterface.cast` method which takes a type (either a native type, such as string or pointer, or a
structure type defined in a :py:class:`SymbolTable <volatility.framework.interfaces.symbols.SymbolTableInterface>`
such as ``<table>!_UNICODE``) and the parameters to that type.

Since the cast value must populate a string typed column, it had to be a Python string (such as being cast to the native
type string) and could not have been a special Structure such as ``_UNICODE``.  For the format hint columns, the format
hint type must be used to ensure the error checking does not fail.


