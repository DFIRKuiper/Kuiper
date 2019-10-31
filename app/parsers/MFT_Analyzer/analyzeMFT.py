#!/usr/bin/python


import mftsession

#from .analyzemft import mftsession


def main(filenamex):
    all_record = []
    session = mftsession.MftSession(filenamex,'outputfilex')
    session.mft_options()
    session.open_files()
    rtn_record  = session.process_mft_file()

    return rtn_record
