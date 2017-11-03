import functools
import struct

def unpack(typ, data):
	if typ == 'string':
		string_size = struct.unpack("<H", data[0:2])[0]
		s = data[2:string_size+2].decode('utf-8')
		return s, string_size+3 # +3 lets us skip the null byte at the end..

def pack(typ, value):
	if typ == 'u16':
		return struct.pack("<H", value)
	elif typ == 'u32':
		return struct.pack("<I", value)
	elif typ == 'u8[]':
		return value
	elif typ == 'u8[*]':
		return struct.pack("<I", len(value)) + value
	elif typ == 'string':
		return struct.pack("<H", len(value) + 1) + value.encode('utf-8') + b'\x00'

def incoming(*args):
	def decorator(f):
		@functools.wraps(f)
		def func(self, data):
			loc = 0
			real_args = []

			for k in args:
				value, size = unpack(k, data[loc:])
				real_args.append(value)
				loc += size

			return f(self, *real_args)
		return func
	return decorator

def outgoing(*args):
	def decorator(f):
		@functools.wraps(f)
		def func(self, data):
			res = f(self, data)
			if len(res) != 3:
				print("Outgoing arg packing: function returned a tuple of length other than 3.")
				return (False, 0x80010005, None) # "Core::Exception",
			data = b''
			ret = []

			for i, k in enumerate(args):
				data += pack(k, res[2][i])
			return (res[0], res[1], data)
		return func
	return decorator


from prudp.protocols.authentication import AuthenticationProtocol

global protocol_list
protocol_list = {}
protocol_list[0x0a] = AuthenticationProtocol()