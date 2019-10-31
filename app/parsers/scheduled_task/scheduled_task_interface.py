import sys
import scheduled_task


def scheduled_task_interface(file , parser):
    try:
        scheduled_task_data = scheduled_task.main(file)
        return [scheduled_task_data]

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        msg = "[-] [Error] " + parser + " Parser: " + str(exc_obj) + " - Line No. " + str(exc_tb.tb_lineno)
        print msg
        return (None , msg)

