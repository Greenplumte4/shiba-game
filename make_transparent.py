from collections import deque
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "assets" / "images"
OUTPUT_DIR = BASE_DIR / "assets" / "images_transparent"

WHITE_THRESHOLD = 240

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

BACKGROUND_NAMES = {
    "background.png",
    "background.jpg",
    "background.jpeg",
    "background.webp",
}


def is_near_white(pixel):
    r, g, b, a = pixel
    return a > 0 and r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD


def remove_edge_white_background(image):
    """
    Only removes white pixels connected to the outer edge of the image.

    This is safer than deleting every white pixel, because it can preserve
    white parts inside the character, such as eyes, face, fur, or bones.
    """
    image = image.convert("RGBA")
    width, height = image.size
    pixels = image.load()

    visited = set()
    queue = deque()

    # Start flood fill from the image border.
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))

    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()

        if (x, y) in visited:
            continue

        if x < 0 or x >= width or y < 0 or y >= height:
            continue

        visited.add((x, y))

        if not is_near_white(pixels[x, y]):
            continue

        r, g, b, a = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)

        queue.append((x + 1, y))
        queue.append((x - 1, y))
        queue.append((x, y + 1))
        queue.append((x, y - 1))

    return image


def main():
    if not SOURCE_DIR.exists():
        print(f"Source folder does not exist: {SOURCE_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for image_path in SOURCE_DIR.iterdir():
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        output_path = OUTPUT_DIR / f"{image_path.stem}.png"

        try:
            image = Image.open(image_path)

            if image_path.name.lower() in BACKGROUND_NAMES:
                # Do not remove the background image's white parts.
                image.convert("RGBA").save(output_path)
                print(f"Copied background: {image_path.name} -> {output_path.name}")
            else:
                cleaned = remove_edge_white_background(image)
                cleaned.save(output_path)
                print(f"Processed: {image_path.name} -> {output_path.name}")

        except Exception as error:
            print(f"Failed to process {image_path.name}: {error}")

    print()
    print("Done.")
    print(f"Transparent images are saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()