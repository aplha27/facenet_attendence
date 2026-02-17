# FaceNet-based Attendance System (Kiosk Edition)

A smart, automated attendance system using FaceNet for facial recognition. This version has been modernized to work as a "Kiosk" – essentially a station where users simply stand in front of a camera to have their attendance marked instantly.

## Features
- **Live Webcam Recognition**: No need to upload files manually; just look at the camera.
- **High Accuracy**: Uses the Google FaceNet model with a strict 75% confidence threshold.
- **Instant Reporting**: Automatically generates Excel (`.xlsx`) reports with Student Name, Status, and **Time**.
- **Kiosk Mode**: No login required. The system boots directly into scanning mode.
- **Secure**: Basic validation and checking of image data.

## Installation

1.  **Prerequisites**: Python 3.10 or 3.11 recommended. C++ Build Tools (for some Python packages).

2.  **Environment Setup**:
    The project uses a standard virtual environment `venv_std`.
    ```powershell
    # Activate the environment
    . .\venv_std\Scripts\Activate.ps1
    ```

3.  **Dependencies**:
    If setting up from scratch:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Start the Server**:
    Make sure your virtual environment is active.
    ```powershell
    python run.py
    ```

2.  **Access the System**:
    Open your web browser and go to:
    [http://localhost:5000](http://localhost:5000)

3.  **Take Attendance**:
    - The page will ask for Camera permissions. Allow them.
    - You will see a live video feed.
    - Click **"Recognize & Mark Attendance"**.
    - If recognized (Confidence > 75%), your attendance is marked.
    - If not recognized or confidence is low, a warning will appear.

4.  **View Reports**:
    Attendance sheets are saved in the `reports/` directory.

## Project Structure
- `attendance/`: Main application code (routes, templates).
- `attendance/facenet/`: FaceNet model and detection logic.
- `reports/`: Generated Excel attendance sheets.
- `uploads/`: Temporary storage for captured images.
- `docs/`: Additional documentation and guides.

## Troubleshooting
- **Camera not working?** Check browser permissions or try a different browser (Chrome/Edge recommended).
- **Low Confidence?** Ensure good lighting and look directly at the camera.
- **Server errors?** Check the terminal for error logs.
