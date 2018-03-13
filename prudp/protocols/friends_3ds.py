from prudp.protocols import incoming,outgoing
import struct
from binascii import unhexlify
import hmac
import hashlib
from rc4 import RC4

class Friends3DSProtocol:
    def __init__(self):
        self.methods = {}
        self.methods[0x01] = self.get_all_information
        self.methods[0x05] = self.method05
        self.methods[0x0b] = self.add_friend_by_principal_id
        self.methods[0x0e] = self.method0e

        self.methods[0x11] = self.sync_friend
        self.methods[0x12] = self.method12
        self.methods[0x13] = self.method13
        self.methods[0x14] = self.method14

    @incoming("u8[5]", "u64", "string", "string")
    def get_all_information(self, *args):
        print(args)
        return (True, 0x00010001, unhexlify("0100010000000000000000000000000000"))
    
    @outgoing("u32")
    def method05(self, data):
        print("method 05:", data)
        return (True, 0x00010001, (0x00010001,))

    #@incoming("")
    @outgoing("u32")
    def add_friend_by_principal_id(self, data):
        print("add friend by principal id:", data)
        return (True, 0x00010001, (0x00010001,))

    @outgoing("u32")
    def method0e(self, data):
        print("method 0e:", data)
        return (True, 0x00010001, (0x00010001))

    @incoming("u64", "list<u32>", "list<u64>")
    @outgoing("list<u32>")
    def sync_friend(self, mostly_lfcs, principal_ids, unknown):
        print("SyncFriend:", mostly_lfcs, principal_ids, unknown)
        return (True, 0x00010001, ([],))
    
    #@incoming("")
    @outgoing("u32")
    def method12(self, data):
        print("method 12:", data)
        return (True, 0x00010001, (0x00010001,))

    #@incoming("")
    @outgoing("u32")
    def method13(self, data):
        print("method 13:", data)
        return (True, 0x00010001, (0x00010001,))

    @incoming("string")
    @outgoing("u32")
    def method14(self, data):
        print("method 14:", data)
        return (True, 0x00010001, (0x00010001,))