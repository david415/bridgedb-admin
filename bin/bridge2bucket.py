#!/usr/bin/python
#
# Dump bridges from BridgeDB's database into bucket files. This is a temp
# solution until we have a real design/implementation.
#
# Copyright (c) 2011, Christian Frome <kaner@strace.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the <organization> nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import re
import sys
import os
import sqlite3
from collections import deque
from datetime import datetime, timedelta

# The name of the file containing the SQLite database
DATABASE_FILE = "/srv/bridges.torproject.org/var/bridgedist.db.sqlite"
# Bucket definitions
FILE_BUCKETS = { "PersonA": 75, "PersonB": "*" }
# How fresh should a bridge be (in days)
BRIDGE_FRESHNESS = 1

class BridgeData:
    """Value class carrying bridge information:
       hex_key      - The unique hex key of the given bridge
       address      - Bridge IP address
       or_port      - Bridge TCP port
       distributor  - The distributor (or pseudo-distributor) through which
                      this bridge is being announced
       first_seen   - When did we first see this bridge online?
       last_seen    - When was the last time we saw this bridge online?
       status       - One of NEW, RUNNING or OLD (see description below),
                      initially is None
    """
    def __init__(self, hex_key, address, or_port, distributor="unallocated",
                 first_seen="", last_seen="", status="OLD", is_free=True):
        self.hex_key = hex_key
        self.address = address
        self.or_port = or_port
        self.distributor = distributor
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.status = status
        self.is_free = is_free

class BucketData:
    """Class carrying bucket information and doing bucket file operations:
       name      - Name of the bucket distributor prefix
       file_name - The bucket file name
       needed    - Needed number of bridges for that bucket
       allocated - Number of already allocated bridges for that bucket
       bridge_dict - A dict of bridges asociated with this bucket
    """
    def __init__(self, name, needed):
        self.name = name
        self.file_name = name + ".brdgs"
        if needed == "*":
            # Set to rediculously high number
            needed = 1000000
        self.needed = int(needed)
        self.allocated = 0
        self.bridge_dict = {}

    def needsBridge(self):
        """Return a Boolean indicating whether or not this bucket still needs
           bridges
        """
        return self.allocated < self.needed

    def addBridge(self, bridge):
        """Add a bridge to this bucket
        """
        bridge.status = "NEW"
        self.bridge_dict[bridge.hex_key] = bridge
        self.allocated += 1

    def removeBridge(self, bridge):
        """Remove a bridge from the list
        """
        del self.bridge_dict[bridge.hex_key]

    def updateBridge(self, bridge):
        """Update an existing bridge
        """
        self.bridge_dict[bridge.hex_key].status = "RUNNING"
        # In case the IP address or the OR port changes, set status to "NEW"
        if self.bridge_dict[bridge.hex_key].address != bridge.address:
            self.bridge_dict[bridge.hex_key].address = bridge.address
            self.bridge_dict[bridge.hex_key].status = "NEW"
        if int(self.bridge_dict[bridge.hex_key].or_port) != int(bridge.or_port):
            self.bridge_dict[bridge.hex_key].or_port = bridge.or_port
            self.bridge_dict[bridge.hex_key].status = "NEW"
        self.allocated += 1

    def readFromFile(self):
        """Parse bridges from a bucket file. The bucket file keeps bridges in a
           format like this per line:

               HEX_KEY IP PORT STATUS

           HEX_KEY is the bridge's key in hexadecimal (taken from the database)
           IP is the bridge's IP address
           PORT is the bridge's listening port
           STATUS is one of the following:
            - NEW: The bridge is brand new, first time we have it in the bucket
              file
            - RUNNING: A bridge we have seen before and is still running/current
            - OLD: This bridge has not been seen running for a while, but we
                   keep it in here for reference. Note that OLD bridges can get
                   back into the RUNNING pool if they become available again.
        """
        # Empty current bridge dict
        self.bridge_dict = {}

        if not os.path.isfile(self.file_name):
            print "Not a file: %s" % self.file_name
            return

        r = re.compile('[ \t]+')

        try:
            f = open(self.file_name, 'r')
            for line in f:
                s = r.split(line)
                bridge = BridgeData(s[0], s[1], s[2], status = s[3])
                self.bridge_dict[bridge.hex_key] = bridge
                self.allocated += 1
            f.close()
        except IOError:
            print >>sys.stderr, "IOError while reading %s" % self.file_name

    def dumpToFile(self):
        """Dump a list of given bridges into a file
        """
        try:
            f = open(self.file_name, 'w')
            for k, v in self.bridge_dict.items():
                l = "%s %s %s %s" % (v.hex_key, v.address, v.or_port, v.status)
                f.write(l + '\n')
            f.close()
        except IOError:
            print "I/O error: %s" % self.file_name

    def resetBridgeState(self):
        """Reset the state of all bridges in this bucket
        """
        self.allocated = 0
        for k, v in self.bridge_dict.items():
            v.status = "OLD"


def getAllBridgesFromDB():
    """Return all bridges from the database. This is ineffective since we only
       need 'unallocated' bridges here, but hey.
    """

    retBridges = []
    # Connect & query
    try:
        conn = sqlite3.Connection(DATABASE_FILE)
        cur = conn.cursor()
    except:
        print >>sys.stderr, "Sad face. Couldn't get any bridges from the db."
        return retBridges

    cur.execute("SELECT hex_key, address, or_port, distributor, "
                "first_seen, last_seen FROM Bridges")
    for b in cur.fetchall():
        bridge = BridgeData(b[0], b[1], b[2], b[3], b[4], b[5])
        retBridges.append(bridge)

    return retBridges

def filterBridges(bridgeList):
    """Filter a list of bridges (throw out old and non-'unallocated' ones)
    """

    retBridges = []

    for bridge in bridgeList:
        # Throw out everything that's 'unallocated'
        if bridge.distributor != "unallocated":
            continue
        last_seen = datetime.strptime(bridge.last_seen, "%Y-%m-%d %H:%M")
        now = datetime.now()
        if (now - last_seen) <= timedelta(days = BRIDGE_FRESHNESS):
            # Keep it
            retBridges.append(bridge)

    return retBridges

def updateBridgeInBucket(bridge, bucketList):
    """Update a bridge if it is part of the bucket list. Return True. If it is
       not part of the bucket list or the bucket doesn't need another bridge,
       return False
    """
    for bucket in bucketList:
        if bridge.hex_key in bucket.bridge_dict.keys():
            if bucket.needsBridge():
                bucket.updateBridge(bridge)
                return True
            else:
                # If this bridge is part of a certain bucket, remove it from
                # that bucket, because if we're here, that bucket wasn't
                # hungry for any new bridges anymore. Not ideal, because this
                # is where bridges could move from one bucket to another. But
                # better than wasting it.
                bucket.removeBridge(bridge)
                break

    return False

def main():
    # Set up bucketList list
    bucketList = []
    for k, v in FILE_BUCKETS.items():
        b = BucketData(k, v)
        bucketList.append(b)

    # Try to fill bridge lists from file
    for bucket in bucketList:
        bucket.readFromFile()
        bucket.resetBridgeState()

    dbBridges = filterBridges(getAllBridgesFromDB())
    # First of all, loop through bridges from the database and see if we need
    # to update anything (bridges should stay in their buckets if possible)
    for bridge in dbBridges:
        if updateBridgeInBucket(bridge, bucketList):
            bridge.is_free = False
            continue
    # Loop through database bridges, merge with (possibly) exisiting ones read
    # from file.
    dequeBucketList = deque(bucketList)
    for bridge in dbBridges:
        # Skip bridges already assigned
        if not bridge.is_free:
            continue
        # Shift right once
        dequeBucketList.rotate(1)
        for bucket in dequeBucketList:
            if bucket.needsBridge():
                bucket.addBridge(bridge)
                break

    # Dump buckets to file
    for bucket in bucketList:
        bucket.dumpToFile()

if __name__ == "__main__":
    main()
