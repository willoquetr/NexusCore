import psutil
import time
from core.database import get_session, HardwareSnapshot
from core.telemetry.lhm_wrapper import HardwareMonitor

class TelemetryCollector:
    def __init__(self):
        self.is_running = False
        self.lhm = HardwareMonitor()
        # Historiques pour lissage (Moyenne mobile sur 5 points)
        self.cpu_history = []
        self.gpu_history = []

    def _smooth_value(self, history, new_val):
        """Ajoute une valeur et retourne la moyenne lissée."""
        history.append(new_val)
        if len(history) > 5:
            history.pop(0)
        return sum(history) / len(history)

    def get_stats(self):
        """Récupère les stats hardware actuelles avec lissage."""
        # 1. Capture brute
        raw_cpu = psutil.cpu_percent(interval=None)
        raw_ram = psutil.virtual_memory().percent
        raw_gpu = 0.0
        
        lhm_data = self.lhm.get_data()
        if lhm_data:
            raw_gpu = lhm_data.get("gpu_load", 0.0)
            cpu_temp = lhm_data.get("cpu_temp", 0.0)
            gpu_temp = lhm_data.get("gpu_temp", 0.0)
        else:
            cpu_temp = 0.0
            gpu_temp = 0.0

        # 2. Lissage (SMA)
        smooth_cpu = self._smooth_value(self.cpu_history, raw_cpu)
        smooth_gpu = self._smooth_value(self.gpu_history, raw_gpu)

        return {
            "cpu": round(smooth_cpu, 1),
            "ram": raw_ram, # RAM est déjà stable en général
            "gpu": round(smooth_gpu, 1),
            "gpu_temp": gpu_temp,
            "cpu_temp": cpu_temp
        }
    
    def close(self):
        if self.lhm:
            self.lhm.close()

    def save_snapshot(self, game_id=None):
        """Enregistre un snapshot dans la base de données."""
        stats = self.get_stats()
        db_session = get_session()
        try:
            snapshot = HardwareSnapshot(
                cpu_usage=stats["cpu"],
                ram_usage=stats["ram"],
                gpu_usage=stats["gpu"],
                gpu_temp=stats["gpu_temp"],
                active_game_id=game_id
            )
            db_session.add(snapshot)
            db_session.commit()
        except Exception as e:
            print(f"Erreur sauvegarde télémétrie: {e}")
        finally:
            db_session.close()

if __name__ == "__main__":
    # Test simple
    collector = TelemetryCollector()
    print("Capture des stats pendant 5 secondes...")
    for _ in range(5):
        print(collector.get_stats())
        time.sleep(1)
