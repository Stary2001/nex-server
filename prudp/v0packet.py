import struct
import hmac
import hashlib
from binascii import hexlify

class PRUDPV0Packet:
    OP_SYN = 0
    OP_CONNECT = 1
    OP_DATA = 2
    OP_DISCONNECT = 3
    OP_HEARTBEAT = 4

    FLAG_ACK = 0x1
    FLAG_RELIABLE = 0x2
    FLAG_NEEDS_ACK = 0x4
    FLAG_HAS_SIZE = 0x8

    def __init__(self, client=None, source=None, dest=None, op=None, flags=None, session=None, sig=None, seq=None, conn_sig=None, fragment=None, data_size=None, data=None, access_key=None, sig_version=None):
        self.client = client
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
        s = "source={:02x}, dest={:02x}, op={}, flags={:04x}, session={:02x}, sig={:08x}, seq={:02x}".format(self.source, self.dest, self.op, self.flags, self.session, struct.unpack("<I", self.sig)[0], self.seq)

        if self.conn_sig != None:
            s += ", conn_sig={:08x}".format(struct.unpack("<I", self.conn_sig)[0])
        elif self.fragment != None:
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
        checksum += sum(data[len(data) & ~3:])
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
        sig = data[5:9]
        seq = struct.unpack("<H", data[9:11])[0]

        conn_sig = None
        fragment = None
        data_size = None
        packet_data = None

        if op == PRUDPV0Packet.OP_SYN or op == PRUDPV0Packet.OP_CONNECT:
            header_size = 15
            conn_sig = data[11:15]
        elif op == PRUDPV0Packet.OP_DATA:
            header_size = 12
            fragment = data[11]
        else:
            header_size = 11

        if flags & PRUDPV0Packet.FLAG_HAS_SIZE != 0:
            data_size = struct.unpack("<H", data[header_size:header_size+2])[0]
            header_size += 2

            packet_data = data[header_size:header_size+data_size]

        if (op == PRUDPV0Packet.OP_DATA or op == PRUDPV0Packet.OP_CONNECT) and flags & PRUDPV0Packet.FLAG_ACK == 0:
            if data_size == None:
                data_size = len(data) - header_size - 1
                packet_data = data[header_size:header_size+data_size]
            if op == PRUDPV0Packet.OP_DATA:
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

    def calc_data_sig(self, enc_data):
        if self.client.server.sig_version != 0 and self.data_size == 0 or self.data == b'':
            return b'\x78\x56\x34\x12'
        else:
            if self.client.server.sig_version == 0:
                if enc_data == None:
                    if self.op == PRUDPV0Packet.OP_DISCONNECT:
                        enc_data = b'\x00'
                    else:
                        enc_data = b''

                if self.client and self.client.server.secure_key != None:
                    enc_data = self.client.server.secure_key + struct.pack("<HB", self.seq, self.fragment) + enc_data
                else:
                    enc_data = struct.pack("<HB", self.seq, self.fragment) + enc_data

            return hmac.HMAC(self.client.server.data_sig_key, enc_data).digest()[:4]

    def calc_sig(self, enc_data, signature):
        if self.op == PRUDPV0Packet.OP_DATA or (self.op == PRUDPV0Packet.OP_DISCONNECT and self.client.server.sig_version == 0): #or (self.op == PRUDPV0Packet.OP_CONNECT and self.data != None):
            return self.calc_data_sig(enc_data)
        elif self.op == PRUDPV0Packet.OP_SYN:
            return b'\x00\x00\x00\x00'
        else:
            return signature

    def encode(self, rc4_state):
        enc_data = None
        if self.data:
            if self.op == PRUDPV0Packet.OP_DATA: # CONNECTs have unencrypted data!
                enc_data = rc4_state.crypt(self.data)
            else:
                enc_data = self.data

        sig = None
        if self.sig == None:
            self.sig = self.calc_sig(enc_data, self.client.client_signature)

        if self.op == PRUDPV0Packet.OP_SYN or self.op == PRUDPV0Packet.OP_CONNECT and self.conn_sig == None:
            self.conn_sig = b'\x00\x00\x00\x00'

        data = b""
        data += struct.pack("BB", self.source, self.dest)
        data += struct.pack("<H", (self.op & 0xF) | (self.flags << 4))
        data += struct.pack("B", self.session)
        data += self.sig
        data += struct.pack("<H", self.seq)

        if self.op == PRUDPV0Packet.OP_SYN or self.op == PRUDPV0Packet.OP_CONNECT:
            data += self.conn_sig
        elif self.op == PRUDPV0Packet.OP_DATA:
            data += struct.pack("<B", self.fragment)

        if self.flags & PRUDPV0Packet.FLAG_HAS_SIZE != 0:
            data += struct.pack("<H", self.data_size)

        if self.data:
            data += enc_data

        data += struct.pack("B", PRUDPV0Packet.calc_checksum(self.client.server.checksum_base, data))
        return data

class PRUDPV0PacketOut(PRUDPV0Packet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direction = 0xafa1
