import os
import base64
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

load_dotenv()

OUTPUT_DIR = "output"
client = OpenAI()  # reads OPENAI_API_KEY from .env


def crop_to_instagram(img):
    """Crop a 2:3 portrait image to Instagram's 4:5 (1080x1350)."""
    width, height = img.size
    target_height = int(width * 5 / 4)       # 4:5 height for this width
    top = (height - target_height) // 2      # cut equally from top and bottom
    img = img.crop((0, top, width, top + target_height))
    return img.resize((1080, 1350))


def generate_slide_image(prompt: str, slide_number: int) -> str:
    """Creates an image for one slide and returns its file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    response = client.images.generate(
        model=os.getenv("OPENAI_IMAGE_MODEL"),
        prompt=prompt,
        size="1024x1536",
        quality=os.getenv("OPENAI_IMAGE_QUALITY", "low"),
        n=1,
    )

    # The image comes back as base64 text → turn it into a real image
    image_bytes = base64.b64decode(response.data[0].b64_json)
    img = Image.open(BytesIO(image_bytes))
    img = crop_to_instagram(img)

    path = os.path.join(OUTPUT_DIR, f"slide_{slide_number}.png")
    img.save(path)
    return path


# Quick test: ONE image (costs about 1 cent)
if __name__ == "__main__":
    path = generate_slide_image(
        "A person sitting by a window, writing in an open journal. "
        "Soft editorial gouache illustration, warm muted earthy palette, soft natural light. "
        "Vertical 4:5 composition with clean empty space in the upper right for text. "
        "No text, letters, numbers, or logos anywhere in the image.",
        1,
    )
    print("Saved:", path)