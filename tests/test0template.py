from xml.dom import minidom
import unittest
import tempfile
import subprocess
import shutil
import os

from zeroinstall.injector import model, qdom

os.environ["http_proxy"] = "http://localhost:9999/bug"
mydir = os.path.dirname(os.path.abspath(__file__))

def test_create(name, stdin):
	child = subprocess.Popen(["0template", name],
			stdin = subprocess.PIPE,
			stdout = subprocess.PIPE,
			stderr = subprocess.STDOUT,
			universal_newlines = True)
	out, unused = child.communicate(stdin)
	assert 'Writing ' + name in out, out
	retval = child.wait()
	assert retval == 0

class Test0Template(unittest.TestCase):
	def setUp(self):
		self.tmpdir = tempfile.mkdtemp('-0template')
		os.chdir(self.tmpdir)

	def tearDown(self):
		os.chdir("/")
		shutil.rmtree(self.tmpdir)
	
	def testCreateLocalBinary(self):
		test_create("binary.xml", "2\n")

		with open("binary.xml", "rb") as stream:
			feed = model.ZeroInstallFeed(qdom.parse(stream), local_path = os.path.abspath("."))

		impl, = feed.implementations.values()
		assert impl.id == "."
		command, = impl.commands
		assert command == "run"
	
	def testCreateLocalSource(self):
		test_create("source.xml", "1\n")

		with open("source.xml", "rb") as stream:
			feed = model.ZeroInstallFeed(qdom.parse(stream), local_path = os.path.abspath("."))

		impl, = feed.implementations.values()
		assert impl.id == "."
		command, = impl.commands
		assert command == "compile"
	
	def testBinary(self):
		test_create("binary.xml.template", "2\n")
		shutil.copyfile(os.path.join(mydir, "myprog-1.0.zip"), "myprog-1.0.zip")
		out = subprocess.check_output(["0template", "binary.xml.template", "version=1.0"], universal_newlines = True)
		self.assertEqual("Writing binary-1.0.xml\n", out)
		with open("binary-1.0.xml", "rb") as stream:
			feed = model.ZeroInstallFeed(qdom.parse(stream), local_path = os.path.abspath("."))
		impl, = feed.implementations.values()
		self.assertEqual('sha1new=67ba178ed33b292efa5ab364d01a8fc13fe9eba3', impl.id)
		command, = impl.commands
		assert command == "run"
	
	def testSource(self):
		test_create("source.xml.template", "1\n")
		shutil.copyfile(os.path.join(mydir, "myprog-1.0.zip"), "myprog-1.0.zip")
		out = subprocess.check_output(["0template", "source.xml.template", "version=1.0"], universal_newlines = True)
		self.assertEqual("Writing source-1.0.xml\n", out)
		with open("source-1.0.xml", "rb") as stream:
			feed = model.ZeroInstallFeed(qdom.parse(stream), local_path = os.path.abspath("."))
		impl, = feed.implementations.values()
		self.assertEqual('sha1new=67ba178ed33b292efa5ab364d01a8fc13fe9eba3', impl.id)
		command, = impl.commands
		assert command == "compile"

if __name__ == '__main__':
	unittest.main()
