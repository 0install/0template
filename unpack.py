# Copyright (C) 2013, Thomas Leonard
# See the README file for details, or visit http://0install.net.

import tempfile, os

from zeroinstall.zerostore import unpack, manifest
from zeroinstall import support

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
