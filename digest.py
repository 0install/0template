# Copyright (C) 2013, Thomas Leonard
# See the README file for details, or visit http://0install.net.

import tempfile
from xml.dom import Node

from zeroinstall.zerostore import manifest
from zeroinstall import zerostore
from zeroinstall.support import tasks
from zeroinstall.injector import namespaces, qdom, model

def get_digest(unpack_dir, alg_name):
	alg = manifest.get_algorithm(alg_name)

	digest = alg.new_digest()
	for line in alg.generate_manifest(unpack_dir):
		digest.update((line + '\n').encode('utf-8'))
	
	return alg.getID(digest)

def dom_to_qdom(delem):
	attrs = {((ns + ' ' + name) if ns else name): value for (ns, name), value in delem.attributes.itemsNS()}
	elem = qdom.Element(delem.namespaceURI, delem.localName, attrs)
	for child in delem.childNodes:
		if child.nodeType == Node.ELEMENT_NODE:
			elem.childNodes.append(dom_to_qdom(child))
	return elem

# <archive href='http://example.com/foo/bar.zip'/> becomes:
# <archive href='bar.zip'/>
def basename_hrefs(method):
	if isinstance(method, (model.DownloadSource, model.FileSource)):
		if '/' in method.url:
			method.url = method.url.rsplit('/', 1)[1]
	elif isinstance(method, model.Recipe):
		for step in method.steps:
			basename_hrefs(step)

class FakeStore:
	def get_tmp_dir_for(self, x):
		return tempfile.mkdtemp(prefix = '0template-')

# Instead of checking the digest matches, we calculate it from the unpacked archive
class FakeStores:
	def __init__(self, impl, real_stores):
		self.impl = impl
		self.stores = [FakeStore()]
		self.real_stores = real_stores

	def check_manifest_and_rename(self, required_digest, unpack_dir, dry_run = False):
		implementation = self.impl

		sha1new = get_digest(unpack_dir, 'sha1new')
		if not implementation.getAttribute('id'):
			implementation.setAttribute('id', sha1new)
		digests = [sha1new]

		def add_digest(alg_name):
			digest_id = get_digest(unpack_dir, alg_name)
			digests.append(digest_id)
			name, value = zerostore.parse_algorithm_digest_pair(digest_id)
			elem.setAttribute(alg_name, value)

		have_manifest_elem = False
		for elem in implementation.getElementsByTagNameNS(namespaces.XMLNS_IFACE, 'manifest-digest'):
			have_manifest_elem = True
			have_digests = False
			for attr_name, value in elem.attributes.items():
				if value: continue
				add_digest(attr_name)
				have_digests = True
			if not have_digests:
				add_digest('sha256new')
		if not have_manifest_elem:
			print("WARNING: no <manifest-digest> element found")

		best_rating = -1
		best_digest = None
		for digest_id in digests:
			alg_name, value = zerostore.parse_algorithm_digest_pair(digest_id)
			alg = manifest.get_algorithm(alg_name)
			if alg.rating > best_rating:
				best_rating = alg.rating
				best_digest = digest_id

		# Cache if necessary (saves downloading it again later)
		stores = self.real_stores
		if stores.lookup_maybe(digests) is None:
			stores.add_dir_to_cache(best_digest, unpack_dir)

def add_digests(feed_path, implementation, config):
	root = qdom.Element(namespaces.XMLNS_IFACE, 'interface', {})
	name = qdom.Element(namespaces.XMLNS_IFACE, 'name', {})
	name.content = 'Test'
	summary = qdom.Element(namespaces.XMLNS_IFACE, 'summary', {})
	summary.content = 'testing'
	test_impl = qdom.Element(namespaces.XMLNS_IFACE, 'implementation', {'id': 'sha1new=1', 'version': '0'})
	root.childNodes = [name, summary, test_impl]

	for child in implementation.childNodes:
		if child.namespaceURI == namespaces.XMLNS_IFACE and child.localName in ('archive', 'file', 'recipe'):
			test_impl.childNodes.append(dom_to_qdom(child))

	feed = model.ZeroInstallFeed(root, local_path = feed_path)
	impl, = feed.implementations.values()
	assert impl.download_sources, "No retrieval methods in implementation!"
	method, = impl.download_sources

	basename_hrefs(method)

	# When fetcher asks FakeStores to check the digest, FakeStores instead stores the actual
	# digest on implementation.
	fake_stores = FakeStores(implementation, config.stores)
	blocker = config.fetcher.download_impl(impl, method, fake_stores)
	tasks.wait_for_blocker(blocker)
