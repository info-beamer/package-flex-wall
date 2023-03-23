#
# Part of info-beamer hosted. You can find the latest version
# of this file at:
#
# https://github.com/info-beamer/package-sdk
#
# Copyright (c) 2021 Florian Wesch <fw@info-beamer.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the
#     distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

VERSION = "1.0"

import sys, threading, heapq, os, itertools
from binascii import hexlify
from collections import namedtuple
from p2plib import PeerGroup, monotonic_time

def log(msg, name='p2pevt.py'):
    print >>sys.stderr, "[{}] {}".format(name, msg)

Event = namedtuple("Event", "timestamp id data")

def chunked_or_empty(lst, n):
    if not lst:
        yield []
    for i in xrange(0, len(lst), n):
        yield lst[i:i + n]

class EventQueue(object):
    def __init__(self):
        self._queue = []
        self._ids = set()

    def add(self, event):
        if event.id in self._ids:
            return False
        heapq.heappush(self._queue, event)
        self._ids.add(event.id)
        return True

    def has_event(self, event_id):
        return event_id in self._ids

    def discard_older(self, threshold_timestamp):
        while self._queue:
            oldest_event = self._queue[0]
            if oldest_event.timestamp >= threshold_timestamp:
                break
            heapq.heappop(self._queue)
            self._ids.remove(oldest_event.id)

    def pop(self):
        if not self._queue:
            return
        oldest_event = self._queue[0]
        heapq.heappop(self._queue)
        self._ids.remove(oldest_event.id)

    def next(self):
        if not self._queue:
            return None
        return self._queue[0]

class OrderedEventGroup(PeerGroup):
    def setup_peer(self):
        self._leader_running = False

        # on leader
        self._send_interval = 0.1
        self._max_events_per_broadcast = 4
        self._leader_events = []
        self._leader_events_lock = threading.Lock()
        self._leader_has_event = threading.Condition(self._leader_events_lock)
        self._leader_id = hexlify(os.urandom(8))
        self._leader_event_seq = itertools.count()

        # on peers
        self._events = EventQueue()
        self._handled_events = EventQueue()
        self._events_lock = threading.Lock()
        self._has_event = threading.Condition(self._events_lock)
        self._last_leader_id = None
        self._leader_time_offset = None

    def _reset_peer(self):
        self._events = EventQueue()
        self._handled_events = EventQueue()
        self._leader_time_offset = None

    def _leader_offset(self, leader_time, our_time, ping):
        true_leader_time = leader_time + ping
        time_offset = true_leader_time - our_time
        if self._leader_time_offset is None:
            self._leader_time_offset = time_offset
        else:
            self._leader_time_offset = 0.99 * self._leader_time_offset + 0.01 * time_offset
        return self._leader_time_offset

    def leader_thread(self):
        while self._leader_running:
            with self._leader_events_lock:
                self._leader_has_event.wait(timeout=self._send_interval)
                now = self.time()
                while self._leader_events and self._leader_events[0].timestamp < now - 1:
                    self._leader_events.pop(0)
                # Find slice of packets to sync to peers
                packet_events, idx = [], 0
                for idx, event in enumerate(self._leader_events):
                    if event.timestamp > now + 1:
                        packet_events = self._leader_events[:idx]
                else:
                    packet_events = self._leader_events

            for events_chunk in chunked_or_empty(packet_events, self._max_events_per_broadcast):
                self.broadcast_to_all(
                    lid = self._leader_id,
                    ts = self.time(),
                    e = events_chunk,
                )

    def on_leader_message(self, message, peer_info):
        # import json; print >>sys.stderr, json.dumps(message), peer_info
        leader_id = (peer_info.device_id, message['lid'])
        with self._events_lock:
            now = self.time()
            if leader_id != self._last_leader_id:
                log("new leader detected. wiping queue")
                self._reset_peer()
                self._last_leader_id = leader_id
            leader_offset = self._leader_offset(message['ts'], now, peer_info.ping)
            # log('leader offset is %f' % (leader_offset,))
            new_events = False
            for event in message['e']:
                event = Event(*event)
                if self._handled_events.has_event(event.id):
                    continue
                new_events = new_events or self._events.add(Event(
                    timestamp = event.timestamp - leader_offset, 
                    id = event.id,
                    data = event.data,
                ))
            if new_events:
                self._has_event.notify()

    def time(self):
        return monotonic_time()

    def send_event(self, timestamp, event):
        if not self._leader_running:
            return
        with self._leader_events_lock:
            self._leader_events.append(Event(timestamp, next(self._leader_event_seq), event))
            self._leader_events.sort()
            self._leader_has_event.notify()

    def events(self):
        wait = 10
        while 1:
            with self._events_lock:
                self._has_event.wait(wait)
                while 1:
                    next_event = self._events.next()
                    if not next_event:
                        wait = 10
                        break
                    now = self.time()
                    wait = next_event.timestamp - now
                    if wait > 0:
                        break
                    try:
                        yield -wait, next_event.data
                    finally:
                        self._handled_events.add(next_event)
                        self._handled_events.discard_older(now - 3)
                        self._events.pop()

    def promote_leader(self, peer_info):
        log("Now a leader: %r" % (peer_info,))
        self._leader_running = True
        self._leader_thread = threading.Thread(target=self.leader_thread)
        self._leader_thread.daemon = True
        self._leader_thread.start()

    def demote_leader(self):
        log("No longer a leader")
        self._leader_running = False
        self._leader_thread.join()


class GroupRPC(OrderedEventGroup):
    def setup_peer(self):
        super(GroupRPC, self).setup_peer()

        from hosted import node
        self._lua = node.rpc()

        thread = threading.Thread(target=self.lua_forwarder)
        thread.daemon = True
        thread.start()

    def lua_forwarder(self):
        for delay, event in self.events():
            log("event delivery time offset is %f" % (delay,))
            getattr(self._lua, event['fn'])(*event['args'])

    def call(self, offset, fn, *args):
        if offset < 0.1:
            log('calls with offset < 0.1 are usually not delivered in time')
        self.send_event(self.time() + offset, dict(
            fn = fn,
            args = args,
        ))
