from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os
import glob
import shutil


class xcbprotoConan(ConanFile):
    homepage = "https://www.x.org/wiki/"
    license = "X11"
    url = "https://github.com/bincrafters/conan-x11"
    author = "Bincrafters <bincrafters@gmail.com>"
    settings = "os", "arch", "compiler", "build_type"
    _source_subfolder = "source_subfolder"
    generators = "pkg_config"
    _autotools = None

    name = "xcb-proto"
    version = "1.13"
    tags = ("conan", "xcb-proto")
    description = 'XML-XCB protocol descriptions used by libxcb for the X11 protocol & extensions'
    exports = ["conanfile_base.py", "patches/*.patch"]
    _patches = []

    def package_info(self):
        if self.name.startswith('lib') and not self.name in ['libfs']:
            self.cpp_info.names['pkg_config'] = self.name[3:]
        self.cpp_info.builddirs.extend([os.path.join("share", "pkgconfig"),
                                        os.path.join("lib", "pkgconfig")])
        self.cpp_info.includedirs = [path for path in self.cpp_info.includedirs if os.path.isdir(path)]
        self.cpp_info.libdirs = [path for path in self.cpp_info.libdirs if os.path.isdir(path)]

    def package_id(self):
        self.info.header_only()

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        with tools.chdir(self._source_subfolder):
            autotools = self._configure_autotools()
            autotools.install(args=["-j1"])
            
        if self.name.startswith('lib') and not self.name in ['libfs']:
            assert(os.path.isfile(os.path.join(self.package_folder, 'lib', 'pkgconfig', self.name[3:] + '.pc')))

    @property
    def _configure_args(self):
        return []

    def _configure_autotools(self):
        if not self._autotools:
            args = ["--disable-dependency-tracking"]
            args.extend(self._configure_args)
            self._autotools = AutoToolsBuildEnvironment(self)
            self._autotools.configure(args=args, pkg_config_paths=self.build_folder)
        return self._autotools

    def build(self):
        for package in self.deps_cpp_info.deps:
            lib_path = self.deps_cpp_info[package].rootpath
            for dirpath, _, filenames in os.walk(lib_path):
                for filename in filenames:
                    if filename.endswith('.pc'):
                        shutil.copyfile(os.path.join(dirpath, filename), filename)
                        tools.replace_prefix_in_pc_file(filename, lib_path)

        with tools.chdir(self._source_subfolder):
            autotools = self._configure_autotools()
            autotools.make()    

    def source(self):
        url = "https://www.x.org/archive/individual/xcb/xcb-proto-1.13.tar.gz"
        tools.get(url, sha256="0698e8f596e4c0dbad71d3dc754d95eb0edbb42df5464e0f782621216fa33ba7")
        for p in self._patches:
            tools.patch(".", "patches/%s" % p)
        extracted_dir = "xcb-proto-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

        
        
