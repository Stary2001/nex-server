import asyncio
from prudp import PRUDPProtocol

loop = asyncio.get_event_loop()
listen = loop.create_datagram_endpoint(PRUDPProtocol, local_addr=('0.0.0.0', 9999))
transport, protocol = loop.run_until_complete(listen)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

transport.close()
loop.close()
