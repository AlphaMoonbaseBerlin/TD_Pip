# TD_PyPain - Python Package Installer
A collection of components to handle virtual 3nvironments and external python packages from withing touchdesigner with a hands-off approach 

# Components
## TD_PIP
TD-Pip implements pip in a complete native way without any external dependencies. This means it uses the touchdesigner native python interpreter and requires not manual instalation or setting of external paths.

## TD_UV
Implements the UV-PackageManager https://github.com/astral-sh/uv
No manual isnatllation required but it does either use the gobal installed UV or downloads and prepares a UV-Installation on demand.

## TD_CONDA
Hands off installer for conda. Can be used to install and run subprocesses that require many dependencies. In genera the heaviest solution in this repo.

### DOCS
If Auto Setup is set to true, the comp will Setup the first time it is initialised. 
The setupprcoess 
- Downloads the latest miniconda-version and unpacks it in to the specified folder.
- Creates a conda environment in the specified folder und the specified name.
- Creates a refference to the ENV-Sitepackagesfolder in the .vscode/settings.json
- 
This process can take a while, so wait a moment.

To use the componnt in TD there is a pretty streight forward API.
You ca use it in two ways: Launch subprocesses or install and import python modules.

#### Installing and Importing modules
To install a module if ot already existing use
```op("TD_Conda").InstallPackage( packageName, installer = "conda"|"pip")```
to check if a module is already installed, if not nstall it, use 
```op("TD_Conda").PrepareModule( moduleName, packageName = moduleName, installer = "conda"|"pip")```

To import the module you need to mount the env. This keeps TD_Conda from poluting other potentia env or TD_Internal modules.
When passing clearModules = False, this will remove the already imported modules from the importCache, resulting in a fresh new import. This is reset after the contextmanager is left. 
This can bue usefull when working with modules that are relying on specifric version of numpy or openCV.
```python
with op("TD_Conda").Mount( clearModules = False):
  import moduleName
```

Example:
```python
op("TD_Conda").PrepareModule("qrcode")
with op("TD_Conda").Mount():
  import qrcode
```

#### Running scripts as subprocesses
If you have a script that is terminated in the same action, you can use another contextManager.
```python
with op("TD_Conda").EnvShell() as envShell:
  envShell.Execute("aimg videogen --start-image rocket.png")
```

If you want to run the process as a damon, use the run-method.
```python
op("TD_Conda").InstallPackage("cuda")
op("TD_Conda").InstallPackage(
       "whisper-live", 
        installer = "pip")
whisperProcess = op("TD_Conda").Run(
        "run_server.py"
    )
```

or, going bare-metal, the spawnMethod
```python
process = op("TD_Conda").SpawnEnvShell()
process.Write("conda install cuda")
process.Write("pip install whisper-live")
process.Write('pip install "numpy==1.26.4 --force')
process.Write("python run_server.py")
```

You can now invoke other commands using the execute function. (Not the best example, but whatever).


