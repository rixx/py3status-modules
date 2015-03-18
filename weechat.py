# -*- coding: utf8 -*-
""" This py3status module polls the weechat status via the relay
protocol and plugin and displays a custom string if there are hightlights
The relay protocol implementation has been taken from qweechat. """

import collections
import socket
import struct
from time import time
import traceback
import zlib


class Py3status:

    ipv6 = False
    sock = None
    has_quit = False
    hostname = '<HOST>'
    port = 9001
    password = '<PASSWORD>'
    symbol = ''
    cache_timeout = 10

    def get_highlights(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }

        if not self._connect():
            print('not connected')
            return response

        self._send("init password=" + self.password)
        self._send("hdata hotlist:gui_hotlist(*)")

        recvbuf = self.sock.recv(4096)
        self.sock.close()

        if recvbuf:
            length = struct.unpack('>i', recvbuf[0:4])[0]
            recvbuf = recvbuf[0:length]

            msg = str(self._decode(recvbuf))

            if not msg:
                return response

            if ("priority: 2" in msg) or ("priority: 3" in msg):
                response['full_text'] = self.symbol
                response['color'] = i3s_config['color_bad']

        return response

    def _connect(self):
        inet = socket.AF_INET6 if self.ipv6 else socket.AF_INET
        try:
            self.sock = socket.socket(inet, socket.SOCK_STREAM)
            self.sock.connect((self.hostname, self.port))
            return True
        except:
            if self.sock:
                self.sock.close()
            return False

    def _send(self, message):
        try:
            message += '\n'
            self.sock.sendall(message.encode('utf-8'))
            return True
        except:
            return False

    def _decode(self, message):
        try:
            proto = Protocol()
            msgd = proto.decode(message, separator=', ')
            return msgd
        except:
            traceback.print_exc()
            return False


class WeechatObject:
    def __init__(self, objtype, value, separator='\n'):
        self.objtype = objtype
        self.value = value
        self.separator = separator
        self.indent = '  ' if separator == '\n' else ''
        self.separator1 = '\n%s' % self.indent if separator == '\n' else ''

    def _str_value(self, v):
        if type(v) is str and v is not None:
            return '\'%s\'' % v
        return str(v)

    def _str_value_hdata(self):
        lines = ['%skeys: %s%s%spath: %s' % (self.separator1,
                                             str(self.value['keys']),
                                             self.separator,
                                             self.indent,
                                             str(self.value['path']))]
        for i, item in enumerate(self.value['items']):
            lines.append('  item %d:%s%s' % (
                (i + 1), self.separator,
                self.separator.join(
                    ['%s%s: %s' % (self.indent * 2, key,
                                   self._str_value(value))
                     for key, value in item.items()])))
        return '\n'.join(lines)

    def _str_value_infolist(self):
        lines = ['%sname: %s' % (self.separator1, self.value['name'])]
        for i, item in enumerate(self.value['items']):
            lines.append('  item %d:%s%s' % (
                (i + 1), self.separator,
                self.separator.join(
                    ['%s%s: %s' % (self.indent * 2, key,
                                   self._str_value(value))
                     for key, value in item.items()])))
        return '\n'.join(lines)

    def _str_value_other(self):
        return self._str_value(self.value)

    def __str__(self):
        self._obj_cb = {
            'hda': self._str_value_hdata,
            'inl': self._str_value_infolist,
        }
        return '%s: %s' % (self.objtype,
                           self._obj_cb.get(self.objtype,
                                            self._str_value_other)())


class WeechatObjects(list):
    def __init__(self, separator='\n'):
        self.separator = separator

    def __str__(self):
        return self.separator.join([str(obj) for obj in self])


class WeechatMessage:
    def __init__(self, size, size_uncompressed, compression, uncompressed,
                 msgid, objects):
        self.size = size
        self.size_uncompressed = size_uncompressed
        self.compression = compression
        self.uncompressed = uncompressed
        self.msgid = msgid
        self.objects = objects

    def __str__(self):
        if self.compression != 0:
            return 'size: %d/%d (%d%%), id=\'%s\', objects:\n%s' % (
                self.size, self.size_uncompressed,
                100 - ((self.size * 100) // self.size_uncompressed),
                self.msgid, self.objects)
        else:
            return 'size: %d, id=\'%s\', objects:\n%s' % (self.size,
                                                          self.msgid,
                                                          self.objects)


class WeechatDict(collections.OrderedDict):
    def __str__(self):
        return '{%s}' % ', '.join(
            ['%s: %s' % (repr(key), repr(self[key])) for key in self])


class Protocol:
    """Decode binary message received from WeeChat/relay."""

    def __init__(self):
        self._obj_cb = {
            'chr': self._obj_char,
            'int': self._obj_int,
            'lon': self._obj_long,
            'str': self._obj_str,
            'buf': self._obj_buffer,
            'ptr': self._obj_ptr,
            'tim': self._obj_time,
            'htb': self._obj_hashtable,
            'hda': self._obj_hdata,
            'inf': self._obj_info,
            'inl': self._obj_infolist,
            'arr': self._obj_array,
        }

    def _obj_type(self):
        """Read type in data (3 chars)."""
        if len(self.data) < 3:
            self.data = ''
            return ''
        objtype = str(self.data[0:3].decode())
        self.data = self.data[3:]
        return objtype

    def _obj_len_data(self, length_size):
        """Read length (1 or 4 bytes), then value with this length."""
        if len(self.data) < length_size:
            self.data = ''
            return None
        if length_size == 1:
            length = struct.unpack('B', self.data[0:1])[0]
            self.data = self.data[1:]
        else:
            length = self._obj_int()
        if length < 0:
            return None
        if length > 0:
            value = self.data[0:length]
            self.data = self.data[length:]
        else:
            value = ''
        return value

    def _obj_char(self):
        """Read a char in data."""
        if len(self.data) < 1:
            return 0
        value = struct.unpack('b', self.data[0:1])[0]
        self.data = self.data[1:]
        return value

    def _obj_int(self):
        """Read an integer in data (4 bytes)."""
        if len(self.data) < 4:
            self.data = ''
            return 0
        value = struct.unpack('>i', self.data[0:4])[0]

        self.data = self.data[4:]
        return value

    def _obj_long(self):
        """Read a long integer in data (length on 1 byte + value as string)."""
        value = self._obj_len_data(1)
        if value is None:
            return None
        return int(value.decode())

    def _obj_str(self):
        """Read a string in data (length on 4 bytes + content)."""
        value = self._obj_len_data(4)
        if value is None:
            return None
        return value.decode()

    def _obj_buffer(self):
        """Read a buffer in data (length on 4 bytes + data)."""
        return self._obj_len_data(4)

    def _obj_ptr(self):
        """Read a pointer in data (length on 1 byte + value as string)."""
        value = self._obj_len_data(1)
        if value is None:
            return None
        return '0x%s' % value.decode()

    def _obj_time(self):
        """Read a time in data (length on 1 byte + value as string)."""
        value = self._obj_len_data(1)
        if value is None:
            return None
        return int(value.decode())

    def _obj_hashtable(self):
        """
        Read a hashtable in data
        (type for keys + type for values + count + items).
        """
        type_keys = self._obj_type()
        type_values = self._obj_type()
        count = self._obj_int()
        hashtable = WeechatDict()
        for i in range(0, count):
            key = self._obj_cb[type_keys]()
            value = self._obj_cb[type_values]()
            hashtable[key] = value
        return hashtable

    def _obj_hdata(self):
        """Read a hdata in data."""
        path = self._obj_str()
        keys = self._obj_str()
        count = self._obj_int()
        list_path = path.split('/')
        list_keys = keys.split(',')
        keys_types = []
        dict_keys = WeechatDict()
        for key in list_keys:
            items = key.split(':')
            keys_types.append(items)
            dict_keys[items[0]] = items[1]
        items = []
        for i in range(0, count):
            item = WeechatDict()
            item['__path'] = []
            pointers = []
            for p in range(0, len(list_path)):
                pointers.append(self._obj_ptr())
            for key, objtype in keys_types:
                item[key] = self._obj_cb[objtype]()
            item['__path'] = pointers
            items.append(item)
        return {
            'path': list_path,
            'keys': dict_keys,
            'count': count,
            'items': items,
        }

    def _obj_info(self):
        """Read an info in data."""
        name = self._obj_str()
        value = self._obj_str()
        return (name, value)

    def _obj_infolist(self):
        """Read an infolist in data."""
        name = self._obj_str()
        count_items = self._obj_int()
        items = []
        for i in range(0, count_items):
            count_vars = self._obj_int()
            variables = WeechatDict()
            for v in range(0, count_vars):
                var_name = self._obj_str()
                var_type = self._obj_type()
                var_value = self._obj_cb[var_type]()
                variables[var_name] = var_value
            items.append(variables)
        return {
            'name': name,
            'items': items
        }

    def _obj_array(self):
        """Read an array of values in data."""
        type_values = self._obj_type()
        count_values = self._obj_int()
        values = []
        for i in range(0, count_values):
            values.append(self._obj_cb[type_values]())
        return values

    def decode(self, data, separator='\n'):
        """Decode binary data and return list of objects."""
        self.data = data
        size = len(self.data)
        size_uncompressed = size
        uncompressed = None
        # uncompress data (if it is compressed)
        compression = struct.unpack('b', self.data[4:5])[0]

        if compression:
            uncompressed = zlib.decompress(self.data[5:])
            size_uncompressed = len(uncompressed) + 5
            u = struct.pack('>i', size_uncompressed) + struct.pack('b', 0)
            uncompressed = u + uncompressed
            self.data = uncompressed
        else:
            uncompressed = self.data[:]

        # skip length and compression flag
        self.data = self.data[5:]
        # read id
        msgid = self._obj_str()
        if msgid is None:
            msgid = ''
        # read objects
        objects = WeechatObjects(separator=separator)
        while len(self.data) > 0:
            objtype = self._obj_type()
            value = self._obj_cb[objtype]()
            objects.append(WeechatObject(objtype, value, separator=separator))
        return WeechatMessage(size, size_uncompressed, compression,
                              uncompressed, msgid, objects)


def hex_and_ascii(data, bytes_per_line=10):
    """Convert a QByteArray to hex + ascii output."""
    num_lines = ((len(data) - 1) // bytes_per_line) + 1
    if num_lines == 0:
        return ''
    lines = []
    for i in range(0, num_lines):
        str_hex = []
        str_ascii = []
        for char in data[i*bytes_per_line:(i*bytes_per_line)+bytes_per_line]:
            byte = struct.unpack('B', char)[0]
            str_hex.append('%02X' % int(byte))
            if byte >= 32 and byte <= 127:
                str_ascii.append(char)
            else:
                str_ascii.append('.')
        fmt = '%%-%ds %%s' % ((bytes_per_line * 3) - 1)
        lines.append(fmt % (' '.join(str_hex), ''.join(str_ascii)))
    return '\n'.join(lines)


if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.get_highlights([], config))
        sleep(1)
