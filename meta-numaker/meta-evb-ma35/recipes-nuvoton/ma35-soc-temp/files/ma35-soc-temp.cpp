// SPDX-License-Identifier: Apache-2.0
#include <boost/asio/io_context.hpp>
#include <boost/asio/steady_timer.hpp>
#include <sdbusplus/asio/connection.hpp>
#include <sdbusplus/asio/object_server.hpp>

#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

namespace fs = std::filesystem;

static constexpr double warningThreshold = 95.0;
static constexpr double criticalThreshold = 105.0;
static constexpr std::chrono::seconds pollInterval(2);

static std::string findThermalZonePath()
{
    // Look for a thermal zone with type "cpu-thermal"
    for (int i = 0; i < 10; ++i)
    {
        std::string typePath = "/sys/class/thermal/thermal_zone" + std::to_string(i) + "/type";
        std::string tempPath = "/sys/class/thermal/thermal_zone" + std::to_string(i) + "/temp";
        if (fs::exists(typePath))
        {
            std::ifstream tf(typePath);
            std::string typeStr;
            if (tf >> typeStr && (typeStr == "cpu-thermal" || typeStr == "cpu_thermal"))
            {
                return tempPath;
            }
        }
    }
    // Fallback to thermal_zone0
    return "/sys/class/thermal/thermal_zone0/temp";
}

static double readSocTemperature(const std::string& tempPath)
{
    std::ifstream file(tempPath);
    if (!file.is_open())
    {
        return std::numeric_limits<double>::quiet_NaN();
    }
    long long rawTemp = 0;
    if (file >> rawTemp)
    {
        // Linux thermal zone returns millidegrees Celsius
        return static_cast<double>(rawTemp) / 1000.0;
    }
    return std::numeric_limits<double>::quiet_NaN();
}

int main()
{
    boost::asio::io_context io;
    auto conn = std::make_shared<sdbusplus::asio::connection>(io);
    conn->request_name("xyz.openbmc_project.MA35SocTemp");

    sdbusplus::asio::object_server server(conn);

    std::string thermalPath = findThermalZonePath();
    std::cout << "MA35 SoC Temp service using thermal sysfs: " << thermalPath << std::endl;

    const std::string sensorObjPath = "/xyz/openbmc_project/sensors/temperature/cpu_thermal";

    // 1. Sensor Value Interface
    auto sensorIface = server.add_interface(sensorObjPath, "xyz.openbmc_project.Sensor.Value");

    double currentTemp = readSocTemperature(thermalPath);
    if (std::isnan(currentTemp))
    {
        currentTemp = 0.0;
    }

    sensorIface->register_property("Value", currentTemp);
    sensorIface->register_property("Unit", std::string("xyz.openbmc_project.Sensor.Value.Unit.DegreesC"));
    sensorIface->register_property("Scale", static_cast<int64_t>(0));
    sensorIface->register_property("MinValue", 0.0);
    sensorIface->register_property("MaxValue", 125.0);
    sensorIface->initialize();

    // 2. Warning Threshold Interface
    auto warningIface = server.add_interface(sensorObjPath, "xyz.openbmc_project.Sensor.Threshold.Warning");
    warningIface->register_property("WarningHigh", warningThreshold);
    warningIface->register_property("WarningLow", 0.0);
    warningIface->register_property("WarningAlarmHigh", currentTemp >= warningThreshold);
    warningIface->register_property("WarningAlarmLow", false);
    warningIface->initialize();

    // 3. Critical Threshold Interface
    auto critIface = server.add_interface(sensorObjPath, "xyz.openbmc_project.Sensor.Threshold.Critical");
    critIface->register_property("CriticalHigh", criticalThreshold);
    critIface->register_property("CriticalLow", 0.0);
    critIface->register_property("CriticalAlarmHigh", currentTemp >= criticalThreshold);
    critIface->register_property("CriticalAlarmLow", false);
    critIface->initialize();

    // 4. OperationalStatus Interface
    auto opStatusIface = server.add_interface(sensorObjPath, "xyz.openbmc_project.State.Decorator.OperationalStatus");
    opStatusIface->register_property("Functional", true);
    opStatusIface->initialize();

    // 5. Availability Interface
    auto availIface = server.add_interface(sensorObjPath, "xyz.openbmc_project.State.Decorator.Availability");
    availIface->register_property("Available", true);
    availIface->initialize();

    // 6. Association Interface (Chassis linking)
    auto assocIface = server.add_interface(sensorObjPath, "xyz.openbmc_project.Association.Definitions");
    std::vector<std::tuple<std::string, std::string, std::string>> associations = {
        {"chassis", "all_sensors", "/xyz/openbmc_project/inventory/system/chassis/system"},
        {"chassis", "all_sensors", "/xyz/openbmc_project/inventory/system/chassis"},
        {"chassis", "all_sensors", "/xyz/openbmc_project/inventory/system/board/system"}
    };
    assocIface->register_property("Associations", associations);
    assocIface->initialize();

    // Periodic polling timer
    auto timer = std::make_shared<boost::asio::steady_timer>(io);
    std::function<void(const boost::system::error_code&)> pollHandler;

    pollHandler = [&, timer](const boost::system::error_code& ec) {
        if (ec)
        {
            return;
        }

        double temp = readSocTemperature(thermalPath);
        if (!std::isnan(temp))
        {
            sensorIface->set_property("Value", temp);
            warningIface->set_property("WarningAlarmHigh", temp >= warningThreshold);
            critIface->set_property("CriticalAlarmHigh", temp >= criticalThreshold);
        }

        timer->expires_after(pollInterval);
        timer->async_wait(pollHandler);
    };

    timer->expires_after(pollInterval);
    timer->async_wait(pollHandler);

    io.run();
    return 0;
}
