# P2P Blockchain

COMP 3010 - Distributed Computing final project. All students have to create and host a server on the school network and host a blockchain on the network. Communication between peers is done using UDP. Consensus is proof-of-work.


## Communication Protocol

Joining the network is done with gossiping through a well-known host. This host will forward the GOSSIP message to all known peers. Gossiping will be used as a ‘keepalive’ ping - re-GOSSIP every 30s to ensure you are not assumed offline. If you have not been heard from in a minute, you will be dropped. The message will be repeated to 3 peers that your peer is tracking, who will then also gossip.

Upon receiving a GOSSIP message, you should reply using GOSSIP-REPLY to the originating sender - to the host and port in the message.

Upon joining - do a consensus to find the longest chain. Request STATS from everyone. Choose the most agreed-upon chain (same height/hash combination).

Once you have the chain, you must verify it. There are cryptographic properties that must be respected by blockchains.

- The hash from the previous block (unless this is the genesis block, in which case this is skipped)
- The name of the miner in minedBy
- The messages in the order provided
- The time the block was mined
- The nonce

Your peer must fulfill the following protocol.

### GOSSIP
Announce your peer to the network. Gossip to one well-known host. Reply to any GOSSIP messages you receive, but do not repeat a gossip message (as known by the ID) that has already been repeated.

```
{
   "type": "GOSSIP",
   "host": "192.168.0.27",
   "port": 8999,
   "id": "5b29f4c7-40ac-4522-b217-e90e9587c1e5",
   "name": "Some name here!"
}

{
   "type": "GOSSIP_REPLY",
   "host": "192.168.0.28",
   "port": 8001,
   "name": "I have a name, too"
}
```
### GET_BLOCK
Requests a single block from a peer. The peer returns the contents of that block.

```
{
   "type": "GET_BLOCK",
   "height": 0
}
Which replies with a GET_BLOCK_REPLY:

{   'type': 'GET_BLOCK_REPLY'
    'hash': '2483cc5c0d2fdbeeba3c942bde825270f345b2e9cd28f22d12ba347300000000',
    'height': 0,
    'messages': [   '3010 rocks',
                    'Warning:',
                    'Procrastinators',
                    'will be sent back',
                    'in time to start',
                    'early.'],
    'minedBy': 'Prof!',
    'nonce': '7965175207940',
    'timestamp': 1699293749,
   }
```

If given GET_BLOCK for an invalid height, return with GET_BLOCK_REPLY with null/None height, message, nonce, and minedBy.

### Announcing new block on the chain

Add a new block to the chain. You must handle receiving these messages appropriately. Verify the hash before adding it to your chain.

```
{
   "type": "ANNOUNCE",
   "height": 3,
   "minedBy": "Rob!",
   "nonce": "27104978",
   "messages": ["test123"],
   "hash": "75fb3c14f11295fd22a42453834bc393872a78e4df1efa3da57a140d96000000"
}
```

There is no reply.

### Get statistics

Get some statistics about the chain in this host.

```
{
   "type":"STATS"
}
```

Reply with the height of your chain and the hash of the block at the maximum height

```
{
   "type": "STATS_REPLY",
   "height": 2,
   "hash": "519507660a0dd9d947e18b863a4a54b90eb53c82dde387e1f5e9b48f3d000000" 
}
```

### Limitations

Ideally, you would not add a block with a word that you have not seen announced. For our needs, we will ignore this, accepting any mined block. In a real blockchain, this would be a SERIOUS issue.

## Deployment

To start the peer

Well-known host and Difficulty is hard coded at the top of the file

```
python3 peer.py host
```

It can take up to 500s to synchronize depending on how many good peers and how fast they respond. After 500s, it will timeout and move to the second chain.

The peers will fully restart if it cannot synchronize after going over every possible chains

After finishing synchronizing, receive the message

```
Hit timeout for getting blocks
Achieve a whole valid chain
```

## Authors

  - **Me**

## Acknowledgments

The project description and idea was taken from my beloved Distributed Computing instructor Robert Guderian
