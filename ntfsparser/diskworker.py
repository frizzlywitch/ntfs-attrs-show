# -*- coding: utf-8 -*-

import mmap
import struct
from record import FileRecord


def get_all_file_records(mft):
    FileRecord.calc_record_size(mft)
    fr_size = FileRecord.FILE_RECORD_SIZE
    records = []
    i = 0
    j = fr_size
    while j < len(mft):
        try:
            fr = FileRecord(mft[i:j], i)
        except AssertionError:
            break
        records.append(fr)
        i = j
        j += fr_size
    return records


def extract_mft_params(data):
    """
    params: data - бинарные данные ntfs диска
    returns: (размер кластера в байтах, смещение mft в кластерах,
        размер mft в кластерах)
    see also: http://www.writeblocked.org/resources/NTFS_CHEAT_SHEETS.pdf
    """
    fmt = 'HB'
    last_idx = struct.calcsize(fmt)
    (bytes_p_sec, sec_p_clust) = struct.unpack(fmt, data[11:11 + last_idx])
    fmt = 'Q8xI'
    last_idx = struct.calcsize(fmt)
    (mft_offset, mft_size) = struct.unpack(fmt, data[48: 48 + last_idx])
    return (bytes_p_sec * sec_p_clust, mft_offset, mft_size)


with open('disk2.img', 'r+b') as f:
    mm = mmap.mmap(f.fileno(), 0)
    p = extract_mft_params(mm)
    offset = p[0] * p[1]
    size = p[0] * p[2]
    mft = mm[offset:offset + size]
    records = get_all_file_records(mft)
    attrs_types = set()
    for r in records:
        for attr in r.attributes:
            attrs_types.add(attr.fields['type'])
    attrs_types = list(attrs_types)
    attrs_types.sort()
    for t in attrs_types:
        print t
    mm.close()
