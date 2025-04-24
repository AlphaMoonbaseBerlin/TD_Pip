
'''Info Header Start
Name : extTDConda
Author : Wieland PlusPlusOne@AMB-ZEPH15
Saveorigin : TD_Pip.toe
Saveversion : 2023.12000
Info Header End'''



from pathlib import Path
import subprocess
from platform import python_version
import sys
import os
from functools import lru_cache
import json
import importlib
from copy import copy

class extTDConda:
	"""
	extTDConda description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		
		self.log = self.ownerComp.op("logger").Log
		class Mount(object):
			def __init__(mountSelf, clearModules = False):
				mountSelf.clearModules = clearModules
				mountSelf.path = None
				mountSelf.modules = None
				mountSelf.pythonpath = ""
				pass

			def __enter__(mountSelf):
				if mountSelf.clearModules:
					mountSelf.modules = sys.modules.copy()
					sys.modules = {}
				mountSelf.path = sys.path.copy()
				mountSelf.environ = copy( os.environ )

				sys.path.insert(
					0,
					self.libPathString
				)
				
				os.environ["PYTHONPATH"] = self.libPathString
				for line in self.activationScript.split("\n"):
					if not line.startswith("@SET"): continue 
					call, target = line.split(" ", maxsplit=1)
					envName, envValue = target.strip('"').split("=")
					os.environ[envName] = envValue


			def __exit__(mountSelf, type, value, traceback):
				if mountSelf.modules:
					sys.modules = mountSelf.modules
				sys.path = mountSelf.path
				os.environ = mountSelf.environ
		self.Mount = Mount

		class EnvShell(object):
			def __init__(contextSelf):
				contextSelf.shellProcess = None
				
			def __enter__(contextSelf):
				self.log("Entering Shell Context")
				contextSelf.shellProcess = self.SpawnEnvShell()
				self.log("Returning shellcontext")
				return contextSelf

			def __exit__(contextSelf, type, value, traceback):
				self.log("Exiting EnvShell")
				# Without this, the command is not getting executed, even though it is getting flushed.
				contextSelf.shellProcess.communicate()				
				contextSelf.shellProcess.terminate()
				contextSelf.shellProcess.wait()

			def Execute(contextSelf, command):
				self.log("Exeuting Command", command)
				contextSelf.shellProcess.Write(command)
				

		self.EnvShell = EnvShell
		if self.ownerComp.par.Autosetup.eval():
			self.Setup()

	@property
	def condaEnv(self):
		Path( "TDImportCache/CondaTemp" ).mkdir(exist_ok=True, parents=True)
		Path( "TDImportCache/CondaHome" ).mkdir(exist_ok=True, parents=True)
		return {
			**os.environ,
			"PATH" : ";".join(
				os.environ["PATH"].split(";") + [
					str(self.condaDirectory.absolute()),
					str(Path(self.condaDirectory, "Scripts").absolute())
				]),
			"TEMP" 	: str(Path( "TDImportCache/CondaTemp" ).absolute()),
			"TMP" 	: str(Path( "TDImportCache/CondaTemp" ).absolute()),
			"USERPROFILE" 	: str(Path( "TDImportCache/CondaHome" ).absolute()),
			"LOCALAPPDATA"  : str(Path( "TDImportCache/LocalAppData" ).absolute())
		}

	@property
	def libPathString(self):
		return str( Path(self.envDirectory, "Lib/site-packages").absolute() )

	@property
	def condaDirectory(self):
		return Path(self.ownerComp.par.Condafolder.eval())

	@property
	def envFolder(self):
		return Path(self.ownerComp.par.Envfolder.eval())

	@property
	def envDirectory(self):
		return Path(self.envFolder, self.ownerComp.par.Envname.eval())
	
	@property
	def condaExe(self):
		return Path(self.condaDirectory, "conda.exe")
	
	@property
	def shell(self):
		if sys.platform == "win32":
			return "cmd.exe"
		elif sys.platform == "darwin":
			return "bash"

	def Setup(self):
		if sys.platform == "darwin":
			raise NotImplemented("MAC OS is currently not supported.")
		
		if (" " in str(self.condaDirectory.absolute()) or 
			" " in str(self.envDirectory.absolute())):
			raise Exception("Invalid path. The path contains spaces.")
		
		if not self.condaDirectory.is_dir(): self.downloadAndUnpack()
		
		if not self.envDirectory.is_dir(): self.createEnv()
		self.setVSCodeSettings()

	def setVSCodeSettings(self):
		self.log("Setting up .vscode file.")
		launchFile = Path( ".vscode/settings.json")
		if not launchFile.is_file():
			launchFile.parent.mkdir(parents=True, exist_ok=True)
			launchFile.touch()
			launchFile.write_text( "{}" )

		with launchFile.open("r+") as launchJson:
			launchDict:dict = json.load( launchJson )

			launchDict.setdefault(
				"python.analysis.extraPaths", 
				[]
				)
			for potentialPath in [
				str(Path(self.envDirectory, "Lib/site-packages"))
			]:
				if potentialPath in launchDict["python.analysis.extraPaths"]: continue
				launchDict["python.analysis.extraPaths"].append( potentialPath )
			launchFile.write_text( json.dumps( launchDict, indent=4 ) )
		return


	@property
	def activationScript(self):
		return self._activationScript( self.envDirectory )
	
	@lru_cache(maxsize=1)
	def _activationScript(self, env):
		# with open(self.condaCommand([f"shell.{self.shell}", "activate", env])) as activationScript:
		self.log("Fetching activationscript.")
		with open(self.condaCommand([f"shell.{self.shell}", "activate", env])) as activationScript:
			result = activationScript.read()
			self.log("Got Activationscript", result)
			return result
	

	def condaCommand(self, commands) -> str:
		self.log("Running Condacommands", commands)
		return subprocess.check_output(
			[self.condaExe] + commands,
			env = self.condaEnv
		).decode()

	def SpawnEnvShell(self):
		shellProcess = subprocess.Popen(
				[self.shell], 
				env = self.condaEnv,
				stdin = subprocess.PIPE,
				text = True
				# stdout=subprocess.PIPE
				)
		self.log("Spawned shellProcess")
		def Write(command:str):
			if isinstance(command, str): command = command.split(" ")
			shellProcess.stdin.write( " ".join(command) + "\n" )
			shellProcess.stdin.flush()
			
		setattr( shellProcess, "Write", Write)
		shellProcess.Write( self.activationScript )
		self.log("Wrote activationScript to shell")
		return shellProcess

	def downloadAndUnpack(self):
		# Downlading 
		self.log("Downloadin Conda Installer")
		condaInstaller:Path 				= self.ownerComp.op("condaDependency").GetRemoteFilepath()
		self.log("Running Installer")
		#self.condaDirectory.mkdir(exist_ok=True, parents=True)

		try:
			#if self.ownerComp.par.Notifiyinstall:
			#	ui.messageBox("Installing Conda",
			#	  f"""Instaling conda in to the project-repository under the path {self.condaDirectory.absolute()}.""")
			subprocess.call([
				condaInstaller,
				"/S", 
				"/V"
				"/InstallationType=JustMe",
				"/AddToPath=0",
				"/RegisterPython=0",
				"/NoRegistry=1", 
				"/NoScripts=1", 
				"/NoShortcuts=1",
				f'/D={self.condaDirectory.absolute()}'
			])
			# result = installProcess.wait()
		#	
		except subprocess.CalledProcessError as grepexc:                                                                                                   
			self.log("error code", grepexc.returncode, grepexc.output)
		self.log("Installed Conda")
		os.rename(
			Path(self.condaDirectory, "_conda.exe"),
			Path(self.condaDirectory, "conda.exe")
		)
		self.log("Renamed _conda.exe")

	def createEnv(self):
		# self.envDirectory.mkdir(exist_ok=True, parents=True)
		self.log("Trying to create the environment.")
		createResult = self.condaCommand([
			"create", "-y",
			"--no-shortcuts",
			"-k",
			"-p", f'{self.envDirectory.absolute()}',
			# f"python={'.'.join(python_version().split('.')[0:2])}"
			f"python={self.ownerComp.par.Pythonversion.eval()}"
		] 
		+ tdu.split( self.ownerComp.par.Setuppackages.eval()))
		self.log("Created the env I hope.")

	def Reset(self):
		self.condaCommand("config --remove-key proxy_servers".split(" "))
		self.condaCommand("clean --source-cache".split(" "))

	def Info(self):
		self.condaCommand(["info"])

	def InstallPackage(self, package, installer = "conda"):
		with self.EnvShell() as shell:
			shell.Execute([installer,"install", package])

	def TestModule(self, module:str) -> bool:
		with self.Mount():
			self.log("Testing for module", module)
			try:
				foundModule = importlib.util.find_spec( module )	
			except ModuleNotFoundError as exc:
				self.log( "Module not Found Exception!", exc )
				return False
			
			if foundModule is None:
				self.log( "Module does not exist", module )
				return False
				
			return True
		
	def PrepareModule(self, moduleName, packageName = "", installer = "conda"):
		if self.TestModule( moduleName ): return
		self.InstallPackage( packageName or moduleName, installer=installer)

	def Run(self, filepath):
		shell = self.SpawnEnvShell()
		shell.Write(["python", str(filepath)])
		return shell