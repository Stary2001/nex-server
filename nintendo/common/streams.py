
import struct


class StreamOut:
	def __init__(self, endian="<"):
		self.endian = endian
		self.data = b""
		self.pos = 0
		
	def seek(self, pos): self.pos = pos
	def tell(self): return self.pos
	def size(self): return len(self.data)
		
	def write(self, data):
		self.data = self.data[:self.pos] + data + self.data[self.pos + len(data):]
		self.pos += len(data)
		
	def u8(self, value): self.write(bytes([value]))
	def u16(self, value): self.write(struct.pack(self.endian + "H", value))
	def u32(self, value): self.write(struct.pack(self.endian + "I", value))
	def u64(self, value): self.write(struct.pack(self.endian + "Q", value))
	
	def s8(self, value): self.write(struct.pack("b", value))
	def s16(self, value): self.write(struct.pack(self.endian + "h", value))
	def s32(self, value): self.write(struct.pack(self.endian + "i", value))
	def s64(self, value): self.write(struct.pack(self.endian + "q", value))
	
	def float(self, value): self.write(struct.pack(self.endian + "f", value))
	def double(self, value): self.write(struct.pack(self.endian + "d", value))
	
	def bool(self, value): self.u8(1 if value else 0)
	
	def list(self, list, func, params):
		for i in list:
			func(i, *params)
	
	def chars(self, data):
		self.write(data.encode("ascii"))
		
	def wchars(self, data):
		self.list([ord(char) for char in data], self.u16)


class StreamIn:
	def __init__(self, data, endian="<"):
		self.endian = endian
		self.data = data
		self.pos = 0
		
	def seek(self, pos): self.pos = pos
	def tell(self): return self.pos
	def size(self): return len(self.data)
		
	def read(self, num):
		data = self.data[self.pos : self.pos + num]
		self.pos += num
		return data
		
	def u8(self): return self.read(1)[0]
	def u16(self): return struct.unpack(self.endian + "H", self.read(2))[0]
	def u32(self): return struct.unpack(self.endian + "I", self.read(4))[0]
	def u64(self): return struct.unpack(self.endian + "Q", self.read(8))[0]
	
	def s8(self): return struct.unpack("b", self.read(1))[0]
	def s16(self): return struct.unpack(self.endian + "h", self.read(2))[0]
	def s32(self): return struct.unpack(self.endian + "i", self.read(4))[0]
	def s64(self): return struct.unpack(self.endian + "q", self.read(8))[0]
	
	def float(self): return struct.unpack(self.endian + "f", self.read(4))[0]
	def double(self): return struct.unpack(self.endian + "d", self.read(8))[0]
	
	def bool(self): return bool(self.u8())
	
	def list(self, func, count, params=None):
		return [func(*params) for i in range(count)]
	
	def chars(self, num):
		return self.read(num).decode("ascii")
		
	def wchars(self, num):	
		return "".join([chr(x) for x in self.list(self.u16, num)])
		
		
class BitStreamOut(StreamOut):
	def __init__(self, endian="<"):
		super().__init__(endian)
		self.bitpos = 0
		
	def align(self):
		if self.bitpos:
			self.bitpos = 0
			self.pos += 1

	def seek(self, pos):
		self.align()
		super().seek(pos)
		
	def write(self, data):
		self.align()
		super().write(data)
	
	def bit(self, value):
		if self.pos < len(self.data):
			byte = self.data[self.pos]
		else:
			byte = 0

		mask = 1 << (7 - self.bitpos)
		if value:
			byte |= mask
		else:
			byte &= ~mask
		
		self.data = self.data[:self.pos] + bytes([byte]) + self.data[self.pos + 1:]

		self.bitpos += 1
		if self.bitpos == 8:
			self.bitpos = 0
			self.pos += 1
			
	def bits(self, value, num):
		for i in range(num):
			self.bit((value >> (num - i - 1)) & 1)
		
		
class BitStreamIn(StreamIn):
	def __init__(self, data, endian="<"):
		super().__init__(data, endian)
		self.bitpos = 0
		
	def align(self):
		if self.bitpos:
			self.bitpos = 0
			self.pos += 1

	def seek(self, pos):
		self.align()
		super().seek(pos)
			
	def read(self, num):
		self.align()
		return super().read(num)
		
	def bit(self):
		byte = self.data[self.pos]
		value = (byte >> (7 - self.bitpos)) & 1
		self.bitpos += 1
		if self.bitpos == 8:
			self.bitpos = 0
			self.pos += 1
		return value
		
	def bits(self, num):
		value = 0
		for i in range(num):
			value <<= 1
			value |= self.bit()
		return value
