# [IMGLAB] — Image Manipulation Lab

**Course:** Introduction to Computer Science (CS-1102)
**Instructor:** Prof. Debayan Gupta, Department of Computer Science, Ashoka University
**Submitted by:** First Year Undergraduate, CS Major, Ashoka University
**Extra Credit Component:** Image Manipulation (up to 5%)
**Submission Deadline:** May 10, EoD

---

## What This Project Does

IMGLAB is a web application that lets a user upload any image and apply ten different image processing effects, all computed server-side in Python. The result is shown instantly using an interactive before/after drag slider, and can be downloaded with one click.

The goal was to go beyond basic colour filters and actually demonstrate the pixel-level mathematics that image manipulation is built on. Every effect in this project is implemented from scratch using Python logic. not CSS tricks or browser filters.

---

## Why I Built It This Way

From class, I understood that at its core, an image is just a 2D array of numbers — each pixel is a triplet `(R, G, B)` with values from 0 to 255. Once I saw images that way, I wanted to build something that made that idea *visible* to anyone, not just people reading code.

The before/after drag slider was a deliberate design choice: it lets you see exactly what the algorithm changed, pixel by pixel, by dragging a line across the image. I thought that was a more honest and interesting way to show the work than just displaying two images side by side.

I also wanted the project to feel like a real piece of software,  with a clean UI, proper client server architecture, and effects that actually required thinking about the math, not just calling one function.

---

## Project Structure

```
image_lab/
├── app.py                  ← Flask backend + all image processing logic
├── requirements.txt        ← Python dependencies
├── templates/
│   └── index.html          ← Frontend UI (upload, buttons, viewer)
└── static/
    ├── style.css           ← Styling
    └── script.js           ← Upload handling, API calls, before/after slider
```

The separation of concerns was intentional: all image logic lives in Python (backend), and the frontend only handles display and user interaction. The browser sends a base64-encoded image to Flask, Python processes it, and sends the result back. No image data is stored on disk.

---

## How to Run

**Step 1 — Install dependencies (only once)**
```bash
pip install -r requirements.txt
```

**Step 2 — Start the Flask server**
```bash
python app.py
```

**Step 3 — Open in browser**
```
http://localhost:5000
```

---

## How to Use

1. **Upload** any image. click the zone or drag and drop a file
2. **Pick an effect** from the panel that appears
3. **Drag the slider** on the result to compare before vs after
4. **Download** the processed image using the button below

---

## The Ten Effects — and the Math Behind Them

### 1. Grayscale
Uses Pillow's `ImageOps.grayscale()`, which converts each pixel to a single luminance value using the standard formula: `L = 0.299R + 0.587G + 0.114B`. The weights are not equal because human eyes are more sensitive to green than to red or blue.

### 2. Invert
Subtracts each channel from 255: `new_pixel = 255 - old_pixel`. Turns dark pixels light and light pixels dark. Implemented with `ImageOps.invert()`.

### 3. Sepia
The most mathematically interesting colour effect. Each output channel is a weighted linear combination of all three input channels:

```
R_out = 0.393·R + 0.769·G + 0.189·B
G_out = 0.349·R + 0.686·G + 0.168·B
B_out = 0.272·R + 0.534·G + 0.131·B
```

This is a matrix transformation applied to every pixel using NumPy, clipped to [0, 255]. The coefficients produce the warm brownish tone associated with old photographs.

### 4. Brightness
Uses `ImageEnhance.Brightness` with a factor of 1.5. A factor of 1.0 returns the original; values above 1 amplify pixel intensity, values below 1 darken it.

### 5. Blur
Applies a Gaussian blur with `ImageFilter.GaussianBlur(radius=5)`. Gaussian blur works by computing a weighted average of neighbouring pixels, where weights follow a bell-curve distribution — pixels closer to the centre of the kernel contribute more to the output than those at the edges.

### 6. Sharpen
Uses `ImageFilter.UnsharpMask` — a counterintuitive name for a sharpening technique. It works by subtracting a blurred copy of the image from the original, which amplifies edges and fine detail while leaving smooth regions unchanged.

### 7. Pixel Art
Exploits how image resampling works. The image is first shrunk to 1/16th of its size using `Image.NEAREST` (no interpolation), then scaled back up to the original size — also with `NEAREST`. Because nearest-neighbour resampling snaps each pixel to its closest neighbour without blending, the result looks like a mosaic of hard-edged colour blocks.

### 8. Pencil Sketch
A multi-step OpenCV pipeline that simulates a hand-drawn pencil sketch:
1. Convert to grayscale
2. Invert the grayscale image
3. Apply Gaussian blur to the inverted image
4. Apply the **dodge blend** formula: `output = gray / (255 - blurred) × 256`

The dodge blend is the key step — it produces high contrast at edges and near-white in uniform regions, replicating how pencil lines appear on paper.

### 9. Contrast
Uses `ImageEnhance.Contrast` with a factor of 1.8. Increases the perceptual difference between light and dark regions by stretching the pixel value distribution away from the midpoint.

### 10. Edge Detection
Uses OpenCV's Canny edge detector, a classic computer vision algorithm. It computes intensity gradients across the image using a Sobel operator, then applies double thresholding to identify strong edges and suppress noise. The output shows only the outlines of objects in the image.

---

## Architecture and Data Flow

```
User uploads image (browser)
        ↓
JavaScript reads file → encodes as base64 string
        ↓
POST /process  →  Flask receives JSON { image, effect }
        ↓
Python decodes base64 → PIL Image object (RGB array)
        ↓
Effect function processes pixel data (Pillow / NumPy / OpenCV)
        ↓
Result Image encoded back to base64 PNG
        ↓
JSON response returned to browser
        ↓
JavaScript decodes → displays in interactive before/after slider
```

---

## Libraries Used

| Library | Version | Purpose |
|---|---|---|
| Flask | 3.x | Web server and HTTP routing |
| Pillow | 12.x | Core image manipulation (most effects) |
| NumPy | 2.x | Pixel array math for sepia transformation |
| OpenCV | 4.x | Sketch pipeline and Canny edge detection |

---

## API Reference

```
POST /process
Content-Type: application/json

Request body:
{
  "image":  "<base64 PNG data URL>",
  "effect": "<effect name>"
}

Response:
{
  "result": "<base64 PNG data URL>"
}
```

Valid effect names: `grayscale`, `invert`, `sepia`, `brightness`, `blur`, `sharpen`, `pixel_art`, `sketch`, `contrast`, `edge_detect`

---

## What I Learned

Before this project, I assumed image filters were something browsers handled automatically. Building this made me realise that every "filter" is just arithmetic on a grid of numbers. and that is both simpler and more interesting than I expected.

The sepia matrix especially surprised me. The idea that you can shift the entire mood of a photograph through a few weighted sums felt like a small revelation. it made the linear algebra we touched on in class feel suddenly very real.

The sketch effect was the hardest to reason about. The dodge blend formula does not look like it should produce pencil lines, but working through the math of why it does — how dividing by an inverted blur amplifies edges, was one of the most satisfying moments of this project.

I also learned a lot about client-server communication by figuring out how to pass image data as base64 strings in JSON. It is a clean and stateless pattern, and understanding it made the whole web architecture click for me.

---

## Requirements

```
flask
pillow
numpy
opencv-python
```

Python 3.8 or higher recommended.
