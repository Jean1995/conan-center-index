from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import get, copy, rmdir, patch, apply_conandata_patches, export_conandata_patches
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.scm import Version
import os

required_conan_version = ">=1.43.0"


class CubicInterpolationConan(ConanFile):
    name = "cubicinterpolation"
    homepage = "https://github.com/MaxSac/cubic_interpolation"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Leightweight interpolation library based on boost and eigen."
    topics = ("interpolation", "splines", "cubic", "bicubic", "boost", "eigen3")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    _cmake = None

    @property
    def _is_msvc(self):
        return str(self.settings.compiler) in ["Visual Studio", "msvc"]

    def export_sources(self):
        #self.copy("CMakeLists.txt")
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            try:
                del self.options.fPIC
            except Exception:
                pass

    def configure(self):
        if self.options.shared:
            try:
                del self.options.fPIC
            except Exception:
                pass

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # TODO: update boost dependency as soon as issue #11207 is fixed
        self.requires("boost/1.75.0")
        self.requires("eigen/3.3.9")

    @property
    def _required_boost_components(self):
        return ["filesystem", "math", "serialization"]

    def validate(self):

        miss_boost_required_comp = any(getattr(self.dependencies["boost"].options, f"without_{boost_comp}", True) for boost_comp in self._required_boost_components)
        if self.dependencies["boost"].options.header_only or miss_boost_required_comp:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires non header-only boost with these components: "
                f"{', '.join(self._required_boost_components)}",
            )

        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "14")

        if str(self.settings.compiler) == "Visual Studio" and Version(self.settings.compiler.version) < "16":    
            raise ConanInvalidConfiguration("Visual Studio < 2019 not yet supported in this recipe")

        if self._is_msvc and self.options.shared:
            raise ConanInvalidConfiguration("cubicinterpolation shared is not supported with Visual Studio")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)  
        tc.variables["BUILD_EXAMPLE"] = False
        tc.variables["BUILD_DOCUMENTATION"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)

        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "CubicInterpolation")
        self.cpp_info.set_property("cmake_target_name", "CubicInterpolation::CubicInterpolation")
        self.cpp_info.libs = ["CubicInterpolation"]
        self.cpp_info.requires = ["boost::headers", "boost::filesystem", "boost::math", "boost::serialization", "eigen::eigen"]

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = "CubicInterpolation"
        self.cpp_info.names["cmake_find_package_multi"] = "CubicInterpolation"
