#
# Part of info-beamer hosted. You can find the latest version
# of this file at:
# 
# https://github.com/info-beamer/package-sdk
#
# Copyright (c) 2014,2015,2016,2017,2018 Florian Wesch <fw@info-beamer.com>
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

VERSION = "1.1"

import os
import sys
import json
import socket
import time
import pyinotify
import thread
import threading
import requests
from tempfile import NamedTemporaryFile

types = {}

def init_types():
    def type(fn):
        types[fn.__name__] = fn
        return fn

    @type
    def color(value):
        return value

    @type
    def string(value):
        return value

    @type
    def text(value):
        return value

    @type
    def section(value):
        return value

    @type
    def boolean(value):
        return value

    @type
    def select(value):
        return value

    @type
    def duration(value):
        return value

    @type
    def integer(value):
        return value

    @type
    def float(value):
        return value

    @type
    def font(value):
        return value

    @type
    def device(value):
        return value

    @type
    def resource(value):
        return value

    @type
    def json(value):
        return value

    @type
    def custom(value):
        return value

    @type
    def date(value):
        return value

init_types()

def log(msg):
    print >>sys.stderr, "[hosted.py] %s" % msg

def abort_service(reason):
    log("restarting service (%s)" % reason)
    try:
        thread.interrupt_main()
    except:
        pass
    time.sleep(2)
    os.kill(os.getpid(), 2)
    time.sleep(2)
    os.kill(os.getpid(), 15)
    time.sleep(2)
    os.kill(os.getpid(), 9)
    time.sleep(100)

class Configuration(object):
    def __init__(self):
        self._restart = False
        self._options = []
        self._config = {}
        self._parsed = {}
        self.parse_node_json(do_update=False)
        self.parse_config_json()

    def restart_on_update(self):
        log("going to restart when config is updated")
        self._restart = True

    def parse_node_json(self, do_update=True):
        with open("node.json") as f:
            self._options = json.load(f)['options']
        if do_update:
            self.update_config()

    def parse_config_json(self, do_update=True):
        with open("config.json") as f:
            self._config = json.load(f)
        if do_update:
            self.update_config()

    def update_config(self):
        if self._restart:
            return abort_service("restart_on_update set")

        def parse_recursive(options, config, target):
            # print 'parsing', config
            for option in options:
                if not 'name' in option:
                    continue
                if option['type'] == 'list':
                    items = []
                    for item in config[option['name']]:
                        parsed = {}
                        parse_recursive(option['items'], item, parsed)
                        items.append(parsed)
                    target[option['name']] = items
                    continue
                target[option['name']] = types[option['type']](config[option['name']])

        parsed = {}
        parse_recursive(self._options, self._config, parsed)
        log("updated config")
        self._parsed = parsed

    @property
    def raw(self):
        return self._config

    @property
    def metadata(self):
        return self._config['__metadata']

    def __getitem__(self, key):
        return self._parsed[key]

    def __getattr__(self, key):
        return self._parsed[key]

def setup_inotify(configuration):
    class EventHandler(pyinotify.ProcessEvent):
        def process_default(self, event):
            basename = os.path.basename(event.pathname)
            if basename == 'node.json':
                log("node.json changed")
                configuration.parse_node_json()
            elif basename == 'config.json':
                log("config.json changed!")
                configuration.parse_config_json()
            elif basename.endswith('.py'):
                abort_service("python file changed")

    wm = pyinotify.WatchManager()

    notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
    notifier.daemon = True
    notifier.start()

    wm.add_watch('.', pyinotify.IN_MOVED_TO)

class Node(object):
    def __init__(self, node):
        self._node = node
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_raw(self, raw):
        log("sending %r" % (raw,))
        self._sock.sendto(raw, ('127.0.0.1', 4444))

    def send(self, data):
        self.send_raw(self._node + data)

    @property
    def is_top_level(self):
        return self._node == "root"

    @property
    def path(self):
        return self._node

    def write_json(self, filename, data):
        f = NamedTemporaryFile(prefix='hosted-py-tmp', dir=os.getcwd())
        try:
            f.write(json.dumps(
                data,
                ensure_ascii=False,
                separators=(',',':'),
            ).encode('utf8'))
        except:
            traceback.print_exc()
            raise
        else:
            f.delete = False
            f.close()
            os.rename(f.name, filename)

    class Sender(object):
        def __init__(self, node, path):
            self._node = node
            self._path = path

        def __call__(self, data):
            if isinstance(data, (dict, list)):
                raw = "%s:%s" % (self._path, json.dumps(
                    data,
                    ensure_ascii=False,
                    separators=(',',':'),
                ).encode('utf8'))
            else:
                raw = "%s:%s" % (self._path, data)
            self._node.send_raw(raw)

    def __getitem__(self, path):
        return self.Sender(self, self._node + path)

    def __call__(self, data):
        return self.Sender(self, self._node)(data)

    def scratch_cached(self, filename, generator):
        cached = os.path.join(os.environ['SCRATCH'], filename)

        if not os.path.exists(cached):
            f = NamedTemporaryFile(prefix='scratch-cached-tmp', dir=os.environ['SCRATCH'])
            try:
                generator(f)
            except:
                raise
            else:
                f.delete = False
                f.close()
                os.rename(f.name, cached)

        if os.path.exists(filename):
            try:
                os.unlink(filename)
            except:
                pass
        os.symlink(cached, filename)

class APIError(Exception):
    pass

class APIProxy(object):
    def __init__(self, apis, api_name):
        self._apis = apis
        self._api_name = api_name

    @property
    def url(self):
        index = self._apis.get_api_index()
        if not self._api_name in index:
            raise APIError("api '%s' not available" % (self._api_name,))
        return index[self._api_name]['url']

    def unwrap(self, r):
        r.raise_for_status()
        resp = r.json()
        if not resp['ok']:
            raise APIError(u"api call failed: %s" % (
                resp.get('error', '<unknown error>'),
            ))
        return resp.get(self._api_name)

    def add_defaults(self, kwargs):
        if not 'timeout' in kwargs:
            kwargs['timeout'] = 10

    def get(self, **kwargs):
        self.add_defaults(kwargs)
        try:
            return self.unwrap(self._apis.session.get(
                url = self.url,
                **kwargs
            ))
        except APIError:
            raise
        except Exception as err:
            raise APIError(err)

    def post(self, **kwargs):
        self.add_defaults(kwargs)
        try:
            return self.unwrap(self._apis.session.post(
                url = self.url(),
                **kwargs
            ))
        except APIError:
            raise
        except Exception as err:
            raise APIError(err)

class APIs(object):
    def __init__(self, config):
        self._config = config
        self._index = None
        self._valid_until = 0
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'hosted.py version/%s' % (VERSION,)
        })

    def update_apis(self):
        log("fetching api index")
        r = self._session.get(
            url = self._config.metadata['api'],
            timeout = 5,
        )
        r.raise_for_status()
        resp = r.json()
        if not resp['ok']:
            raise APIError("cannot retrieve api index")
        self._index = resp['apis']
        self._valid_until = resp['valid_until'] - 300

    def get_api_index(self):
        with self._lock:
            now = time.time()
            if now > self._valid_until:
                self.update_apis()
            return self._index

    @property
    def session(self):
        return self._session

    def list(self):
        try:
            index = self.get_api_index()
            return sorted(index.keys())
        except Exception as err:
            raise APIError(err)

    def __getitem__(self, api_name):
        return APIProxy(self, api_name)

    def __getattr__(self, api_name):
        return APIProxy(self, api_name)


class Device(object):
    def __init__(self):
        self._socket = None

    def ensure_connected(self):
        if self._socket:
            return True
        try:
            log("establishing upstream connection")
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(os.getenv('SYNCER_SOCKET', "/tmp/syncer"))
            return True
        except Exception as err:
            log("cannot connect to upstream socket: %s" % (err,))
            return False

    def send_raw(self, raw):
        try:
            if self.ensure_connected():
                self._socket.send(raw + '\n')
        except Exception as err:
            log("cannot send to upstream: %s" % (err,))
            if self._socket:
                self._socket.close()
            self._socket = None

    def send_upstream(self, **data):
        self.send_raw(json.dumps(data))

    def turn_screen_off(self):
        self.send_raw("tv off")

    def turn_screen_on(self):
        self.send_raw("tv on")

    def screen(self, on=True):
        if on:
            self.turn_screen_on()
        else:
            self.turn_screen_off()

    def reboot(self):
        self.send_raw("reboot")

    def restart_infobeamer(self):
        self.send_raw("infobeamer restart")

    def verify_cache(self):
        self.send_raw("syncer verify_cache")

if __name__ == "__main__":
    device = Device()
    while 1:
        try:
            command = raw_input("syncer> ")
            device.send_raw(command)
        except (KeyboardInterrupt, EOFError):
            break
        except:
            import traceback
            traceback.print_exc()
else:
    log("starting version %s" % (VERSION,))
    node = NODE = Node(os.environ['NODE'])
    device = DEVICE = Device()
    config = CONFIG = Configuration()
    api = API = APIs(CONFIG)
    setup_inotify(CONFIG)
    log("ready to go!")
