document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startButton = document.getElementById('startCamera');
    const takeSelfieButton = document.getElementById('takeSelfie');
    const smileStatus = document.getElementById('smileStatus');
    
    // Global variables
    let stream = null;
    let isCheckingSmile = false;
    let lastCaptureTime = 0;
    const captureInterval = 3000; // Minimum 3 seconds between automatic captures
    
    // Start camera
    startButton.addEventListener('click', async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });
            
            video.srcObject = stream;
            startButton.disabled = true;
            takeSelfieButton.disabled = false;
            smileStatus.textContent = "Camera started. Smile detection active!";
            
            // Start smile detection
            startSmileDetection();
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            smileStatus.textContent = "Error accessing camera. Please check permissions.";
        }
    });
    
    // Take manual selfie
    takeSelfieButton.addEventListener('click', () => {
        captureSelfie();
    });
    
    // Start smile detection loop
    function startSmileDetection() {
        if (isCheckingSmile) return;
        isCheckingSmile = true;
        
        // Check for smile every 500ms
        setInterval(() => {
            if (!stream) return;
            
            // Capture current frame
            const context = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert to base64
            const imageData = canvas.toDataURL('image/jpeg');
            
            // Send to backend for smile detection
            fetch('/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: imageData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.smile_detected) {
                    smileStatus.textContent = "Smile detected!";
                    
                    // Check if enough time has passed since last capture
                    const now = Date.now();
                    if (now - lastCaptureTime > captureInterval) {
                        captureSelfie();
                        lastCaptureTime = now;
                    }
                } else {
                    smileStatus.textContent = data.error ? 
                        `Error: ${data.error}` : 
                        "No smile detected. Smile to take a selfie!";
                }
            })
            .catch(error => {
                console.error('Error detecting smile:', error);
                smileStatus.textContent = "Error communicating with server.";
            });
            
        }, 500);
    }
    
    // Capture and save selfie
    function captureSelfie() {
        if (!stream) return;
        
        // Draw current frame
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Convert to base64
        const imageData = canvas.toDataURL('image/jpeg');
        
        // Save image on server
        fetch('/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                smileStatus.textContent = "Selfie captured!";
                
                // Add new image to gallery without reloading
                const galleryContainer = document.querySelector('.gallery-container');
                const noImagesMessage = galleryContainer.querySelector('p');
                
                if (noImagesMessage) {
                    galleryContainer.innerHTML = '';
                }
                
                const newItem = document.createElement('div');
                newItem.className = 'gallery-item';
                
                const newImage = document.createElement('img');
                newImage.src = `/static/${data.path}`;
                newImage.alt = 'Selfie';
                
                newItem.appendChild(newImage);
                galleryContainer.prepend(newItem);
                
                // After 2 seconds, reset status
                setTimeout(() => {
                    smileStatus.textContent = "Smile detection active!";
                }, 2000);
            } else if (data.error) {
                smileStatus.textContent = `Error: ${data.error}`;
            }
        })
        .catch(error => {
            console.error('Error saving selfie:', error);
            smileStatus.textContent = "Error saving selfie.";
        });
    }
    
    // Clean up on page unload
    window.addEventListener('beforeunload', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
});
