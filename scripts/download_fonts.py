import os

import requests

# Create fonts directory if it doesn't exist
os.makedirs("data/fonts", exist_ok=True)

# List of Google Fonts handwriting fonts and their URLs
FONTS = {
    "Childrens-Handwriting": "https://github.com/google/fonts/raw/main/ofl/comicneue/ComicNeue-Regular.ttf",
    "KidsHandwriting": "https://github.com/google/fonts/raw/main/ofl/indieflower/IndieFlower-Regular.ttf",
    "MessyHandwriting": "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf",
}


def download_font(name, url):
    print(f"Downloading {name}...")
    response = requests.get(url)
    if response.status_code == 200:
        font_path = f"data/fonts/{name}.ttf"
        with open(font_path, "wb") as f:
            f.write(response.content)
        print(f"Successfully downloaded {name} to {font_path}")
    else:
        print(f"Failed to download {name}: Status code {response.status_code}")


def main():
    for name, url in FONTS.items():
        download_font(name, url)


if __name__ == "__main__":
    main()
