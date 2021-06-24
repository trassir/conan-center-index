from conans import ConanFile, CMake, tools
import os
import shutil

class AxtlsConan(ConanFile):
    name = "axtls"
    license = "GPL-3.0"
    author = "Vladimir Looze <looze@dssl.ru>"
    url = "example.com"
    description = "The axTLS embedded SSL project is a library designed for platforms with small memory requirements"
    topics = ("ssl", "crypto", "openssl")
    settings = "os", "compiler", "build_type", "arch"
    options = {}
    default_options = ""
    exports_sources = [
        "patches/**"
    ]

    @property
    def _source_subfolder(self):
        return os.path.join(self.source_folder, "axtls-code")

    def _make(self, args):
        self.run("make -C {source} {args}".format(source = self._source_subfolder, args = args))

    def _configure(self):
        prefix = tools.unix_path(self.package_folder)

        shutil.copyfile(
            os.path.join(self._source_subfolder, "config", "linuxconfig"),
            os.path.join(self._source_subfolder, "config", ".config"))

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

        if self.version in self.conan_data["patches"]:
            for patch in self.conan_data["patches"][self.version]:
                tools.patch(base_path = self._source_subfolder, **patch)

    def build(self):
        self._configure()
        self._make("-j%d" % tools.cpu_count())

    def package(self):
        self._make("install")

    def package_info(self):
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)
        self.cpp_info.libs = ["axtls"]
