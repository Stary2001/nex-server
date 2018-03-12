import functools
import struct
from prudp.protocols.types import *

def unpack(typ, data):
	"""if typ == 'string':
		string_size = struct.unpack("<H", data[0:2])[0]
		print(data[2:string_size+2])
		s = data[2:string_size+2 - 1].decode('utf-8') # remove the null byte from the final string!
		print(s)
		return s, string_size+3 # +3 lets us skip the null byte at the end..
	elif typ == 'u32':
		return struct.unpack("<I", data[0:4])[0], 4
	elif typ[0:4] == 'list': # list<type>
		item_type = typ[5:-1]
		for item in value:
			data += pack(item)

		return data"""
	
	factory = Type.get_type(typ)
	if factory:
		return factory.unpack(data)
	else:
		raise NotImplementedError("Don't know how to unpack {}".format(typ))

def pack(typ, value):
	"""
	elif typ == 'u8[*]':
		return struct.pack("<I", len(value)) + value
	elif typ == 'string':
		return struct.pack("<H", len(value) + 1) + value.encode('utf-8') + b'\x00'
	elif typ[0:4] == 'list': # list<type>
		data = struct.pack("<I", len(value))
		item_type = typ[5:-1]
		for item in value:
			data += pack(item)

		return data"""

	factory = Type.get_type(typ)
	if factory:
		return factory.pack(value)
	else:
		raise NotImplementedError("Don't know how to pack {}".format(typ))

def incoming(*args):
	def decorator(f):
		@functools.wraps(f)
		def func(self, data):
			print(data)
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
		def func(self, *argz):
			res = f(self, *argz)
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
from prudp.protocols.secure_connection import SecureConnectionProtocol

global protocol_list
protocol_list = {}
protocol_list[0x0a] = AuthenticationProtocol()
protocol_list[0x0b] = SecureConnectionProtocol()
