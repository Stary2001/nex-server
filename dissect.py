from prudp import PRUDPV0Packet
from rc4 import RC4
from binascii import hexlify, unhexlify
from pcapfile import savefile
import sys
import struct

f = open(sys.argv[1], 'rb')
pcapfile = savefile.load_savefile(f, verbose=True, layers=3)

src_addr = None
dst_addr = None

rc4_c = RC4(b'CD&ML', reset=False)
rc4_s = RC4(b'CD&ML', reset=False)

for p in pcapfile.packets:
    data = unhexlify(p.packet.payload.payload.payload)

    if data[0:2] == b'\xaf\xa1':
        print(">>> ", end="")
        p = PRUDPV0Packet.decode(data, rc4_c)
    elif data[0:2] == b'\xa1\xaf':
        print("<<< ", end="")
        p = PRUDPV0Packet.decode(data, rc4_s)
    #print(p)

    if p.op == PRUDPV0Packet.OP_SYN:
        print("SYN seq {}{}".format(p.seq, " (ack)" if p.flags & PRUDPV0Packet.FLAG_ACK else ""))
    elif p.op == PRUDPV0Packet.OP_CONNECT:
        print("CONNECT seq {}{}".format(p.seq, " (ack)" if p.flags & PRUDPV0Packet.FLAG_ACK else ""))
    if p.op == PRUDPV0Packet.OP_DATA:
        if p.flags & PRUDPV0Packet.FLAG_ACK:
            print("Data ack for seq {}".format(p.seq))
        else:
            print("Data packet seq {}: {}".format(p.seq, hexlify(p.data).decode('ascii')))
            data_len = struct.unpack("<I", p.data[0:4])[0]
            proto_with_flag = p.data[4]
            proto_id = proto_with_flag & ~0x80

            if proto_with_flag & 0x80:
                # Request.
                call_id = struct.unpack("<I", p.data[5:9])[0]
                method = struct.unpack("<I", p.data[9:13])[0]
                arg_data = p.data[13:data_len+13]
                print("NEX request, call_id={:08x}, method={:08x}, data={}".format(call_id, method, hexlify(arg_data)))
            else:
                success = p.data[5]
                if success:
                    call_id = struct.unpack("<I", p.data[6:10])[0]
                    method = struct.unpack("<I", p.data[10:14])[0]
                    arg_data = p.data[14:data_len+14]
                    print("NEX response, success. call_id={:08x}, method={:08x}, response_data={}".format(call_id, method, hexlify(arg_data)))
                else:
                    result = struct.unpack("<I", p.data[6:10])[0]
                    call_id = struct.unpack("<I", p.data[10:14])[0]
                    print("NEX response, failure. call_id={:08x}, result={:08x}".format(call_id, result))
    elif p.op == PRUDPV0Packet.OP_HEARTBEAT:
        print("Heartbeat seq {}".format(p.seq))
    elif p.op == PRUDPV0Packet.OP_DISCONNECT:
        print("Disconnect request seq {}".format(p.seq))