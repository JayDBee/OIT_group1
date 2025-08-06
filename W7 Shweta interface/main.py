from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
import aiofiles
from typing import Optional
import asyncio
from datetime import datetime

app = FastAPI(title="ASL Translation API", version="1.0.0")

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class TranslationResponse(BaseModel):
    translation_id: str
    status: str
    message: str

class TranslationResult(BaseModel):
    translation_id: str
    status: str
    translated_text: Optional[str] = None
    confidence: Optional[float] = None
    processed_at: Optional[datetime] = None
    error: Optional[str] = None

# In-memory store (use Redis/DB in production)
translations_store = {}

# Import your ML modules
import numpy as np
import cv2
import mediapipe as mp
from tensorflow.keras.models import load_model
import language_tool_python
import string
# from my_functions import *  # Uncomment and make sure my_functions.py is in your path

# Initialize your model and tools (do this once at startup)
try:
    # Load your trained model
    asl_model = load_model('my_model')
    
    # Load action labels
    PATH = os.path.join('data')
    actions = np.array(os.listdir(PATH))
    
    # Initialize grammar correction tool
    grammar_tool = language_tool_python.LanguageToolPublicAPI('en-UK')
    
    print("ASL model and tools loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    asl_model = None
    actions = None
    grammar_tool = None

async def process_asl_video(video_path: str, translation_id: str):
    """
    Process ASL video with your ML model
    """
    try:
async def process_asl_video(video_path: str, translation_id: str):
    """
    Process ASL video using your MediaPipe + TensorFlow model
    """
    try:
        if asl_model is None or actions is None:
            raise Exception("Model not loaded properly")
        
        def run_asl_prediction(video_path):
            """Your ASL prediction logic adapted for video files"""
            sentence = []
            keypoints = []
            last_prediction = []
            
            # Open the video file instead of camera
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"Cannot open video file: {video_path}")
            
            # Create holistic object for sign prediction
            with mp.solutions.holistic.Holistic(
                min_detection_confidence=0.75, 
                min_tracking_confidence=0.75
            ) as holistic:
                
                while cap.isOpened():
                    ret, image = cap.read()
                    if not ret:
                        break
                    
                    # Process the image and obtain sign landmarks
                    # You'll need to import your functions or recreate them
                    results = image_process(image, holistic)  # From your my_functions.py
                    
                    # Extract keypoints from the pose landmarks
                    keypoints.append(keypoint_extraction(results))  # From your my_functions.py
                    
                    # Check if 10 frames have been accumulated
                    if len(keypoints) == 10:
                        # Convert keypoints list to numpy array
                        keypoints_array = np.array(keypoints)
                        
                        # Make prediction using your loaded model
                        prediction = asl_model.predict(keypoints_array[np.newaxis, :, :])
                        
                        # Clear keypoints for next set of frames
                        keypoints = []
                        
                        # Check if prediction confidence is above 0.9
                        if np.amax(prediction) > 0.9:
                            predicted_action = actions[np.argmax(prediction)]
                            
                            # Check if different from last prediction
                            if last_prediction != predicted_action:
                                sentence.append(predicted_action)
                                last_prediction = predicted_action
                
                cap.release()
            
            # Post-process the sentence
            if sentence:
                # Capitalize first word
                sentence[0] = sentence[0].capitalize()
                
                # Handle letter combinations (your alphabet logic)
                processed_sentence = []
                i = 0
                while i < len(sentence):
                    current_word = sentence[i]
                    
                    # Check for letter combinations
                    if i < len(sentence) - 1:
                        next_word = sentence[i + 1]
                        if (current_word in string.ascii_lowercase or 
                            current_word in string.ascii_uppercase) and \
                           (next_word in string.ascii_lowercase or 
                            next_word in string.ascii_uppercase):
                            # Combine letters
                            combined = current_word + next_word
                            processed_sentence.append(combined.capitalize())
                            i += 2  # Skip next word since we combined it
                            continue
                    
                    processed_sentence.append(current_word)
                    i += 1
                
                # Join words into sentence
                raw_text = ' '.join(processed_sentence)
                
                # Apply grammar correction
                if grammar_tool:
                    corrected_text = grammar_tool.correct(raw_text)
                    return {
                        "text": corrected_text,
                        "raw_text": raw_text,
                        "confidence": 0.9  # You could calculate average confidence
                    }
                else:
                    return {
                        "text": raw_text,
                        "raw_text": raw_text,
                        "confidence": 0.9
                    }
            else:
                return {
                    "text": "No signs detected",
                    "raw_text": "",
                    "confidence": 0.0
                }
        
        # Run your model in a thread pool to avoid blocking
        import concurrent.futures
        import functools
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor, 
                functools.partial(run_asl_prediction, video_path)
            )
        
        # Extract results
        translated_text = result.get("text", "")
        confidence = result.get("confidence", 0.0)
        
        # Update store
        translations_store[translation_id] = {
            "status": "completed",
            "translated_text": translated_text,
            "confidence": confidence,
            "processed_at": datetime.now(),
            "error": None
        }
        
        # Clean up video file
        if os.path.exists(video_path):
            os.remove(video_path)
            
    except Exception as e:
        translations_store[translation_id] = {
            "status": "failed",
            "translated_text": None,
            "confidence": None,
            "processed_at": datetime.now(),
            "error": str(e)
        }

@app.get("/")
async def root():
    return {"message": "ASL Translation API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/upload", response_model=TranslationResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique ID
    translation_id = str(uuid.uuid4())
    
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Save uploaded file
    file_path = f"uploads/{translation_id}_{file.filename}"
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Initialize translation record
    translations_store[translation_id] = {
        "status": "processing",
        "translated_text": None,
        "confidence": None,
        "processed_at": None,
        "error": None
    }
    
    # Start background processing
    background_tasks.add_task(process_asl_video, file_path, translation_id)
    
    return TranslationResponse(
        translation_id=translation_id,
        status="processing",
        message="Video uploaded successfully and is being processed"
    )

@app.get("/translation/{translation_id}", response_model=TranslationResult)
async def get_translation(translation_id: str):
    if translation_id not in translations_store:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    data = translations_store[translation_id]
    
    return TranslationResult(
        translation_id=translation_id,
        status=data["status"],
        translated_text=data["translated_text"],
        confidence=data["confidence"],
        processed_at=data["processed_at"],
        error=data["error"]
    )

@app.get("/translations")
async def list_translations():
    """Get all translations (for debugging/admin)"""
    return {
        "translations": [
            {"id": tid, **data} for tid, data in translations_store.items()
        ]
    }

@app.delete("/translation/{translation_id}")
async def delete_translation(translation_id: str):
    if translation_id not in translations_store:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    del translations_store[translation_id]
    return {"message": "Translation deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)