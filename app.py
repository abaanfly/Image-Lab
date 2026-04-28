"""
Image Manipulation Lab - Backend
CS Extra Credit Project
Uses: Flask, Pillow, NumPy, OpenCV
"""

import io
import base64
import numpy as np
import cv2
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

app = Flask(__name__)

# ─────────────────────────────────────────
#  HELPER: PIL Image  ↔  base64 string
# ─────────────────────────────────────────

def image_to_base64(img: Image.Image) -> str:
    """Convert a PIL Image to a base64-encoded PNG string."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def base64_to_image(data_url: str) -> Image.Image:
    """Convert a base64 data URL back to a PIL Image."""
    # Remove the 'data:image/...;base64,' prefix
    header, data = data_url.split(",", 1)
    raw_bytes = base64.b64decode(data)
    return Image.open(io.BytesIO(raw_bytes)).convert("RGB")


def pil_to_cv2(img: Image.Image):
    """Convert PIL Image → OpenCV (numpy BGR array)."""
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def cv2_to_pil(arr) -> Image.Image:
    """Convert OpenCV (numpy BGR array) → PIL Image."""
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


# ─────────────────────────────────────────
#  IMAGE MANIPULATION FUNCTIONS (Python)
# ─────────────────────────────────────────

def apply_grayscale(img: Image.Image) -> Image.Image:
    """Convert image to grayscale then back to RGB."""
    return ImageOps.grayscale(img).convert("RGB")


def apply_invert(img: Image.Image) -> Image.Image:
    """Invert all pixel colours."""
    return ImageOps.invert(img)


def apply_sepia(img: Image.Image) -> Image.Image:
    """
    Sepia tone effect using a matrix transformation.
    Each output pixel is a weighted blend of the R, G, B inputs.
    """
    pixels = np.array(img, dtype=np.float64)          # shape: (H, W, 3)

    r = pixels[:, :, 0]
    g = pixels[:, :, 1]
    b = pixels[:, :, 2]

    # Classic sepia formula
    new_r = np.clip(r * 0.393 + g * 0.769 + b * 0.189, 0, 255)
    new_g = np.clip(r * 0.349 + g * 0.686 + b * 0.168, 0, 255)
    new_b = np.clip(r * 0.272 + g * 0.534 + b * 0.131, 0, 255)

    sepia = np.stack([new_r, new_g, new_b], axis=2).astype(np.uint8)
    return Image.fromarray(sepia)


def apply_brightness(img: Image.Image, factor: float = 1.5) -> Image.Image:
    """
    Adjust brightness.
    factor < 1  →  darker
    factor = 1  →  original
    factor > 1  →  brighter
    """
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)


def apply_blur(img: Image.Image, radius: int = 5) -> Image.Image:
    """Gaussian blur using Pillow's built-in filter."""
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_sharpen(img: Image.Image) -> Image.Image:
    """Sharpen edges using an unsharp mask."""
    return img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))


def apply_pixel_art(img: Image.Image, block_size: int = 16) -> Image.Image:
    """
    Pixel-art / mosaic effect.
    Shrink the image down then scale it back up — each 'block'
    becomes a solid colour square, giving the retro pixel look.
    """
    w, h = img.size
    small_w = max(1, w // block_size)
    small_h = max(1, h // block_size)

    # Shrink → blocky
    small = img.resize((small_w, small_h), Image.NEAREST)
    # Stretch back to original size (no interpolation → hard edges)
    pixelated = small.resize((w, h), Image.NEAREST)
    return pixelated


def apply_sketch(img: Image.Image) -> Image.Image:
    """
    Pencil-sketch effect using OpenCV.
    Steps:
      1. Convert to grayscale
      2. Invert the grayscale
      3. Gaussian-blur the inverted image
      4. Dodge-blend: divide grayscale by blurred-invert
         → produces pencil-line look
    """
    cv_img = pil_to_cv2(img)
    gray   = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    inverted = cv2.bitwise_not(gray)
    blurred  = cv2.GaussianBlur(inverted, (21, 21), sigmaX=0, sigmaY=0)

    # Dodge blend formula: output = gray / (1 - blurred/255)
    sketch = cv2.divide(gray, 255 - blurred, scale=256)

    # Convert single-channel back to 3-channel RGB
    sketch_rgb = cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(sketch_rgb)


def apply_contrast(img: Image.Image, factor: float = 1.8) -> Image.Image:
    """Enhance image contrast."""
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)


def apply_edge_detect(img: Image.Image) -> Image.Image:
    """
    Edge detection using OpenCV's Canny algorithm.
    Highlights borders between colour regions.
    """
    cv_img  = pil_to_cv2(img)
    gray    = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    edges   = cv2.Canny(gray, threshold1=80, threshold2=160)
    rgb     = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb)


# ─────────────────────────────────────────
#  EFFECT REGISTRY
#  Maps effect name (sent from JS) → function
# ─────────────────────────────────────────

EFFECTS = {
    "grayscale":    apply_grayscale,
    "invert":       apply_invert,
    "sepia":        apply_sepia,
    "brightness":   apply_brightness,
    "blur":         apply_blur,
    "sharpen":      apply_sharpen,
    "pixel_art":    apply_pixel_art,
    "sketch":       apply_sketch,
    "contrast":     apply_contrast,
    "edge_detect":  apply_edge_detect,
}


# ─────────────────────────────────────────
#  FLASK ROUTES
# ─────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    """
    Receive JSON:  { image: <base64 data URL>, effect: <string> }
    Return  JSON:  { result: <base64 data URL> }
    """
    data      = request.get_json()
    image_b64 = data.get("image")
    effect    = data.get("effect", "grayscale")

    if not image_b64:
        return jsonify({"error": "No image received"}), 400

    # Decode the incoming image
    img = base64_to_image(image_b64)

    # Apply the chosen effect
    if effect not in EFFECTS:
        return jsonify({"error": f"Unknown effect: {effect}"}), 400

    result_img = EFFECTS[effect](img)

    # Encode result back to base64 and return
    return jsonify({"result": image_to_base64(result_img)})


# ─────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)