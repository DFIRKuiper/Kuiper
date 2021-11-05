from struct import unpack
from binascii import unhexlify
import binascii
import datetime

def decoding(content):
    try:
        test_file_path = content[16:24].encode("hex")
        nt_timestamp = unpack("<Q", unhexlify(test_file_path))[0]
        epoch = datetime(1601, 1, 1, 0, 0, 0)
        nt_datetime = epoch + timedelta(microseconds= (nt_timestamp / 10) )
        return str(nt_datetime).replace(" ","T")
    except Exception as e:
        print str(e)
        return "1700-01-01T00:00:00"

def main(file_path):
    # lst_file = os.listdir(dir)
    result={}
    file = open(file_path,"r")
    content = file.read()

    # ==== file size
    result['file_size'] = str( unpack("<Q", unhexlify(content[8:16].encode("hex")))[0] )

    # ==== deleted time
    # date_del = decoding(file_path)
    epoch = datetime.datetime(1601, 1, 1, 0, 0, 0)
    nt_timestamp = unpack("<Q", unhexlify(content[16:24].encode("hex")))[0]
    nt_datetime = epoch + datetime.timedelta(microseconds= (nt_timestamp / 10) )
    result['Deleted_Time'] = str(nt_datetime).replace(' ' , 'T')

    
    # check if header 0x1 (windows Vista, 7, 8, or 8.1)
    if binascii.hexlify(content[0:8] ).startswith( '01' ):
        # ==== win version
        win_ver = 'win_vista_7_8_8.1'

        # ==== Path
        deleted_file_path = content[24:].replace('\x00' , '')
        
    else:
        # ==== win version
        win_ver = 'win_10'

        # ==== Path
        deleted_file_path = content[28:]

    result['win_version'] = win_ver
    result['Path'] = deleted_file_path
    result['File_Name'] = deleted_file_path.split('\\')[-1]
    
    # ==== file path
    result['Recycle_bin_file'] = file_path.split('/')[-1]
    
    result['@timestamp'] = result['Deleted_Time']

    return [result]
