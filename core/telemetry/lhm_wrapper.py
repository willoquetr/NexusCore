import clr # pythonnet
import os
import sys
from core.logger import logger
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Chemin vers la DLL (DEDANS l'EXE)
DLL_PATH = resource_path("libs/LibreHardwareMonitorLib.dll")

class HardwareMonitor:
    def __init__(self):
        self.computer = None
        self.enabled = False
        
        if os.path.exists(DLL_PATH):
            try:
                # Débloquer la DLL si besoin (Windows bloque parfois les DLL téléchargées)
                # Mais ici on charge juste
                clr.AddReference(DLL_PATH)
                from LibreHardwareMonitor import Hardware
                self.computer = Hardware.Computer()
                self.computer.IsCpuEnabled = True
                self.computer.IsGpuEnabled = True
                self.computer.IsMemoryEnabled = True
                self.computer.IsMotherboardEnabled = True
                self.computer.Open()
                self.enabled = True
                logger.info("Telemetry: LibreHardwareMonitor DLL loaded successfully.")
                
                # Log detected hardware
                for hw in self.computer.Hardware:
                    logger.info(f"Telemetry: Detected Hardware -> {hw.HardwareType}: {hw.Name}")
                    
            except Exception as e:
                logger.error(f"Telemetry: Error loading LHM DLL: {e}", exc_info=True)
                self.enabled = False
        else:
            logger.warning(f"Telemetry: DLL not found at {DLL_PATH}. Using psutil fallback.")
            self.enabled = False

        # Definition dynamique du Visitor seulement si DLL chargée
        if self.enabled:
            from LibreHardwareMonitor.Hardware import IVisitor
            
            class UpdateVisitor(IVisitor):
                __namespace__ = "NexusCore.Telemetry"
                
                def VisitComputer(self, computer):
                    computer.Traverse(self)
                def VisitHardware(self, hardware):
                    hardware.Update()
                    for subHardware in hardware.SubHardware:
                        subHardware.Accept(self)
                def VisitSensor(self, sensor):
                    pass
                def VisitParameter(self, parameter):
                    pass
            
            self.visitor = UpdateVisitor()
        else:
            self.visitor = None

    def get_data(self):
        if not self.enabled:
            return None

        data = {
            "cpu_temp": 0.0,
            "gpu_temp": 0.0,
            "gpu_load": 0.0,
            "gpu_memory_used": 0.0,
            "gpu_memory_total": 0.0
        }

        try:
            self.computer.Accept(self.visitor)
            
            for hardware in self.computer.Hardware:
                # CPU
                if "Cpu" in str(hardware.HardwareType): 
                    for sensor in hardware.Sensors:
                        if str(sensor.SensorType) == "Temperature":
                            # On priorise le "Package" ou le "Core Max"
                            if "Package" in sensor.Name or "Total" in sensor.Name or "Max" in sensor.Name:
                                data["cpu_temp"] = sensor.Value if sensor.Value else data["cpu_temp"]
                            elif data["cpu_temp"] == 0:
                                data["cpu_temp"] = sensor.Value if sensor.Value else 0
                            
                # GPU (Intel, Nvidia, AMD)
                if "Gpu" in str(hardware.HardwareType):
                    for sensor in hardware.Sensors:
                        if str(sensor.SensorType) == "Temperature":
                            data["gpu_temp"] = max(data["gpu_temp"], sensor.Value if sensor.Value else 0)
                        elif str(sensor.SensorType) == "Load" and ("Core" in sensor.Name or "GPU Core" in sensor.Name):
                            data["gpu_load"] = sensor.Value if sensor.Value else 0
                             
        except Exception as e:
            # print(f"Erreur lecture sensors: {e}") # Silent fail pour éviter spam
            pass
            
        return data

    def close(self):
        if self.computer:
            self.computer.Close()

# Pas de classe globale UpdateVisitor ici pour éviter l'erreur d'import

