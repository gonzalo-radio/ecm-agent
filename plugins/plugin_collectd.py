# -*- coding:utf-8 -*-

# Copyright (C) 2012 Juan Carlos Moreno <juancarlos.moreno at ecmanaged.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# collect.py: the python collectd-unixsock module.
#
# Requires collectd to be configured with the unixsock plugin, like so:
#
# LoadPlugin unixsock
# <Plugin unixsock>
#   SocketFile "/var/run/collectd-unixsock"
#   SocketPerms "0775"
# </Plugin>
#
# Copyright (C) 2008 Clay Loveless <clay@killersoft.com>
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

import os
import socket
from sys import stderr

# Local
from __plugin import ECMPlugin

DEFAULT_COLLECTD_SOCK = '/var/run/collectd-unixsock'

class ECMCollectd(ECMPlugin):
    def cmd_collectd_get(self, *argv, **kwargs):
        sock_file = kwargs.get('sock_file', None)
        
        if not sock_file: 
            sock_file = DEFAULT_COLLECTD_SOCK

        if not os.path.exists(sock_file):
            raise Exception('Collectd socket not found')

        c = Collectd(sock_file, noisy=False)
        _list = c.list_val()
        ret = {}

        for val in _list:
            stamp, identifier = val.split()
            ret[identifier] = {}
            ret[identifier]['timestamp'] = stamp
            values = c.get_val(identifier)
            ret[identifier]['values'] = values

        return ret


class Collectd():
    def __init__(self, path, noisy=False):
        self.noisy = noisy
        self.path = path
        self._sock = self._connect()

    def flush(self, timeout=None, plugins=[], identifiers=[]):
        """Send a FLUSH command.

        Full documentation:
            http://collectd.org/wiki/index.php/Plain_text_protocol#FLUSH

        """
        # have to pass at least one plugin or identifier
        if not plugins and not identifiers:
            return None
        args = []
        if timeout:
            args.append("timeout=%s" % timeout)
        if plugins:
            plugin_args = map(lambda x: "plugin=%s" % x, plugins)
            args.extend(plugin_args)
        if identifiers:
            identifier_args = map(lambda x: "identifier=%s" % x, identifiers)
            args.extend(identifier_args)
        return self._cmd('FLUSH %s' % ' '.join(args))

    def get_val(self, identifier, flush_after=True):
        """Send a GETVAL command.

        Also flushes the identifier if flush_after is True.

        Full documentation:
            http://collectd.org/wiki/index.php/Plain_text_protocol#GETVAL

        """
        num_values = self._cmd('GETVAL "%s"' % identifier)
        if not num_values or num_values < 0:
            raise KeyError("Identifier '%s' not found" % identifier)
        lines = self._read_lines(num_values)
        if flush_after:
            self.flush(identifiers=[identifier])

        return lines

    def list_val(self):
        """Send a LISTVAL command.

        Full documentation:
            http://collectd.org/wiki/index.php/Plain_text_protocol#LISTVAL

        """
        numvalues = self._cmd('LISTVAL')
        lines = []
        if numvalues:
            lines = self._read_lines(numvalues)

        return lines

    def _cmd(self, c):
        try:
            return self._cmd_attempt(c)
        except socket.error, (errno, errstr):
            stderr.write("[error] Sending to socket failed: [%d] %s\n"
                         % (errno, errstr))
            self._sock = self._connect()
            return self._cmd_attempt(c)

    def _cmd_attempt(self, c):
        if self.noisy:
            print "[send] %s" % c
        if not self._sock:
            stderr.write("[error] Socket unavailable. Can not send.")
            return False
        self._sock.send(c + "\n")
        status_message = self._read_line()
        if self.noisy:
            print "[recive] %s" % status_message
        if not status_message:
            return None
        code, message = status_message.split(' ', 1)

        if int(code):
            return int(code)
        return False

    def _connect(self):
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.path)
            if self.noisy:
                print "[socket] connected to %s" % self.path
            return sock
        except socket.error, (errno, errstr):
            stderr.write("[error] Connecting to socket failed: [%d] %s"
                         % (errno, errstr))
            return None

    def _read_line(self):
        """Read single line from socket"""
        if not self._sock:
            stderr.write("[error] Socket unavailable. Can not read.")
            return None
        try:
            data = ''
            buf = []
            recv = self._sock.recv
            while data != "\n":
                data = recv(1)
                if not data:
                    break
                if data != "\n":
                    buf.append(data)
            return ''.join(buf)
        except socket.error, (errno, errstr):
            stderr.write("[error] Reading from socket failed: [%d] %s"
                         % (errno, errstr))
            self._sock = self._connect()
            return None

    def _read_lines(self, sizehint=0):
        """Read multiple lines from socket"""
        _list = []
        while True:
            line = self._read_line()
            if not line:
                break
            _list.append(line)
            total = len(_list)
            if sizehint and total >= sizehint:
                break

        return _list

    def __del__(self):
        if not self._sock:
            return
        try:
            self._sock.close()
        except socket.error, (errno, errstr):
            stderr.write("[error] Closing socket failed: [%d] %s"
                         % (errno, errstr))


ECMCollectd().run()
