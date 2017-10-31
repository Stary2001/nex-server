import asyncio
from rc4 import RC4

class PRUDPV0Packet:
    def decode(self, rc4_state):
        pass

class PRUDPClient:
    STATE_EXPECT_SYN = 0
    STATE_EXPECT_CONNECT = 1
    STATE_CONNECTED = 2

    def __init__(self, rc4_key):
        self.rc4_state_encrypt = RC4(rc4_key)
        self.rc4_state_decrypt = RC4(rc4_key)

        state = PRUDPClient.STATE_EXPECT_SYN

    def decode_packet(self, data):
        # ...
        # return a PRUDPV0Packet
        pass

    def encode_packet(self):
        # ...
        # return a bytestring
        pass

    def handle_data(self, data):
        return self.handle_packet(self.decode_packet(data))

    def handle_packet(self, packet):
        # ...
        # do something here?
        pass

# TODO: big issue with this is stray UDP packets.
# Time out connections after <some time> of lingering in STATE_EXPECT_SYN.

class PRUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
        self.connections = {}

    def datagram_received(self, data, addr):
        if not addr in self.connections:
            client = PRUDPClient(b"CD&ML")
            self.connections[addr] = client
        else:
            client = self.connections[addr]

        client.handle_data(data)