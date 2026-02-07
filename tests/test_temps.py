import wmi

def test_wmi_temps():
    print("Tentative de lecture des températures via WMI...")
    try:
        w = wmi.WMI(namespace="root\wmi")
        temperature_info = w.MSAcpi_ThermalZoneTemperature()
        for temp in temperature_info:
            # La temp est souvent en dixièmes de Kelvin
            celsius = (temp.CurrentTemperature / 10.0) - 273.15
            print(f"Zone Thermique: {celsius:.1f}°C")
    except Exception as e:
        print(f"Erreur WMI Standard: {e}")

    print("\nTentative via OpenHardwareMonitor (si installé)...")
    try:
        w_ohm = wmi.WMI(namespace="root\OpenHardwareMonitor")
        sensors = w_ohm.Sensor()
        for sensor in sensors:
            if sensor.SensorType == "Temperature":
                print(f"{sensor.Name}: {sensor.Value}°C")
    except Exception as e:
        print(f"OpenHardwareMonitor WMI non détecté: {e}")

if __name__ == "__main__":
    test_wmi_temps()
