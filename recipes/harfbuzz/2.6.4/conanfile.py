from conans import ConanFile, CMake, tools
import os


class HarfbuzzConan(ConanFile):
    name = "harfbuzz"
    version = "2.6.4"
    description = "HarfBuzz is an OpenType text shaping engine."
    topics = ("conan", "harfbuzz", "opentype", "text", "engine")
    url = "http://github.com/bincrafters/conan-harfbuzz"
    homepage = "http://harfbuzz.org"
    license = "MIT"
    exports = ["FindHarfBuzz.cmake", "LICENSE.md"]
    exports_sources = ["CMakeLists.txt", "source_subfolder.patch"]
    generators = "cmake"
    short_paths = True

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_freetype": [True, False],
        "with_icu": [True, False],
        "with_glib": [True, False],
        "with_gdi": [True, False],
        "with_uniscribe": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_freetype": True,
        "with_icu": False,
        "with_glib": True,
        "with_gdi": True,
        "with_uniscribe": True
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def requirements(self):
        if self.options.with_freetype:
            self.requires.add("freetype/2.10.1")
        if self.options.with_icu:
            self.requires.add("icu/64.2")
        if self.options.with_glib:
            self.requires.add("glib/2.64.0")

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        else:
            del self.options.with_gdi
            del self.options.with_uniscribe

    def source(self):
        source_url = "https://github.com/harfbuzz/harfbuzz"
        sha256 = "8745f0a6e3f233e961fdfec6882a9b03171603eb60ec9169fe8ba58f288fc5fd"
        tools.get("{0}/archive/{1}.tar.gz".format(source_url, self.version), sha256=sha256)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)
        tools.patch(patch_file="source_subfolder.patch")

    def _configure_cmake_compiler_flags(self, cmake):
        flags = []
        compiler = str(self.settings.compiler)
        if compiler in ("clang", "apple-clang"):
            flags.append("-Wno-deprecated-declarations")
        cmake.definitions["CMAKE_C_FLAGS"] = " ".join(flags)
        cmake.definitions["CMAKE_CXX_FLAGS"] = cmake.definitions["CMAKE_C_FLAGS"]

        return cmake

    def _configure_cmake_macos(self, cmake):
        if str(self.settings.os) in ["Macos", "iOS", "watchOS", "tvOS"]:
            cmake.definitions["CMAKE_MACOSX_RPATH"] = True
        return cmake

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake = self._configure_cmake_compiler_flags(cmake)
        cmake = self._configure_cmake_macos(cmake)
        cmake.definitions["HB_HAVE_FREETYPE"] = self.options.with_freetype
        cmake.definitions["HB_BUILD_TESTS"] = False
        cmake.definitions["HB_HAVE_ICU"] = self.options.with_icu
        cmake.definitions["HB_HAVE_GLIB"] = self.options.with_glib

        if self.options.with_icu:
            cmake.definitions["CMAKE_CXX_STANDARD"] = "17"

        if self.settings.os == "Windows":
            cmake.definitions["HB_HAVE_GDI"] = self.options.with_gdi
            cmake.definitions["HB_HAVE_UNISCRIBE"] = self.options.with_uniscribe

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("FindHarfBuzz.cmake")
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "harfbuzz"))
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("m")
        if self.settings.os == "Windows" and not self.options.shared:
            self.cpp_info.system_libs.extend(["dwrite", "rpcrt4", "usp10", "gdi32", "user32"])
        if self.settings.os == "Macos":
            self.cpp_info.frameworks.extend(["CoreFoundation", "CoreGraphics", "CoreText"])