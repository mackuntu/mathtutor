import os
from PIL import Image, ImageDraw, ImageFont

# Directory to store the assets
output_dir = "assets"
os.makedirs(output_dir, exist_ok=True)

# Emojis and corresponding file names
emoji_data = {
    "🚀": "rocket.png",
    "🌕": "moon.png",
    "⭐": "star.png",
    "🌟": "shining_star.png",
    "🪐": "planet.png",
    "🌌": "galaxy.png",
}

# Define the font for macOS
font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
font_size = 64  # Size of the emoji

# Generate each emoji as an image
for emoji, filename in emoji_data.items():
    # Create an image with a transparent background
    img = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Load the emoji font
    font = ImageFont.truetype(font_path, font_size)

    # Calculate position to center the emoji
    position = (0, 0)

    # Draw the emoji
    draw.text(position, emoji, font=font, embedded_color=True)

    # Save the image
    img.save(os.path.join(output_dir, filename))

print(f"Emoji images saved to {output_dir}")
