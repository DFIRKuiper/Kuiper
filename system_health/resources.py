# ========================== Descrption
# this script used to collect the system resources
from datetime import datetime 
import psutil
# this function return system resources (Disk, Memory, CPU )
def get_system_resources(disk_path="/"):
    cpu_percent= num_cores= num_cpu_thrd= hdd = memory= swap= None
    try:
        hdd             = dict(psutil.disk_usage(disk_path)._asdict())
    except Exception as e:
        pass

    # ====================== CPU ========================= # 
    
    try:
        cpu_percent     = psutil.cpu_percent(interval=None, percpu=True)
        num_cores       = psutil.cpu_count(logical=False)
        num_cpu_thrd    = psutil.cpu_count()
    except Exception as e:
        pass

    # ====================== Memory / Swap ========================= # 
    try:
        memory             = dict(psutil.virtual_memory()._asdict())
        swap            = dict(psutil.swap_memory()._asdict())
    except Exception as e:
        pass

    return {
        'disk'                  : hdd,
        'CPU': {
            'utilization'       : cpu_percent,
            'cpus_num'          : num_cores,
            'thrds_num'         : num_cpu_thrd
        },
        'memory'                : memory,
        'swap'                  : swap,
    }


# ====================== this function return the process details based on pid
def process_details(pid):
    proc = psutil.Process(pid)

    # children - workers
    workers = []
    for worker_proc in proc.children():
        worker_details = worker_proc.as_dict()
        # count number of connections per worker
        worker_connections = 0
        if 'connections' in worker_details.keys() and worker_details['connections'] is not None:
            for con in worker_details['connections']:
                dict_conn = dict(con._asdict())
                if dict_conn['status'] == "ESTABLISHED" and dict_conn['laddr'][0] != dict_conn['raddr'][0]:
                    worker_connections += 1
    
        
        workers.append( {
            'status': worker_details['status'],
            'wpid' : worker_details['pid'],
            'cpu_percent' : worker_proc.as_dict()['cpu_percent'],
            'memory_percent' : worker_details['memory_percent'],
            'create_time' : datetime.fromtimestamp(worker_details['create_time']).strftime("%Y-%m-%d %H:%M:%S"),
            'connections' : worker_connections
        } )

    # memory
    proc_mem = dict(proc.memory_info()._asdict())

    # connections
    proc_connection = {}
    if len(proc.connections()) > 0:
        proc_conn = dict(proc.connections()[0]._asdict())
        proc_connection = {
            'status'     : proc_conn['status'],
            'IP'         : proc_conn['laddr'][0],
            'Port'         : proc_conn['laddr'][1]
        }

    proc_dict = proc.as_dict()
    proc_details = {
        'cmdline'         : ' '.join(proc_dict['cmdline']),
        'cpu_num'         : proc_dict['cpu_num'],
        'cpu_percent'     : proc.as_dict()['cpu_percent'],
        'create_time'     : datetime.fromtimestamp(proc_dict['create_time']).strftime("%Y-%m-%d %H:%M:%S"),
        'memory_percent': proc_dict['memory_percent'],
        'name'            : proc_dict['name'],
        'pid'             : proc_dict['pid'],
        'ppid'             : proc_dict['ppid'],
        "status"        : proc_dict['status'],
        'username'        : proc_dict['username'],
        'connection'    : proc_connection,
        'memory'         : proc_mem,
        'workers'        : workers
    }

    return proc_details
