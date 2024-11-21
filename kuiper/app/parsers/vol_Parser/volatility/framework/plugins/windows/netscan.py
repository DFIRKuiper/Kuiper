# This file is Copyright 2019 Volatility Foundation and licensed under the Volatility Software License 1.0
# which is available at https://www.volatilityfoundation.org/license/vsl-v1.0
#

import datetime
import logging
from typing import Iterable, List, Optional

from volatility.framework import constants, exceptions, interfaces, renderers, symbols
from volatility.framework.configuration import requirements
from volatility.framework.renderers import format_hints
from volatility.framework.symbols import intermed
from volatility.framework.symbols.windows.extensions import network
from volatility.plugins import timeliner
from volatility.plugins.windows import info, poolscanner

vollog = logging.getLogger(__name__)


class NetScan(interfaces.plugins.PluginInterface, timeliner.TimeLinerInterface):
    """Scans for network objects present in a particular windows memory image."""

    _required_framework_version = (2, 0, 0)
    _version = (1, 0, 0)

    @classmethod
    def get_requirements(cls):
        return [
            requirements.TranslationLayerRequirement(name = 'primary',
                                                     description = 'Memory layer for the kernel',
                                                     architectures = ["Intel32", "Intel64"]),
            requirements.SymbolTableRequirement(name = "nt_symbols", description = "Windows kernel symbols"),
            requirements.VersionRequirement(name = 'poolscanner',
                                            component = poolscanner.PoolScanner,
                                            version = (1, 0, 0)),
            requirements.VersionRequirement(name = 'info', component = info.Info, version = (1, 0, 0)),
            requirements.BooleanRequirement(
                name = 'include-corrupt',
                description =
                "Radically eases result validation. This will show partially overwritten data. WARNING: the results are likely to include garbage and/or corrupt data. Be cautious!",
                default = False,
                optional = True),
        ]

    @staticmethod
    def create_netscan_constraints(context: interfaces.context.ContextInterface,
                                   symbol_table: str) -> List[poolscanner.PoolConstraint]:
        """Creates a list of Pool Tag Constraints for network objects.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            symbol_table: The name of an existing symbol table containing the symbols / types

        Returns:
            The list containing the built constraints.
        """

        tcpl_size = context.symbol_space.get_type(symbol_table + constants.BANG + "_TCP_LISTENER").size
        tcpe_size = context.symbol_space.get_type(symbol_table + constants.BANG + "_TCP_ENDPOINT").size
        udpa_size = context.symbol_space.get_type(symbol_table + constants.BANG + "_UDP_ENDPOINT").size

        # ~ vollog.debug("Using pool size constraints: TcpL {}, TcpE {}, UdpA {}".format(tcpl_size, tcpe_size, udpa_size))

        return [
            # TCP listener
            poolscanner.PoolConstraint(b'TcpL',
                                       type_name = symbol_table + constants.BANG + "_TCP_LISTENER",
                                       size = (tcpl_size, None),
                                       page_type = poolscanner.PoolType.NONPAGED | poolscanner.PoolType.FREE),
            # TCP Endpoint
            poolscanner.PoolConstraint(b'TcpE',
                                       type_name = symbol_table + constants.BANG + "_TCP_ENDPOINT",
                                       size = (tcpe_size, None),
                                       page_type = poolscanner.PoolType.NONPAGED | poolscanner.PoolType.FREE),
            # UDP Endpoint
            poolscanner.PoolConstraint(b'UdpA',
                                       type_name = symbol_table + constants.BANG + "_UDP_ENDPOINT",
                                       size = (udpa_size, None),
                                       page_type = poolscanner.PoolType.NONPAGED | poolscanner.PoolType.FREE)
        ]

    @classmethod
    def determine_tcpip_version(cls, context: interfaces.context.ContextInterface, layer_name: str,
                                nt_symbol_table: str) -> str:
        """Tries to determine which symbol filename to use for the image's tcpip driver. The logic is partially taken from the info plugin.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            nt_symbol_table: The name of the table containing the kernel symbols

        Returns:
            The filename of the symbol table to use.
        """

        # while the failsafe way to determine the version of tcpip.sys would be to
        # extract the driver and parse its PE header containing the versionstring,
        # unfortunately that header is not guaranteed to persist within memory.
        # therefore we determine the version based on the kernel version as testing
        # with several windows versions has showed this to work out correctly.

        is_64bit = symbols.symbol_table_is_64bit(context, nt_symbol_table)

        if is_64bit:
            arch = "x64"
        else:
            arch = "x86"

        vers = info.Info.get_version_structure(context, layer_name, nt_symbol_table)

        kuser = info.Info.get_kuser_structure(context, layer_name, nt_symbol_table)

        try:
            vers_minor_version = int(vers.MinorVersion)
            nt_major_version = int(kuser.NtMajorVersion)
            nt_minor_version = int(kuser.NtMinorVersion)
        except ValueError:
            # vers struct exists, but is not an int anymore?
            raise NotImplementedError("Kernel Debug Structure version format not supported!")
        except:
            # unsure what to raise here. Also, it might be useful to add some kind of fallback,
            # either to a user-provided version or to another method to determine tcpip.sys's version
            raise exceptions.VolatilityException(
                "Kernel Debug Structure missing VERSION/KUSER structure, unable to determine Windows version!")

        vollog.debug("Determined OS Version: {}.{} {}.{}".format(kuser.NtMajorVersion, kuser.NtMinorVersion,
                                                                 vers.MajorVersion, vers.MinorVersion))

        if nt_major_version == 10 and arch == "x64":
            # win10 x64 has an additional class type we have to include.
            class_types = network.win10_x64_class_types
        else:
            # default to general class types
            class_types = network.class_types

        # these versions are listed explicitly because symbol files differ based on
        # version *and* architecture. this is currently the clearest way to show
        # the differences, even if it introduces a fair bit of redundancy.
        # furthermore, it is easy to append new versions.
        if arch == "x86":
            version_dict = {
                (6, 0, 6000): "netscan-vista-x86",
                (6, 0, 6001): "netscan-vista-x86",
                (6, 0, 6002): "netscan-vista-x86",
                (6, 0, 6003): "netscan-vista-x86",
                (6, 1, 7600): "netscan-win7-x86",
                (6, 1, 7601): "netscan-win7-x86",
                (6, 1, 8400): "netscan-win7-x86",
                (6, 2, 9200): "netscan-win8-x86",
                (6, 3, 9600): "netscan-win81-x86",
                (10, 0, 10240): "netscan-win10-x86",
                (10, 0, 10586): "netscan-win10-x86",
                (10, 0, 14393): "netscan-win10-14393-x86",
                (10, 0, 15063): "netscan-win10-15063-x86",
                (10, 0, 16299): "netscan-win10-15063-x86",
                (10, 0, 17134): "netscan-win10-15063-x86",
                (10, 0, 17763): "netscan-win10-15063-x86",
                (10, 0, 18362): "netscan-win10-15063-x86",
                (10, 0, 18363): "netscan-win10-15063-x86"
            }
        else:
            version_dict = {
                (6, 0, 6000): "netscan-vista-x64",
                (6, 0, 6001): "netscan-vista-sp12-x64",
                (6, 0, 6002): "netscan-vista-sp12-x64",
                (6, 0, 6003): "netscan-vista-sp12-x64",
                (6, 1, 7600): "netscan-win7-x64",
                (6, 1, 7601): "netscan-win7-x64",
                (6, 1, 8400): "netscan-win7-x64",
                (6, 2, 9200): "netscan-win8-x64",
                (6, 3, 9600): "netscan-win81-x64",
                (10, 0, 10240): "netscan-win10-x64",
                (10, 0, 10586): "netscan-win10-x64",
                (10, 0, 14393): "netscan-win10-x64",
                (10, 0, 15063): "netscan-win10-15063-x64",
                (10, 0, 16299): "netscan-win10-15063-x64",
                (10, 0, 17134): "netscan-win10-15063-x64",
                (10, 0, 17763): "netscan-win10-15063-x64",
                (10, 0, 18362): "netscan-win10-15063-x64",
                (10, 0, 18363): "netscan-win10-15063-x64"
            }

        # when determining the symbol file we have to consider the following cases:
        # the determined version's symbol file is found by intermed.create -> proceed
        # the determined version's symbol file is not found by intermed -> intermed will throw an exc and abort
        # the determined version has no mapped symbol file -> if win10 use latest, otherwise throw exc
        # windows version cannot be determined -> throw exc
        filename = version_dict.get((nt_major_version, nt_minor_version, vers_minor_version))
        if not filename:
            if nt_major_version == 10:
                # NtMajorVersion of 10 without a match means a newer version than listed
                # hence try the latest supported version. If this one throws an error,
                # support has to be added manually.
                win_10_versions = sorted([key for key in list(version_dict.keys()) if key[0] == 10])
                # as win10 MinorVersion counts upwards we can take the last entry
                latest_version = win_10_versions[-1]
                filename = version_dict.get(latest_version)
                vollog.debug("Unable to find exact matching symbol file, going with latest: {}".format(filename))
            else:
                raise NotImplementedError("This version of Windows is not supported: {}.{} {}.{}!".format(
                    nt_major_version, nt_minor_version, vers.MajorVersion, vers_minor_version))

        vollog.debug("Determined symbol filename: {}".format(filename))

        return filename, class_types

    @classmethod
    def create_netscan_symbol_table(cls, context: interfaces.context.ContextInterface, layer_name: str,
                                    nt_symbol_table: str, config_path: str) -> str:
        """Creates a symbol table for TCP Listeners and TCP/UDP Endpoints.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            nt_symbol_table: The name of the table containing the kernel symbols
            config_path: The config path where to find symbol files

        Returns:
            The name of the constructed symbol table
        """
        table_mapping = {"nt_symbols": nt_symbol_table}

        symbol_filename, class_types = cls.determine_tcpip_version(
            context,
            layer_name,
            nt_symbol_table,
        )

        return intermed.IntermediateSymbolTable.create(context,
                                                       config_path,
                                                       "windows",
                                                       symbol_filename,
                                                       class_types = class_types,
                                                       table_mapping = table_mapping)

    @classmethod
    def scan(cls,
             context: interfaces.context.ContextInterface,
             layer_name: str,
             nt_symbol_table: str,
             netscan_symbol_table: str) -> \
            Iterable[interfaces.objects.ObjectInterface]:
        """Scans for network objects using the poolscanner module and constraints.

        Args:
            context: The context to retrieve required elements (layers, symbol tables) from
            layer_name: The name of the layer on which to operate
            nt_symbol_table: The name of the table containing the kernel symbols
            netscan_symbol_table: The name of the table containing the network object symbols (_TCP_LISTENER etc.)

        Returns:
            A list of network objects found by scanning the `layer_name` layer for network pool signatures
        """

        constraints = cls.create_netscan_constraints(context, netscan_symbol_table)

        for result in poolscanner.PoolScanner.generate_pool_scan(context, layer_name, nt_symbol_table, constraints):

            _constraint, mem_object, _header = result
            yield mem_object

    def _generator(self, show_corrupt_results: Optional[bool] = None):
        """ Generates the network objects for use in rendering. """

        netscan_symbol_table = self.create_netscan_symbol_table(self.context, self.config["primary"],
                                                                self.config["nt_symbols"], self.config_path)

        for netw_obj in self.scan(self.context, self.config['primary'], self.config['nt_symbols'],
                                  netscan_symbol_table):

            vollog.debug("Found netw obj @ 0x{:2x} of assumed type {}".format(netw_obj.vol.offset, type(netw_obj)))
            # objects passed pool header constraints. check for additional constraints if strict flag is set.
            if not show_corrupt_results and not netw_obj.is_valid():
                continue

            if isinstance(netw_obj, network._UDP_ENDPOINT):
                vollog.debug("Found UDP_ENDPOINT @ 0x{:2x}".format(netw_obj.vol.offset))

                # For UdpA, the state is always blank and the remote end is asterisks
                for ver, laddr, _ in netw_obj.dual_stack_sockets():
                    yield (0, (format_hints.Hex(netw_obj.vol.offset), "UDP" + ver, laddr, netw_obj.Port, "*", 0, "",
                               netw_obj.get_owner_pid() or renderers.UnreadableValue(), netw_obj.get_owner_procname()
                               or renderers.UnreadableValue(), netw_obj.get_create_time()
                               or renderers.UnreadableValue()))

            elif isinstance(netw_obj, network._TCP_ENDPOINT):
                vollog.debug("Found _TCP_ENDPOINT @ 0x{:2x}".format(netw_obj.vol.offset))
                if netw_obj.get_address_family() == network.AF_INET:
                    proto = "TCPv4"
                elif netw_obj.get_address_family() == network.AF_INET6:
                    proto = "TCPv6"
                else:
                    proto = "TCPv?"

                try:
                    state = netw_obj.State.description
                except ValueError:
                    state = renderers.UnreadableValue()

                yield (0, (format_hints.Hex(netw_obj.vol.offset), proto, netw_obj.get_local_address()
                           or renderers.UnreadableValue(), netw_obj.LocalPort, netw_obj.get_remote_address()
                           or renderers.UnreadableValue(), netw_obj.RemotePort, state, netw_obj.get_owner_pid()
                           or renderers.UnreadableValue(), netw_obj.get_owner_procname() or renderers.UnreadableValue(),
                           netw_obj.get_create_time() or renderers.UnreadableValue()))

            # check for isinstance of tcp listener last, because all other objects are inherited from here
            elif isinstance(netw_obj, network._TCP_LISTENER):
                vollog.debug("Found _TCP_LISTENER @ 0x{:2x}".format(netw_obj.vol.offset))

                # For TcpL, the state is always listening and the remote port is zero
                for ver, laddr, raddr in netw_obj.dual_stack_sockets():
                    yield (0, (format_hints.Hex(netw_obj.vol.offset), "TCP" + ver, laddr, netw_obj.Port, raddr, 0,
                               "LISTENING", netw_obj.get_owner_pid() or renderers.UnreadableValue(),
                               netw_obj.get_owner_procname() or renderers.UnreadableValue(), netw_obj.get_create_time()
                               or renderers.UnreadableValue()))
            else:
                # this should not happen therefore we log it.
                vollog.debug("Found network object unsure of its type: {} of type {}".format(netw_obj, type(netw_obj)))

    def generate_timeline(self):
        for row in self._generator():
            _depth, row_data = row
            # Skip network connections without creation time
            if not isinstance(row_data[9], datetime.datetime):
                continue
            row_data = [
                "N/A" if isinstance(i, renderers.UnreadableValue) or isinstance(i, renderers.UnparsableValue) else i
                for i in row_data
            ]
            description = "Network connection: Process {} {} Local Address {}:{} " \
                          "Remote Address {}:{} State {} Protocol {} ".format(row_data[7], row_data[8],
                                                                              row_data[2], row_data[3],
                                                                              row_data[4], row_data[5],
                                                                              row_data[6], row_data[1])
            yield (description, timeliner.TimeLinerType.CREATED, row_data[9])

    def run(self):
        show_corrupt_results = self.config.get('include-corrupt', None)

        return renderers.TreeGrid([
            ("Offset", format_hints.Hex),
            ("Proto", str),
            ("LocalAddr", str),
            ("LocalPort", int),
            ("ForeignAddr", str),
            ("ForeignPort", int),
            ("State", str),
            ("PID", int),
            ("Owner", str),
            ("Created", datetime.datetime),
        ], self._generator(show_corrupt_results = show_corrupt_results))
