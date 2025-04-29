from flask import Flask, render_template, request, jsonify
import cv2
import os
import base64
import numpy as np
from datetime import datetime
import urllib.request
import sys

app = Flask(__name__)

# Ensure images directory exists
IMAGE_FOLDER = os.path.join('static', 'images')
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Ensure haarcascade directory exists
CASCADE_FOLDER = 'haarcascade'
if not os.path.exists(CASCADE_FOLDER):
    os.makedirs(CASCADE_FOLDER)

# Define the cascade file paths
face_cascade_path = os.path.join(CASCADE_FOLDER, 'haarcascade_frontalface_default.xml')
smile_cascade_path = os.path.join(CASCADE_FOLDER, 'haarcascade_smile.xml')

# Download cascade files if they don't exist
def download_cascade_files():
    cascade_urls = {
        'haarcascade_frontalface_default.xml': 
            'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml',
        'haarcascade_smile.xml': 
            'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_smile.xml'
    }
    
    for filename, url in cascade_urls.items():
        filepath = os.path.join(CASCADE_FOLDER, filename)
        
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            try:
                print(f"Downloading {filename}...")
                urllib.request.urlretrieve(url, filepath)
                print(f"Downloaded {filename} successfully")
            except Exception as e:
                print(f"Error downloading {filename}: {e}")
                return False
    return True

# Download the cascade files if needed
download_cascade_files()

# Attempt to load the cascade classifiers
try:
    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    smile_cascade = cv2.CascadeClassifier(smile_cascade_path)
    
    # Verify the classifiers loaded correctly
    if face_cascade.empty():
        print(f"ERROR: Face cascade failed to load! Path: {face_cascade_path}")
    else:
        print("Face cascade loaded successfully!")
        
    if smile_cascade.empty():
        print(f"ERROR: Smile cascade failed to load! Path: {smile_cascade_path}")
    else:
        print("Smile cascade loaded successfully!")
        
except Exception as e:
    print(f"Error loading cascade files: {e}")
    face_cascade = cv2.CascadeClassifier()
    smile_cascade = cv2.CascadeClassifier()

@app.route('/')
def index():
    # Check if cascade files loaded successfully
    cascade_status = {
        'face_loaded': not face_cascade.empty(),
        'smile_loaded': not smile_cascade.empty()
    }
    
    # Get all image files for gallery
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('.jpg', '.jpeg', '.png'))]
    image_files.sort(key=lambda x: os.path.getctime(os.path.join(IMAGE_FOLDER, x)), reverse=True)
    image_paths = [os.path.join('images', img) for img in image_files]
    
    return render_template('index.html', images=image_paths, cascade_status=cascade_status)

@app.route('/detect', methods=['POST'])
def detect():
    # Check if classifiers are available
    if face_cascade.empty() or smile_cascade.empty():
        return jsonify({
            'smile_detected': False, 
            'error': 'Cascade classifiers not loaded properly. Please check the console for errors.'
        })
    
    try:
        # Get image data from request
        image_data = request.json['image'].split(',')[1]
        
        # Convert base64 to image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Variables to track smile detection  
        smile_detected = False
        
        # Check each face for smiles
        for (x, y, w, h) in faces:
            # Get region of interest (face area)
            roi_gray = gray[y:y+h, x:x+w]
            
            # Detect smiles within the face
            smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
            
            if len(smiles) > 0:
                smile_detected = True
                break
        
        return jsonify({'smile_detected': smile_detected})
    except Exception as e:
        print(f"Error in smile detection: {e}")
        return jsonify({'smile_detected': False, 'error': str(e)}), 500

@app.route('/save', methods=['POST'])
def save():
    try:
        # Get image data from request
        image_data = request.json['image'].split(',')[1]
        
        # Convert base64 to image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smile_{timestamp}.jpg"
        filepath = os.path.join(IMAGE_FOLDER, filename)
        
        # Save image
        cv2.imwrite(filepath, img)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': os.path.join('images', filename)
        })
    except Exception as e:
        print(f"Error saving image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
