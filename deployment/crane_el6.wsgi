# see /usr/share/doc/python-jinja2-26-2.6/README.Fedora for details on why
# this unpleasantry is necessary.
import sys
sys.path.insert(0, '/usr/lib/python2.6/site-packages/Jinja2-2.6-py2.6.egg')

from crane.wsgi import application
