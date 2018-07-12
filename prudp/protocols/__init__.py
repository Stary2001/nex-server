import functools
import struct
from nintendo.nex.streams import StreamIn, StreamOut
import prudp.protocols.types

def incoming(*args):
	funcs = []
	for a in args:
		if not callable(a):
			if a.startswith("list"):
				try:
					f = getattr(StreamIn, a[5:-1].lower())
				except:
					try:
						cls = getattr(types, a[5:-1])
						f = lambda cls=cls: s.extract(cls)
					except:
						print("Failed to get type", a)
						exit()
				funcs.append(lambda s, f=f: s.list(f, params=[s]))
			else:
				try:
					funcs.append(getattr(StreamIn, a.lower()))
				except:
					try:
						cls = getattr(types, a)
						funcs.append(lambda s, cls=cls: s.extract(cls))
					except:
						print("Failed to get type for in", a)
						exit()
		else:
			funcs.append(lambda s, o: s.extract(o))

	def decorator(f):
		@functools.wraps(f)
		def func(self, data):
			loc = 0
			real_args = []
			stream = StreamIn(data)
			for k in funcs:
				real_args.append(k(stream))
			return f(self, *real_args)
		return func
	return decorator

def outgoing(*args):
	funcs = []
	for a in args:
		if not callable(a):
			if a.startswith("list"):
				try:
					f = getattr(StreamOut, a[5:-1])
				except:
					try:
						f = getattr(types, a[5:-1]).streamin
					except:
						print("Failed to get type", a)
						exit()

				funcs.append(lambda s, o, f=f: s.list(o, f, params=[s]))
			else:
				try:
					funcs.append(getattr(StreamOut, a.lower()))
				except:
					funcs.append(lambda s, o: o.streamin(s))
		else:
			funcs.append(lambda s, o: o.pack(s))

	def decorator(f):
		@functools.wraps(f)
		def func(self, *argz):
			res = f(self, *argz)
			if len(res) != 3:
				print("Outgoing arg packing: function returned a tuple of length other than 3.")
				return (False, 0x80010005, None) # "Core::Exception",
			data = b''
			ret = []
			stream = StreamOut()
			for i, k in enumerate(funcs):
				k(stream, res[2][i])
			return (res[0], res[1], stream.data)
		return func
	return decorator

from prudp.protocols.authentication import AuthenticationProtocol
from prudp.protocols.secure_connection import SecureConnectionProtocol
from prudp.protocols.friends_3ds import Friends3DSProtocol
from prudp.protocols.matchmaking_extension import MatchmakingExtensionProtocol
from prudp.protocols.utility import UtilityProtocol

global protocol_list
protocol_list = {}
protocol_list[0x0a] = AuthenticationProtocol
protocol_list[0x0b] = SecureConnectionProtocol
protocol_list[0x65] = Friends3DSProtocol
protocol_list[0x6d] = MatchmakingExtensionProtocol
protocol_list[0x6e] = UtilityProtocol