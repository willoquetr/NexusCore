from PIL import Image
import os

def create_nexus_icon(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        return

    img = Image.open(input_path).convert("RGBA")
    
    # Trouver la bounding box des pixels non transparents (le N)
    bbox = img.getbbox()
    if bbox:
        # On recadre sur le contenu
        content = img.crop(bbox)
        
        # On veut un carré pour l'icône
        w, h = content.size
        side = max(w, h)
        new_img = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        # Centrer le N
        new_img.paste(content, ((side - w) // 2, (side - h) // 2))
        
        # Sauvegarder en ICO avec plusieurs tailles standards
        new_img.save(output_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Icon created successfully: {output_path}")
    else:
        print("Error: Could not find content in image")

if __name__ == "__main__":
    create_nexus_icon("assets/logonexuscore.png", "NexusCore.ico")
