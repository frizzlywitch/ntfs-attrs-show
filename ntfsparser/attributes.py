# -*- coding: utf-8 -*-

import struct


class Attribute(object):
    """
    Contains fields:
        offset = int() thos offset is relative inside of file-record
        attr_fields = {}
    """
    # TODO: flags more informative
    ATTR_COMMON_FORMAT = '2I2B3H'
    ATTR_COMMON_SIZE = struct.calcsize(ATTR_COMMON_FORMAT)
    ATTR_COMMON_KEYS = ['type', 'len_with_aheader', 'nonresident',
        'name_len', 'name_offset', 'flags', 'attr_id']
    ATTR_UNCOMMON_INFO = {
            # keys:
            # [0] - True if resident, False - nonresident
            # values:
            # [0] - format
            # [1] - fields keys
            True: ('16xIH2B', ['len_attr', 'attr_data_offset', 'idx_flag', 'padding']),
            False: ('16x2Q2HI3Q', ['starting_VCN', 'last_VCN', 'data_runs_offset',
                'compr_unit_size', 'padding', 'alloc_attr_size', 'real_attr_size', 'size_of_stream']),
    }

    def __init__(self, raw_attr, offset):
        self._bin = raw_attr
        self.offset = offset
        self._parse_common_fields()
        self._parse_uncommon_fields()
        self._parse_name()

    def _parse_common_fields(self):
        assert self.ATTR_COMMON_SIZE == 16
        assert len(self._bin) >= 16
        common_values = struct.unpack(
            self.ATTR_COMMON_FORMAT, self._bin[:self.ATTR_COMMON_SIZE]
        )
        self.header_fields = dict(zip(self.ATTR_COMMON_KEYS, common_values))

    def _parse_uncommon_fields(self):
        assert self.header_fields, 'attr fields is empty'
        (fmt, keys) = self.ATTR_UNCOMMON_INFO[self.is_resident()]
        sz = struct.calcsize(fmt)
        values = struct.unpack(fmt, self._bin[:sz])
        fields_upd = dict(zip(keys, values))
        self.header_fields.update(fields_upd)

    def _parse_name(self):
        if not self.is_named():
            return
        i = self.header_fields['name_offset']
        j = i + self.header_fields['name_len']
        self.header_fields['name'] = unicode(self._bin[i:j])

    def is_resident(self):
        return self.header_fields['nonresident'] == 0

    def is_named(self):
        return self.header_fields['name_len'] != 0


class StandartInformation(Attribute):
    ATTR_DATA_FORMAT = '4Q4I'
    ATTR_DATA_EXTEND = '2I2Q'
    ATTR_DATA_KEYS = ['c_time', 'a_time', 'm_time', 'r_time',
            'dos_file_permissions', 'max_num_of_versions',
            'version_num', 'class_id', 'owner_id', 'security_id',
            'quota_charged', 'upd_seq_num']

    def __init__(self, raw_attr, offset):
        super(StandartInformation, self).__init__(raw_attr, offset)
        assert self.header_fields, 'Attr fields is empty'
        fmt = self.ATTR_DATA_FORMAT
        size = struct.calcsize(fmt)
        i = self.header_fields['attr_data_offset']
        j = i + size
        if j < len(self._bin):
            fmt += self.ATTR_DATA_EXTEND
            size = struct.calcsize(fmt)
            j = i + size
        values = struct.unpack(fmt, self._bin[i:j])
        self.data_fields = dict(zip(self.ATTR_DATA_KEYS, values))


class FileName(Attribute):
    # TODO: flags field in filename attribute is interesting
    # make it more detailed
    ATTR_DATA_FORMAT = '7Q2I2B'
    ATTR_DATA_SIZE = struct.calcsize(ATTR_DATA_FORMAT)
    ATTR_DATA_KEYS = ['c_time', 'a_time', 'm_time', 'r_time',
            'allocated_size_of_file', 'real_size_of_file', 'flags',
            'reparse', 'filename_len_in_chars', 'filename_namespace']

    def __init__(self, raw_attr, offset):
        super(FileName, self).__init__(raw_attr, offset)
        assert self.header_fields, 'Attr fields is empty'
        i = self.header_fields['attr_data_offset']
        j = i + self.ATTR_DATA_SIZE
        values = struct.unpack(self.ATTR_DATA_FORMAT, self._bin[i:j])
        self.data_fields = dict(zip(self.ATTR_DATA_KEYS, values))

        self._extract_filename()

    def _extract_filename(self):
        i = 66
        j = self.data_fields['filename_len_in_chars'] * 2
        self.data_fields['filename'] = unicode(self._bin[i:j])


class ObjectId(Attribute):
    ATTR_DATA_FORMAT = '2Q'
    ATTR_DATA_EXTEND = '6Q'
    ATTR_DATA_KEYS = ['guid_obj_id', 'guid_birth_vol_id',
            'guid_birth_obj_id', 'guid_domain_id']

    def __init__(self, raw_attr, offset):
        super(ObjectId, self).__init__(raw_attr, offset)
        assert self.header_fields, 'Attr fields is empty'
        fmt = self.ATTR_DATA_FORMAT
        size = struct.calcsize(fmt)
        i = self.header_fields['attr_data_offset']
        j = i + size
        if j < len(self._bin):
            fmt += self.ATTR_DATA_EXTEND
            size = struct.calcsize(fmt)
            j = i + size
        values = struct.unpack(self.ATTR_DATA_FORMAT, self._bin[i:j])
        self.raw_values = []
        self.view_values = []
        for i in range(0, len(values) - 1, 2):
            v = (values[i], values[i + 1])
            self.raw_values.append(v)
            view_v = str(hex(v[0])) + str(hex(v[1]))[2:]  # rm '0x'
            self.view_values.append(view_v)
        self.data_fields = dict(zip(self.ATTR_DATA_KEYS, self.view_values))


class VolumeName(Attribute):
    def __init__(self, raw_attr, offset):
        super(VolumeName, self).__init__(raw_attr, offset)
        assert self.header_fields, 'Attr fields is empty'
        i = self.header_fields['attr_data_offset']
        self.data_fields = {'volume_name': unicode(self._bin[i:])}


class VolumeInformation(Attribute):
    # TODO: detailed flags
    ATTR_DATA_FORMAT = '8x2BH'
    ATTR_DATA_SIZE = struct.calcsize(ATTR_DATA_FORMAT)
    ATTR_DATA_KEYS = ['major_version_number', 'minor_version_number',
            'flags']

    def __init__(self, raw_attr, offset):
        super(VolumeInformation, self).__init__(raw_attr, offset)
        assert self.header_fields, 'Attr fields is empty'
        i = self.header_fields['attr_data_offset']
        j = i + self.ATTR_DATA_SIZE
        values = struct.unpack(self.ATTR_DATA_FORMAT, self._bin[i:j])
        self.data_fields = dict(zip(self.ATTR_DATA_KEYS, values))


class Data(Attribute):
    def __init__(self, raw_attr, offset):
        super(Data, self).__init__(raw_attr, offset)
        assert self.header_fields, 'Attr fields is empty'
        if self.is_resident():
            i = self.header_fields['attr_data_offset']
        else:
            i = self.header_fields['data_runs_offset']
        j = self.header_fields['len_with_aheader']
        self.data_fields = {'data': self._bin[i:j]}


class IndexRoot(Attribute):
    ATTR_DATA_FORMAT = '3IB'
    ATTR_DATA_SIZE = struct.calcsize(ATTR_DATA_FORMAT)
    ATTR_DATA_KEYS = ['attr_type', 'collation_rule',
            'size_of_index_alloc_entry', 'clusters_per_index_record']

    def __init__(self, raw_attr, offset):
        super(IndexRoot, self).__init__(raw_attr, offset)
        i = self.header_fields['attr_data_offset']
        j = i + self.ATTR_DATA_SIZE
        values = struct.unpack(self.ATTR_DATA_FORMAT, self._bin[i:j])
        self.data_fields = dict(zip(self.ATTR_DATA_KEYS, values))


class Bitmap(Attribute):
    def __init__(self, raw_attr, offset):
        super(Bitmap, self).__init__(raw_attr, offset)
        if self.is_resident():
            i = self.header_fields['attr_data_offset']
        else:
            i = self.header_fields['data_runs_offset']
        j = self.header_fields['len_with_aheader']
        self.data_fields = {'bit_field': self._bin[i:j]}
