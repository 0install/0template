# Copyright (C) 2013, Thomas Leonard
# See the README file for details, or visit http://0install.net.

from zeroinstall.zerostore import manifest
from zeroinstall import zerostore
from zeroinstall.injector import namespaces

def get_digest(unpack_dir, alg_name):
	alg = manifest.get_algorithm(alg_name)

	digest = alg.new_digest()
	for line in alg.generate_manifest(unpack_dir):
		digest.update((line + '\n').encode('utf-8'))
	
	return alg.getID(digest)

def add_digests(implementation, unpack_dir, stores):
	sha1new = get_digest(unpack_dir, 'sha1new')
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
	if stores.lookup_maybe(digests) is None:
		stores.add_dir_to_cache(best_digest, unpack_dir)
