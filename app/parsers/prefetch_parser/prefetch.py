########################
# Windows 10 Prefetch Parser
# Created by 505Forensics (http://www.505forensics.com)
#
# Usage: Utilize this script to parse either a single or set of Windows 10 prefetch files
#
# Dependencies: This script requires the installation of libscca (https://github.com/libyal/libscca), and was only tested in a Linux environment
#
# Output: Script will output in CSV to stdout by default.
#
#######################
import argparse
import csv
import sys
import os
import json
# Try importing pyscca; fail if it doesn't import
try:
    import pyscca #Import pyscca, necessary from libscca
except ImportError:
    print "Please install libscca with Python bindings"

output = {}





# Parse individual file. Output is placed in 'output' dictionary
def parse_file(pf_file,volume_information):
    try:
        scca = pyscca.open(pf_file)
        last_run_times = []

        for x in range(8):
            try:
                if scca.get_last_run_time_as_integer(x) > 0:
                    last_run_times.append(scca.get_last_run_time(x).strftime("%Y-%m-%dT%H:%M:%S")) #str conversion utilized to change from datetime into human-readable
                else:
                    last_run_times.append('1700-01-01T00:00:00')
            except:
                last_run_times.append('1700-01-01T00:00:00')

        # === run_count
        run_count = 0
        try:
            if scca.get_run_count() is not None:
                run_count = scca.run_count
        except:
            pass
        # === executable_filename
        executable_filename = scca.executable_filename
        if executable_filename is None:
            executable_filename = '-'.join( pf_file.split('/')[-1].split('-')[0:-1] )

        # === Prefetch hash
        prefetch_hash = format(scca.prefetch_hash, 'x').upper()
        if prefetch_hash == '0':
            prefetch_hash = pf_file.split('/')[-1].split('-')[-1].replace('.pf' , '')

        output[str(executable_filename)] = [str(run_count), prefetch_hash.upper(), last_run_times ]

        if volume_information:
            output[str(executable_filename)].append(scca.number_of_volumes)
            volumes = []
            for i in range(scca.number_of_volumes):
                volume = [str(scca.get_volume_information(i).device_path), scca.get_volume_information(i).creation_time.strftime("%Y-%m-%d %H:%M:%S"), format(scca.get_volume_information(i).serial_number,'x').upper()]
                volumes.append(volume)

            output[str(executable_filename)].append(volumes)
        return output
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "[-] [Error] " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        return None

# Parse an entire directory of Prefetch files. Note that it searches based on .pf extension
def parse_dir(dir,volume_information):
    for item in os.listdir(dir):
        if item.endswith(".pf"): #Only focus on .pf files
            parse_file(dir+item,volume_information)
        else:
            continue
    return output

def outputResults(output):
    #if output_type:
    for k, v in output.iteritems():
        json_output = {
            'Executable_Name' : k,
            'Run_Count' : v[0],
            'Location_Hash' :  v[1],
        }
        #Let the script iterate through run times for us, instead of just dumping a list
        run_list = {}
        
        first_date = v[2][0]
        last_date = '1700-01-01T00:00:00'
        for i in range(8):
            run_list['Run_Time_{}'.format(i)] = v[2][i]
            if v[2][i] < first_date and v[2][i] != '1700-01-01T00:00:00':
                first_date = v[2][i]
            if v[2][i] > last_date:
                last_date = v[2][i]

        json_output['Run_Times'] = run_list
        json_output['first_run'] = first_date
        json_output['last_run'] = last_date
        json_output['@timestamp'] = first_date

    return json_output


def main(path):
    output = parse_file(path,False)
    rtn = outputResults(output)
    rtn['prefetch_file'] = path.split('/')[-1]
    return rtn
