from conans import ConanFile, tools, Meson, VisualStudioBuildEnvironment
import glob
import os
import shutil


class GStreamerConan(ConanFile):
    name = "gst-build"
    version = "1.17.1"
    description = "GStreamer is a development framework for creating applications like media players, video editors, streaming media broadcasters and so on"
    topics = ("conan", "gstreamer", "multimedia", "video", "audio", "broadcasting", "framework", "media")
    url = "https://github.com/GStreamer/gst-build/"
    homepage = "https://gstreamer.freedesktop.org/"
    license = "GPL-2.0-only"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {"shared": True, "fPIC": True, "glib:with_pcre": False, "glib:with_elf": False, "glib:with_selinux": False, "glib:with_mount": False, "*:shared": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    exports_sources = ["patches/*.diff"]

    requires = ("glib/2.64.0@bincrafters/stable",
                "libdrm/2.4.100",
                "libva/1.5.1",
                "libffi/3.2.1@bincrafters/stable",
                "mesa/19.3.1",
                "openh264/1.7.0")

    generators = "pkg_config"

    def build_requirements(self):
        self.build_requires("meson/0.53.2")

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def build_requirements(self):
        self.build_requires("meson/0.53.2")
    #    if not tools.which("pkg-config") or self.settings.os == "Windows":
    #        self.build_requires("pkg-config_installer/0.29.2@bincrafters/stable")
    #    self.build_requires("bison/3.5.3")
    #    self.build_requires("flex/2.6.4")


    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("%s-%s" % (self.name, self.version), self._source_subfolder)

    def _apply_patches(self):
        for filename in sorted(glob.glob("patches/*.diff")):
            self.output.info('applying patch "%s"' % filename)
            tools.patch(base_path=self._source_subfolder, patch_file=filename)

    def _configure_meson(self):
        meson = Meson(self)
        defs = dict()

        defs["ges"] = "disabled"
        defs["vaapi"] = "disabled"
        defs["examples"] = "disabled"
        defs["tests"] = "disabled"
        defs["introspection"] = "disabled"
        defs["gtk_doc"] = "disabled"
        defs["doc"] = "disabled"
        defs["omx"] = "disabled"
        defs["python"] = "disabled"
        defs["gst-examples"] = "disabled"
        #defs["libav"] = "disabled"
        meson.configure(build_folder=self._build_subfolder,
                        source_folder=self._source_subfolder,
                        defs=defs)
        return meson

    def _copy_pkg_config(self, name):
        root = self.deps_cpp_info[name].rootpath
        pc_dir = os.path.join(root, 'lib', 'pkgconfig')
        pc_files = glob.glob('%s/*.pc' % pc_dir)
        if not pc_files:  # zlib store .pc in root
            pc_files = glob.glob('%s/*.pc' % root)
        for pc_name in pc_files:
            new_pc = os.path.basename(pc_name)
            self.output.warn('copy .pc file %s' % os.path.basename(pc_name))
            shutil.copy(pc_name, new_pc)
            prefix = tools.unix_path(root) if self.settings.os == 'Windows' else root
            tools.replace_prefix_in_pc_file(new_pc, prefix)

    def build(self):
        #self._apply_patches()
        self._copy_pkg_config("glib")
        #with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
        meson = self._configure_meson()
        tools.replace_in_file(os.path.join(self._build_subfolder, "..", self._source_subfolder, "subprojects","gstreamer", "meson.build"), "cdata.set('HAVE_UNWIND', 1)", "#cdata.set('HAVE_UNWIND', 1)")
        tools.replace_in_file(os.path.join(self._build_subfolder, "..", self._source_subfolder, "subprojects","gst-devtools", "validate", "gst", "validate", "gst-validate-scenario.c"), "#if !GLIB_CHECK_VERSION(2,54,0)", "#if GLIB_CHECK_VERSION(2,54,0)")
        meson.build()

        with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
            meson = self._configure_meson()
            meson.build()

    def _fix_library_names(self, path):
        # regression in 1.16
        if self.settings.compiler == "Visual Studio":
            with tools.chdir(path):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info("rename %s into %s" % (filename_old, filename_new))
                    shutil.move(filename_old, filename_new)


    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
            meson = self._configure_meson()
            meson.install()

        # self._fix_library_names(os.path.join(self.package_folder, "lib"))
        # self._fix_library_names(os.path.join(self.package_folder, "lib", "gstreamer-1.0"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        # self.cpp_info.includedirs = [os.path.join("include", "gstreamer-1.0")]

        # gst_plugin_path = os.path.join(self.package_folder, "lib", "gstreamer-1.0")
        # if self.options.shared:
        #     self.output.info("Appending GST_PLUGIN_PATH env var : %s" % gst_plugin_path)
        #     self.env_info.GST_PLUGIN_PATH.append(gst_plugin_path)
        # else:
        #     self.cpp_info.libdirs.append(gst_plugin_path)
        #     self.cpp_info.libs.extend(["gstcoreelements",
        #                                "gstcoretracers"])
        # self.cpp_info.libs.extend(["gstreamer-1.0", "gstbase-1.0", "gstcontroller-1.0", "gstnet-1.0"])

        # if self.settings.os == "Linux":
        #     self.cpp_info.libs.append("dl")
        # elif self.settings.os == "Windows":
        #     self.cpp_info.libs.append("ws2_32")
        # if not self.options.shared:
        #     self.cpp_info.defines.append("GST_STATIC_COMPILATION")
        # gstreamer_root = self.package_folder
        # self.output.info("Creating GSTREAMER_ROOT env var : %s" % gstreamer_root)
        # self.env_info.GSTREAMER_ROOT = gstreamer_root
        # gst_plugin_scanner = "gst-plugin-scanner.exe" if self.settings.os == "Windows" else "gst-plugin-scanner"
        # gst_plugin_scanner = os.path.join(self.package_folder, "bin", "gstreamer-1.0", gst_plugin_scanner)
        # self.output.info("Creating GST_PLUGIN_SCANNER env var : %s" % gst_plugin_scanner)
        # self.env_info.GST_PLUGIN_SCANNER = gst_plugin_scanner
        # if self.settings.arch == "x86":
        #     self.output.info("Creating GSTREAMER_ROOT_X86 env var : %s" % gstreamer_root)
        #     self.env_info.GSTREAMER_ROOT_X86 = gstreamer_root
        # elif self.settings.arch == "x86_64":
        #     self.output.info("Creating GSTREAMER_ROOT_X86_64 env var : %s" % gstreamer_root)
        #     self.env_info.GSTREAMER_ROOT_X86_64 = gstreamer_root

