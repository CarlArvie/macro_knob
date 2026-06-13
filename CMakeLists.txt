cmake_minimum_required(VERSION 3.15)
project(KnobLaunch CXX)

# Target MSVC with C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Download nlohmann/json.hpp
if(NOT EXISTS ${CMAKE_SOURCE_DIR}/include/nlohmann/json.hpp)
    message(STATUS "Downloading nlohmann/json.hpp...")
    file(DOWNLOAD 
        https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp 
        ${CMAKE_SOURCE_DIR}/include/nlohmann/json.hpp
        SHOW_PROGRESS
    )
endif()

# Source files
set(SOURCES
    src/main.cpp
    src/config_store.h
    src/config_store.cpp
    src/input_hook.h
    src/input_hook.cpp
    src/radial_menu.h
    src/radial_menu.cpp
    src/macro_runner.h
    src/macro_runner.cpp
)

# Output binary to bin/knoblaunch.exe
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)

# Create executable with WIN32 subsystem
add_executable(knoblaunch WIN32 ${SOURCES})

# Target include directories
target_include_directories(knoblaunch PRIVATE 
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
)

# Enable Unicode and set warnings as errors for MSVC
if(MSVC)
    target_compile_definitions(knoblaunch PRIVATE UNICODE _UNICODE)
    target_compile_options(knoblaunch PRIVATE /W4 /WX)
else()
    # Fallback/Other compilers
    target_compile_definitions(knoblaunch PRIVATE UNICODE _UNICODE)
    target_compile_options(knoblaunch PRIVATE -Wall -Wextra -Werror)
endif()

# Link required libraries
target_link_libraries(knoblaunch PRIVATE
    user32
    shell32
    gdi32
    gdiplus
    shlwapi
)

# Copy executable to workspace root after build
add_custom_command(TARGET knoblaunch POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
            $<TARGET_FILE:knoblaunch>
            ${CMAKE_SOURCE_DIR}/knoblaunch.exe
    COMMENT "Copying knoblaunch.exe to workspace root"
)

