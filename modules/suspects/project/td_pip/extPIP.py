'''Info Header Start
Name : extPIP
Author : Wieland@AMB-ZEPH15
Saveorigin : Project.toe
Saveversion : 2023.11880
Info Header End'''
from pathlib import Path
import subprocess
import importlib
import os
import shutil
from typing import List, TypeVar, cast, Generic, Union

import tempfile

import sys
from types import ModuleType
from zipfile import ZipFile

USE_PREFFERENCE_PATH_STORAGE_KEY = "TD_PIP_USE_PREFERENCE"
T = TypeVar("T")



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

		# 2023 now ships its own python, which is nice. So no need to install it in to our little local env.
		if int(app.version.split(".")[0]) < 2023:
			self.installPIP()
		
		#Backward Compatbiel
		self.init_local_library = self.initLocalLibrary
		#self.Import_Module = self.ImportModule
		self.TestPackage = self.TestModule

	@property
	def _pythonExecuteable(self):
		try:
			return app.pythonExecutable
		except AttributeError:
			return self._backwarsdComptaiblePythonExecuteable

	@property
	def _backwarsdComptaiblePythonExecuteable(self):
		if sys.platform == "win32":
			return f"{app.binFolder}/python.exe"
		if sys.platform == "linux" or sys.platform == "linux2":
			raise NotImplemented("So, you are running TD on Linux? Sweet! Still, no TD-PIP for you either.")
		raise NotImplemented(f"{sys.platform} OS Not Supported.")
	

	@property
	def packageCache(self):
		return self.ownerComp.op("cacheRepo").Repo
	
	def RemoveCachedPackage(self, packagePipName:str):
		try:
			self.packageCache.vfs[f"{packagePipName}"].destroy()
		except:
			pass


	def unpackPackage(self, packagePipName:str):
		self.Log("Checking if package is local existent.", packagePipName)
		unpackDir = Path("TDImportCache/PIP_Cache")
		try:
			exportedArchive = self.packageCache.vfs[packagePipName].export(
						unpackDir
					)
			shutil.unpack_archive(
					exportedArchive,
					extract_dir=unpackDir,
					format="zip"
				) 
			return unpackDir
		except Exception as e:
			self.Log("No cached package found", e)
			return None

	def CachePackage(self, packagePipName:str, additional_settings:List[str] = []):
		self.Log( "Packaging Package", packagePipName)
		try:
			with tempfile.TemporaryDirectory() as downloadDestination:
				debug( downloadDestination)
				subprocess.check_call([
					self._pythonExecuteable, 
					"-m", 
					"pip", 
					"download", 
					packagePipName, 
					"--dest", downloadDestination])
				
				packageArchive = shutil.make_archive(
					packagePipName,
					"zip",
					root_dir= downloadDestination
					)
				self.RemoveCachedPackage( packagePipName )
				self.packageCache.vfs.addFile(
					packageArchive,
					overrideName = packagePipName
				)
				self.packageCache.cook( force = True, recurse = True )

		except Exception as e: 
			self.Log("Failed Caching Package", packagePipName, e)
			return False
		
		return True

	def Freeze( self, requirementsFilepath = "", additional_settings:List[str]=[]):
		outputPath = Path( requirementsFilepath or self.ownerComp.par.Requirementsfile.eval() )
		self.Log( "Writing requirements.txt")
		result = subprocess.check_output([
				self._pythonExecuteable, 
				"-m", 
				"pip", 
				"freeze", 
				"--path", self.localLibPath.replace('\\', '/') 
				] + additional_settings )
		outputPath.touch()
		outputPath.write_bytes( result )
	
	def InstallRequirements(self,requirementsFilepath = "", additional_settings:List[str] = []):
		self.Log( "Installing requirements.txt")
		try:
			pass
			#something iffy with the built in way of handling it, using our own here.
			# with Path("./requirements.txt").open() as requirementsFile:
			#	for line in requirementsFile:
			#		self.InstallPackage( line, additional_settings=additional_settings )
			subprocess.check_call([
				self._pythonExecuteable, 
				"-m", 
				"pip", 
				"install", 
				"-r", os.path.abspath( Path( requirementsFilepath or self.ownerComp.par.Requirementsfile.eval() ) ),
				"--target", self.localLibPath.replace('\\', '/')] + additional_settings)
		except Exception as e: 
			self.Log("Failed Installing requirements.txt", e)
			return False
		
		return True

	def InstallPackages(self, packagePipNames:Union[List[str], str], additionalSettings:List[str]=[]):
		if isinstance( packagePipNames, str): packagePipNames = tdu.split( packagePipNames )
		for packageName in packagePipNames:
			self.InstallPackage( packageName, additional_settings=additionalSettings)

		 
	def InstallPackage(self, packagePipName:str, additional_settings:List[str] = []):
		self.Log( "Installing Package", packagePipName)

		if packagedPackage := self.unpackPackage( packagePipName):
			self.Log("Found package packaged. Installing from local.")
			additional_settings += ["--find-links", packagedPackage]
			if self.ownerComp.par.Useonlycachedpackage.eval():
				additional_settings += ["--no-index"]
		
		try:
			subprocess.check_call([
				self._pythonExecuteable, 
				"-m", 
				"pip", 
				"install", 
				packagePipName, 
				"--target", self.localLibPath.replace('\\', '/')] + additional_settings)
		except Exception as e: 
			self.Log("Failed Installing Package", packagePipName, e)
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

	def Import_Module( self, module_name:str, pip_name = "", additional_settings:List[str] = []) -> ModuleType:
		return self.ImportModule( module_name, pipPackageName=pip_name, additionalSettings=additional_settings)
		

	def ImportModule(self, moduleName:str, pipPackageName:str = '', additionalSettings:List[str]=[] ):
		_pipPackageName = pipPackageName or moduleName
		if not self.TestModule(moduleName, silent = True): 
			if not self.InstallPackage(_pipPackageName, additional_settings=additionalSettings):
				raise ModuleNotFoundError
		return importlib.import_module(moduleName)

	def PrepareModule(self, moduleName:str, pipPackageName:str = '', additionalSettings:List[str]=[] ):
		if self.TestModule( moduleName, silent=True): return True
		return self.InstallPackage(pipPackageName or moduleName, additional_settings=additionalSettings)
	


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
	
		

