from prudp import PRUDPV0Packet
from prudp.protocols import incoming, outgoing
from prudp.protocols.types import KerberosContainer, Buffer, String
from rc4 import RC4
from binascii import hexlify, unhexlify
from pcapfile import savefile
import sys
import struct
import hashlib

f = open(sys.argv[1], 'rb')
pcapfile = savefile.load_savefile(f, verbose=True, layers=3)

src_addr = None
dst_addr = None

user_pid = 1863211397
user_password = "|+GF-i):/7Z87_:q"

connections = {}

last_secure_addr = None
last_secure_key = None

def do_nex(proto, method_with_flag, data):
    global last_secure_addr, last_secure_key
    method = method_with_flag &~0x8000

    if proto == 0x0a and (method == 1 or method == 2):
        kerb_ticket, kerb_ticket_len = Buffer.unpack(data[8:])
        k, _ = KerberosContainer(user_pid = user_pid, user_password = user_password).unpack(kerb_ticket)
        secure_url, secure_url_len = String.unpack(data[8 + kerb_ticket_len:])
        print(secure_url)

        secure_url = dict(map(lambda x: x.split('='), secure_url.replace('prudps:/', '').split(';')))
        last_secure_addr = (secure_url['address'].encode(), int(secure_url['port']))
    elif proto == 0x0a and method == 3:
        kerb_ticket, kerb_ticket_len = Buffer.unpack(data[4:])
        k, _ = KerberosContainer(user_pid = user_pid, user_password = user_password).unpack(kerb_ticket)
        secure_key = k[0:16]
        if k[16] != 0:
            secure_key = k[0:32]
        connections[last_secure_addr] = {'c_state': RC4(secure_key, reset=False), 's_state': RC4(secure_key, reset=False)}

def calc_checksum(checksum, data):
    words = struct.unpack_from("<"+"I"*(len(data)//4),data)
    temp = sum(words) & 0xffffffff
    checksum += sum(data[len(data) & ~3:])
    checksum += sum(struct.pack("I", temp))
    return checksum & 0xff

for p in pcapfile.packets:
    ip = p.packet.payload
    if type(ip) == bytes:
        continue
    udp = ip.payload

    if p.packet.type != 2048:
        continue

    if type(p.packet.payload.payload) == bytes: # idk
        continue

    current_connection = None
    if (ip.src, udp.src_port) in connections:
        current_connection = connections[(ip.src, udp.src_port)]
    elif (ip.dst, udp.dst_port) in connections:
        current_connection = connections[(ip.dst, udp.dst_port)]

    data = unhexlify(p.packet.payload.payload.payload)

    if data[0:2] == b'\xaf\xa1':
        print(">>> ", end="")
        real_p = p
        if current_connection == None:
            p = PRUDPV0Packet.decode(data, None)
        else:
            p = PRUDPV0Packet.decode(data, current_connection['c_state'])
        if ip.dst == b'35.163.2.89' and (calc_checksum(sum(b'6181dff1'), data[:-1]) != data[-1]):
            print("checksum failure!!!!!!!!!!")
            exit()
    elif data[0:2] == b'\xa1\xaf':
        print("<<< ", end="")
        real_p = p
        if current_connection == None:
            p = PRUDPV0Packet.decode(data, None)
        else:
            p = PRUDPV0Packet.decode(data, current_connection['s_state'])

        if ip.src == b'35.163.2.89' and (calc_checksum(sum(b'6181dff1'), data[:-1]) != data[-1]):
                print("checksum failure!!!!!!!!!!")
                exit()
    else:
        continue

    if p.op == PRUDPV0Packet.OP_SYN:
        print("SYN seq {}{} {}:{}".format(p.seq, " (ack)" if p.flags & PRUDPV0Packet.FLAG_ACK else "", ip.dst, udp.dst_port))
        if data[0:2] == b'\xaf\xa1':
            if not (ip.dst, udp.dst_port) in connections:
                print("creating conn for ", ip.dst, udp.dst_port)
                connections[(ip.dst, udp.dst_port)] = {'c_state': RC4(b'CD&ML', reset=False), 's_state': RC4(b'CD&ML', reset=False)}
    elif p.op == PRUDPV0Packet.OP_CONNECT:
        print("CONNECT seq {}{}".format(p.seq, " (ack)" if p.flags & PRUDPV0Packet.FLAG_ACK else ""))
    elif p.op == PRUDPV0Packet.OP_DATA:
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
                print("NEX request, call_id={:08x}, proto={:02x}, method={:08x}, data={}".format(call_id, proto_id, method, hexlify(arg_data)))
            else:
                success = p.data[5]
                if success:
                    call_id = struct.unpack("<I", p.data[6:10])[0]
                    method = struct.unpack("<I", p.data[10:14])[0]
                    arg_data = p.data[14:data_len+14]
                    print("NEX response, success. call_id={:08x}, proto={:02x}, method={:08x}, response_data={}".format(call_id, proto_id, method, hexlify(arg_data)))
                    do_nex(proto_id, method, arg_data)
                else:
                    result = struct.unpack("<I", p.data[6:10])[0]
                    call_id = struct.unpack("<I", p.data[10:14])[0]
                    print("NEX response, failure. call_id={:08x}, result={:08x}".format(call_id, result))
    elif p.op == PRUDPV0Packet.OP_HEARTBEAT:
        print("Heartbeat seq {}".format(p.seq))
    elif p.op == PRUDPV0Packet.OP_DISCONNECT:
        print("Disconnect request seq {}".format(p.seq))
        if (ip.src, udp.src_port) in connections:
            print("Deleting ", (ip.src, udp.src_port))
            del connections[(ip.src, udp.src_port)]
        elif (ip.dst, udp.dst_port) in connections:
            print("Deleting ", (ip.dst, udp.dst_port))
            del connections[(ip.dst, udp.dst_port)]
