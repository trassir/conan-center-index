from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanInvalidConfiguration
import os


class PkgConfigConan(ConanFile):
    name = "pkg-config_installer"
    version = "0.29.2"
    description = "The pkg-config program is used to retrieve information about installed libraries in the system"
    topics = ("conan", "pkg-config", "package config")
    url = "https://github.com/bincrafters/conan-pkg-config_installer"
    homepage = "https://www.freedesktop.org/wiki/Software/pkg-config/"
    license = "GPL-2.0-or-later"
    exports = ["LICENSE.md"]
    settings = "os_build", "arch_build", "compiler"
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    @property
    def _is_mingw_windows(self):
        return self.settings.os_build == "Windows" and self.settings.compiler == "gcc" and os.name == "nt"

    def build_requirements(self):
        if self._is_mingw_windows and "CONAN_BASH_PATH" not in os.environ:
            self.build_requires("msys2/20190524")

    def source(self):
        source_url = "https://pkg-config.freedesktop.org/releases/pkg-config-%s.tar.gz" % self.version
        tools.get(source_url,
                  sha256="6fc69c01688c9458a57eb9a1664c9aba372ccda420a02bf4429fe610e7e7d591")
        os.rename("pkg-config-" + self.version, self._source_subfolder)

    def build(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("builds with Visual Studio aren't currently supported, "
                                            "use MinGW instead to build for Windows")
        with tools.chdir(self._source_subfolder):
            # http://www.linuxfromscratch.org/lfs/view/systemd/chapter06/pkg-config.html
            args = ["--with-internal-glib", "--disable-host-tool"]
            env_build = AutoToolsBuildEnvironment(self, self._is_mingw_windows)
            env_build.configure(args=args)
            env_build.make()
            env_build.install()

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        if self._is_mingw_windows:
            package_folder = tools.unix_path(os.path.join(self.package_folder, "bin"))
            tools.run_in_windows_bash(self, "cp $(which libwinpthread-1.dll) {}".format(package_folder))

    def package_id(self):
        del self.info.settings.compiler

    def package_info(self):
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
