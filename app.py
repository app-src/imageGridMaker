from flask import Flask, render_template, request, send_file
import os
from PIL import Image, ImageOps
import io
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    # Get input values
    image_file = request.files["image"]
    margin = int(request.form.get("margin", 0))
    ratio = request.form.get("ratio", "1:1")
    sheet_size = request.form.get("sheet_size", "A4")
    black_white = request.form.get("black_white", "false") == "true"

    # Parse ratio
    width_ratio, height_ratio = map(int, ratio.split(":"))

    # Define sheet size dimensions (in pixels at 300 DPI)
    sheet_sizes = {
        "A3": (3508, 4961),
        "A4": (2480, 3508),
        "A5": (1748, 2480),
    }
    sheet_width, sheet_height = sheet_sizes.get(sheet_size, sheet_sizes["A4"])

    # Load and process image
    img = Image.open(image_file)

    # Crop image to maintain the specified ratio
    img_width, img_height = img.size
    target_width = img_width
    target_height = img_width * height_ratio // width_ratio

    if target_height > img_height:
        target_height = img_height
        target_width = img_height * width_ratio // height_ratio

    left = (img_width - target_width) // 2
    top = (img_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    img = img.crop((left, top, right, bottom))

    if black_white:
        img = ImageOps.grayscale(img)

    # Create grid of sheets
    img_width, img_height = img.size
    cols = img_width // (sheet_width - 2 * margin)
    rows = img_height // (sheet_height - 2 * margin)

    output_paths = []

    for row in range(rows):
        for col in range(cols):
            left = col * (sheet_width - 2 * margin)
            top = row * (sheet_height - 2 * margin)
            right = left + sheet_width - 2 * margin
            bottom = top + sheet_height - 2 * margin

            cropped = img.crop((left, top, right, bottom))

            # Add margins
            bordered = ImageOps.expand(cropped, border=margin, fill="white")

            # Label the image
            label = f"{chr(65 + col)}{row + 1}"
            output_path = os.path.join(OUTPUT_FOLDER, f"grid_{label}.png")
            bordered.save(output_path)
            output_paths.append(output_path)

    # Create a ZIP file
    zip_path = os.path.join(OUTPUT_FOLDER, "output.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file_path in output_paths:
            zf.write(file_path, os.path.basename(file_path))

    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
