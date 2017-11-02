import asyncio
import struct
from rc4 import RC4
from binascii import hexlify

class PRUDPV0Packet:
    OP_SYN = 0
    OP_CONNECT = 1
    OP_DATA = 2
    OP_DISCONNECT = 3

    FLAG_ACK = 0x1
    FLAG_RELIABLE = 0x2
    FLAG_NEEDS_ACK = 0x4
    FLAG_HAS_SIZE = 0x8

    def __init__(self, source=None, dest=None, op=None, flags=None, session=None, sig=None, seq=None, conn_sig=None, fragment=None, data_size=None, data=None):
        self.source = source
        self.dest = dest
        self.op = op
        self.flags = flags
        self.session = session
        self.sig = sig
        self.seq = seq
        self.conn_sig = conn_sig
        self.fragment = fragment
        self.data_size = data_size
        self.data = data

    def __repr__(self):
        s = "source={:02x}, dest={:02x}, op={}, flags={:04x}, session={:02x}, sig={:08x}, seq={:02x}".format(self.source, self.dest, self.op, self.flags, self.session, self.sig, self.seq)

        if self.conn_sig != None:
            s += ", conn_sig={:08x}".format(self.conn_sig)
        else:
            s += ", fragment={:02x}".format(self.fragment)

        if self.data_size != None:
            s += ", data_size={:04x}".format(self.data_size)
        if self.data != None:
            s += "\ndata: {}".format(hexlify(self.data))
        return s

    @staticmethod
    def calc_checksum(checksum, data):
        words = struct.unpack_from("<"+"I"*(len(data)//4),data)
        temp = sum(words) & 0xffffffff

        checksum += sum(data[-(len(data) & 3):])
        checksum += sum(struct.pack("I", temp))

        return checksum & 0xff

    @staticmethod
    def decode(data, rc4_state):
        source = data[0]
        dest = data[1]

        op_flags = struct.unpack("<H", data[2:4])[0]
        op = op_flags & 0xF
        flags = (op_flags & 0xFFF0) >> 4

        session = data[4]
        sig = struct.unpack("<I", data[5:9])[0]
        seq = struct.unpack("<H", data[9:11])[0]

        conn_sig = None
        fragment = None
        data_size = None
        packet_data = None

        if op == PRUDPV0Packet.OP_SYN or op == PRUDPV0Packet.OP_CONNECT:
            header_size = 15
            conn_sig = struct.unpack("<I", data[11:15])[0]
        else:
            header_size = 12
            fragment = data[11]

        if flags & PRUDPV0Packet.FLAG_HAS_SIZE != 0:
            data_size = struct.unpack("<H", data[header_size:header_size+2])
            header_size += 2

        return PRUDPV0Packet(source=source,
                             dest=dest,
                             op=op,
                             flags=flags,
                             session=session,
                             sig=sig,
                             seq=seq,
                             conn_sig=conn_sig,
                             fragment=fragment,
                             data_size=data_size,
                             data=packet_data)

    def encode(self, rc4_state):
        if self.sig == None:
            self.sig = 0

        if self.conn_sig == None:
            self.conn_sig = 0

        data = b""
        data += struct.pack("BB", self.source, self.dest)
        data += struct.pack("<H", (self.op & 0xF) | (self.flags << 4))
        data += struct.pack("B", self.session)
        data += struct.pack("<I", self.sig)
        data += struct.pack("<H", self.seq)

        if self.op == PRUDPV0Packet.OP_SYN or self.op == PRUDPV0Packet.OP_CONNECT:
            data += struct.pack("<I", self.conn_sig)
        else:
            data += struct.pack("<B", self.fragment)

        if self.flags & PRUDPV0Packet.FLAG_HAS_SIZE != 0:
            data += struct.pack("<H", self.data_size)

        if self.data:
            data += rc4_state.crypt(self.data)

        data += struct.pack("B", PRUDPV0Packet.calc_checksum(sum("ridfebb9".encode("ascii")), data))
        return data

class PRUDPV0PacketOut(PRUDPV0Packet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direction = 0xafa1

class PRUDPClient:
    STATE_EXPECT_SYN = 0
    STATE_EXPECT_CONNECT = 1
    STATE_CONNECTED = 2

    def __init__(self, rc4_key):
        self.rc4_state_encrypt = RC4(rc4_key)
        self.rc4_state_decrypt = RC4(rc4_key)

        self.cur_seq = 0
        self.state = PRUDPClient.STATE_EXPECT_SYN

        self.last_sig = None

    def decode_packet(self, data):
        return PRUDPV0Packet.decode(data, self.rc4_state_decrypt)

    def handle_data(self, data):
        return self.handle_packet(self.decode_packet(data))

    def handle_packet(self, packet):
        if self.state == PRUDPClient.STATE_EXPECT_SYN:
            if packet.op == PRUDPV0Packet.OP_SYN: # SYN
                print("Got SYN!")
                print(packet)
                self.state = PRUDPClient.STATE_EXPECT_CONNECT

                packet_out = PRUDPV0PacketOut()
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_SYN
                packet_out.flags = PRUDPV0Packet.FLAG_ACK | PRUDPV0Packet.FLAG_HAS_SIZE
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.data_size = 0

                p = packet_out.encode(self.rc4_state_encrypt)
                print("Sending", packet_out)
                return p
            else:
                #print("Got a non-SYN in EXPECT_SYN")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_EXPECT_CONNECT:
            if packet.op == PRUDPV0Packet.OP_CONNECT:
                print("Got CONNECT!")
                print(packet)
                self.state = PRUDPClient.STATE_CONNECTED

                packet_out = PRUDPV0PacketOut()
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_CONNECT
                packet_out.flags = PRUDPV0Packet.FLAG_ACK | PRUDPV0Packet.FLAG_HAS_SIZE
                packet_out.session = packet.session
                packet_out.seq = packet.seq
                packet_out.data_size = 0
                packet_out.sig = packet.conn_sig

                p = packet_out.encode(self.rc4_state_encrypt)
                print("Sending", packet_out)
                return p
            else:
                #print("Got a non-CONNECT in EXPECT_CONNECT")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_CONNECTED:
            print("Connected:")
            print(packet)
# TODO: big issue with this is stray UDP packets.
# Time out connections after <some time> of lingering in STATE_EXPECT_SYN.

class PRUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
        self.connections = {}

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        #print(data,addr)
        if not addr in self.connections:
            client = PRUDPClient(b"CD&ML")
            self.connections[addr] = client
        else:
            client = self.connections[addr]

        packet = client.handle_data(data)
        if packet != None:
            print("Sending data", packet)
            self.transport.sendto(packet, addr)