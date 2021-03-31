
import io
import os 
from urllib import request
import json 
import datetime
import argparse

import volatility.plugins
from volatility.framework import automagic, constants, contexts, exceptions, interfaces, plugins, configuration
from volatility import framework

from volatility import framework

import volatility.framework.interfaces.renderers
from volatility.framework.interfaces.renderers import RenderOption
from volatility.framework.interfaces.configuration import *
from volatility.framework.automagic import stacker
from volatility.framework.renderers import format_hints

from volatility.cli import text_renderer, volargparse

import parser_plugins



# return json in a beautifier
def json_beautifier(js):
    return json.dumps(js, indent=4, sort_keys=True)

# this dictionary contains the list of plugins information
plugin_info_dict = {
    'mem_info'          : {'name': 'windows.info.Info'                          , 'function': parser_plugins.mem_info.imain},
    'mem_cmdline'       : {'name': 'windows.cmdline.CmdLine'                    , 'function': parser_plugins.mem_cmdline.imain},
    'mem_dlllist'       : {'name': 'windows.dlllist.DllList'                    , 'function': parser_plugins.mem_dlllist.imain},
    'mem_pslist'        : {'name': 'windows.pslist.PsList'                      , 'function': parser_plugins.mem_pslist.imain},
    'mem_FileScan'      : {'name': 'windows.filescan.FileScan'                  , 'function': parser_plugins.mem_FileScan.imain},
    'mem_ProcessSID'    : {'name': 'windows.getsids.GetSIDs'                    , 'function': parser_plugins.mem_ProcessSID.imain},
    'mem_handles'       : {'name': 'windows.handles.Handles'                    , 'function': parser_plugins.mem_handles.imain},
    'mem_ModScan'       : {'name': 'windows.modscan.ModScan'                    , 'function': parser_plugins.mem_ModScan.imain},
    'mem_Modules'       : {'name': 'windows.modules.Modules'                    , 'function': parser_plugins.mem_Modules.imain},
    'mem_mutantScan'    : {'name': 'windows.mutantscan.MutantScan'              , 'function': parser_plugins.mem_mutantScan.imain},
    'mem_netScan'       : {'name': 'windows.netscan.NetScan'                    , 'function': parser_plugins.mem_netScan.imain},
    'mem_ProcessPrivs'  : {'name': 'windows.privileges.Privs'                   , 'function': parser_plugins.mem_ProcessPrivs.imain},
    'mem_hiveList'      : {'name': 'windows.registry.hivelist.HiveList'         , 'function': parser_plugins.mem_hiveList.imain},
    'mem_userAssist'    : {'name': 'windows.registry.userassist.UserAssist'     , 'function': parser_plugins.mem_userAssist.imain},
    'mem_SSDT'          : {'name': 'windows.ssdt.SSDT'                          , 'function': parser_plugins.mem_SSDT.imain},
    'mem_symlink'       : {'name': 'windows.symlinkscan.SymlinkScan'            , 'function': parser_plugins.mem_symlink.imain},
    'mem_vadInfo'       : {'name': 'windows.vadinfo.VadInfo'                    , 'function': parser_plugins.mem_vadInfo.imain},
    'mem_virtMap'       : {'name': 'windows.virtmap.VirtMap'                    , 'function': parser_plugins.mem_virtMap.imain},
    'mem_timeliner'     : {'name': 'timeliner.Timeliner'                        , 'function': parser_plugins.mem_timeliner.imain},
    'mem_envars'        : {'name': 'windows.envars.Envars'                      , 'function': parser_plugins.mem_envars.imain}
}


class PrintedProgress(object):
    """A progress handler that prints the progress value and the description
    onto the command line."""

    def __init__(self):
        self._max_message_len = 0

    def __call__(self, progress: Union[int, float], description: str = None):
        """A simple function for providing text-based feedback.

        .. warning:: Only for development use.

        Args:
            progress: Percentage of progress of the current procedure
        """
        message = "\rProgress: {0: 7.2f}\t\t{1:}".format(round(progress, 2), description or '')
        message_len = len(message)
        self._max_message_len = max([self._max_message_len, message_len])

class Vol_Parser():
    
    _type_renderers = {
        format_hints.HexBytes: text_renderer.quoted_optional(text_renderer.hex_bytes_as_text),
        volatility.framework.interfaces.renderers.Disassembly: text_renderer.quoted_optional(text_renderer.display_disassembly),
        datetime.datetime: lambda x: x.isoformat() if not isinstance(x, volatility.framework.interfaces.renderers.BaseAbsentValue) else None,
        volatility.framework.renderers.UnreadableValue: lambda x: None,
        'default': lambda x: x
    }

    # this function to parse the TreeGrid object into json format
    def render(self, grid: interfaces.renderers.TreeGrid):
        outfd = sys.stdout

        final_output = (
            {}, [])  # type: Tuple[Dict[str, List[interfaces.renderers.TreeNode]], List[interfaces.renderers.TreeNode]]

        
        def visitor(
                node: interfaces.renderers.TreeNode,
                accumulator: Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]
        ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
            # Nodes always have a path value, giving them a path_depth of at least 1, we use max just in case
            
            acc_map, final_tree = accumulator
            
            node_dict = {'__children': []}  # type: Dict[str, Any]
            for column_index in range(len(grid.columns)):
                column = grid.columns[column_index]
                renderer = self._type_renderers.get(column.type, self._type_renderers['default'])
                data = renderer(list(node.values)[column_index])
                if isinstance(data, interfaces.renderers.BaseAbsentValue):
                    data = None
                node_dict[column.name] = data

            if node.parent:
                acc_map[node.parent.path]['__children'].append(node_dict)
            else:
                final_tree.append(node_dict)
            
            acc_map[node.path] = node_dict
            
            return (acc_map, final_tree)
        
        if not grid.populated:
            grid.populate(visitor, final_output)
        else:
            grid.visit(node = None, function = visitor, initial_accumulator = final_output)
        return final_output[1]


    # this is for output file handle
    def file_handler_class_factory( self, direct = True):
        output_dir = 'out'

        class CLIFileHandler(interfaces.plugins.FileHandlerInterface):

            def _get_final_filename(self):
                """Gets the final filename"""
                if output_dir is None:
                    raise TypeError("Output directory is not a string")
                os.makedirs(output_dir, exist_ok = True)

                pref_name_array = self.preferred_filename.split('.')
                filename, extension = os.path.join(output_dir, '.'.join(pref_name_array[:-1])), pref_name_array[-1]
                output_filename = "{}.{}".format(filename, extension)

                counter = 1
                while os.path.exists(output_filename):
                    output_filename = "{}-{}.{}".format(filename, counter, extension)
                    counter += 1
                return output_filename

        class CLIMemFileHandler(io.BytesIO, CLIFileHandler):
            def __init__(self, filename: str):
                io.BytesIO.__init__(self)
                CLIFileHandler.__init__(self, filename)

            def close(self):
                # Don't overcommit
                if self.closed:
                    return

                self.seek(0)

                output_filename = self._get_final_filename()

                with open(output_filename, "wb") as current_file:
                    current_file.write(self.read())
                    self._committed = True
                    vollog.log(logging.INFO, "Saved stored plugin file: {}".format(output_filename))

                super().close()

        class CLIDirectFileHandler(CLIFileHandler):
            def __init__(self, filename: str):
                fd, self._name = tempfile.mkstemp(suffix = '.vol3', prefix = 'tmp_', dir = output_dir)
                self._file = io.open(fd, mode = 'w+b')
                CLIFileHandler.__init__(self, filename)
                for item in dir(self._file):
                    if not item.startswith('_') and not item in ['closed', 'close', 'mode', 'name']:
                        setattr(self, item, getattr(self._file, item))

            def __getattr__(self, item):
                return getattr(self._file, item)

            @property
            def closed(self):
                return self._file.closed

            @property
            def mode(self):
                return self._file.mode

            @property
            def name(self):
                return self._file.name

            def close(self):
                """Closes and commits the file (by moving the temporary file to the correct name"""
                # Don't overcommit
                if self._file.closed:
                    return

                self._file.close()
                output_filename = self._get_final_filename()
                os.rename(self._name, output_filename)

        if direct:
            return CLIDirectFileHandler
        else:
            return CLIMemFileHandler

    def __init__(self, image_path, plugin_name, plugins_path):
        framework.require_interface_version(2, 0, 0)

        # import the plugin files
        failures = framework.import_files(volatility.plugins, True)
        
        # load the framework plugins list
        plugin_list = framework.list_plugins()
        
        plugin_info = self.getPlugin(plugin_name)
        if plugin_info is None:
            raise Exception("Plugin information for ["+plugin_name+"] not found")
        plugin_info['obj'] = plugin_list[plugin_info['name']]

        # image path
        file_name = os.path.abspath(image_path)
        if not os.path.exists(file_name):
            raise Exception("File does not exist: {}".format(file_name))
            
        # set context
        self.ctx = contexts.Context()  # Construct a blank context
        automagics = automagic.available(self.ctx)
        automagics = automagic.choose_automagic(automagics, plugin_info['obj'])

        single_location = "file:" + request.pathname2url(file_name)
        self.ctx.config['automagic.LayerStacker.single_location'] = single_location

        
        # build plugin context
        base_config_path = os.path.abspath(plugins_path)
        progress_callback = PrintedProgress()
        

        constructed = plugins.construct_plugin(self.ctx, automagics, plugin_info['obj'], base_config_path, progress_callback, self.file_handler_class_factory())

        
        
        # run the plugin and render the results to json
        treegrid    = constructed.run()

        #renderers = dict([(x.name.lower(), x) for x in framework.class_subclasses(text_renderer.CLIRenderer)])
        #renderers['quick']().render(treegrid)

        #print(treegrid)
        results     = self.render(treegrid)
        #print(results)
        self.removeKeySpace(results)
        
        # go for the function that parse the json results to get clean output
        self.results = plugin_info['function'](results)



    # this function return the plugin information from the dict
    def getPlugin(self, plugin_name):
        for p in plugin_info_dict:
            if p == plugin_name:
                return plugin_info_dict[p]
        
        return None

    # this will remove the space from all json keys, and replace it with "_"
    def removeKeySpace(self, json_obj):
        if isinstance(json_obj,list):
            for i in range(len(json_obj)):
                for k in json_obj[i].keys():
                    if " " in k: 
                        json_obj[i][k.replace(" " , "_")] = json_obj[i][k]
                        del json_obj[i][k]
                
        if isinstance(json_obj,dict):
            for k in json_obj.keys():
                if " " in k: 
                    json_obj[k.replace(" " , "_")] = json_obj[i][k]
                    del json_obj[k]

def imain(file,parser):
    try:
        v = Vol_Parser(image_path=file , plugin_name=parser, plugins_path='./volatility/framework/plugins/')

        return v.results

    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        msg = "[-] [Error] " + str(parser) + " Parser: " + str(exc_obj) + ".."+str(e)+"- Line No. " + str(exc_tb.tb_lineno)
        return (None , msg)



def main():

    parser = argparse.ArgumentParser(prog='vol_Parser.py', description="Run Volatility Parser.\n\n", epilog='Plugins List: ' + ', '.join(plugin_info_dict.keys()) )
    parser.add_argument("-f",  "--file", action="store",help="dump file path")
    parser.add_argument("-p", "--plugin", action="store", help="Select single plugin from plugins list")
    parser.add_argument("-ls",  "--list", action="store_true", help="list all plugins")
    parser.add_argument("-k", "--kuiper",  action="store_true", help="Enable kuiper output")
    args = parser.parse_args()

    # if asked for plugin list
    if args.list:
        print("Volatility parser support the following plugins:")
        for k in plugin_info_dict.keys():
            print( "\t" + k)
        return
    
    if args.file is None or args.plugin is None:
        print("Error: you should specify both dump file --file and the plugin --plugin")
        return
    
    results = imain(args.file , args.plugin)
    if len(results) and results[0] is None:
        print("Error: " + results[1])
        return
    
    if args.kuiper:
        print(results)
    else:
        print(json_beautifier(results))


main()