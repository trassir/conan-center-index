from conans import tools
import os
import sys
sys.path.append('../..')
from conanfile_base import BaseHeaderOnly

class xcbprotoConan(BaseHeaderOnly):
    basename = "xcb-proto"
    name = basename.lower()
    version = "1.13"
    tags = ("conan", "xcb-proto")
    description = 'XML-XCB protocol descriptions used by libxcb for the X11 protocol & extensions'
    exports = ["conanfile_base.py", "patches/*.patch"]
    _patches = []

    

    def source(self):
        url = "https://www.x.org/archive/individual/xcb/xcb-proto-1.13.tar.gz"
        tools.get(url, sha256="0698e8f596e4c0dbad71d3dc754d95eb0edbb42df5464e0f782621216fa33ba7")
        for p in self._patches:
            tools.patch(".", "patches/%s" % p)
        extracted_dir = "xcb-proto-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def package_info(self):
        super(xcbprotoConan, self).package_info()
        
        
