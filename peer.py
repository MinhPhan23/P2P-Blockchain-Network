import json
import sys
import traceback
import uuid
import socket
import select
import time
import random
import hashlib
import copy
import os
import threading

WELL_KNOWN = ('silicon.cs.umanitoba.ca', 8999)
DIFFICULTY = 8
NO_TIMEOUT = 1000000000
MAX_LENGTH = 100000

myself = ''

peersList = [WELL_KNOWN]
peersTimeout = [time.time()+NO_TIMEOUT]

def miner(params):
    try:
        newBlock = {
            "type": "ANNOUNCE",
            "height": params['height'],
            "minedBy": "Nico Nico Nii",
            "nonce": "",
            "messages": ["Need that 10%"],
            "hash": "",
            "timestamp": 0
        }
        print(newBlock)
        found = False
        while True and not params['exit'] and not found:
            hashBase = hashlib.sha256()
                    # get the most recent hash
                    # add it to this hash
            hashBase.update(params['lastHash'].encode())
            
            # add the miner
            hashBase.update(newBlock['minedBy'].encode())

            # add the messages in order
            for m in newBlock['messages']:                
                hashBase.update(m.encode())
            
            # the time (different because this is a number, not a string)
            newBlock['timestamp'] = int(time.time())
            hashBase.update(newBlock['timestamp'].to_bytes(8, 'big'))  
            
            nonce = os.urandom(10)
            newBlock['nonce'] = nonce.hex()
            # add the nonce
            hashBase.update(newBlock['nonce'].encode())   

            # get the pretty hexadecimal
            hash = hashBase.hexdigest()
            
            if hash[-1 * DIFFICULTY:] == '0' * DIFFICULTY:
                found = True
                newBlock['hash'] = hash
                
        if found:
            print("found a new block")
            for peer in peersList:
                params['socket'].sendto(json.dumps(newBlock).encode(), peer)
            params['socket'].sendto(json.dumps(newBlock).encode(), myself)
    except Exception as e:
        print(e)
        print("Miner down")
        print(traceback.format_exc())

threadParams = {'height': 0, 'lastHash': '', 'socket': None, 'exit': False}
minerThread = threading.Thread(target=miner, args=(threadParams,))

def resetMiner():
    try:
        global minerThread
        threadParams['exit'] = True
        try:
            minerThread.join()
        except RuntimeError as e:
            pass
        threadParams['exit'] = False
        threadParams['height'] = blockchain.height
        threadParams['lastHash'] = blockchain.chain[blockchain.height-1]['hash']
        print('Start the miner')
        minerThread = threading.Thread(target=miner, args=(threadParams,))
        minerThread.start()
    except Exception as e:
        print(e)
        print('Cant reset miner')
        print(traceback.format_exc())

def getPeersTimeout():
    result = []
    for timeout in peersTimeout:
        result.append(max(0.0001,timeout-time.time()))
    return result

def handlePeersTimeout():
    i = 0
    while True:
        if i >= len(peersTimeout):
            break
        if time.time() >= peersTimeout[i]:
            peersList.pop(i)
            peersTimeout.pop(i)
            i-=1
        i+=1

class BlockChain():
    def __init__(self) -> None:
        self.chain = [None]*MAX_LENGTH
        self.height = 0
    
    def checkValidBlock(self, block):
        try:
            validBlock = True
            if block['type'] != 'GET_BLOCK_REPLY':
                #print('Type is not get block reply')
                validBlock = False
            hash = block['hash']
            if hash[-1 * DIFFICULTY:] != '0' * DIFFICULTY:
                #print("Block was not difficult enough: {}".format(hash))
                validBlock = False
            messages = block['messages']
            if len(messages) > 10 or not isinstance(messages,list):
                #print('Len is larger than 10 or the messages are not in list')
                validBlock = False
            if not isinstance(block['height'], int) or block['height'] > MAX_LENGTH-1:
                validBlock = False
                #print("height is not integer")
            for message in messages:
                if len(message) > 20:
                    #print('Message len is longer than 20')
                    validBlock = False
                    break
            if len(block['nonce']) > 40:
                #print('Nonce is longer than 40: ' + block['nonce'])
                validBlock = False
                
            if not isinstance(block['minedBy'], str):
                validBlock = False
                #print('Mined by is not a string')
                
            if not isinstance(block['timestamp'], int):
                validBlock = False
                #print('time is not an int')
            
        except KeyError as e:
            validBlock = False
            print(e)
        except TypeError as e:
            validBlock = False
            print(e)
        return validBlock
            
    def validateTop(self, block):
        lastHash = self.chain[self.height-1]['hash']
        hashBase = hashlib.sha256()
            # get the most recent hash
            # add it to this hash
        hashBase.update(lastHash.encode())            

        # add the miner
        hashBase.update(block['minedBy'].encode())

        # add the messages in order
        for m in block['messages']:                
            hashBase.update(m.encode())

        # the time (different because this is a number, not a string)
        hashBase.update(block['timestamp'].to_bytes(8, 'big'))   

        # add the nonce
        hashBase.update(block['nonce'].encode())   

        # get the pretty hexadecimal
        hash = hashBase.hexdigest()
        
        return hash == block['hash']
    
    def validate(self):
        valid = True
        for i in range(self.height):
            if valid != True:
                break
            
            hashBase = hashlib.sha256()
            if i != 0:
                # get the most recent hash
                # add it to this hash
                hashBase.update(lastHash.encode())            

            # add the miner
            hashBase.update(self.chain[i]['minedBy'].encode())

            # add the messages in order
            for m in self.chain[i]['messages']:                
                hashBase.update(m.encode())

            # the time (different because this is a number, not a string)
            hashBase.update(self.chain[i]['timestamp'].to_bytes(8, 'big'))   

            # add the nonce
            hashBase.update(self.chain[i]['nonce'].encode())   

            # get the pretty hexadecimal
            hash = hashBase.hexdigest()   
            if hash != self.chain[i]['hash']:
                self.chain.pop(i)
                valid = False
            lastHash = hash
        return valid
    
    def addBlock(self, block):
        validBlock = True
        try:
            validBlock = self.checkValidBlock(block)
            if validBlock:
                self.chain[block['height']] = block
            else:
                #print("Failed to add")
                pass
        except KeyError as e:
            print(e)
    
    def missingBlock(self):
        miss = []
        for i in range(self.height):
            try:
                if self.chain[i] == None:
                    miss.append(i)
            except IndexError as e:
                print(str(e)+' the current height is '+str(self.height))
        return miss
    
    def getBlock(self, index):
        try:
            result = self.chain[index]
        except IndexError:
            result = None
            
        return result
    
    def copy(self, other):
        self.chain = copy.deepcopy(other.chain)
        self.height = other.height

blockchain = BlockChain()

def handleAnnounce(consensus, block):
    try:
        print('Get announce')
        block['type'] = 'GET_BLOCK_REPLY'
        if blockchain.checkValidBlock(block):
            print('Current height '+str(blockchain.height))
            if blockchain.validateTop(block):
                print("Newly announced block added")
                blockchain.addBlock(block)
                blockchain.height+=1
                resetMiner()
            elif block['height'] > blockchain.height+1:
                consensus.doConsensus()
            else:
                print("Not validate and wrong height")
        else:
            print("Invalid annouced block")
                
    except KeyError as e:
        print(e)

class Gossip():
    def __init__(self, host, port, peerSoc):
        self.host = host
        self.port = port
        self.peerSoc = peerSoc
        self.TIMEOUT = 60
        self.NAME = 'Nico Nico Nii'
        self.rePingTime = time.time()
        self.gossipIdList = []
        self.gossipListTimeout = []

    def sendGossip(self):
        id =  uuid.uuid4()
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": id.__str__(),
            "name": self.NAME
        }
        self.gossipIdList.append(message['id'])
        self.rePingTime = time.time()+self.TIMEOUT
        
        if len(peersList) > 3:
            repeatList = random.sample(peersList, 3)
        else:
            repeatList = peersList
        print('GOSSIP to ' + str(repeatList))
        for peer in repeatList:
            self.peerSoc.sendto(json.dumps(message).encode(), peer)
        
    def sendReply(self, addr):
        message = {
            "type": "GOSSIP_REPLY",
            "host": self.host,
            "port": self.port,
            "name": self.NAME
        }
        try:
            self.peerSoc.sendto(json.dumps(message).encode(), addr)
        except json.JSONDecodeError as e:
                print(e)
        
    def repeat(self, message):
        if len(peersList) > 3:
            repeatList = random.sample(peersList, 3)
        else:
            repeatList = peersList
            
        for peer in repeatList:
            try:
                self.peerSoc.sendto(json.dumps(message).encode(), peer)
            except json.JSONDecodeError as e:
                print(e)
                
    def handleGossip(self, message):
        try:
            if message['type'] == 'GOSSIP':
                self.sendReply((message['host'], message['port']))
                if message['id'] not in self.gossipIdList:
                    self.gossipIdList.append(message['id'])
                    self.repeat(message)
            elif message['type'] == 'GOSSIP_REPLY':
                peer = (message['host'], message['port'])
                if peer not in peersList and peer != myself:
                    peersList.append(peer)
                    peersTimeout.append(time.time()+self.TIMEOUT)
                elif peer != myself and peer != WELL_KNOWN:
                    peersTimeout[peersList.index(peer)] = time.time()+self.TIMEOUT
        except KeyError as e:
            print(e)
            
    def nextPing(self):
        result = []
        result.append(max(0.0001, self.rePingTime-time.time()))
        return result

    def rePing(self):
        if time.time() >= self.rePingTime:
            self.sendGossip()

class Consensus():
    def __init__(self, peerSoc) -> None:
        self.peerSoc = peerSoc
        self.RE_CONSENSUS_TIME = 500
        self.CONSENSUS_TIMEOUT = 5
        self.GETBLOCK_TIMEOUT = 3
        self.MOVE_CHAIN_TIMEOUT = 500
        self.reConsensusTime = time.time() + self.CONSENSUS_TIMEOUT
        self.consensusTime = time.time() + NO_TIMEOUT
        self.getBlockTime = time.time() + NO_TIMEOUT
        self.moveChainTime = time.time() + NO_TIMEOUT
        self.doingConsensus = False
        self.statList = []
        self.agreedPeersList = []
        self.tempChain = BlockChain()
    
    def doConsensus(self):
        if not self.doingConsensus:
            print('Start doing consensus')
            self.statList = []
            self.agreedPeersList = []
            self.tempChain = BlockChain()
            self.doingConsensus = True
            message = {
                "type":"STATS"
            }
            try:
                print('Peer list '+str(peersList))
                for peer in peersList:
                    self.peerSoc.sendto(json.dumps(message).encode(), peer)
                self.consensusTime = time.time() + self.CONSENSUS_TIMEOUT
                self.reConsensusTime = time.time() + self.RE_CONSENSUS_TIME
            except json.JSONDecodeError as e:
                    print(e)
                    
    def handleStat(self, message, addr):
        try:
            if message['type'] == 'STATS':
                reply = {
                    'type' : 'STATS_REPLY',
                    'height' : None,
                    'hash' : None
                }
                if blockchain.height != 0:
                    reply['hash'] = blockchain.chain[blockchain.height-1]['hash']
                    reply['height'] = blockchain.height
                self.peerSoc.sendto(json.dumps(reply).encode(), addr)
            elif message['type'] == 'STATS_REPLY':
                self.handleStatReply(message, addr)
        except KeyError as e:
            print(e)
                
    def handleStatReply(self, message, addr):
        if self.doingConsensus:
            try:
                stat = {
                    'hash' : message['hash'],
                    'height' : message['height']
                }
                if not isinstance(stat['height'], int):
                    raise TypeError
                repeat = stat in self.statList 
                if stat['height'] < 6000 and stat['hash'][-1 * DIFFICULTY:] == '0' * DIFFICULTY and not repeat:
                    self.statList.append(stat)
                    self.agreedPeersList.append([addr])
                elif repeat:
                    self.agreedPeersList[self.statList.index(stat)].append(addr)
                
            except KeyError as e:
                print(e)
            except TypeError as e:
                print(e)
            
    def handleBlockRequest(self, message, addr):
        try:
            reply = {
                'type': 'GET_BLOCK_REPLY',
                'hash': None,
                'height': None,
                'messages': None,
                'minedBy': None,
                'nonce': None,
                'timestamp': time.time(),
            }
            if blockchain.height > message['height']:
                reply = blockchain.chain[message['height']]
            self.peerSoc.sendto(json.dumps(reply).encode(), addr)
        
        except KeyError as e:
            print(e)
        except TypeError as e:
            print(e)
            
    def requestBlock(self):
        print('Requesting blocks from peers')
        message = {   
            "type": "GET_BLOCK",
            "height": 0
        }
        self.tempChain.height = self.statList[0]['height']
        missing = self.tempChain.missingBlock()
        print('Still missing '+str(len(missing))+' blocks')
        if (len(missing))<100:
            print(missing)
        peers =  self.statList[0]['peers']
        numPeers = len(peers)
        count = random.randint(0, numPeers)
        for i in range(50):
            for j in range(len(missing)):
                message['height'] = missing[j]
                self.peerSoc.sendto(json.dumps(message).encode(), peers[count%numPeers])
                count+=1
                
        if len(missing) == 0:
            self.getBlockTime = time.time()
        else:
            self.getBlockTime = time.time() + self.GETBLOCK_TIMEOUT
            
    def handleBlockReply(self, message):
        if self.doingConsensus:
            self.tempChain.addBlock(message)
            missing = self.tempChain.missingBlock()
            if len(missing) == 0:
                valid = self.tempChain.validate()
                if valid:
                    self.getBlockTime = time.time()
                else:
                    print('Invalid chain keep trying')
                    self.requestBlock()
                    
    def handleGetBlockTimeout(self):
        if time.time() >= self.getBlockTime:
            print('Hit timeout for getting blocks')
            missing = self.tempChain.missingBlock()
            if len(missing) != 0 and time.time() < self.moveChainTime:
                self.requestBlock()
            elif time.time() >= self.moveChainTime or not self.tempChain.validate:
                print('Getting second best chain')
                self.statList.pop(0)
                self.tempChain = BlockChain()
                #if the only accepted chain is invalid, something is wrong, do consensus again from start
                if len(self.statList) > 0:
                    self.requestBlock()
                    self.moveChainTime = time.time() + self.MOVE_CHAIN_TIMEOUT
                else:
                    self.doingConsensus = False
                    self.doConsensus()
            else:
                print('Achieve a whole valid chain')
                self.doingConsensus = False
                oldHeight  = blockchain.height
                blockchain.copy(self.tempChain)
                if (oldHeight < blockchain.height):
                    resetMiner()
                self.getBlockTime = time.time() + NO_TIMEOUT
                self.reConsensusTime = time.time() + self.RE_CONSENSUS_TIME
                self.moveChainTime = time.time() + NO_TIMEOUT
                
    def handleConsensusTimeout(self):
        if time.time() >= self.consensusTime:
            print('Hit consensus timeout')
            if len(self.statList)!=0:
                for i in range(len(self.statList)):
                    self.statList[i]['peers'] = self.agreedPeersList[i]
                    self.statList[i]['count'] = len(self.agreedPeersList[i])

                self.statList.sort(key = lambda x: (x['height'], x['count']), reverse=True)
                if blockchain.height != 0:
                    self.statList.insert(0, self.statList[0])
                print("Current statlist "+str(self.statList))
                print('Consensus STAT done')
                
                self.tempChain.copy(blockchain)
                self.requestBlock()
                self.moveChainTime = time.time() + self.MOVE_CHAIN_TIMEOUT
                self.consensusTime = time.time() + NO_TIMEOUT
            else:
                print("Do request Stat again")
                self.doingConsensus = False
                self.doConsensus()
    
    def handleReConsensusTimeout(self):
        if time.time() >= self.reConsensusTime:
            self.doConsensus()
            self.reConsensusTime = time.time() + self.RE_CONSENSUS_TIME
            
    def getTimeout(self):
        result = []
        result.append(max(0.0001, self.reConsensusTime-time.time()))
        result.append(max(0.0001, self.consensusTime-time.time()))
        result.append(max(0.0001, self.getBlockTime-time.time()))
        return result
            
def createSocketAndRun(port):
    global threadParams
    #create socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as peerSocket:
        threadParams['socket'] = peerSocket
        try:
            peerSocket.setblocking(0)
            host = socket.gethostname()
            IPAddr = socket.gethostbyname(host)
            
            peerSocket.bind((IPAddr, port))
            print('Peer host at ' + IPAddr + ' ' + str(port))
            
            global myself
            myself = (IPAddr, port)
            
            gossip = Gossip(IPAddr, port, peerSocket)
            consensus = Consensus(peerSocket)
            #gossip to well known host
            gossip.sendGossip()
            
            socketList=[peerSocket]
            while True:
                try:
                    timeout = min(gossip.nextPing()+getPeersTimeout()+consensus.getTimeout())
                    (readable, writable, erro) = select.select(
                        socketList,
                        [],
                        [],
                        timeout
                    )
                    for sock in readable:
                        data, addr = sock.recvfrom(1024)
                        data = json.loads(data.decode('utf-8'))
                        try:
                            messageType = data['type']
                            
                            if 'GOSSIP' in messageType:
                                gossip.handleGossip(data)
                                
                            elif 'STATS' in messageType:
                                consensus.handleStat(data, addr)
                                
                            elif 'CONSENSUS' in messageType:
                                print('Receive CONSENSUS REQUEST')
                                consensus.doConsensus()
                                
                            elif 'GET_BLOCK_REPLY' in messageType:
                                consensus.handleBlockReply(data)
                                
                            elif 'GET_BLOCK' in messageType:
                                consensus.handleBlockRequest(data, addr)
                                
                            elif 'ANNOUNCE' in messageType:
                                handleAnnounce(consensus, data)
                        except TypeError as e:
                            pass
                    gossip.rePing()
                    handlePeersTimeout()
                    consensus.handleConsensusTimeout()
                    consensus.handleReConsensusTimeout()
                    consensus.handleGetBlockTimeout()
                except json.JSONDecodeError as e:
                    pass
        except KeyError as e:
            pass
        except ValueError as e:
            pass

def main():
    try:
        if len(sys.argv) != 2:
            raise SystemError('Wrong argument')
        
        port = int(sys.argv[1])
        while True:
            try:
                createSocketAndRun(port)
            except BlockingIOError as e:
                print(e)
                print(traceback.format_exc())
            except socket.error as e:
                print(e)
                print(traceback.format_exc())
            except Exception as e:
                print(e)
                print('Something is wrong while running, restart the peer')
                print(traceback.format_exc())
                pass
                
    except SystemError as e:
        print(e)
        print(traceback.format_exc())
    except ValueError as e:
        print(e)
        print(traceback.format_exc())
  
main()       