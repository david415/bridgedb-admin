#!/bin/bash
#
# Unused for quite some time:
#
# bridgedb@ponticum:/srv/bridges.torproject.org$ stat bin/dump_and_send_buckets.sh
#   File: `bin/dump_and_send_buckets.sh'
#   Size: 155             Blocks: 8          IO Block: 4096   regular file
# Device: fe20h/65056d    Inode: 131279      Links: 1
# Access: (0755/-rwxr-xr-x)  Uid: ( 1531/bridgedb)   Gid: ( 1531/bridgedb)
# Access: 2014-01-13 01:42:08.357733333 +0000
# Modify: 2012-10-27 01:22:32.017034473 +0000
# Change: 2012-10-27 01:22:32.017034473 +0000
#  Birth: -

cd /srv/bridges.torproject.org/run
/srv/bridges.torproject.org/bin/bridge2bucket.py
/srv/bridges.torproject.org/bin/sendBridgesFromBuckets.py
