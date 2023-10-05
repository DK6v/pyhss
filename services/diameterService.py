import asyncio
import sys, os, json
import time, yaml, uuid
from datetime import datetime
sys.path.append(os.path.realpath('../lib'))
from messagingAsync import RedisMessagingAsync
from diameterAsync import DiameterAsync
from banners import Banners
from logtool import LogTool
import traceback

class DiameterService:
    """
    PyHSS Diameter Service
    A class for handling diameter inbounds and replies on Port 3868, via TCP.
    Functions in this class are high-performance, please edit with care. Last profiled on 20-09-2023.
    """

    def __init__(self):
        try:
            with open("../config.yaml", "r") as self.configFile:
                self.config = yaml.safe_load(self.configFile)
        except:
            print(f"[Diameter] [__init__] Fatal Error - config.yaml not found, exiting.")
            quit()

        self.redisUseUnixSocket = self.config.get('redis', {}).get('useUnixSocket', False)
        self.redisUnixSocketPath = self.config.get('redis', {}).get('unixSocketPath', '/var/run/redis/redis-server.sock')
        self.redisHost = self.config.get('redis', {}).get('host', 'localhost')
        self.redisPort = self.config.get('redis', {}).get('port', 6379)
        self.redisReaderMessaging = RedisMessagingAsync(host=self.redisHost, port=self.redisPort, useUnixSocket=self.redisUseUnixSocket, unixSocketPath=self.redisUnixSocketPath)
        self.redisWriterMessaging = RedisMessagingAsync(host=self.redisHost, port=self.redisPort, useUnixSocket=self.redisUseUnixSocket, unixSocketPath=self.redisUnixSocketPath)
        self.redisPeerMessaging = RedisMessagingAsync(host=self.redisHost, port=self.redisPort, useUnixSocket=self.redisUseUnixSocket, unixSocketPath=self.redisUnixSocketPath)
        self.banners = Banners()
        self.logTool = LogTool(config=self.config)
        self.diameterLibrary = DiameterAsync(logTool=self.logTool)
        self.activePeers = {}
        self.diameterRequestTimeout = int(self.config.get('hss', {}).get('diameter_request_timeout', 10))
        self.benchmarking = self.config.get('benchmarking', {}).get('enabled', False)
        self.benchmarkingInterval = self.config.get('benchmarking', {}).get('reporting_interval', 3600)
        self.diameterRequests = 0
        self.diameterResponses = 0
    
    async def validateDiameterInbound(self, clientAddress: str, clientPort: str, inboundData) -> bool:
        """
        Asynchronously validates a given diameter inbound, and increments the 'Number of Diameter Inbounds' metric.
        """
        try:
            packetVars, avps = await(self.diameterLibrary.decodeDiameterPacket(inboundData))
            originHost = (await(self.diameterLibrary.getAvpData(avps, 264)))[0]
            originHost = bytes.fromhex(originHost).decode("utf-8")
            peerType = await(self.diameterLibrary.getPeerType(originHost))
            self.activePeers[f"{clientAddress}-{clientPort}"].update({'diameterHostname': originHost,
                                                                      'peerType': peerType,
                                                                     })
            return True
        except Exception as e:
            await(self.logTool.logAsync(service='Diameter', level='warning', message=f"[Diameter] [validateDiameterInbound] Exception: {e}\n{traceback.format_exc()}"))
            await(self.logTool.logAsync(service='Diameter', level='warning', message=f"[Diameter] [validateDiameterInbound] AVPs: {avps}\nPacketVars: {packetVars}"))
            return False

    async def handleActiveDiameterPeers(self):
        """
        Prunes stale entries from self.activePeers, and
        keeps the ActiveDiameterPeers key in Redis current.
        """
        while True:
            try:
                if not len(self.activePeers) > 0:
                    await(asyncio.sleep(1))
                    continue

                activeDiameterPeersTimeout = self.config.get('hss', {}).get('active_diameter_peers_timeout', 3600)

                stalePeers = []

                for key, connection in self.activePeers.items():
                    if connection.get('connectionStatus', '') == 'disconnected': 
                        if (datetime.now() - datetime.strptime(connection['disconnectTimestamp'], "%Y-%m-%d %H:%M:%S")).seconds > activeDiameterPeersTimeout:
                            stalePeers.append(key)
                
                if len(stalePeers) > 0:
                    await(self.logTool.logAsync(service='Diameter', level='debug', message=f"[Diameter] [handleActiveDiameterPeers] Pruning disconnected peers: {stalePeers}"))
                    for key in stalePeers:
                        del self.activePeers[key]
                    await(self.logActivePeers())
                
                await(self.redisPeerMessaging.setValue(key='ActiveDiameterPeers', value=json.dumps(self.activePeers), keyExpiry=86400))

                await(asyncio.sleep(1))
            except Exception as e:
                print(e)
                await(asyncio.sleep(1))
                continue

    async def logActivePeers(self):
        """
        Logs the number of active connections on a rolling basis.
        """
        activePeers = self.activePeers
        if not len(activePeers) > 0:
            activePeers = ''
        await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [logActivePeers] {len(self.activePeers)} Active Peers {activePeers}"))

    async def logProcessedMessages(self):
        """
        Logs the number of processed messages on a rolling basis.
        """
        if not self.benchmarking:
            return False

        benchmarkInterval = int(self.benchmarkingInterval)

        while True:
            await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [logProcessedMessages] Processed {self.diameterRequests} inbound diameter messages in the last {self.benchmarkingInterval} second(s)"))
            await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [logProcessedMessages] Processed {self.diameterResponses} outbound in the last {self.benchmarkingInterval} second(s)"))
            self.diameterRequests = 0
            self.diameterResponses = 0
            await(asyncio.sleep(benchmarkInterval))

    async def readInboundData(self, reader, clientAddress: str, clientPort: str, socketTimeout: int, coroutineUuid: str) -> bool:
        """
        Reads and parses incoming data from a connected client. Validated diameter messages are sent to the redis queue for processing.
        Terminates the connection if diameter traffic is not received, or if the client disconnects.
        """
        await(self.logTool.logAsync(service='Diameter', level='debug', message=f"[Diameter] [readInboundData] [{coroutineUuid}] New connection from {clientAddress} on port {clientPort}"))
        peerIsValidated = False
        while True:
            try:

                inboundData = await(asyncio.wait_for(reader.read(8192), timeout=socketTimeout))

                if reader.at_eof():
                    await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [readInboundData] [{coroutineUuid}] Socket Timeout for {clientAddress} on port {clientPort}, closing connection."))
                    return False
                
                if len(inboundData) > 0:
                    await(self.logTool.logAsync(service='Diameter', level='debug', message=f"[Diameter] [readInboundData] [{coroutineUuid}] Received data from {clientAddress} on port {clientPort}"))
                    
                    if not peerIsValidated:
                        if not await(self.validateDiameterInbound(clientAddress, clientPort, inboundData)):
                            await(self.logTool.logAsync(service='Diameter', level='warning', message=f"[Diameter] [readInboundData] [{coroutineUuid}] Invalid Diameter Inbound, discarding data."))
                            await(asyncio.sleep(0))
                            continue
                        else:
                            await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [readInboundData] [{coroutineUuid}] Validated peer: {clientAddress} on port {clientPort}"))
                            peerIsValidated = True

                    inboundQueueName = f"diameter-inbound"
                    inboundHexString = json.dumps({"diameter-inbound": inboundData.hex(), "inbound-received-timestamp": time.time_ns(), "clientAddress": clientAddress, "clientPort": clientPort})
                    await(self.logTool.logAsync(service='Diameter', level='debug', message=f"[Diameter] [readInboundData] [{coroutineUuid}] Queueing {inboundHexString}"))
                    await(self.redisReaderMessaging.sendMessage(queue=inboundQueueName, message=inboundHexString, queueExpiry=self.diameterRequestTimeout))
                    if self.benchmarking:
                        self.diameterRequests += 1
                    await(asyncio.sleep(0))
                        
            except Exception as e:
                await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [readInboundData] [{coroutineUuid}] Socket Exception for {clientAddress} on port {clientPort}, closing connection.\n{e}"))
                return False

    async def writeOutboundData(self, writer, clientAddress: str, clientPort: str, socketTimeout: int, coroutineUuid: str) -> bool:
        """
        Waits for a message to be received from Redis, then sends to the connected client.
        """
        await(self.logTool.logAsync(service='Diameter', level='debug', message=f"[Diameter] [writeOutboundData] [{coroutineUuid}] writeOutboundData with host {clientAddress} on port {clientPort}"))
        while not writer.transport.is_closing():
            try:
                await(self.logTool.logAsync(service='Diameter', level='debug', message=f"[Diameter] [writeOutboundData] [{coroutineUuid}] Waiting for messages for host {clientAddress} on port {clientPort}"))
                pendingOutboundMessage = json.loads((await(self.redisWriterMessaging.awaitMessage(key=f"diameter-outbound-{clientAddress}-{clientPort}")))[1])
                await(self.logTool.logAsync(service='Diameter', level='debug', message=f"[Diameter] [writeOutboundData] [{coroutineUuid}] Received message: {pendingOutboundMessage} for host {clientAddress} on port {clientPort}"))
                diameterOutboundBinary = bytes.fromhex(pendingOutboundMessage.get('diameter-outbound', ''))
                await(self.logTool.logAsync(service='Diameter', level='debug', message=f"[Diameter] [writeOutboundData] [{coroutineUuid}] Sending: {diameterOutboundBinary.hex()} to to {clientAddress} on {clientPort}."))
                writer.write(diameterOutboundBinary)
                await(writer.drain())
                if self.benchmarking:
                    self.diameterResponses += 1
                await(asyncio.sleep(0))
            except Exception as e:
                await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [writeOutboundData] [{coroutineUuid}] Connection closed for {clientAddress} on port {clientPort}, closing writer."))
                return False

    async def handleConnection(self, reader, writer):
        """
        For each new connection on port 3868, create an asynchronous reader and writer, and handle adding and updating self.activePeers.
        If a reader or writer returns false, ensure that the connection is torn down entirely.
        """
        try:
            coroutineUuid = str(uuid.uuid4())
            (clientAddress, clientPort) = writer.get_extra_info('peername')
            await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] New Connection from: {clientAddress} on port {clientPort}"))
            if f"{clientAddress}-{clientPort}" not in self.activePeers:
                self.activePeers[f"{clientAddress}-{clientPort}"] = {
                                                                        "connectTimestamp": '',
                                                                        "disconnectTimestamp": '',
                                                                        "reconnectionCount": 0,
                                                                        "ipAddress":'',
                                                                        "port":'',
                                                                        "connectionStatus": '',
                                                                        "diameterHostname": '',
                                                                        "peerType": '',
                                                                        }
            else:
                reconnectionCount = self.activePeers.get(f"{clientAddress}-{clientPort}", {}).get('reconnectionCount', 0)
                reconnectionCount += 1
                self.activePeers[f"{clientAddress}-{clientPort}"].update({
                                                                        "reconnectionCount": reconnectionCount
                                                                        })

            self.activePeers[f"{clientAddress}-{clientPort}"].update({                
                                                                    "connectTimestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                    "ipAddress":clientAddress,
                                                                    "port": clientPort,
                                                                    "connectionStatus": 'connected',
                                                                    })
            await(self.logActivePeers())

            readTask = asyncio.create_task(self.readInboundData(reader=reader, clientAddress=clientAddress, clientPort=clientPort, socketTimeout=self.socketTimeout, coroutineUuid=coroutineUuid))
            writeTask = asyncio.create_task(self.writeOutboundData(writer=writer, clientAddress=clientAddress, clientPort=clientPort, socketTimeout=self.socketTimeout, coroutineUuid=coroutineUuid))

            completeTasks, pendingTasks =  await(asyncio.wait([readTask, writeTask], return_when=asyncio.FIRST_COMPLETED))

            for pendingTask in pendingTasks:
                try:
                    pendingTask.cancel()
                    await(asyncio.sleep(0.1))
                except asyncio.CancelledError:
                    pass
      
            writer.close()
            await(writer.wait_closed())
            self.activePeers[f"{clientAddress}-{clientPort}"].update({
                                                                    "connectionStatus": 'disconnected',
                                                                    "disconnectTimestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                    })
            await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [handleConnection] [{coroutineUuid}] Connection closed for {clientAddress} on port {clientPort}."))
            await(self.logActivePeers())
            return
        
        except Exception as e:
            await(self.logTool.logAsync(service='Diameter', level='info', message=f"[Diameter] [handleConnection] [{coroutineUuid}] Unhandled exception in diameterService.handleConnection: {e}"))
            return

    async def startServer(self, host: str=None, port: int=None, type: str=None):
        """
        Start a server with the given parameters and handle new clients with self.handleConnection.
        Also create a single instance of self.handleActiveDiameterPeers and self.logProcessedMessages.
        """

        if host is None:
            host=str(self.config.get('hss', {}).get('bind_ip', '0.0.0.0')[0])
        
        if port is None:
            port=int(self.config.get('hss', {}).get('bind_port', 3868))
        
        if type is None:
            type=str(self.config.get('hss', {}).get('transport', 'TCP'))

        self.socketTimeout = int(self.config.get('hss', {}).get('client_socket_timeout', 300))

        if type.upper() == 'TCP':
            server = await(asyncio.start_server(self.handleConnection, host, port))
        else:
            return False
        servingAddresses = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        await(self.logTool.logAsync(service='Diameter', level='info', message=f"{self.banners.diameterService()}\n[Diameter] Serving on {servingAddresses}"))
        handleActiveDiameterPeerTask = asyncio.create_task(self.handleActiveDiameterPeers())
        if self.benchmarking:
            logProcessedMessagesTask = asyncio.create_task(self.logProcessedMessages())

        async with server:
            await(server.serve_forever())


if __name__ == '__main__':
    diameterService = DiameterService()
    asyncio.run(diameterService.startServer())