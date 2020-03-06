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
            main(['install', "mercurial"])

    def source(self):
        print(json.dumps(dict(os.environ), indent=4))
        self.run("hg clone {url} {folder}".format(url = self.url, folder = self._source_subfolder))
        with tools.chdir(self._source_subfolder):
            self.run("hg up -C -r {rev}".format(rev = self.version))

    def build(self):
        with tools.chdir(self._source_subfolder):
            self.run("python2 build.py prepare")
            if tools.is_apple_os(self.settings.os):
                self.run(("python2 configure.py"
                      + " --deployment-target=10.12"
                      + " -b {prefix}/bin"
                      + " -d {prefix}/lib/python2.7/site-packages"
                      + " -e {prefix}/include/python2.7"
                      + " -v {prefix}/share/sip/"
                ).format(
                    prefix = tools.unix_path(self.package_folder)
                ))
            self.run("make -j%d" % tools.cpu_count())

    def package(self):
        with tools.chdir(self._source_subfolder):
            self.run("make install")
        if tools.is_apple_os(self.settings.os):
            with tools.chdir(self.package_folder):
                self.run("mv lib/python2.7/site-packages lib/python2.7/lib-dynload")

    def package_info(self):
        self.cpp_info.bindirs = ["bin"]
        self.cpp_info.includedirs = ["include/python2.7"]
