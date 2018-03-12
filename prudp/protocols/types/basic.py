import struct

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

class StringType(Type):
	def __init__(self):
		super().__init__("string")

	def pack(self, to_pack):
		return struct.pack("<H",len(to_pack) + 1) + to_pack.encode('utf-8') + b'\x00'

	def unpack(self, to_unpack):
		string_size = struct.unpack("<H", to_unpack[0:2])[0]
		s = to_unpack[2:string_size+2 - 1].decode('utf-8') # remove the null byte from the final string!
		return s, string_size+3 # +3 lets us skip the null byte at the end..

class VariableBytesType(Type):
	def __init__(self):
		super().__init__("u8[*]")
	
	def pack(self, to_pack):
		return struct.pack("<I", len(to_pack)) + to_pack
	
	def unpack(self, to_unpack):
		raise NotImplementedError("No")

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

BasicU8 = StructType('u8', fmt="B")
BasicU16 = StructType('u16', fmt="H")
BasicU32 = StructType('u32', fmt="I")
String = StringType()
VarBytes = VariableBytesType()
ListU8 = ListType(BasicU8)
ListString = ListType(String)