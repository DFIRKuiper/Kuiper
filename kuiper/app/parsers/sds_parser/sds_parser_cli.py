from ntfs_sds_parser import PySDSParser
import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NTFS Security Descriptor Stream ($Secure:$SDS) parser - Developded by AbdulRhman Alfaifi')
    parser.add_argument("SDS_FILE",help='$Secure:$SDS file path')
    parser.add_argument("-o","--output",help='The file path to write the output to (default: stdout)')

    args = parser.parse_args()

    if args.output:
        output = open(args.output, "w")
    else:
        output = sys.stdout
    
    parser = PySDSParser(args.SDS_FILE)

    for entry in parser:
        if not entry.is_error:
            output.write(f"{entry.to_json()}\n")
        else:
            sys.stderr.write("Error Parsing record\n")