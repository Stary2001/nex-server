import functools
import struct
from prudp.protocols.types import *

def unpack(typ, data):
	factory = Type.get_type(typ)
	if factory:
		return factory.unpack(data)
	else:
		raise NotImplementedError("Don't know how to unpack {}".format(typ))

def pack(typ, value):
	factory = Type.get_type(typ)
	if factory:
		return factory.pack(value)
	else:
		raise NotImplementedError("Don't know how to pack {}".format(typ))

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
from prudp.protocols.friends_3ds import Friends3DSProtocol

global protocol_list
protocol_list = {}
protocol_list[0x0a] = AuthenticationProtocol()
protocol_list[0x0b] = SecureConnectionProtocol()
protocol_list[0x65] = Friends3DSProtocol()