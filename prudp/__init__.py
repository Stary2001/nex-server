import asyncio
import struct
from rc4 import RC4

class PRUDPV0Packet:
    FLAG_RELIABLE = 0x2
    FLAG_NEEDS_ACK = 0x4
    FLAG_HAS_SIZE = 0x8

    def __init__(self, direction, op, flags, seq, conn_sig, session, sig):
        self.direction = direction
        self.op = op
        self.flags = flags
        self.seq = seq
        self.conn_sig = conn_sig
        self.session = session
        self.sig = sig

    @classmethod
    def decode(self, data, rc4_state):
        # Decode the packet header..
        direction = struct.unpack("<H", data[0:2])[0]

        op_flags = struct.unpack("<H", data[2:4])[0]
        op = op_flags & 0xF
        flags = (op_flags & 0xFFF0) >> 4

        session = data[4]
        sig = struct.unpack("<I", data[5:9])[0]
        seq = struct.unpack("<H", data[9:11])[0]
        conn_sig = struct.unpack("<I", data[11:15])[0]

        print("direction={:04x}, op_flags={:04x}, session={:02x}, sig={:08x}, seq={:02x}, conn_sig={:08x}".format(direction, op_flags, session, sig, seq, conn_sig))

        return PRUDPV0Packet(direction=direction, op=op, flags=flags, seq=seq, conn_sig=conn_sig, session=session, sig=sig)

    def encode(self, rc4_state):
        pass

class PRUDPClient:
    STATE_EXPECT_SYN = 0
    STATE_EXPECT_CONNECT = 1
    STATE_CONNECTED = 2

    def __init__(self, rc4_key):
        self.rc4_state_encrypt = RC4(rc4_key)
        self.rc4_state_decrypt = RC4(rc4_key)

        state = PRUDPClient.STATE_EXPECT_SYN

    def calc_checksum(self, checksum,data):
        words = struct.unpack_from("<"+"I"*(len(data)//4),data)
        temp = sum(words) & 0xffffffff

        checksum+=sum(data[-(len(data) & 3):])
        checksum+=sum(struct.pack("I", temp))

        return checksum & 0xff


    def decode_packet(self, data):
        return PRUDPV0Packet.decode(data,self.rc4_state_decrypt)

    def encode_packet(self):
        # ...
        # return a bytestring
        data=b""
        data+=struct.pack("BB",self.source,self.dest)
        data+=struct.pack("<H",self.op | self.flags)
        data+=struct.pack("B",self.session)
        data+=struct.pack("<I",self.sig)
        data+=struct.pack("<H",self.seq)
        data+=struct.pack("<I",0)
        data+=struct.pack("<H",0)
        data+=struct.pack("B",self.calc_checksum(sum("ridfebb9".encode("ascii")),data))
        return data

    def handle_data(self, data):
        return self.handle_packet(self.decode_packet(data))

    def handle_packet(self, packet):
        # ...
        # do something here?
        if True:
            self.source = 0xa1
            self.dest = 0xaf
            self.op = packet.op
            self.flags = 0x90
            self.sig = packet.conn_sig
            self.session = packet.session
            self.seq = packet.seq
            self.size = 0
            return self.encode_packet()

# TODO: big issue with this is stray UDP packets.
# Time out connections after <some time> of lingering in STATE_EXPECT_SYN.

class PRUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
        self.connections = {}

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if not addr in self.connections:
            client = PRUDPClient(b"CD&ML")
            self.connections[addr] = client
        else:
            client = self.connections[addr]

        packet = client.handle_data(data)
        self.transport.sendto(packet, addr)
