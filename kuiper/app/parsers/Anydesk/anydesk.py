import sys
import re
import io

def open_file_with_encoding(file_path, encoding):
    try:
        with io.open(file_path, 'r', encoding=encoding) as f:
            return f.readlines()
    except UnicodeDecodeError:
        return None

def anydesk(file, parser):
    encodings = ['utf-8', 'iso-8859-1', 'cp1252']
    lines = None
    for enc in encodings:
        lines = open_file_with_encoding(file, enc)
        if lines is not None:
            break

    if lines is None:
        return None

    try:
        data = []
        for line in lines:
            if not line.strip():
                continue

            match = re.match(r'\s*(\w+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(.+)$', line)
            if match:
                log_level, timestamp, command = match.groups()
                data.append({"@timestamp": timestamp, "data": command})
            else:
                data.append({"@timestamp": "1700-01-01 00:00:00", "data": line.strip()})
        return data
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        parsed_data = anydesk(file_path, 'anydesk')
        for item in parsed_data:
            print(item)
