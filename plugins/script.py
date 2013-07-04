# -*- coding:utf-8 -*-

from ecmplugin import ECMPlugin

from tempfile import mkdtemp
from base64 import b64decode
from shutil import rmtree
from os import environ

import simplejson as json

class ECMScript(ECMPlugin):
    def cmd_script_run(self, *argv, **kwargs):
        """script.run script(b64) extension envars runas executable"""

        script_base64       = kwargs.get('script',None)
        script_extension    = kwargs.get('extension',None)
        script_envars       = kwargs.get('envars',None)
        script_runas        = kwargs.get('runas',None)
        script_executable   = kwargs.get('executable',None)

        if not script_extension:
            script_extension = '.cmd'

        if not script_base64:
            raise Exception('Invalid argument')

        try:
            # Write down
            tmp_dir = mkdtemp()
            tmp_file = tmp_dir + '/script' + script_extension
            fh = open(tmp_file, "wb")
            fh.write(b64decode(script_base64))
            fh.close()

        except:
            raise Exception("Unable to decode script")

        # Set environment variables before execution
        script_envars = None
        try:
            if script_envars:
                script_envars = b64decode(script_envars)
                script_envars = json.loads(script_envars)

        except: pass

        if script_executable:
            cmd = script_executable + ' ' + tmp_file
            out, stdout, stderr = self._execute_command(cmd, runas=script_runas, workdir=tmp_dir, envars=script_envars)
        else:
            out, stdout, stderr = self._execute_file(tmp_file, runas=script_runas, workdir = tmp_dir, envars=script_envars)

        rmtree(tmp_dir, ignore_errors = True)
        return  self._format_output(out, stdout, stderr)

ECMScript().run()
