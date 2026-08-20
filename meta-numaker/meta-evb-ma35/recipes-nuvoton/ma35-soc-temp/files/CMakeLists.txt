cmake_minimum_required(VERSION 3.10)
project(ma35-soc-temp CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(GNUInstallDirs)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SDBUSPLUS REQUIRED sdbusplus)
pkg_check_modules(SYSTEMD REQUIRED libsystemd)

find_package(Boost REQUIRED)

add_executable(ma35-soc-temp ma35-soc-temp.cpp)

target_include_directories(ma35-soc-temp PRIVATE
    ${Boost_INCLUDE_DIRS}
    ${SDBUSPLUS_INCLUDE_DIRS}
    ${SYSTEMD_INCLUDE_DIRS}
)

target_link_libraries(ma35-soc-temp PRIVATE
    ${SDBUSPLUS_LIBRARIES}
    ${SYSTEMD_LIBRARIES}
    pthread
)

install(TARGETS ma35-soc-temp DESTINATION ${CMAKE_INSTALL_BINDIR})
