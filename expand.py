from xml.dom import minidom, Node
import argparse
import sys
import os
import string

from __main__ import die

formatter = string.Formatter()

class UsedDict:
	def __init__(self, underlying):
		self.underlying = underlying
		self.used = set()
	
	def __getitem__(self, key):
		assert key != 'foo'
		if key in self.underlying:
			self.used.add(key)
			return self.underlying[key]
		else:
			value = os.getenv(key)
			if value is None:
				die("Missing value for '{key}'".format(key = key))
			else:
				return value

	def keys(self):
		return self.underlying.keys()

# Process each text node and attribute in doc.
# Any string containing "{" is expanded using the mapping 'env'
# It is an error if any mapping is unused.
def process_doc(doc, env):
	wrapped_env = UsedDict(env)

	# Expand the template strings with the command-line arguments
	def expand(template_string):
		return formatter.vformat(template_string, [], wrapped_env)	

	def process(elem):
		for name, value in elem.attributes.items():
			if '{' in value:
				elem.attributes[name] = expand(value)
		for child in elem.childNodes:
			if child.nodeType == Node.TEXT_NODE:
				child.data = expand(child.data)
			elif child.nodeType == Node.ELEMENT_NODE:
				process(child)

	result = process(doc.documentElement)
	for x in env:
		if x not in wrapped_env.used:
			die("Unused parameter '{name}'".format(name = x))
	return result
