# -*- coding: utf-8 -*-

import argparse
from mft import MFT, Disk

parser = argparse.ArgumentParser()
parser.add_argument("PATH")
args = parser.parse_args()

path = args.PATH
disk = Disk(path)
mp = MFT.extract_mft_params(disk.data)
i = mp['cluster_size'] * mp['mft_offset']
j = i + mp['cluster_size'] * mp['mft_size']
mft = MFT(disk.data[i:j], **mp)

records = mft.records
print len(records)
print len(filter(lambda r: r.is_active(), records))
r = records[0]
for a in r.attributes:
    print type(a)
