# Copyright (C) 2013, Thomas Leonard
# See the README file for details, or visit http://0install.net.

from __future__ import print_function

from xml.dom import minidom, Node
import argparse
import os
import sys
import string
import shutil

if sys.version_info[0] >= 3:
	from urllib import request
else:
	import urllib as request

from zeroinstall import support
from zeroinstall.injector import namespaces
from zeroinstall.injector.config import load_config

def die(msg):
	print(msg, file=sys.stderr)
	sys.exit(1)

import expand
import unpack
import digest

version = '0.1'

config = load_config()

parser = argparse.ArgumentParser(description='Fill in a 0install feed template.')
parser.add_argument('template', help='the template file to process')
parser.add_argument('substitutions', metavar='name=value', help='values to insert', nargs='*')

args = parser.parse_args()

template = args.template

if not os.path.exists(template):
	import create
	create.create(args)
	sys.exit(0)

if not template.endswith('.xml.template'):
	die("Template must be named *.xml.template, not {template}".format(template = template))
output_file_stem = template[:-13]

env = {}
for subst in args.substitutions:
	if '=' not in subst:
		die("Substitutions must be in the form name=value, not {subst}".format(subst = subst))
	name, value = subst.split('=', 1)
	if name in env:
		die("Multiple values given for {name}!".format(name = name))
	env[name] = value

# Load the template
doc = minidom.parse(args.template)

# Expand {} template strings
expand.process_doc(doc, env)

template_dir = os.path.dirname(os.path.abspath(output_file_stem))

def process_archives(parent):
	for elem in parent.childNodes:
		if elem.namespaceURI != namespaces.XMLNS_IFACE: continue

		if elem.localName in ('archive', 'file'):
			# Download the archive if missing
			href = elem.getAttribute('href')
			assert href, "missing href on <archive>"
			local_copy = os.path.join(template_dir, os.path.basename(href))
			if not os.path.exists(local_copy):
				print("Downloading {href} to {local_copy}".format(**locals()))
				req = request.urlopen(href)
				with open(local_copy + '.part', 'wb') as local_stream:
					shutil.copyfileobj(req, local_stream)
				support.portable_rename(local_copy + '.part', local_copy)
				req.close()

			# Set the size attribute
			elem.setAttribute('size', str(os.stat(local_copy).st_size))

			# Unpack (a rather inefficient way to guess the 'extract' attribute)
			tmpdir = unpack.unpack_to_tmp(href, local_copy, elem.getAttribute('type'))
			try:
				unpack_dir = os.path.join(tmpdir, 'unpacked')

				# Set the extract attribute
				extract = elem.getAttribute('extract') or unpack.guess_extract(unpack_dir)
				if extract:
					elem.setAttribute('extract', extract)
					unpack_dir = os.path.join(unpack_dir, extract)
					assert os.path.isdir(unpack_dir), "Not a directory: {dir}".format(dir = unpack_dir)
			finally:
				support.ro_rmtree(tmpdir)
		elif elem.localName == 'recipe':
			process_archives(elem)

# Process implementations
for elem in doc.documentElement.getElementsByTagNameNS(namespaces.XMLNS_IFACE, 'implementation'):
	process_archives(elem)
	digest.add_digests(args.template, elem, config)

impls = doc.getElementsByTagNameNS(namespaces.XMLNS_IFACE, 'implementation')
output_file = output_file_stem + '-' + impls[0].getAttribute('version') + '.xml'

print("Writing", output_file)
with open(output_file, 'wt') as stream:
	stream.write('<?xml version="1.0"?>\n')
	doc.documentElement.writexml(stream)
	stream.write('\n')
