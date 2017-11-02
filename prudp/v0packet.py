import struct
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

            packet_data = data[header_size:header_size+data_size]
        elif op == PRUDPV0Packet.OP_DATA:
            data_size = len(data) - header_size - 1
            packet_data = data[header_size:header_size+data_size]
            packet_data = rc4_state.crypt(packet_data)

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
