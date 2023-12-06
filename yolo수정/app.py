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
        detected_labels = set()  # 중복된 라벨을 방지하기 위한 집합(set)
        detected_objects = []
        for detection in results.pred[0]:
            class_index = int(detection[5])
            class_name = model.model.names[class_index]

            # 중복된 라벨인 경우 무시
            if class_name in detected_labels:
                continue

            box = detection[:4]  # Bounding box coordinates
            detected_objects.append({"class_name": class_name, "box": box})
            detected_labels.add(class_name)

        # Draw bounding boxes and labels on the image
        draw = ImageDraw.Draw(image)
        for obj in detected_objects:
            x1, y1, x2, y2 = map(int, obj["box"])
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

            font = ImageFont.load_default()  # Load a default font
            label = obj['class_name']
            draw.text((x1, y1), label, fill="red", font=font)

            # 감지된 객체를 확인하고 클래스 이름에 따라 링크 추가
            if label == "Pumpkin powdery mildew":
                link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-3-1.html"
            elif label == "Sweet pumpkin spot disease":
                 link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-3-2.html"
            elif label == "pepper-mild-mottle-virus":
                 link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-6-1.html"
            elif label == "TYLCV":
                 link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-5-2.html"
            elif label == "tomato-leaf-mould":
                 link ="http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-5-1.html"
            elif label == "Melon-powderymildew":
                 link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-2-1.html"
            elif label == "Downy-mildew":
                 link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-2-2.html"
            elif label == "cucumber_powdery-mildew":
                 link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-3-5.html"
            elif label == "cucumber_downy-mildew":
                 link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-3-1.html"   
            else:
                 label== "Ascochyta-leaf-spot"     
                 link = "http://farmerai.knuit.com.s3-website.ap-northeast-2.amazonaws.com/list-6-2.html" 
            obj["link"] = link

        # Convert the image to base64 for displaying in HTML
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return render_template('index.html', img_base64=img_base64, detected_objects=detected_objects)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
