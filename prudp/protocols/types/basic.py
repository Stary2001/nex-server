import struct
import datetime

# TODO: make List automatic (list<blah> returns a ListType(getType(blah)))

types = {}

class Type:
	def __init__(self, name):
		global types
		self.name = name
		types[name] = self

	@staticmethod
	def get_type(name):
		global types
		if name in types:
			return types[name]
		else:
			return None

	def pack(self):
		""" Should return a bytestring."""
		pass

	def unpack(self, data):
		""" Should return the data and the unpacked length."""
		pass

class StructType(Type):
	def __init__(self, name, fmt):
		super().__init__(name)
		self.fmt = fmt
		self.len = struct.calcsize(fmt)

	def pack(self, to_pack):
		return struct.pack(self.fmt, to_pack)

	def unpack(self, to_unpack):
		return struct.unpack(self.fmt, to_unpack[0:self.len])[0], self.len

class BoolType(Type):
	def __init__(self):
		super().__init__("bool")

	def pack(self, to_pack):
		return b'\x01' if to_pack else b'\x00'

	def unpack(self, to_unpack):
		return to_unpack[0] != 0, 1

class StringType(Type):
	def __init__(self):
		super().__init__("string")

	def pack(self, to_pack):
		return struct.pack("<H",len(to_pack) + 1) + to_pack.encode('utf-8') + b'\x00'

	def unpack(self, to_unpack):
		print("k", to_unpack)
		string_size = struct.unpack("<H", to_unpack[0:2])[0]
		s = to_unpack[2:string_size+2 - 1].decode('utf-8') # remove the null byte from the final string!
		print(s)
		return s, string_size+2

class BufferType(Type):
	def __init__(self, name):
		super().__init__(name)

	def pack(self, to_pack):
		return struct.pack("<I", len(to_pack)) + to_pack

	def unpack(self, to_unpack):
		data_len = struct.unpack("<I", to_unpack[0:4])[0]
		return to_unpack[4:data_len+4], data_len + 4

class ListType(Type):
	def __init__(self, containing_type):
		super().__init__("list<" + containing_type.name + ">")
		self.containing_type = containing_type

	def pack(self, to_pack):
		data = struct.pack("<I", len(to_pack))
		for item in to_pack:
			data += self.containing_type.pack(item)
		return data

	def unpack(self, to_unpack):
		items = []
		n_items = struct.unpack("<I",to_unpack[0:4])[0]
		curr = 4 # Skip the list length.
		for k in range(1, n_items+1):
			item, item_len = self.containing_type.unpack(to_unpack[curr:])
			items.append(item)
			curr += item_len
		return items, curr

class NEXDateTimeType(Type):
	def __init__(self):
		super().__init__("DateTime")

	def pack(self, to_pack):
		raise NotImplementedError("NEXDateTimeType packing is not implemented!")

	def unpack(self, to_unpack):
		packed_date, _ = BasicU64.unpack(to_unpack)
		year = packed_date & (0xffff << 24) >> 24
		month = packed_date & (0xf << 20) >> 20
		day = packed_date & (0xf << 16) >> 16
		hour = packed_date & (0xf << 12) >> 12
		minute = packed_date & (0x3f << 6) >> 6
		second = packed_date & 0x3f
		return datetime.datetime(year, month, day, hour, minute, second), 8

BasicU8 = StructType('u8', fmt='B')
BasicU16 = StructType('u16', fmt='H')
BasicU32 = StructType('u32', fmt='I')
BasicU64 = StructType('u64', fmt='Q')
String = StringType()
Bool = BoolType()
VarBytes = BufferType('u8[*]')
Buffer = BufferType('Buffer')
ListU8 = ListType(BasicU8)
ListU32 = ListType(BasicU32)
ListU64 = ListType(BasicU64)
ListString = ListType(String)
ListBuffer = ListType(Buffer)

NEXDateTime = NEXDateTimeType()