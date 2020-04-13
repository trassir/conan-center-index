from conans import ConanFile, CMake, tools
import os


class QtWebKitConan(ConanFile):
    name = "qtwebkit"
    version = "dev"
    license = "LGPL-2.0-or-later, LGPL-2.1-or-later, BSD-2-Clause"
    homepage = "https://github.com/qtwebkit/qtwebkit"
    description = "Qt port of WebKit"
    topics = ("qt", "browser-engine", "webkit", "qt5", "qml", "qtwebkit")
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "virtualenv", "txt"
    exports_sources = "../../*"
    no_copy_source = True
    _source_subfolder = "."
    _build_subfolder = "build_subfolder"

    options = {
        "with_bmalloc": [True, False],
        "with_geolocation": [True, False],
        "with_webcrypto": [True, False],
        "with_gstreamer": [True, False],
        "with_libhyphen": [True, False],
        "with_woff2": [True, False]
        }
  
    default_options = {
        "icu:shared": True,

        "libxml2:shared": True,
        "libxslt:shared": True,

        "libjpeg-turbo:shared": False,
        "zlib:shared": False,
        "libpng:shared": False,
        "sqlite3:shared": False,
        "libwebp:shared": False,

        "with_bmalloc": True,

        "with_geolocation": False,
        "with_webcrypto": False,
        "with_gstreamer": False,

        "with_libhyphen": False,
        "with_woff2": False,

        "qt:qtdeclarative": True,
        "qt:qtlocation": True,
        "qt:qtsensors": True,
	"qt:qtquickcontrols": True,
	"qt:qtquickcontrols2": True,
	"qt:qtwebchannel": True,

        "qt:qtsvg": True,
        "qt:qtx11extras": True,
        "qt:qtimageformats": True,
        "qt:qtscript": True,

        "qt:with_glib": False,
        "qt:with_harfbuzz": False,
        "qt:with_pcre2": False,
        "qt:with_mysql": False,
        "qt:with_sdl2": False,
        "qt:with_zstd": False
    }

    requires = (
        "qt/5.14.0@bincrafters/stable",
        "openssl/1.1.1d",
        "libjpeg-turbo/2.0.4",
        "libpng/1.6.37",
        "libwebp/1.1.0",
        "sqlite3/3.31.0",
        "icu/64.2",
        "libxml2/2.9.9",
        "libxslt/1.1.33",
        "zlib/1.2.11"
    )

    def build_requirements(self):
        pass

    def requirements(self):
        if self.options["with_webcrypto"]:
            self.requires("libgcrypt/1.8.4@bincrafters/stable")

        if self.options["with_gstreamer"]:
            self.requires["gstreamer/1.16.0@bincrafters/stable"]

        if self.options["with_libhyphen"]:
            pass # TODO add dependency when somebody will write receipt for libhyphen

        if self.options["with_woff2"]:
            pass # TODO wait until https://github.com/qtwebkit/conan-woff2 will be deployed on bintray

    def source(self):
        # use git clone for receiving sources 
        # git clone https://github.com/qtwebkit/qtwebkit.git
        pass

    def _configure_cmake(self):
        cmake = CMake(self)

        cmake.definitions["PORT"] = "Qt"

        # TODO on linux we should check kernel version. On kernels < 3.4 bmalloc cannot be compiled
        if not self.options["with_bmalloc"]:
            cmake.definitions["USE_SYSTEM_MALLOC"] = "ON"
        if not self.options["with_geolocation"]:
            # TODO check if QtLocation module was built
            cmake.definitions["ENABLE_GEOLOCATION"] = "OFF"             
        if not self.options["with_webcrypto"]:
            cmake.definitions["ENABLE_WEB_CRYPTO"] = "OFF"
        if not self.options["with_gstreamer"]:
            cmake.definitions["USE_GSTREAMER"] = "OFF"
        if not self.options["with_libhyphen"]:
            cmake.definitions["USE_LIBHYPHEN"] = "OFF"
        if not self.options["with_woff2"]:
            cmake.definitions["USE_WOFF2"] = "OFF"

        cmake.definitions["QT_CONAN_DIR"] = self.build_folder

        qt_dir = self.deps_cpp_info["qt"]
        cmake.definitions["Qt5_DIR"] = os.path.join(qt_dir.libdirs[0], "cmake", "Qt5")

        cmake.configure(build_folder=self._build_subfolder, source_folder=self._source_subfolder)

        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()
        cmake.install()

    def package(self):
        pass

    def package_info(self):
        pass
