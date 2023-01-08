'''Info Header Start
Name : extPIP
Author : Admin@DESKTOP-RTI312L
Version : 0
Build : 5
Savetimestamp : 2023-01-08T13:44:33.209168
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
		
	def InstallPackage(self, package):
		logger.Log( "Installing Package", package)
		try:
			subprocess.check_call([self.python_exec, "-m", "pip", "install", package, "--target", "{}".format(self.local_lib_path.replace('\\', '/'))])
		except: 
			logger.Log("Failed Installing Package", package)
			return False
		
		return True
		
			
		#subprocess.check_call([self.python_exec, "-m", "pip", "install", package])
		
	def UninstallPackage(self, package):
		#subprocess.check_call([self.python_exec, "-m", "pip", "uninstall", package, "--target", "{}".format(self.local_lib_path.replace('\\', '/'))])
		debug("Uninstall no longer supported, please remove files by hand.")
		
		
	def TestPackage(self, package, silent = False):
		logger.Log("Testing for package", package)
		try:
			importlib.import_module(package)
		except:
			logger.Log( "Package does not exist", package)
			if not silent: ui.messageBox('Does not exist', 'The package is not installed')
			return False
			
		if not silent: ui.messageBox('Does exist', 'The package is installed')
		return True
			
	
	def Import_Module(self, module, pip_name = ''):
		if not pip_name: pip_name = module
		if not self.TestPackage(module, silent = True): 
			if not self.InstallPackage(pip_name):
				return False
		return importlib.import_module(module)
	
	def add_path_to_syspath(self, path:str):
		if path in sys.path: 
			logger.Log( "Local lib already in syspath")
			return
		sys.path.insert(0, path)

	def add_path_to_envpath(self, path:str):
		python_pathes = [ element for element in os.environ.get("PYTHONPATH", "").split(os.pathsep) if element]		
		if path in python_pathes: 
			logger.Log( "Local Library already in pythonpath")
			return
		os.environ["PYTHONPATH"] = os.pathsep.join( [path] + python_pathes)

	def init_local_library(self):
		logger.Log( "Initializing Local Library", self.path )
		os.makedirs(self.path, exist_ok = True)
		self.local_lib_path = os.path.abspath(self.path)
		self.add_path_to_syspath( self.local_lib_path )
		self.add_path_to_envpath( self.local_lib_path )
		
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







