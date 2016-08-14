#!/usr/bin/env python3

# import asyncio
import socket
import struct
# import simplejson
import json
import pprint
from time import sleep

HOST = 'HEOS-Player.rydbrink.local'
PORT = 1255

DISCOVERY_MSG = ('M-SEARCH * HTTP/1.1',
                 'ST: urn:schemas-denon-com:device:ACT-Denon:1',
                 'MX: 3',
                 'MAN: "ssdp:discover"',
                 'HOST: 239.255.255.250:1900', '', '')


class HeosException(Exception):
    def __init__(self, id, message):
        self.id = id
        self.message = message


class Heos(object):

    def __init__(self, host=HOST):
        self._players = None
        self._pid = None
        self._play_state = None
        # create a socket object
        self._connection = None

    def _parse_ssdp(self, data):
        result = {}
        for line in data.decode().rsplit('\r\n'):
            try:
                key, value = line.rsplit(': ')
                result[key.lower()] = value
            except:
                pass
        return result

    def _parse_ssdp_location(self, data):
        import re
        location = self._parse_ssdp(data)['location']
        pprint.pprint(location)
        address = re.search('https?://([^:/]+)[:/].*$', location)
        return address.group(1)

    def discover(self, addr=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        # addr = socket.gethostname(socket.getfqdn())
        if addr:
            sock.bind((addr, 1900))

        # addr = sock.getsockname()[0]
        # sock.close()

        msg = "\r\n".join(DISCOVERY_MSG).encode('ascii')
        sock.sendto(msg, ('239.255.255.250', 1900))

        try:
            data = sock.recv(1024)
            address = self._parse_ssdp_location(data)
        finally:
            sock.close()
            return address

    def connect(self, host=HOST, port=PORT):
        pprint.pprint((host, port))
        self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connection.connect((host, port))

    def send_command(self, command, message=None):
        msg = 'heos://' + command
        if message:
            if 'pid' in message.keys() and message['pid'] is None:
                message['pid'] = self._get_pid()
            msg += '?' + '&'.join("{}={}".format(key, val) for (key, val) in message.items())
        msg += '\r\n'
        pprint.pprint(msg)
        self._connection.send(msg.encode('ascii'))

        return self.recv_reply(command)

    def _parse_message(self, message):
        return dict(elem.split('=') for elem in message.split('&'))

    def parse_command(self, command, data):
        try:
            if command == data['heos']['command']:
                if 'fail' == data['heos']['result']:
                    raise HeosException(data['heos']['message'])
                if 'payload' in data.keys():
                    return data['payload']
                else:
                    return self._parse_message(data['heos']['message'])
        except:
            pass

        return None

    def recv_reply(self, command):
        while True:
            msg = self._connection.recv(1024*1024)
            pprint.pprint(msg)
            # simplejson doesnt need to decode from byte to ascii
            data = json.loads(msg.decode('ascii'))
            reply = self.parse_command(command, data)
            if reply is not None:
                pprint.pprint(reply)
                return reply

    def close(self):
        self._connection.close()
        self._connection = None

    def get_players(self):
        # heos.send_command('system/register_for_change_events?enable=on')
        reply = self.send_command('player/get_players')
        if reply:
            self._pid = reply[0]['pid']
        return self._pid

    def _get_pid(self):
        return self._pid

    def get_player_info(self, pid=None):
        reply = self.send_command('player/get_player_info', {'pid': pid})

    def get_play_state(self, pid=None):
        reply = self.send_command('player/get_play_state', {'pid': pid})
        if reply:
            self._play_state = reply['state']
        return self._play_state

    def get_mute_state(self, pid=None):
        reply = self.send_command('player/get_mute', {'pid': pid})
        if reply:
            self._mute_state = reply['state']
        return self._mute_state

    def get_volume(self, pid=None):
        reply = self.send_command('player/get_volume', {'pid': pid})
        if reply:
            self._volume_level = reply['level']
        return self._volume_level

    def set_volume(self, volume_level, pid=None):
        if volume_level > 100:
            volume_level = 100
        if volume_level < 0:
            volume_level = 0
        reply = self.send_command('player/set_volume', {'pid': pid, 'level': volume_level})
        if reply:
            self._volume_level = reply['level']
        return self._volume_level

    def volume_level_up(self, step=10, pid=None):
        volume = self.get_volume(pid)
        self.set_volume(volume_level + step, pid)

    def volume_level_down(self, step=10, pid=None):
        volume = self.get_volume(pid)
        self.set_volume(volume_level - step, pid)

    def play_url(self, url, in_secs=0, pid=None):
        # volume_old = self.get_volume(pid)
        # secs_to_go = in_secs

        # # drop volume
        # vol = volume_old
        # while vol != 0:
        #     vol = self.get_volume(pid)
        #     sleep(0.2)
        #     secs_to_go -= 0.2
        #     volume_diff = int(vol / secs_to_go)
        #     self.volume_level_down(volume_diff, pid)
        #     vol -= volume_diff

        # self.set_volume(volume_old, pid)
        self.send_command('browser/playstream', {'pid': pid, 'url': url})

        return None

    def get_groups(self):
        reply = self.send_command('group/get_groups')

    def toggle_mute(self, pid=None):
        reply = self.send_command('player/toggle_mute', {'pid': pid})


if __name__ == "__main__":
    heos = Heos()
    # host = heos.discover('10.0.0.1')
    host = heos.discover()
    heos.connect(host)
    heos.get_players()
    # heos.get_player_info()
    heos.get_play_state()
    heos.get_mute_state()
    heos.get_volume()
    heos.get_groups()
    heos.close()
