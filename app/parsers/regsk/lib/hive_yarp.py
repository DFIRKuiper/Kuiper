from yarp import Registry


def get_hive(reg_hive,log_files):
    hive = Registry.RegistryHive(open(reg_hive, 'rb'))
    try:
        if log_files['LOG'] !=None:
            log0 = open(log_files[u'LOG'], 'rb')
        else:
            log0 = None

        if log_files['LOG1'] !=None:
            log1 = open(log_files[u'LOG1'], 'rb')
        else:
            log1 = None

        if log_files['LOG2'] !=None:
            log2 = open(log_files[u'LOG2'], 'rb')
        else:
            log2 = None

        recovery_result = hive.recover_auto(log0,log1,log2)

        # print(u"Recovery Results: {}".format(recovery_result))
    except Exception as error:
        print (error)

    return hive
