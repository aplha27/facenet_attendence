# Project Journey: Steps Taken

This document outlines the complete process taken to transform the initial FaceNet-based Attendance System into a fully functional, webcam-integrated, kiosk-style application.

## 1. Initial Assessment and Cleanup
- **Analysis**: Explored the directory structure and identified a mix of temporary files, broken environments, and displaced documentation.
- **Cleanup**:
  - Created `docs/` and moved existing documentation (`TRAINING_GUIDE.md`, etc.) there.
  - Created `scripts/` and moved utility scripts (`setup_training.py`, etc.) there.
  - Deleted unwanted directories: `.hypothesis`, `.kiro`, `.qodo`, `.pytest_cache`.
- **Environment**:
  - The existing environment was broken.
  - Created a new standard Python 3.11 virtual environment (`venv_std`).
  - Installed compatible versions of `tensorflow`, `opencv-python`, `scikit-learn`, `Flask`, and others.

## 2. Model Training Repair
- **Dependency Fixes**: Patched the code to support TensorFlow 2.x using `tensorflow.compat.v1` and disabled eager execution.
- **Library Updates**: Replaced deprecated `scipy.misc` image operations with `PIL` (Pillow).
- **Model Acquisition**: Downloaded the missing FaceNet pre-trained model `20180402-114759`.
- **Training**: successfully ran `train_model.py` to train the classifier on the dataset.

## 3. Application Restoration
- **Server Fixes**:
  - Fixed `ImportError` in `run.py` and `routes.py`.
  - Installed missing `Flask-HTTPAuth` dependency.
  - Disabled debug mode in `run.py` to prevent reloader crashes in the background.
- **Face Recognition Enablement**:
  - Restored commented-out logic in `attendance/routes.py`.
  - Implemented a TensorFlow-compatible face recognition pipeline using the trained model and MTCNN.

## 4. Feature Enhancements
- **Kiosk Mode**:
  - Removed login requirements for the "Take Attendance" page.
  - Redirected the home route (`/`) directly to the attendance page (`/take`) for instant access.
- **Webcam Integration**:
  - Replaced the file upload form in `take.html` with a live HTML5 `<video>` feed.
  - Added JavaScript to capture frames from the webcam and upload them via AJAX.
- **Accuracy Threshold**:
  - Implemented a strict **75% confidence threshold**. Attendance is only marked if the model is >75% sure of the match.
- **Report Enhancement**:
  - Added a **Time** column to the generated Excel reports to track exactly when attendance was marked.

## 5. Bug Fixes
- **Attributes**: Fixed an `AttributeError` in `file_handler.py` where it referenced `allowed_extensions` instead of `allowed_file_types` from the config.
- **Imports**: Fixed circular and missing imports in the security utility modules.

## Final Status
The system is now a robust, touch-free attendance kiosk that runs on a local server, captures live video, recognizes faces with high accuracy, and auto-generates detailed Excel reports.
