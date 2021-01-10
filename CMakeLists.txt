cmake_minimum_required(VERSION 3.13.4)

project(EPISURG)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/EPISURG")
set(EXTENSION_CATEGORY "EPISURG")
set(EXTENSION_CONTRIBUTORS "Fernando Perez-Garcia (University College London)")
set(EXTENSION_DESCRIPTION "This is an example of a simple extension")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/EPISURG.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/EPISURG/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(EPISURGBrowser)
add_subdirectory(EPISURGSegment)
add_subdirectory(EPISURGBase)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
