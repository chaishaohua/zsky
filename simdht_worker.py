#!/usr/bin/env python
# encoding: utf-8
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
"""
磁力搜索meta信息入库程序
xiaoxia@xiaoxia.org  2015.6 Forked CreateChen's Project: https://github.com/CreateChen/simDownloader
2017.7 我本戏子修复bug
使用说明：
pip install pymysql
pip install DBUtils
"""

import hashlib
import os
import SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
import time
import datetime
import traceback
import sys
import json
import socket
import threading
from hashlib import sha1
from random import randint
from struct import unpack
from socket import inet_ntoa
from threading import Timer, Thread
from time import sleep
from collections import deque
from Queue import Queue
#import pygeoip
import pymysql

try:
    raise
    import libtorrent as lt
    import ltMetadata
except:
    lt = None
    print sys.exc_info()[1]

import metautils
import simMetadata
from bencode import bencode, bdecode
from metadata import save_metadata

DB_NAME = 'zsky'
DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASS = ''
BOOTSTRAP_NODES = (
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881),
    ('tracker.pirateparty.gr',6969),
    ('tracker.coppersurfer.tk',6969),
    ('tracker.leechers-paradise.org',6969),
    ('9.rarbg.com',2710),
    ('p4p.arenabg.com',1337),
    ('tracker.opentrackr.org',1337),
    ('public.popcorn-tracker.org',6969),
    ('tracker.internetwarriors.net',1337),
    ('tracker1.wasabii.com.tw',6969),
    ('tracker.zer0day.to',1337),
    ('tracker.mg64.net',6969),
    ('peerfect.org',6969),
    ('open.facedatabg.net',6969),
    ('mgtracker.org',6969),
    ('ipv4.tracker.harry.lu',80),
    ('tracker.xku.tv',6969),
    ('tracker.vanitycore.co',6969),
    ('tracker.swateam.org.uk',2710),
    ('packages.crunchbangplusplus.org',6969),
    ('zephir.monocul.us',6969),
    ('ulfbrueggemann.no-ip.org',6969),
    ('trackerxyz.tk',1337),
    ('tracker2.wasabii.com.tw',6969),
    ('tracker2.christianbro.pw',6969),
    ('tracker.tvunderground.org.ru',3218),
    ('tracker.torrent.eu.org',451),
    ('tracker.tiny-vps.com',6969),
    ('tracker.kuroy.me',5944),
    ('tracker.kamigami.org',2710),
    ('tracker.halfchub.club',6969),
    ('tracker.grepler.com',6969),
    ('tracker.filetracker.pl',8089),
    ('tracker.files.fm',6969),
    ('tracker.edoardocolombo.eu',6969),
    ('tracker.doko.moe',6969),
    ('tracker.dler.org',6969),
    ('tracker.desu.sh',6969),
    ('tracker.cypherpunks.ru',6969),
    ('tracker.cyberia.is',6969),
    ('tracker.christianbro.pw',6969),
    ('tracker.bluefrog.pw',2710),
    ('tracker.acg.gg',2710),
    ('tr.cili001.com',6666),
    ('thetracker.org',80),
    ('retracker.lanta-net.ru',2710),
    ('inferno.demonoid.pw',3418),
    ('explodie.org',6969),
    ('bt.xxx-tracker.com',2710),
    ('86.19.29.160',6969),
    ('208.67.16.113',8000),
    ('z.crazyhd.com',2710),
    ('tracker1.xku.tv',6969),
    ('tracker.skyts.net',6969),
    ('tracker.safe.moe',6969),
    ('tracker.piratepublic.com',1337),
    ('tracker.justseed.it',1337),
    ('sandrotracker.biz',1337),
    ('oscar.reyesleon.xyz',6969),
    ('open.stealth.si',80),
    ('allesanddro.de',1337),
)
TID_LENGTH = 2
RE_JOIN_DHT_INTERVAL = 3
TOKEN_LENGTH = 2

MAX_QUEUE_LT = 10000
MAX_QUEUE_PT = 10000

#geoip = pygeoip.GeoIP('GeoIP.dat')


#def is_ip_allowed(ip):
#    return geoip.country_code_by_addr(ip) not in ('CN','TW','HK')

def entropy(length):
    return "".join(chr(randint(0, 255)) for _ in xrange(length))


def random_id():
    h = sha1()
    h.update(entropy(20))
    return h.digest()


def decode_nodes(nodes):
    n = []
    length = len(nodes)
    if (length % 26) != 0:
        return n

    for i in range(0, length, 26):
        nid = nodes[i:i+20]
        ip = inet_ntoa(nodes[i+20:i+24])
        port = unpack("!H", nodes[i+24:i+26])[0]
        n.append((nid, ip, port))

    return n


def timer(t, f):
    Timer(t, f).start()


def get_neighbor(target, nid, end=10):
    return target[:end]+nid[end:]


class KNode(object):

    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port


class DHTClient(Thread):

    def __init__(self, max_node_qsize):
        Thread.__init__(self)
        self.setDaemon(True)
        self.max_node_qsize = max_node_qsize
        self.nid = random_id()
        self.nodes = deque(maxlen=max_node_qsize)

    def send_krpc(self, msg, address):
        try:
            self.ufd.sendto(bencode(msg), address)
        except Exception:
            pass

    def send_find_node(self, address, nid=None):
        nid = get_neighbor(nid, self.nid) if nid else self.nid
        tid = entropy(TID_LENGTH)
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {
                "id": nid,
                "target": random_id()
            }
        }
        self.send_krpc(msg, address)

    def join_DHT(self):
        for address in BOOTSTRAP_NODES:
            self.send_find_node(address)

    def re_join_DHT(self):
        if len(self.nodes) == 0:
            self.join_DHT()
        timer(RE_JOIN_DHT_INTERVAL, self.re_join_DHT)

    def auto_send_find_node(self):
        wait = 1.0 / self.max_node_qsize
        while True:
            try:
                node = self.nodes.popleft()
                self.send_find_node((node.ip, node.port), node.nid)
            except IndexError:
                pass
            try:
                sleep(wait)
            except KeyboardInterrupt:
                os._exit(0)

    def process_find_node_response(self, msg, address):
        nodes = decode_nodes(msg["r"]["nodes"])
        for node in nodes:
            (nid, ip, port) = node
            if len(nid) != 20: continue
            if ip == self.bind_ip: continue
            n = KNode(nid, ip, port)
            self.nodes.append(n)


class DHTServer(DHTClient):

    def __init__(self, master, bind_ip, bind_port, max_node_qsize):
        DHTClient.__init__(self, max_node_qsize)

        self.master = master
        self.bind_ip = bind_ip
        self.bind_port = bind_port

        self.process_request_actions = {
            "get_peers": self.on_get_peers_request,
            "announce_peer": self.on_announce_peer_request,
        }

        self.ufd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.ufd.bind((self.bind_ip, self.bind_port))

        timer(RE_JOIN_DHT_INTERVAL, self.re_join_DHT)


    def run(self):
        self.re_join_DHT()
        while True:
            try:
                (data, address) = self.ufd.recvfrom(65536)
                msg = bdecode(data)
                self.on_message(msg, address)
            except Exception:
                pass

    def on_message(self, msg, address):
        try:
            if msg["y"] == "r":
                if msg["r"].has_key("nodes"):
                    self.process_find_node_response(msg, address)
            elif msg["y"] == "q":
                try:
                    self.process_request_actions[msg["q"]](msg, address)
                except KeyError:
                    self.play_dead(msg, address)
        except KeyError:
            pass

    def on_get_peers_request(self, msg, address):
        try:
            infohash = msg["a"]["info_hash"]
            tid = msg["t"]
            nid = msg["a"]["id"]
            token = infohash[:TOKEN_LENGTH]
            msg = {
                "t": tid,
                "y": "r",
                "r": {
                    "id": get_neighbor(infohash, self.nid),
                    "nodes": "",
                    "token": token
                }
            }
            self.master.log_hash(infohash, address)
            self.send_krpc(msg, address)
        except KeyError:
            pass

    def on_announce_peer_request(self, msg, address):
        try:
            infohash = msg["a"]["info_hash"]
            token = msg["a"]["token"]
            nid = msg["a"]["id"]
            tid = msg["t"]

            if infohash[:TOKEN_LENGTH] == token:
                if msg["a"].has_key("implied_port ") and msg["a"]["implied_port "] != 0:
                    port = address[1]
                else:
                    port = msg["a"]["port"]
                self.master.log_announce(infohash, (address[0], port))
        except Exception:
            print 'error'
            pass
        finally:
            self.ok(msg, address)

    def play_dead(self, msg, address):
        try:
            tid = msg["t"]
            msg = {
                "t": tid,
                "y": "e",
                "e": [202, "Server Error"]
            }
            self.send_krpc(msg, address)
        except KeyError:
            pass

    def ok(self, msg, address):
        try:
            tid = msg["t"]
            nid = msg["a"]["id"]
            msg = {
                "t": tid,
                "y": "r",
                "r": {
                    "id": get_neighbor(nid, self.nid)
                }
            }
            self.send_krpc(msg, address)
        except KeyError:
            pass

class Master(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True)
        self.queue = Queue()
        self.metadata_queue = Queue()
        from DBUtils.PooledDB import PooledDB
        self.pool = PooledDB(pymysql,50,host=DB_HOST,user=DB_USER,passwd=DB_PASS,db=DB_NAME,port=3306,charset="utf8mb4") #50为连接池里的最少连接数
        self.dbconn = self.pool.connection() 
        #self.dbconn = mdb.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME, charset='utf8mb4')
        #self.dbconn.autocommit(False)
        self.dbcurr = self.dbconn.cursor()
        self.dbcurr.execute('SET NAMES utf8mb4')
        self.n_reqs = self.n_valid = self.n_new = 0
        self.n_downloading_lt = self.n_downloading_pt = 0
        self.visited = set()

    def got_torrent(self):
        binhash, address, data, dtype, start_time = self.metadata_queue.get()
        if dtype == 'pt':
            self.n_downloading_pt -= 1
        elif dtype == 'lt':
            self.n_downloading_lt -= 1
        if not data:
            return
        self.n_valid += 1

        save_metadata(self.dbcurr, binhash, address, start_time, data)
        self.n_new += 1


    def run(self):
        self.name = threading.currentThread().getName()
        print self.name, 'starting'
        while True:
            while self.metadata_queue.qsize() > 0:
                self.got_torrent()
            address, binhash, dtype = self.queue.get()
            if binhash in self.visited:
                continue
            if len(self.visited) > 100000:
                self.visited = set()
            self.visited.add(binhash)

            self.n_reqs += 1
            info_hash = binhash.encode('hex')

            utcnow = datetime.datetime.utcnow()
            date = (utcnow + datetime.timedelta(hours=8))
            date = datetime.datetime(date.year, date.month, date.day ,date.hour ,date.minute ,date.second)

            # Check if we have this info_hash
            self.dbcurr.execute('SELECT id FROM search_hash WHERE info_hash=%s', (info_hash,))
            y = self.dbcurr.fetchone()
            if y:
                self.n_valid += 1
                # 更新最近发现时间，请求数
                self.dbcurr.execute('UPDATE search_hash SET last_seen=%s, requests=requests+1 WHERE info_hash=%s', (utcnow, info_hash))
            else:
                if dtype == 'pt':
                    t = threading.Thread(target=simMetadata.download_metadata, args=(address, binhash, self.metadata_queue))
                    t.setDaemon(True)
                    t.start()
                    self.n_downloading_pt += 1
                elif dtype == 'lt' and self.n_downloading_lt < MAX_QUEUE_LT:
                    t = threading.Thread(target=ltMetadata.download_metadata, args=(address, binhash, self.metadata_queue))
                    t.setDaemon(True)
                    t.start()
                    self.n_downloading_lt += 1

            if self.n_reqs >= 1000:
                self.dbcurr.execute('INSERT INTO search_statusreport(date,new_hashes,total_requests, valid_requests)  VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE ' +
                    'total_requests=total_requests+%s, valid_requests=valid_requests+%s, new_hashes=new_hashes+%s',
                    (date, self.n_new, self.n_reqs, self.n_valid, self.n_reqs, self.n_valid, self.n_new))
                self.dbconn.commit()
                #print '\n', date, u'总请求数:', self.n_reqs, u'可用数:', self.n_valid, u'新Hash:', self.n_new, u'队列长度:', self.queue.qsize(), 
                #print u'simMetadata下载数:', self.n_downloading_pt, u'ltMetadata下载数:', self.n_downloading_lt, 
                self.n_reqs = self.n_valid = self.n_new = 0

    def log_announce(self, binhash, address=None):
        self.queue.put([address, binhash, 'pt'])

    def log_hash(self, binhash, address=None):
        if not lt:
            return
        #if is_ip_allowed(address[0]):
        #    return
        if self.n_downloading_lt < MAX_QUEUE_LT:
            self.queue.put([address, binhash, 'lt'])


def announce(info_hash, address):
    binhash = info_hash.decode('hex')
    master.log_announce(binhash, address)
    return 'ok'


class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
    pass

def rpc_server():
    rpcserver = ThreadXMLRPCServer(('localhost', 8004), logRequests=False)
    rpcserver.register_function(announce, 'announce')
    print 'Start xmlrpcserver...'
    rpcserver.serve_forever()


if __name__ == "__main__":
    # max_node_qsize越大，占用带宽越大，爬取速度越快
    master = Master()
    master.start()

    rpcthread = threading.Thread(target=rpc_server)
    rpcthread.setDaemon(True)
    rpcthread.start()

    dht = DHTServer(master, "0.0.0.0", 6881, max_node_qsize=200)
    dht.start()
    dht.auto_send_find_node()
