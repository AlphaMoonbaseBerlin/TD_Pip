

'''Info Header Start
Name : extPIP
Author : Wieland@AMB-ZEPH15
Saveorigin : Project.toe
Saveversion : 2022.28040
Info Header End'''
from pathlib import Path
import subprocess
import importlib
import os

import sys
from types import ModuleType
import ensurepip
import requests
from io import BytesIO
from zipfile import ZipFile

USE_PREFFERENCE_PATH_STORAGE_KEY = "TD_PIP_USE_PREFERENCE"

class extPIP:
	"""
	extPIP description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		
		self.Log = self.ownerComp.op("logger").Log

		self.Log("Initialising Component")

		self.localLibPath = ''
		self.initLocalLibrary()
		self.installPIP()
		
		#Backward Compatbiel
		self.init_local_library = self.initLocalLibrary
		self.Import_Module = self.ImportModule
		self.TestPackage = self.TestModule

	@property
	def pythonExecuteable(self):
		if sys.platform == "darwin":
			raise NotImplemented("MAC OS is currently not supported")
		if sys.platform == "win32":
			return f"{app.binFolder}/python.exe"
		if sys.platform == "linux" or sys.platform == "linux2":
			raise NotImplemented("So, you are running TD on Linux? Sweet! Still, no TD-PIP for you either.")
		raise Exception("Unknown operating system.")
	
	def InstallPackage(self, packagePipName:str, additional_settings:list[str] = []):
		self.Log( "Installing Package", packagePipName)
		try:
			subprocess.check_call([
				self.pythonExecuteable, 
				"-m", 
				"pip", 
				"install", 
				packagePipName, 
				"--target", self.localLibPath.replace('\\', '/')] + additional_settings)
		except: 
			self.Log("Failed Installing Package", packagePipName)
			return False
		
		return True
	
	def UpgradePackage(self, packagePipName:str ):
		return self.InstallPackage( packagePipName, additional_settings=["--upgrade"])
		#subprocess.check_call([self.python_exec, "-m", "pip", "install", package])
		
	def UninstallPackage(self, packagePipName:str ):
		#subprocess.check_call([self.python_exec, "-m", "pip", "uninstall", package, "--target", "{}".format(self.local_lib_path.replace('\\', '/'))])
		debug("Uninstall no longer supported, please remove files by hand.")
		
		
	def TestModule(self, module:str, silent:bool = False):
		self.Log("Testing for package", module)
		
		foundModule:ModuleType = importlib.util.find_spec( module )	
		if foundModule is None:
			self.Log( "Package does not exist", module )
			if not silent: ui.messageBox('Does not exist', 'The package is not installed')
			return False
			
		if not silent: ui.messageBox('Does exist', 'The package is installed')
		return True
			
	
	def ImportModule(self, moduelName:str, pipPackageName:str = '', additional_settings:list[str]=[] ):
		pipPackageName = pipPackageName or moduelName

		if not self.TestModule(moduelName, silent = True): 
			if not self.InstallPackage(pipPackageName, additional_settings=additional_settings):
				return False
		return importlib.import_module(moduelName)
	
	def initLocalLibrary(self):
		self.Log( "Initializing Local Library")
		
		self.localLibPath:str = str( self.path.absolute() )

		if str( self.localLibPath ) in sys.path: 
			self.Log( "Local Library exists")
			return
		
		self.path.mkdir( parents=True, exist_ok=True)

		sys.path.insert(0, self.localLibPath)
		os.environ['PYTHONPATH'] = self.localLibPath

		self.Log( "Local Library initialised.", self.localLibPath )
		
	@property
	def path(self):
		if ui.preferences['general.pythonpackages64'] :
			if op("/").fetch(USE_PREFFERENCE_PATH_STORAGE_KEY, None) is None:
				if ui.messageBox(
					"Python Path Deteced", 
					"It seems like you already have a pythonpath set. Would you like to use it?", 
					buttons = ["Yes", "No"] ):
					op("/").store(USE_PREFFERENCE_PATH_STORAGE_KEY, True)

				if op("/").fetch(USE_PREFFERENCE_PATH_STORAGE_KEY, None):
					return Path( ui.preferences['general.pythonpackages64'] )
				
		return Path( self.ownerComp.par.Library.eval() )

	def pipPath(self) -> Path:
		return Path(self.path, "pip")

	def unpackFromEnsurePip(self):
		for whlFile in Path( app.binFolder, "Lib\ensurepip\_bundled").iterdir():
			if whlFile.suffix != ".whl": continue
			self.Log("Installing PIP-Element from", whlFile)
			with ZipFile(whlFile, 'r') as zip_file:
				zip_file.extractall(path = self.path)

	def installPIP(self):
		if self.TestModule("pip", silent = True):
			self.Log( "Pip already installed.")
			return
		
		self.unpackFromEnsurePip()
		
		#upgrading PIP and setupTools to latest versions!
		self.InstallPackage( "pip", additional_settings=["--upgrade"])
		self.InstallPackage( "setuptools", additional_settings=["--upgrade"])
	
		






