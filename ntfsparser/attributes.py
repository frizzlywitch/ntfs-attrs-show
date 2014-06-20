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
        'name_len', 'name_offset', 'flags', 'attr_id']
    ATTRS_HEADERS = {
            # keys:
            # [0] - True if resident, False - nonresident
            # values:
            # [0] - format
            # [1] - fields keys
            True: ('16xIH2B', ['len_attr', 'attr_data_offset', 'idx_flag', 'padding']),
            False: ('16x2Q2HI3Q', ['starting_VCN', 'last_VCN', 'data_runs_offset',
                'compr_unit_size', 'padding', 'alloc_attr_size', 'real_attr_size', 'size_of_stream']),
    }
    ATTRS_BODIES_FORMATS = {
        16: ('4Q6I2Q', ['c_time', 'a_time', 'm_time', 'r_time',
            'dos_file_permissions', 'max_nums_of_versions', 'version_number',
            'class_id', 'owner_id', 'security_id', 'quota_charged', 'upd_seq_num']),  # 0x10
        48: ('7Q2I2B', ['ref_to_parent_dir', 'c_time', 'a_time', 'm_time', 'r_time',
            'alloc_size_of_file', 'real_size_of_file', 'file_flags', 'reparse',
            'name_len_in_chars', 'name_len_namespace'],
            FileAttribute._handle_file_name),  # 0x30
        64: ('8Q', None, FileAttribute._handle_obj_ids),  # 0x40
        80: (),  # TODO: 0x50
        96: (None, None, FileAttribute._get_volume_name),  # 0x60
        112: ('8x2BH', ['major_version', 'minor_version', 'volume_flags'],
            FileAttribute._extract_volume_flags),  # 0x70
        128: (None, None, FileAttribute._extract_data),  # 0x80
        144: '',  # 0x90
        160: '',  # 0xA0
        176: '',  # 0xB0
        256: '',  # 0x100
    }

    def __init__(self, raw_attr, offset):
        self._bin = raw_attr
        self.offset = offset
        self._parse_common_fields()
        self._parse_uncommon_fields()
        self._parse_name()
        self._parse_body()

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
        (fmt, keys) = self.ATTRS_HEADERS[self.is_resident()]
        sz = struct.calcsize(fmt)
        values = struct.unpack(fmt, self._bin[:sz])
        fields_upd = dict(zip(keys, values))
        self.fields.update(fields_upd)

    def _parse_name(self):
        if not self.is_named():
            return
        i = self.fields['name_offset']
        j = i + self.fields['name_len']
        self.fields['name'] = unicode(self._bin[i:j])

    def _parse_body(self):
        pass

    def _handle_file_name(self):
        pass

    def is_resident(self):
        return self.fields['nonresident'] == 0

    def is_named(self):
        return self.fields['name_len'] != 0
