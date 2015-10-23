from distutils.core import setup
import py2exe

setup(
	windows=['rocketlogs.py'],
	options={
		"py2exe": {
			"compressed": True,
			"optimize": 2,
			"bundle_files": 2
		}
	});