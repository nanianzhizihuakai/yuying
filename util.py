import hashlib
import time
import datetime
import random
from common import KEY
import struct

# https://docs.python.org/3/library/struct.html
# https://docs.python.org/3/library/struct.html#struct-format-strings
# > big-endian
# I unsigned int (4 byte)

WAV_HEADER_LEN = 44


def compose_wav_header(bytes_len, num_channels=1, bit_size=16, sample_rate=16000):
    assert(num_channels in [1, 2], 'num_channels must be 1 or 2!')

    header_arr = []

    header_arr.append(b'RIFF')

    header_arr.append(struct.pack('<I', bytes_len + WAV_HEADER_LEN - 8))

    header_arr.append(b'WAVE')
    header_arr.append(b'fmt ')

    header_arr.append(struct.pack('<I', 16))

    header_arr.append(struct.pack('<H', 1))

    header_arr.append(struct.pack('<H', num_channels))

    header_arr.append(struct.pack('<I', sample_rate))

    bytes_per_sec = sample_rate * bit_size * num_channels // 8
    header_arr.append(struct.pack('<I', bytes_per_sec))

    block_alignment = bit_size * num_channels // 8
    header_arr.append(struct.pack('<H', block_alignment))

    header_arr.append(struct.pack('<H', bit_size))

    header_arr.append(b'data')

    header_arr.append(struct.pack('<I', bytes_len))

    header_bytes = b''.join(header_arr)

    assert(WAV_HEADER_LEN == len(header_bytes), f'Header size must be {WAV_HEADER_LEN} bytes!')

    return header_bytes


def md5(xstr):
    """https://stackoverflow.com/questions/5297448/how-to-get-md5-sum-of-a-string-using-python"""
    xmd5 = hashlib.md5(xstr.encode('utf-8')).hexdigest()
    return xmd5


def uuid():
    xns = time.time_ns()
    xns = '%020d' % xns
    xrand = random.randint(0, 999999)
    xrand = '%06d' % xrand
    xuuid = xns + '_' + xrand
    return xuuid


def merge_dialog_in_and_out(rows_in, rows_out):
    """dialog log: DESC"""
    rows = rows_in + rows_out
    rows = sorted(rows, key=lambda row: row[KEY], reverse=True)  # DESC
    return rows


def translate_ns(ns):
    ms = ns // 1000
    mili = ms // 1000
    s = mili // 1000
    ms_ = mili % 1000
    dt = datetime.datetime.fromtimestamp(s)
    xstr = dt.strftime('%Y-%m-%d %H:%M:%S')
    return '%s.%03d' % (xstr, ms_)


if '__main__' == __name__:
    print(uuid())
