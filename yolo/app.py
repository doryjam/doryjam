from flask import Flask, request, render_template
import torch
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

app = Flask(__name__)

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template('index.html', error="No image file uploaded")
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return render_template('index.html', error="No selected image file")
        
        image = Image.open(image_file)
        
        # Convert the image to RGB mode if it's in RGBA mode
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # Perform inference with YOLOv5
        results = model(image)
        
        # Process the results
        detected_objects = []
        for detection in results.pred[0]:
            class_index = int(detection[5])
            class_name = model.model.names[class_index]
            box = detection[:4]  # Bounding box coordinates
            detected_objects.append({"class_name": class_name, "box": box})
        
        # Draw bounding boxes and labels on the image
        draw = ImageDraw.Draw(image)
        for obj in detected_objects:
            x1, y1, x2, y2 = map(int, obj["box"])
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
            
            font = ImageFont.load_default()  # Load a default font
            label = obj['class_name']
            draw.text((x1, y1), label, fill="red", font=font)
        
        # Convert the image to base64 for displaying in HTML
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return render_template('index.html', img_base64=img_base64, detected_objects=detected_objects)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
