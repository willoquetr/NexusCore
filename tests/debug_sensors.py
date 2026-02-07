import clr
import os
import sys
import time

# Chemin vers la DLL
DLL_PATH = os.path.join(os.getcwd(), "libs", "LibreHardwareMonitorLib.dll")

def debug_lhm():
    if not os.path.exists(DLL_PATH):
        print(f"ERREUR: DLL non trouvée à {DLL_PATH}")
        return

    try:
        clr.AddReference(DLL_PATH)
        from LibreHardwareMonitor import Hardware
        
        computer = Hardware.Computer()
        computer.IsCpuEnabled = True
        computer.IsGpuEnabled = True
        computer.IsMemoryEnabled = True
        computer.IsMotherboardEnabled = True
        computer.Open()
        
        print(f"{'TYPE':<15} | {'HARDWARE':<20} | {'SENSOR':<25} | {'VALUE'}")
        print("-" * 80)
        
        # On force un update
        for hardware in computer.Hardware:
            hardware.Update()
            for sub in hardware.SubHardware:
                sub.Update()
            
            for sensor in hardware.Sensors:
                print(f"{str(hardware.HardwareType):<15} | {hardware.Name[:20]:<20} | {sensor.Name[:25]:<25} | {sensor.Value}")
            
            for sub in hardware.SubHardware:
                for sensor in sub.Sensors:
                    print(f"SUB-{str(sub.HardwareType):<11} | {sub.Name[:20]:<20} | {sensor.Name[:25]:<25} | {sensor.Value}")

        computer.Close()
        
    except Exception as e:
        print(f"ERREUR DIAGNOSTIC: {e}")

if __name__ == "__main__":
    debug_lhm()
