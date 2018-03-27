#!/usr/bin/env python

import os
import logging

import ConfigParser
import argparse
from jinja2 import Environment, PackageLoader
from bs4 import BeautifulSoup

# Helper
def normalize(s):
  if s:
    return '"%s"' % s.replace('"', '""')
  else:
    return '""'

# Setup logging
script_name = os.path.splitext(os.path.basename(__file__))[0]
logging.basicConfig()
logger = logging.getLogger(script_name)
logger.setLevel(logging.DEBUG)

# Parse command line options
parser = argparse.ArgumentParser(
    description='Converts KeePass XML file to 1Password CSV')
parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
args = parser.parse_args()

# Read config file
config = ConfigParser.SafeConfigParser()
config.read(os.path.join('etc', script_name + '.conf'))

passwords_xml = BeautifulSoup(open(config.get('General', 'input')))
logger.info('KeePass XML file is opened')

passwords = []

for group in passwords_xml.keepassfile.root.find_all('group', recursive=False):
  for entry in group.find_all('entry', recursive=False):
    password = {
      'title': '',
      'username': '',
      'password': '',
      'url': '',
      'notes': '',
    }
    for string in entry.find_all('string', recursive=False):
      if string.key.string == 'Title':
        password['title'] = normalize(string.value.string)
      elif string.key.string == 'UserName':
        password['username'] = normalize(string.value.string)
      elif string.key.string == 'Password':
        password['password'] = normalize(string.value.string)
      elif string.key.string == 'URL':
        password['url'] = normalize(string.value.string.replace('http://', '')) if string.value.string else ''
      elif string.key.string == 'Notes':
          # Convert <br> to line breaks:
          notes = '\n'.join(unicode(element) for element in string.value.contents if element.name != 'br')
          password['notes'] = normalize(notes)
    passwords.append(password)

# Prepare output file
env = Environment(loader=PackageLoader('__main__', 'templates'))
template = env.get_template('passwords.tmpl')
output = open(config.get('General', 'output'), 'w')
output.write(template.render(passwords = passwords).encode('utf-8'))
output.close()

logger.info('1Password CSV file is written')
