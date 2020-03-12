from conans import ConanFile, CMake, tools
import os
import shutil

class AxtlsConan(ConanFile):
    name = "axtls"
    version = "1.5.3"
    license = "GPL-3.0"
    author = "Vladimir Looze <looze@dssl.ru>"
    url = "example.com"
    description = "The axTLS embedded SSL project is a library designed for platforms with small memory requirements"
    topics = ("ssl", "crypto", "openssl")
    settings = "os", "compiler", "build_type", "arch"
    options = {}
    default_options = ""
    export_sources = [
        "osx10_compat.patch",
        "SNI.patch",
    ]
    _source_subfolder = "axtls-code"

    def _make(self, args):
        self.run("make -C {source} {args}".format(source = self._source_subfolder, args = args))

    def _configure(self):
        prefix = tools.unix_path(self.package_folder)

        shutil.copyfile(
            os.path.join(self._source_subfolder,"config", "linuxconfig"),
            os.path.join(self._source_subfolder,"config", ".config"))

        options = [
            "CONFIG_SSL_SNI=y",
        ]

        tools.replace_in_file(os.path.join(self._source_subfolder, "config", ".config"),
            "PREFIX=\"/usr/local\"",
            "PREFIX=\"{prefix}\"\n{options}".format(prefix = prefix, options = "\n".join(options)))

        if tools.is_apple_os(self.settings.os):
            tools.replace_in_file(os.path.join(self._source_subfolder, "config", "makefile.conf"),
                                  "LDSHARED = -shared",
                                  "LDSHARED = -dynamiclib")
        self._make("oldconfig")

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        # download sources
        tools.get(**self.conan_data["sources"][self.version])

        # check recipe conistency
        tools.check_with_algorithm_sum("sha1", "osx10_compat.patch", "e211d33b1198e932ac251a811b783583ce1ec278")
        tools.check_with_algorithm_sum("sha1", "SNI.patch",          "13ec4af9bab09839a4cd6fc0d7c935749cba04f9")

        # apply patches
        tools.patch(base_path = self._source_subfolder, patch_file = "SNI.patch", strip = 1)

        if tools.is_apple_os(self.settings.os):
            tools.patch(base_path = self._source_subfolder, patch_file = "osx10_compat.patch", strip = 1)

    def build(self):
        self._configure()
        self._make("-j%d" % tools.cpu_count())

    def package(self):
        self._make("install")

    def package_info(self):
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)
        self.cpp_info.libs = ["axtls"]
