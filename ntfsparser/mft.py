# -*- coding: utf-8 -*-

import os
import stat
import mmap
import struct
from subprocess import Popen
from record import FileRecord


PATH = 'disk2.img'


class MFT(object):
    def __init__(self, raw_data, **mft_params):
        self._bin = raw_data
        self.params = mft_params
        self._get_all_file_records()

    def _get_all_file_records(self):
        FileRecord.calc_record_size(self._bin)
        fr_size = FileRecord.FILE_RECORD_SIZE
        self.records = []
        i = 0
        j = fr_size
        while j < len(self._bin):
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


class Disk(object):
    # TODO: file destructor
    def __init__(self, path):
        self.path = path
        self._mmap()
        '''
        stat_info = os.stat(path)
        if stat.S_ISBLK(stat_info):
            self._create_tmp_img()
            self._mmap()
        elif stat.S_ISREG(stat_info):
            self._mmap()
        else:
            raise Exception('Invalid filetype of input file')
        '''

    def _mmap(self):
        self.file_ = open(self.path, 'r+b')
        self.data = mmap.mmap(self.file_.fileno(), 0)

    def _create_tmp_img(self):
        self.path2 = self.path
        self.path = '/tmp/disk.img'
        with Popen(["dd", "if=" + self.path2, "of=" + self.path]) as pipe:
            pipe.communicate()
