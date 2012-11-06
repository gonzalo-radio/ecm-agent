#!/usr/bin/env python

#In windows . is not on python path.
import sys
sys.path.append(".")

from sys import exit
import random
from os.path import join, dirname

#Local
from configobj import ConfigObj

if len(sys.argv) == 2:
    uuid = sys.argv[1]
else:
    print "Usage: "
    print "%s XXXX-XXXX-XXX-XXX" % sys.argv[0]
    print "where XXXX-XXXX-XXX-XXX is the manualy set up UUID for the agent."
    sys.exit(1)


#Parse config file or end execution
try:
    config_filename = join(dirname(__file__), 'ecm_agent.cfg')
    config = ConfigObj(config_filename)
except:
    print 'Unable to read the config file at %s' % config_filename
    print 'Agent will now quit'
    sys.exit(2)


config['XMPP']['user'] = '%s@%s' % (uuid, config['XMPP']['host'])
config['XMPP']['password'] = hex(random.getrandbits(128))[2:-1]
config['XMPP']['manual'] = True

config.write()

print 'Manual configuration override succeeded.'