import os
import stat
import glob
import shutil
import json
from conans import ConanFile, AutoToolsBuildEnvironment, tools

_openSSL = "OpenSSL"

# based on https://github.com/conan-community/conan-ncurses/blob/stable/6.1/conanfile.py
class SipConan(ConanFile):
    name = "sip"
    version = "4.19.3"
    license = "GPL2"
    homepage = "https://www.riverbankcomputing.com/software/sip/intro"
    description = "SIP comprises a code generator and a Python module"
    url = "https://www.riverbankcomputing.com/hg/sip"
    settings = "os", "compiler", "build_type", "arch"
    options = {}
    default_options = {}
    exports = ""
    _source_subfolder = "source_subfolder"

    def system_requirements(self):
        import pip
        if hasattr(pip, "main"):
            pip.main(["install", "mercurial"])
        else:
            from pip._internal import main
            main.main(['install', "mercurial"])
        if tools.os_info.is_windows:
            installer = tools.SystemPackageTool(tool=tools.ChocolateyTool())
            installer.install("winflexbison3")
        if tools.os_info.is_macos:
            installer = tools.SystemPackageTool(tool=tools.BrewTool())
            installer.install("bison")
            installer.install("flex")

    def source(self):
        self.run("hg clone {url} {folder}".format(url = self.url, folder = self._source_subfolder))
        with tools.chdir(self._source_subfolder):
            self.run("hg up -C -r {rev}".format(rev = self.version))

    def build(self):
        with tools.chdir(self._source_subfolder):
            self.run("python build.py prepare")
            if tools.os_info.is_macos:
                self.run(("python configure.py"
                      + " --deployment-target=10.12"
                      + " -b {prefix}/bin"
                      + " -d {prefix}/lib/python2.7/site-packages"
                      + " -e {prefix}/include/python2.7"
                      + " -v {prefix}/share/sip/"
                ).format(
                    prefix = tools.unix_path(self.package_folder)
                ))
                self.run("make -j%d" % tools.cpu_count())
            if tools.os_info.is_windows:
                self.run(("python configure.py"
                      + " -b {prefix}/bin"
                      + " -d {prefix}/lib/python2.7/site-packages"
                      + " -e {prefix}/include/python2.7"
                      + " -v {prefix}/share/sip/"
                ).format(
                    prefix = self.package_folder
                ))
                # cannot be bothered to fix build of siplib which we don't use anyway
                with tools.chdir("sipgen"):
                    self.run("nmake")

    def package(self):
        if tools.os_info.is_macos:
            with tools.chdir(self._source_subfolder):
                self.run("make install")
            with tools.chdir(self.package_folder):
                self.run("mv lib/python2.7/site-packages lib/python2.7/lib-dynload")
        if tools.os_info.is_windows:
            with tools.chdir(self._source_subfolder):
                # partial execution of installation step due to siplib not being built
                with tools.chdir("sipgen"):
                    self.run("nmake install")
                with tools.chdir("siplib"):
                    self.run("mkdir {prefix}\\include\\python2.7\\".format(prefix = self.package_folder))
                    self.run("copy /y sip.h {prefix}\\include\\python2.7\\sip.h".format(prefix = self.package_folder))

    def package_info(self):
        self.cpp_info.bindirs = ["bin"]
        self.cpp_info.includedirs = ["include/python2.7"]
