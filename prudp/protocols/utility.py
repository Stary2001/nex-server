from prudp.protocols import incoming,outgoing
import struct
from binascii import unhexlify

class UtilityProtocol:
    def __init__(self, server):
        self.methods = {}
        self.methods[0x05] = self.GetAssociatedNexUniqueIdWithMyPrincipalId
        self.server = server

    @incoming("u32", "u32")
    @outgoing("u64", "u64")
    def GetAssociatedNexUniqueIdWithMyPrincipalId(self, pid, what):
        print(pid, what)
        success = True
        result = 0x00010001
        return (success, result, (0, 0))