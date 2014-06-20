# -*- coding: utf-8 -*-

import struct
import mmap
from pprint import pprint

DEBUG = False


class FileAttribute:
    """
    Contains fields:
        offset = int() thos offset is relative inside of file-record
        attr_fields = {}
    """
    ATTR_COMMON_FORMAT = '2I2B3H'
    ATTR_COMMON_SIZE = struct.calcsize(ATTR_COMMON_FORMAT)
    ATTR_COMMON_KEYS = ['type', 'len_with_aheader', 'nonresident',
        'name_len', 'name_offset', 'flags', 'attr_id',
    ]

    def __init__(self, raw_attr, offset):
        self._bin = raw_attr
        self.offset = offset
        self.ATTRS_PARSERS = {
            # [0] - True if resident, False - otherwise
            # [1] - True if named, False - otherwise
            (True, True): self._parse_resident_named_attr,
            (True, False): self._parse_resident_unnamed_attr,
            (False, True): self._parse_unresident_named_attr,
            (False, False): self._parse_unresident_unnamed_attr,
        }
        self._parse_common_fields()
        self._parse_uncommon_fields()

    def _parse_common_fields(self):
        assert self.ATTR_COMMON_SIZE == 16
        assert len(self._bin) >= 16
        common_values = struct.unpack(
            self.ATTR_COMMON_FORMAT, self._bin[:self.ATTR_COMMON_SIZE]
        )
        self.fields = dict(zip(self.ATTR_COMMON_KEYS, common_values))
        if DEBUG:
            pprint(self.attr_fields)

    def _parse_uncommon_fields(self):
        assert self.fields, 'attr fields is empty'
        af = self.fields
        flag = af['nonresident'] == 0
        name_len = af['name_len'] != 0
        self.ATTRS_PARSERS[(flag, name_len)]()

    def _parse_resident_named_attr(self):
        if DEBUG:
            print 'resident, named'

    def _parse_resident_unnamed_attr(self):
        if DEBUG:
            print 'resident, unnamed'

    def _parse_unresident_named_attr(self):
        if DEBUG:
            print 'unresident, named'

    def _parse_unresident_unnamed_attr(self):
        if DEBUG:
            print 'unresident, unnamed'


class FileRecord:
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
    ATTR_LEN_FORMAT = '4xI'
    ATTR_LEN_SIZE = struct.calcsize(ATTR_LEN_FORMAT)
    ATTR_LEN = lambda self, attr: struct.unpack(
        self.ATTR_LEN_FORMAT, attr[:self.ATTR_LEN_SIZE]
    )[0]

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
        if DEBUG:
            pprint(self.header)

    def _parse_attributes(self):
        assert self.header, 'Header is empty, cant parse attributes'
        assert self.ATTR_LEN_SIZE == 8
        i = self.header['attr_offset']  # 'i' will attr offset
        a_len = 0
        bound = self.header['real_size']
        while i + a_len < bound:
            i += a_len
            a_len = self.ATTR_LEN(self._bin[i:])
            if a_len == 0 or a_len >= bound:
                break
            fa = FileAttribute(self._bin[i:i + a_len], i)
            self.attributes.append(fa)


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
        print hex(t)
    mm.close()
