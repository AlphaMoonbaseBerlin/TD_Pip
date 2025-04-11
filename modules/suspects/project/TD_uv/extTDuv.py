"""Info Header Start
Name : extTDuv
Author : Wieland PlusPlusOne@AMB-ZEPH15
Saveorigin : TD_Pip.toe
Saveversion : 2023.12000
Info Header End"""

import importlib
import os
import platform
import subprocess
import sys
import zipfile
from copy import copy
from pathlib import Path
from types import ModuleType


def uv_required(function):
    def wrapper(self, *args, **kwargs):
        if not self.check_uv:
            self.setup_uv()
        return function(self, *args, **kwargs)

    return wrapper


def project_required(function):
    def wrapper(self, *args, **kwargs):
        if not self.check_project:
            self.setup_project()
        return function(self, *args, **kwargs)

    return wrapper


class extTDuv:
    """
    extTDuv description
    """

    def __init__(self, owner_comp):
        # The component to which this extension is attached
        self.ownerComp = owner_comp
        self.Log = self.ownerComp.op("logger").Log

        class Mount:
            def __init__(self, clear_modules=False):
                self.clear_modules = clear_modules
                pass

            def __enter__(self):
                if self.clear_modules:
                    self.modules = sys.modules.copy()
                    sys.modules = {}
                self.mountEnv()

            def __exit__(self, type, value, traceback):
                self.unmountEnv()
                if self.clear_modules:
                    sys.modules = self.modules

        self.Mount = Mount

        class MountModule:
            def __init__(
                self,
                module_name: str,
                pip_package_name: str = "",
                additional_settings=list,
                clear_modules=False,
            ):
                self.clearModules = clear_modules
                self.moduleName = module_name
                self.pipPackagName = pip_package_name
                self.additionalSettings = additional_settings
                pass

            def __enter__(self):
                if self.clearModules:
                    self.modules = sys.modules.copy()
                    sys.modules = {}
                self.mountEnv()
                return self.import_module(
                    self.moduleName,
                    pip_package_name=self.pipPackagName,
                    additional_settings=self.additionalSettings,
                )

            def __exit__(mountSelf, type, value, traceback):
                self.unmount_env()
                if mountSelf.clearModules:
                    sys.modules = mountSelf.modules

        self.MountModule = MountModule

    def uv_download_target(self):
        if sys.platform == "win32":
            return "uv-x86_64-pc-windows-msvc.zip"
        if sys.platform == "darwin" and platform.processor() == "i386":
            return "uv-x86_64-apple-darwin.tar.gz"
        if sys.platform == "dawrin" and platform.processor() == "arm":
            return "uv-aarch64-apple-darwin.tar.gz"

        raise NotImplementedError(f"{sys.platform} OS Not Supported.")

    @property
    def check_uv(self):
        result = self.run_uv_command(["version", "-q"])
        return result == 0

    @property
    def check_project(self):
        return Path("pyproject.toml").is_file()

    @property
    def uv_folder(self):
        return str(Path("TDImportCache/uv").absolute())

    @property
    def local_lib_path(self):
        return ".venv/Lib/site-packages"

    def mount_env(self):
        self._pathCopy = copy(sys.path)
        self._envCopy = copy(os.environ)
        sys.path.insert(0, self.local_lib_path)
        os.environ["PYTHONPATH"] = self.local_lib_path

    def unmount_env(self):
        sys.path = self._pathCopy
        os.environ = self._envCopy

    def run_uv_command(self, commands):
        if isinstance(commands, str):
            commands = commands.split(" ")

        return subprocess.call(
            ["uv", *commands],
            env={**os.environ, "PATH": ";".join([self.uv_folder, *os.environ["PATH"].split(";")])},
            shell=True,
        )

    def setup_uv(self):
        download_uv_zip = self.ownerComp.op("uvDependency").GetRemoteFilepath()
        if Path(download_uv_zip).suffix == "gz":
            raise NotImplementedError(
                "gz files not implemented. Its like Matroschka and I am to lazy rn to take care of that..."
            )
        # Like, srsly, someone pls.
        with zipfile.ZipFile(download_uv_zip, "r") as zip_ref:
            zip_ref.extractall(self.uv_folder)

    @uv_required
    def setup_project(self):
        return (
            self.run_uv_command(f"init --python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}") == 0
        )

    @uv_required
    @project_required
    def install_package(self, packagePipName: str, additional_settings: list[str] = []):
        return self.run_uv_command(["add", packagePipName] + additional_settings) == 0

    @project_required
    def test_module(self, module: str, silent: bool = False):
        """
        Check if a given moduel is alread installed.
        Note, this does not test for a package but the module itself.
        """
        self.Log("Testing for package", module)
        with self.Mount():
            try:
                found_module: ModuleType = importlib.util.find_spec(module)
            except ModuleNotFoundError as exc:
                self.Log("Module not Found Exception!", exc)
                return False
            if found_module is None:
                self.Log("Package does not exist", module)
                if not silent:
                    ui.messageBox("Does not exist", "The package is not installed")
                return False

            if not silent:
                ui.messageBox("Does exist", "The package is installed")
            return True

    @uv_required
    @project_required
    def import_module(
        self,
        name: str,
        pip_package_name: str = "",
        additional_settings: list[str] = list,
    ):
        """
        Installs the module if not already installed and returns the module.
        Use instead of the default import method.
        Deprecatd. use PrepareModule instead for proper code completion.
        """
        _pip_package_name = pip_package_name or name

        if not self.test_module(
            name,
            silent=True,
        ) and not self.install_package(
            _pip_package_name,
            additional_settings=additional_settings,
        ):
            raise ModuleNotFoundError

        return importlib.import_module(name)
