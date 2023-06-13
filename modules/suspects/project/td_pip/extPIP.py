'''Info Header Start
Name : extPIP
Author : wieland@MONOMANGO
Version : 0
Build : 6
Savetimestamp : 2023-06-13T12:34:10.193280
Saveorigin : Project.toe
Saveversion : 2022.28040
Info Header End'''
import subprocess
import importlib
import os

import sys

import requests
from io import BytesIO
from zipfile import ZipFile

logger = op("logger")

class extPIP:
	"""
	extPIP description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.python_exec = app.binFolder + '/python.exe'
		logger.Log("Initialising Component")
		self.local_lib_path = ''
		self.init_local_library()
		self.install_pip()
		
	def InstallPackage(self, package, additional_settings = []):
		logger.Log( "Installing Package", package)
		try:
			subprocess.check_call([self.python_exec, "-m", "pip", "install", package, "--target", "{}".format(self.local_lib_path.replace('\\', '/'))] + additional_settings)
		except: 
			logger.Log("Failed Installing Package", package)
			return False
		
		return True
	
	def UpgradePackage(self, package):
		return self.InstallPackage( package, additional_settings=["--upgrade"])
		#subprocess.check_call([self.python_exec, "-m", "pip", "install", package])
		
	def UninstallPackage(self, package):
		#subprocess.check_call([self.python_exec, "-m", "pip", "uninstall", package, "--target", "{}".format(self.local_lib_path.replace('\\', '/'))])
		debug("Uninstall no longer supported, please remove files by hand.")
		
		
	def TestPackage(self, package, silent = False):
		logger.Log("Testing for package", package)
		
		found_package = importlib.util.find_spec( package )	
		if found_package is None:
			logger.Log( "Package does not exist", package)
			if not silent: ui.messageBox('Does not exist', 'The package is not installed')
			return False
			
		if not silent: ui.messageBox('Does exist', 'The package is installed')
		return True
			
	
	def Import_Module(self, module, pip_name = '', additional_settings=[] ):
		if not pip_name: pip_name = module
		if not self.TestPackage(module, silent = True): 
			if not self.InstallPackage(pip_name, additional_settings=additional_settings):
				return False
		return importlib.import_module(module)
	
	def init_local_library(self):
		logger.Log( "Initializing Local Library")
		os.makedirs(self.path, exist_ok = True)
		self.local_lib_path = os.path.abspath(self.path)
		if self.local_lib_path in sys.path: 
			logger.Log( "Local Library exists")
			return
		sys.path.insert(0, self.local_lib_path)
		os.environ['PYTHONPATH'] = self.local_lib_path
		logger.Log( "Local Library initialised.")
	@property
	def path(self):
		return self.ownerComp.par.Library.eval().rstrip("/\\")

	def install_pip(self):
		if os.path.isdir( f"{self.path}/pip" ): 
			logger.Log( "Pip already installed.")
			return
			
		response = requests.get( "https://pypi.org/pypi/pip/json" )
		for url_dict in response.json()["urls"]:
			if url_dict["packagetype"] != "bdist_wheel": continue
			byte_data = requests.get( url_dict["url"] ).content
			filelike_object = BytesIO( byte_data )
			with ZipFile(filelike_object, 'r') as zip_file:
				zip_file.extractall(path = self.path)

			
		logger.Log( "Testing for Setuptools")	
		if not self.TestPackage("setuptools", silent = True): 
			logger.Log( "Installing Setuptools during init." )
			self.InstallPackage("setuptools")







