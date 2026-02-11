from PIL import Image
import os
import sys

def convert_logo():
    # Possible locations for the logo
    possible_paths = [
        os.path.join("static", "uploads", "logo.png"),
        os.path.join("static", "logo.png")
    ]
    
    logo_path = None
    for path in possible_paths:
        if os.path.exists(path):
            logo_path = path
            break
            
    if not logo_path:
        print("Error: logo.png not found in static/uploads/ or static/")
        sys.exit(1)
        
    try:
        img = Image.open(logo_path)
        img.save("logo.ico", format="ICO", sizes=[(256, 256)])
        print(f"Successfully converted {logo_path} to logo.ico")
    except Exception as e:
        print(f"Error converting logo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    convert_logo()
