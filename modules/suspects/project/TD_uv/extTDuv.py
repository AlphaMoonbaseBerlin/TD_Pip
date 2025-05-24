

'''Info Header Start
Name : extTDuv
Author : Wieland PlusPlusOne@AMB-ZEPH15
Saveorigin : TD_Pip.toe
Saveversion : 2023.12000
Info Header End'''
import subprocess
from functools import cached_property
import os
import zipfile

from types import ModuleType
from typing import List
from pathlib import Path
import importlib
# import importlib
import sys
from copy import copy

import platform

def UvRequired(function):
	def wrapper(self, *args, **kwargs):
		self.Log("UV Required. Checking.")
		if not self.checkUv: 
			self.Log("UV Not found. Running setup.")
			self.SetupUv()
		return function(self, *args, **kwargs)
	wrapper.__name__ = f"UvRequired_{function.__name__}"
	return wrapper

def ProjectRequired(function):
	def wrapper(self, *args, **kwargs):
		self.Log("Project Required. Checking.")
		if not self.checkProject: 
			self.Log("Project not found. Running setup.")
			self.SetupProject()
		return function(self, *args, **kwargs)
	wrapper.__name__ = f"ProjectRequired_{function.__name__}"
	return wrapper
 

def VenvRequired(function):
	def wrapper(self, *args, **kwargs):
		self.Log("Venv Required. Checking.")
		if not self.checkVenv: 
			self.Log("Venv. Running setup.")
			self.SetupVenv()
		return function(self, *args, **kwargs)
	wrapper.__name__ = f"VenvRequired_{function.__name__}"
	return wrapper

class extTDuv:
	"""
	extTDuv description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.Log = self.ownerComp.op("logger").Log
		self.ownerComp.op("logger").par.Clear.pulse()
		class Mount(object):
			def __init__(mountSelf, clearModules = False):
				mountSelf.clearModules = clearModules
				pass

			def __enter__(mountSelf):
				self.Log("Entering ENV Mount")
				if mountSelf.clearModules:
					mountSelf.modules = sys.modules.copy()
					sys.modules = {}
				self.mountEnv()

			def __exit__(mountSelf, type, value, traceback):
				self.Log("Exiting ENV Mount.")
				self.unmountEnv()
				if mountSelf.clearModules:
					sys.modules = mountSelf.modules	
		self.Mount = Mount

		class MountModule(object):
			def __init__(mountSelf, 
					moduleName:str, 
					pipPackageName:str = '',
					additionalSettings = [],
					clearModules = False):
				mountSelf.clearModules = clearModules
				mountSelf.moduleName = moduleName
				mountSelf.pipPackagName = pipPackageName
				mountSelf.additionalSettings = additionalSettings
				pass

			def __enter__(mountSelf):
				self.Log("Entering Module Mount", mountSelf.moduleName)
				if mountSelf.clearModules:
					mountSelf.modules = sys.modules.copy()
					sys.modules = {}
				# Now we can be sure that it exists. I assume importlib is checking if the path is valid already when setting the value?
				self.mountEnv()
				try:
					return self.ImportModule( 
						mountSelf.moduleName, 
						pipPackageName		= mountSelf.pipPackagName,
						additionalSettings	= mountSelf.additionalSettings
					)
				except Exception as e:
					mountSelf.__exit__(type(e), e, None)
					raise e

			def __exit__(mountSelf, exc_type, exc_val, exc_tb):
				self.Log("Exiting Module Mount")
				self.unmountEnv()
				if mountSelf.clearModules:
					sys.modules = mountSelf.modules	
				return True
			
		self.MountModule = MountModule


	def UvDownloadTarget(self):
		if sys.platform == "win32":
			return "uv-x86_64-pc-windows-msvc.zip"
		if sys.platform == "darwin" and platform.processor() == "i386":
			return "uv-x86_64-apple-darwin.tar.gz"
		if sys.platform == "dawrin" and platform.processor() == "arm":
			return "uv-aarch64-apple-darwin.tar.gz"
	
		raise NotImplemented(f"{sys.platform} OS Not Supported.")
	
	#@property
	@cached_property
	def checkUv(self):
		result = self.runUvCommand(["version", "-q"])
		self.Log("Checking UV", result == 0)
		return result == 0
	
	# @property
	@cached_property
	def checkProject(self):
		self.Log("Checking Project", Path("pyproject.toml").is_file())
		return Path("pyproject.toml").is_file()
	
	# @property
	@cached_property
	def checkVenv(self):
		self.Log("Checking Project", Path(self.localLibPath).is_dir())
		return Path(self.localLibPath).is_dir()
	
	@property
	def uvFolder(self):
		return str(Path("TDImportCache/uv").absolute())
	
	@property
	def localLibPath(self):
		#return os.path.abspath(".venv/Lib/site-packages")
		return ".venv/Lib/site-packages"

	def mountEnv(self):
		self.Log("Mounting ENV.", self.localLibPath)
		self._pathCopy = copy( sys.path )
		self._envCopy = copy( os.environ )
		sys.path.insert(0, self.localLibPath)
		os.environ['PYTHONPATH'] = self.localLibPath
		
	def unmountEnv(self):
		self.Log("UnMounting ENV.")
		sys.path = self._pathCopy
		os.environ = self._envCopy

	def runUvCommand(self, commands):
		if isinstance( commands, str): commands = commands.split(" ")
		self.Log("Running ENV Command", " ".join( commands ))
		return subprocess.call( ["uv"] + commands, env= {
			**os.environ,
			"PATH" : ";".join([ self.uvFolder ] + os.environ["PATH"].split(";"))
		},
		 shell=True )

	def SetupUv(self):
		self.Log("Setting up UV.")
		downloadUvZip = self.ownerComp.op("uvDependency").GetRemoteFilepath()
		if Path( downloadUvZip).suffix == "gz":
			raise NotImplemented("gz files not implemented. Its like Matroschka and I am to lazy rn to take care of that...")
			# Like, srsly, someone pls.
		with zipfile.ZipFile(downloadUvZip, 'r') as zip_ref:
			zip_ref.extractall(self.uvFolder)
		
		del self.checkUv

	@UvRequired
	def SetupProject(self):
		result = self.runUvCommand(f"init --python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}") == 0
		del self.checkProject
		return result
	
	@ProjectRequired
	@UvRequired
	def SetupVenv(self):
		result = self.runUvCommand(f"venv") == 0
		del self.checkVenv
		return result

	@UvRequired
	@ProjectRequired
	@VenvRequired
	def InstallPackage(self, packagePipName:str, additional_settings:List[str] = []):
		sourceIndex = ""
		for _index, element in enumerate( additional_settings ):
			if element in ["--index", "-i"]: 
				sourceIndex = additional_settings[ _index +1 ]
				break
		self.ownerComp.op("dependecyTableRepo").Repo.row( packagePipName ) or self.ownerComp.op("dependecyTableRepo").Repo.appendRow([packagePipName, sourceIndex])
		self.Log("Installing Package", packagePipName)
		return self.runUvCommand(["add", packagePipName] + additional_settings) == 0

	@VenvRequired
	def TestModule(self, module:str, silent:bool = False):
		"""
			Check if a given moduel is alread installed. 
			Note, this does not test for a package but the module itself.
		"""
		self.Log("Testing for package", module)
		
		with self.Mount():
			try:
				foundModule:ModuleType = importlib.util.find_spec( module )	
			except ModuleNotFoundError as exc:
				self.Log( "Module not Found Exception!", exc )
				return False
			if foundModule is None:
				self.Log( "Package does not exist", module )
				if not silent: ui.messageBox('Does not exist', 'The package is not installed')
				return False
				
			if not silent: ui.messageBox('Does exist', 'The package is installed')
			return True

	@ProjectRequired
	@VenvRequired
	def ImportModule(self, moduleName:str, pipPackageName:str = '', additionalSettings:List[str]=[] ):
		"""
			Installs the module if not already installed and returns the module.
			Use instead of the default import method.
			Deprecatd. use PrepareModule instead for proper code completion.
		"""

		_pipPackageName = pipPackageName or moduleName
		self.Log("Importing Module", moduleName, pipPackageName)
		if not self.TestModule(moduleName, silent = True): 
			self.Log("Not Found, running install.")
			if not self.InstallPackage(_pipPackageName, additional_settings=additionalSettings):
				raise ModuleNotFoundError
		return importlib.import_module(moduleName)