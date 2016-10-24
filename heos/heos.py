#!/usr/bin/env python3
" Heos python lib "

import socket
import json
from pprint import pprint
# from time import sleep
import heos.heosupnp as heosupnp

HEOS_PORT = 1255

class HeosException(Exception):
    " HeosException class "
    # pylint: disable=super-init-not-called
    def __init__(self, message):
        self.message = message


class Heos(object):
    " Heos class "

    def __init__(self, host=None, verbose=False):
        self._host = host
        self._players = None
        self._play_state = None
        self._mute_state = None
        self._volume_level = None

        self._verbose = verbose
        self._player_id = None
        self._connection = None
        self._upnp = heosupnp.HeosUpnp()
        self._upnp_renderer = None

        if not self._host:
            # host = self._discover_ssdp()
            url = self._upnp.discover()
            self._host = self._url_to_addr(url)
        self.connect()

        try:
            self._player_id = self.get_players()[0]['pid']
        except TypeError:
            print('[E] No player found')

    @staticmethod
    def _url_to_addr(url):
        import re
        try:
            addr = re.search('https?://([^:/]+)[:/].*$', url)
            return addr.group(1)
        except:         # pylint: disable=bare-except
            return None

    def connect(self):
        self._connect(self._host)

    def _connect(self, host, port=HEOS_PORT):
        " connect "
        self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connection.connect((host, port))

    def send_command(self, command, message=None):
        " send command "
        msg = 'heos://' + command
        if message:
            if 'pid' in message.keys() and message['pid'] is None:
                message['pid'] = self._get_player_id()
            msg += '?' + '&'.join("{}={}".format(key, val) for (key, val) in message.items())
        msg += '\r\n'
        if self._verbose:
            pprint(msg)
        self._connection.send(msg.encode('ascii'))
        return self._recv_reply(command)

    @staticmethod
    def _parse_message(message):
        " parse message "
        return dict(elem.split('=') for elem in message.split('&'))

    def _parse_command(self, command, data):
        " parse command "
        try:
            if command == data['heos']['command']:
                if data['heos']['result'] == 'fail':
                    raise HeosException(data['heos']['message'])
                if 'payload' in data.keys():
                    return data['payload']
                else:
                    return self._parse_message(data['heos']['message'])
        # pylint: disable=bare-except
        except:
            pass

        return None

    def _recv_reply(self, command):
        " recv reply "
        while True:
            msg = self._connection.recv(64*1024)
            if self._verbose:
                pprint(msg)
                pprint(msg.decode())
            # simplejson doesnt need to decode from byte to ascii
            data = json.loads(msg.decode())
            reply = self._parse_command(command, data)
            if reply is not None:
                if self._verbose:
                    pprint(reply)
                return reply

    def close(self):
        " close "
        self._connection.close()
        self._connection = None

    def get_players(self):
        " get players "
        # heos.send_command('system/register_for_change_events?enable=on')
        return self.send_command('player/get_players')

    def _get_player_id(self):
        return self._player_id

    def get_player_info(self):
        " get player info "
        return self.send_command('player/get_player_info', {'pid': self._get_player_id()})

    def get_play_state(self):
        " get play state "
        reply = self.send_command('player/get_play_state', {'pid': self._get_player_id()})
        if reply:
            self._play_state = reply['state']
        return self._play_state

    def get_mute_state(self):
        " get mute state "
        reply = self.send_command('player/get_mute', {'pid': self._get_player_id()})
        if reply:
            self._mute_state = reply['state']
        return self._mute_state

    def get_volume(self):
        " get volume "
        reply = self.send_command('player/get_volume', {'pid': self._get_player_id()})
        if reply:
            self._volume_level = reply['level']
        return self._volume_level

    def set_volume(self, volume_level):
        " set volume "
        if volume_level > 100:
            volume_level = 100
        if volume_level < 0:
            volume_level = 0
        reply = self.send_command('player/set_volume', {'pid': self._get_player_id(),
                                                        'level': volume_level})
        if reply:
            self._volume_level = reply['level']
        return self._volume_level

    def volume_level_up(self, step=10):
        " volume level up "
        volume_level = self.get_volume()
        self.set_volume(volume_level + step)

    def volume_level_down(self, step=10):
        " volume level down "
        volume_level = self.get_volume()
        self.set_volume(volume_level - step)

    def _set_play_state(self, state):
        " set play state "
        if state not in ('play', 'pause', 'stop'):
            HeosException('Not an accepted play state {}.'.format(state))

        reply = self.send_command('player/set_play_state', {'pid': self._get_player_id(),
                                                            'state': state})
        if reply:
            self._play_state = state

    def stop(self):
        " stop player "
        self._set_play_state('stop')

    def play(self):
        " play "
        self._set_play_state('play')

    def pause(self):
        " pause "
        self._set_play_state('pause')

    def get_now_playing_media(self):
        " get playing media "
        reply = self.send_command('player/get_now_playing_media', {'pid': self._get_player_id()})
        return reply

    def get_queue(self):
        " get queue "
        reply = self.send_command('player/get_queue', {'pid': self._get_player_id()})
        return reply

    def clear_queue(self):
        " clear queue "
        reply = self.send_command('player/clear_queue', {'pid': self._get_player_id()})
        return reply

    def play_next(self):
        " play next "
        reply = self.send_command('player/play_prev', {'pid': self._get_player_id()})
        return reply

    def play_prev(self):
        " play prev "
        reply = self.send_command('player/play_prev', {'pid': self._get_player_id()})
        return reply

    def play_queue(self, qid):
        " play queue "
        reply = self.send_command('player/play_queue', {'pid': self._get_player_id(),
                                                        'qid': qid})
        return reply

    def get_groups(self):
        " get groups "
        reply = self.send_command('group/get_groups')
        return reply

    def toggle_mute(self):
        " toggle mute "
        reply = self.send_command('player/toggle_mute', {'pid': self._get_player_id()})
        return reply

    def get_music_sources(self):
        " get music sources "
        reply = self.send_command('browser/get_music_sources', {'range': '0,29'})
        return reply

    def get_browse_source(self, sid):
        " browse source "
        reply = self.send_command('browser/browse', {'sid': sid, 'range': '0,29'})
        return reply

    def play_content(self, content, content_type='audio/mpeg'):
        self._upnp.play_content(content, content_type)


def main():
    " main "
    heos = Heos(verbose=True)
    # heos.get_player_info()
    heos.get_play_state()
    heos.get_mute_state()
    heos.get_volume()
    heos.set_volume(10)
    heos.get_groups()

    with open('hello.mp3', mode='rb') as f:
        content = f.read()
    content_type = 'audio/mpeg'
    heos.play_content(content, content_type)
    heos.close()

if __name__ == "__main__":
    main()
