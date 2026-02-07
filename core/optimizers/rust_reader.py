import os
import re

class RustConfigReader:
    def __init__(self, install_dir=None):
        self.install_dir = install_dir
        self.config_path = self._find_config()

    def _find_config(self):
        """Tente de localiser le fichier client.cfg."""
        paths_to_check = []
        if self.install_dir:
            paths_to_check.append(os.path.join(self.install_dir, "cfg", "client.cfg"))
        
        # Chemins communs par défaut
        common_steam = r"C:\Program Files (x86)\Steam\steamapps\common\Rust\cfg\client.cfg"
        paths_to_check.append(common_steam)

        for p in paths_to_check:
            if os.path.exists(p):
                return p
        return None

    def read_settings(self):
        """Lit et parse les réglages importants."""
        if not self.config_path:
            return None

        settings = {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Regex pour capturer les paramètres type: graphics.quality "3"
            patterns = {
                "graphics_quality": r'graphics\.quality\s+"(\d+)"',
                "shadow_distance": r'graphics\.shadowdistance\s+"([\d\.]+)"',
                "draw_distance": r'graphics\.drawdistance\s+"([\d\.]+)"',
                "water_quality": r'water\.quality\s+"(\d+)"',
                "anti_aliasing": r'graphics\.antialiasing\s+"([^"]+)"',
                "fov": r'graphics\.fov\s+"([\d\.]+)"'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    settings[key] = match.group(1)
            
            return settings
        except Exception as e:
            print(f"Erreur lecture config Rust: {e}")
            return None
