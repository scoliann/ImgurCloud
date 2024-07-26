'''
    This file contains function pairs to encode data from format_X -> bytes
    and to decode data from bytes -> format_X.
'''


def file_to_bytes(s_file_path):
    o_file = open(s_file_path, 'rb')
    lo_payload_bytes = o_file.read()
    o_file.close()
    return lo_payload_bytes


def bytes_to_file(lo_payload_bytes, s_file_path):
    o_file = open(s_file_path, 'wb')
    o_file.write(lo_payload_bytes)
    o_file.close()
    return s_file_path


