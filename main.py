import asyncio
from prudp import NEXProtocol

loop = asyncio.get_event_loop()
listen = loop.create_datagram_endpoint(NEXProtocol, local_addr=('0.0.0.0', 60000))
transport, protocol = loop.run_until_complete(listen)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

transport.close()
loop.close()
