# Live WebRTC Project

This project implements a WebRTC application using FastAPI for the backend and Streamlit for the frontend. The application allows users to connect in real-time through peer-to-peer communication.

## Project Structure

```
live_webrtc
├── main.py                # FastAPI application with WebSocket support
├── streamlit_app
│   ├── index.py          # Streamlit app for the index page
│   └── answer.py         # Streamlit app for the answer page
├── static                 # Directory for static files (CSS, JS, images)
├── templates              # Directory for HTML templates (to be replaced by Streamlit)
├── requirements.txt       # List of dependencies
└── README.md              # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd live_webrtc
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI application:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Run the Streamlit application:**
   - For the index page:
     ```bash
     streamlit run streamlit_app/index.py
     ```
   - For the answer page:
     ```bash
     streamlit run streamlit_app/answer.py
     ```

## Usage

- Navigate to the Streamlit index page to connect to the WebRTC service.
- Follow the prompts to establish a peer-to-peer connection.
- Use the answer page to respond to connection requests.

## Dependencies

- FastAPI
- Streamlit
- WebSocket
- asyncio
- uuid

Ensure that all dependencies are listed in the `requirements.txt` file for easy installation.