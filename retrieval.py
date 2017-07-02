# Copyright (C) 2013, Thomas Leonard
# See the README file for details, or visit http://0install.net.

import tempfile, os, sys, shutil

if sys.version_info[0] >= 3:
	from urllib import request
else:
	import urllib as request

from zeroinstall import support
from zeroinstall.injector import namespaces
from zeroinstall.zerostore import unpack, manifest

def process_elements(parent, template_dir):
	for elem in parent.childNodes:
		if elem.namespaceURI != namespaces.XMLNS_IFACE: continue

		if elem.localName == 'archive':
			process_archive(elem, template_dir)
		elif elem.localName == 'file':
			process_file(elem, template_dir)
		elif elem.localName == 'recipe':
			process_elements(elem, template_dir)

def process_archive(elem, template_dir):
	href = elem.getAttribute('href')
	assert href, "missing href on <archive>"
	local_copy = os.path.join(template_dir, os.path.basename(href))
	if not os.path.exists(local_copy):
		download(href, local_copy)

	# Set the size attribute
	elem.setAttribute('size', str(os.stat(local_copy).st_size))

	if not elem.hasAttribute('extract'):
		# Unpack (a rather inefficient way to guess the 'extract' attribute)
		tmpdir = unpack_to_tmp(href, local_copy, elem.getAttribute('type'))
		try:
			unpack_dir = os.path.join(tmpdir, 'unpacked')

			# Set the extract attribute
			extract = guess_extract(unpack_dir)
			if extract:
				elem.setAttribute('extract', extract)
				unpack_dir = os.path.join(unpack_dir, extract)
				assert os.path.isdir(unpack_dir), "Not a directory: {dir}".format(dir = unpack_dir)
		finally:
			support.ro_rmtree(tmpdir)
	else:
		extract = elem.getAttribute('extract')
		if extract == "":
			# Remove empty element
			elem.removeAttribute('extract')

def process_file(elem, template_dir):
	href = elem.getAttribute('href')
	assert href, "missing href on <file>"
	local_copy = os.path.join(template_dir, os.path.basename(href))
	if not os.path.exists(local_copy):
		download(href, local_copy)

	# Set the size attribute
	elem.setAttribute('size', str(os.stat(local_copy).st_size))

def download(href, local_copy):
	print("Downloading {href} to {local_copy}".format(**locals()))
	req = request.urlopen(href)
	with open(local_copy + '.part', 'wb') as local_stream:
		shutil.copyfileobj(req, local_stream)
	support.portable_rename(local_copy + '.part', local_copy)
	req.close()

def unpack_to_tmp(url, archive_file, mime_type):
	"""Creates a temporary directory and unpacks the archive to it in "unpacked".
	Permissions are correct for importing into the cache.
	Returns the tmpdir."""
	if not mime_type:
		mime_type = unpack.type_from_url(url)
		assert mime_type, "Can't guess MIME type from {url}".format(url = url)

	tmpdir = tempfile.mkdtemp('-0template')
	try:
		# Must be readable to helper process running as 'zeroinst'...
		old_umask = os.umask(0o022)
		try:
			unpack_dir = os.path.join(tmpdir, 'unpacked')
			os.mkdir(unpack_dir)

			with open(archive_file, 'rb') as stream:
				unpack.unpack_archive(url, stream, unpack_dir,
						      type = mime_type, start_offset = 0)
				manifest.fixup_permissions(unpack_dir)
		finally:
			os.umask(old_umask)
	except:
		support.ro_rmtree(tmpdir)
		raise
	return tmpdir

def guess_extract(unpack_dir):
	items = os.listdir(unpack_dir)
	if len(items) == 1 and \
	   os.path.isdir(os.path.join(unpack_dir, items[0])) and \
	   items[0] not in ('usr', 'opt', 'bin', 'etc', 'sbin', 'doc', 'var'):
		return items[0]
	return None
