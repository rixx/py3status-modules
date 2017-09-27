# -*- coding: utf-8 -*-
"""
@author rixx
"""
import fcntl
import socket
import struct
import subprocess
from time import time

import json
import bs4
import requests



class Py3status:

    # available configuration parameters
    cache_timeout = 60
    url = 'pretix.instance/control/event/organizer_slug/event_slug/quotas/my_quota'
    login_url = 'pretix.instance/control/login'
    user = ''
    password = ''

    def check_tickets(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }

        try:
            client = requests.session()
            client.get(self.login_url, verify=False)

            csrftoken = client.cookies['pretix_csrftoken']
            login_data = {'email': self.user, 'password': self.password, 'csrfmiddlewaretoken': csrftoken}
            r = client.post(self.login_url, data=login_data, verify=False, headers=dict(Referer=self.login_url))

            r = client.get(self.url + '', verify=False)
            soup = bs4.BeautifulSoup(r.content, 'html.parser')
            num = json.loads(soup.find(id='quota-chart-data').get_text())[-1]['value']

            if num > 50:
                response['color'] = i3s_config['color_good']
            else:
                response['color'] = i3s_config['color_bad']
        except:
            num = ''
            response['color'] = i3s_config['color_bad']

        response['full_text'] = ' {}'.format(num)
        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        subprocess.call(['xdg-open', self.url])


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
        print(x.check_tickets([], config))
        sleep(1)
