# Copyright (C) 2013, Thomas Leonard
# See the README file for details, or visit http://0install.net.

import os
from xml.dom import minidom
from zeroinstall.injector import namespaces

from __main__ import die

mydir = os.path.dirname(__file__)

def get_choice(msg, options):
	print()
	print(msg)
	print()
	for i, label in options:
		print("{i}) {label}".format(i = i, label = label))
	while True:
		try:
			n = int(input("\n> "))
		except ValueError:
			print("Not an integer")
			continue

		for i, label in options:
			if i == n:
				return n
		print("Invalid choice")

def create(options):
	template = options.template

	if options.substitutions:
		die("{template} does not exist".format(template = template))

	if template.endswith('.xml.template'):
		remote = True
	elif template.endswith('.xml'):
		remote = False
	else:
		die("'{template}' does not end with .xml.template or .xml".format(template = template))
	
	print("'{template}' does not exist; creating new template.".format(template = template))
	if not remote:
		print("\nAs it ends with .xml, not .xml.template, I assume you want a feed for\n"
		      "a local project (e.g. a Git checkout). If you want a template for\n"
		      "publishing existing releases, use {template}.template instead.".format(
			      template = template))
	
	doc = minidom.parse(os.path.join(mydir, "example.xml"))

	impls = doc.getElementsByTagNameNS(namespaces.XMLNS_IFACE, 'implementation')
	impls[0].parentNode.removeChild(impls[0] if remote else impls[1])

	choice = get_choice("Does your program need to be compiled before it can be used?", [
		(1, "Generate a source template (e.g. for compiling C source code)"),
		(2, "Generate a binary template (e.g. for a pre-compiled binary or script)"),
	])

	commands = doc.getElementsByTagNameNS(namespaces.XMLNS_IFACE, 'command')
	commands[0].parentNode.removeChild(commands[choice - 1])

	if choice == 1:
		impl, = doc.getElementsByTagNameNS(namespaces.XMLNS_IFACE, 'implementation')
		impl.setAttribute('arch', '*-src')

	assert not os.path.exists(template), template
	print("\nWriting", template)
	with open(template, 'wt') as stream:
		stream.write('<?xml version="1.0"?>\n')
		doc.documentElement.writexml(stream)
		stream.write('\n')
