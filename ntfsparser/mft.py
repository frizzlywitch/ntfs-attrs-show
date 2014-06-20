# -*- coding: utf-8 -*-

import mmap
import struct
from record import FileRecord


class MFT(object):
    def __init__(self, raw_data, **mft_params):
        self._bin = raw_data
        self._get_all_file_records()

    def _get_all_file_records(self):
        FileRecord.calc_record_size(self._bin)
        fr_size = FileRecord.FILE_RECORD_SIZE
        self.records = []
        i = 0
        j = fr_size
        while j < len(mft):
            try:
                fr = FileRecord(self._bin[i:j], i)
            except AssertionError:
                break
            self.records.append(fr)
            i = j
            j += fr_size

    @staticmethod
    def extract_mft_params(ntfs_data):
        """
        params: data - бинарные данные ntfs диска
        returns: (размер кластера в байтах, смещение mft в кластерах,
            размер mft в кластерах)
        see also: http://www.writeblocked.org/resources/NTFS_CHEAT_SHEETS.pdf
        """
        fmt = 'HB'
        last_idx = struct.calcsize(fmt)
        (bytes_p_sec, sec_p_clust) = struct.unpack(fmt, ntfs_data[11:11 + last_idx])
        fmt = 'Q8xI'
        last_idx = struct.calcsize(fmt)
        (mft_offset, mft_size) = struct.unpack(fmt, ntfs_data[48: 48 + last_idx])
        return {
            'cluster_size': bytes_p_sec * sec_p_clust,
            'mft_offset': mft_offset,
            'mft_size': mft_size
        }


with open('disk2.img', 'r+b') as f:
    mm = mmap.mmap(f.fileno(), 0)
    p = MFT.extract_mft_params(mm)
    offset = p['cluster_size'] * p['mft_offset']
    size = p['cluster_size'] * p['mft_size']
    mft = mm[offset:offset + size]
    records = MFT(mft).records
    for i in range(4):
        r = records[i]
        for a in r.attributes:
            print type(a)
    mm.close()
