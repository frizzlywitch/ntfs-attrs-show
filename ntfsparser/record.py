# -*- coding: utf-8 -*-

import struct
from attributes import *


class FileRecord(object):
    """
    Contains fields:
        offset = int() - this offset is relative inside of mft
        header = {}
        attributes = []
    """
    FILE_RECORD_SIZE = None
    HEADER_FORMAT = '4x2HQ4H2IQH2xI'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    HEADER_KEYS = ['upd_seq_offset', 'upd_seq_size', 'lsn',
        'seq_num', 'hard_link_count', 'attr_offset',
        'flags', 'real_size', 'allocated_size', 'base_ref',
        'next_att_id', 'rec_no',
    ]
    ATTR_LEN_FORMAT = '2I'
    ATTR_LEN_SIZE = struct.calcsize(ATTR_LEN_FORMAT)
    ATTR_INFO = lambda self, attr: struct.unpack(
        self.ATTR_LEN_FORMAT, attr[:self.ATTR_LEN_SIZE]
    )

    ATTRS = {
        16: StandartInformation,  # 0x10
        48: FileName,             # 0x30
        64: ObjectId,             # 0x40
        96: VolumeName,           # 0x60
        112: VolumeInformation,   # 0x70
        128: Data,                # 0x80
        144: IndexRoot,           # 0x90
        176: Bitmap,              # 0xB0
    }

    @staticmethod
    def calc_record_size(mft):
        if FileRecord.FILE_RECORD_SIZE is not None:
            return
        assert mft.startswith('FILE')
        mft2 = mft[4:]
        FileRecord.FILE_RECORD_SIZE = mft2.index('FILE') + 4

    def __init__(self, raw_record, offset):
        assert raw_record.startswith('FILE'), \
                'Not a file-record raw data'
        assert raw_record.count('FILE') == 1, \
                'More than one record in raw data'
        self._bin = raw_record
        self.offset = offset
        self._parse_header()

        self.attributes = []
        self._parse_attributes()

    def _parse_header(self):
        assert self.HEADER_SIZE == 16 * 3
        header_fields = struct.unpack(self.HEADER_FORMAT,
                self._bin[:self.HEADER_SIZE])
        assert len(self.HEADER_KEYS) == len(header_fields)
        self.header = dict(zip(self.HEADER_KEYS, header_fields))

    def _parse_attributes(self):
        assert self.header, 'Header is empty, cant parse attributes'
        assert self.ATTR_LEN_SIZE == 8
        i = self.header['attr_offset']  # 'i' will attr offset
        a_len = 0
        bound = self.header['real_size']
        while i + a_len < bound:
            i += a_len
            (a_id, a_len) = self.ATTR_INFO(self._bin[i:])
            if a_len == 0 or a_len >= bound:
                break
            class_ = self.ATTRS.get(a_id)
            if class_:
                fa = class_(self._bin[i:i + a_len], i)
            else:
                fa = Attribute(self._bin[i:i + a_len], i)
            self.attributes.append(fa)

    def is_active(self):
        flags = self.header['flags']
        return flags == 1 or flags == 2
