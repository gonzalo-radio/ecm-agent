#!/usr/bin/env python

import os, string, random, re
import platform
import urllib2

from subprocess import call

class ECMCommon():
    def _file_write(self,file,content=None):
        try:
            _path = os.path.dirname(file)
            if not os.path.exists(_path):
                os.mkdir(_path)

            f = open(file,'w')
            if content:
                f.write(content)
            f.close()

        except:
            raise Exception("Unable to write file: %s" % file)

    def _file_read(self,file):
        try:
            if os.path.isfile(file):
                f = open(file,'r')
                retval = f.read()
                f.close()
                return retval

        except:
            raise Exception("Unable to read file: %s" % file)

    def _secret_gen(self):
        chars = string.ascii_uppercase + string.digits  + '!@#$%^&*()'
        return ''.join(random.choice(chars) for x in range(60))

    def _clean_stdout(self,output):
        ''' Remove color chars from output
        '''
        r = re.compile("\033\[[0-9;]+m", re.MULTILINE)
        return r.sub('', output)

    def _download_file(self, url, file):
        try:
            req = urllib2.urlopen(url.replace("'",""))
            CHUNK = 256 * 10240
            with open(file, 'wb') as fp:
                while True:
                    chunk = req.read(CHUNK)
                    if not chunk: break
                    fp.write(chunk)
        except:
            return False

        return file

    def _install_package(self,package,update = True):
        """ Try to install package
        """
        try:
            (distribution,version,tmp)=platform.dist()

            if distribution.lower() == 'debian' or distribution.lower() == 'ubuntu':
                os.environ['DEBIAN_FRONTEND'] = 'noninteractive'

                if update: call(['apt-get','-y','-qq','update'])
                ret_code = call(['apt-get','-o','Dpkg::Options::=--force-confold',
                                '--allow-unauthenticated','--force-yes',
                                 '-y','-qq','install',package])

            elif distribution.lower() == 'centos' or distribution.lower() == 'redhat':
                if update: call(['yum','-y','clean','all'])
                ret_code = call(['yum','-y','--nogpgcheck','install',package])

            elif distribution.lower() == 'arch':
                if update: call(['pacman','-Sy'])
                if update: call(['pacman','-S','--noconfirm','pacman'])
                ret_code = call(['pacman','-S','--noconfirm',package])

            else:
                raise Exception("Distribution not supported: " + distribution)

            return ret_code

        except:
            raise Exception("Error installing %s" % package)

