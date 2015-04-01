# -*- coding: utf-8 -*-
"""
Start/stop sshuttle and show status.

@author rixx
"""
import os
import subprocess
import time


class Py3status:

    # available configuration parameters.
    cache_timeout = 30
    color_good = None
    color_bad = None
    hide_if_disconnected = False
    host = '<HOST>'
    ip = '<IP>'
    pidfile = '/tmp/sshuttle'
    text_up = 'up'
    text_down = 'down'

    def __init__(self):
        self.last_check = 0
        self.status = 'unconnected'

    def check_sshuttle(self, i3s_output_list, i3s_config):
        response = {}

        if time.time() < self.last_check + self.cache_timeout:
            response['cached_until'] = self.last_check
        else:
            self.last_check = time.time()
            response['cached_until'] = self.last_check + self.cache_timeout

            if self._get_ip() == self.ip:
                self.status = 'connected'
            else:
                self.status = 'unconnected'

        if self.status == 'unconnected':
            response['full_text'] = self.text_down
            response['color'] = self.color_bad if self.color_bad \
                    else i3s_config['color_bad']
        elif self.status == 'connected':
            response['full_text'] = self.text_up
            response['color'] = self.color_good if self.color_good \
                    else i3s_config['color_good']
        return response

    def _get_ip(self):
        return subprocess.check_output(['curl','http://canihazip.com/s']).decode()

    def _is_running(self):
        return False

    def on_click(self, i3s_output_list, i3s_config, event):
        if self.status == 'connected':
            try:
                pid = open(self.pidfile).read().strip()
                subprocess.call(['kill', pid])
            except:
                pass
            self.status = 'unconnected'
        else:
            uid = str(os.getuid())
            auth_sock = '/run/user/' + uid + '/keyring/ssh'
            e = dict(os.environ, **{"SSH_AUTH_SOCK": auth_sock})

            p = '--pidfile=' + self.pidfile
            subprocess.check_output(['sshuttle', p, '--daemon', '--dns', '-r',\
                    self.host, '0/0'], env=e)
            self.status = 'connected'
        subprocess.check_output(['killall', '-USR1', 'py3status'])


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.check_sshuttle([], config))
        sleep(1)
        print(x.on_click(None, config, {}))
