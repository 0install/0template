from xml.dom import minidom, Node
import argparse
import sys
import string

formatter = string.Formatter()

class UsedDict:
	def __init__(self, underlying):
		self.underlying = underlying
		self.used = set()
	
	def __getitem__(self, key):
		assert key != 'foo'
		self.used.add(key)
		return self.underlying[key]

	def keys(self):
		return self.underlying.keys()

# Process each text node and attribute in doc.
# Any string containing "{" is expanded using the mapping 'env'
# It is an error if any mapping is unused.
def process_doc(doc, env):
	wrapped_env = UsedDict(env)

	# Expand the template strings with the command-line arguments
	def expand(template_string):
		try:
			return formatter.vformat(template_string, [], wrapped_env)
		except KeyError as ex:
			raise KeyError("{ex} while expanding '{template}'".format(
				ex = repr(ex), template = template_string))

	def process(elem):
		for name, value in elem.attributes.items():
			if '{' in value:
				elem.attributes[name] = expand(value)
		for child in elem.childNodes:
			if child.nodeType == Node.TEXT_NODE:
				child.data = expand(child.data)
			elif child.nodeType == Node.ELEMENT_NODE:
				process(child)

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
