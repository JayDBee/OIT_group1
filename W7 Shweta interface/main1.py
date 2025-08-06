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

# Mock ML modules for demo purposes
import time
import random
import string

# Mock model and tools (for demo only)
print("Running in demo mode - no ML libraries required!")
asl_model = "mock_model"
actions = ["hello", "world", "thank", "you", "please", "sorry", "good", "morning"]
grammar_tool = "mock_grammar_tool"

async def process_asl_video(video_path: str, translation_id: str):
    """
    Mock ASL video processing for demo purposes
    """
    try:
        # Simulate processing time
        await asyncio.sleep(3)
        
        # Generate mock translation results
        mock_sentences = [
            "Hello how are you today",
            "Thank you very much",
            "Good morning everyone", 
            "Please help me with this",
            "Sorry I am late",
            "Nice to meet you"
        ]
        
        # Pick a random sentence
        translated_text = random.choice(mock_sentences)
        confidence = round(random.uniform(0.85, 0.98), 2)
        
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
        templates = Jinja2Templates(directory="templates")

# attempt to connect home.html to the FastAPI app
#@app.get("/", response_class=HTMLResponse)
#async def home(request: Request):
#    return templates.TemplateResponse("home.html", {"request": request})
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