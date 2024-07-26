'''
    This file contains function pairs that compress and decompress data.
'''


# Do imports
import zlib


def compress_zlib(lo_payload_bytes, i_compression_level):

    # Compress bytes
    lo_compressed_bytes = zlib.compress(lo_payload_bytes, level=i_compression_level)

    # Return
    return lo_compressed_bytes


def decompress_zlib(lo_payload_bytes):

    # Decompress bytes
    lo_decompressed_bytes = zlib.decompress(lo_payload_bytes)

    # Return
    return lo_decompressed_bytes


