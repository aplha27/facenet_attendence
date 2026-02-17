# FaceNet based Attendance System (Modernized)
> A **Deep Learning** based Web Application for marking attendance of students by recognizing the student's faces from the surveillance video footage of classroom.

## 🎉 Recent Updates
- ✅ **Modernized Configuration System** - Environment-based configuration management
- ✅ **Simplified Training Pipeline** - Easy-to-use model training with `simple_train.py`
- ✅ **Improved Architecture** - Modular code structure with services, models, and utilities
- ✅ **Cross-Platform Support** - Works on Windows, Linux, and macOS
- ✅ **Better Error Handling** - Comprehensive logging and error messages

## Features
- 🎯 **Face Recognition** - Automatic student identification using deep learning
- 📊 **Attendance Reports** - Generate Excel reports with attendance data
- 👥 **Multi-Student Support** - Recognize multiple students in a single image
- 🔐 **User Authentication** - Secure login system for teachers/administrators
- 📱 **Responsive UI** - Works on desktop and mobile devices
- ⚙️ **Easy Configuration** - Environment-based settings management

## Technology Stack
- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Face Detection**: OpenCV Haar Cascades
- **Face Recognition**: MobileNetV2 + SVM Classifier
- **Report Generation**: XlsxWriter, Pandas
- **Authentication**: Flask-Login, Flask-Bcrypt

## Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd FaceNet-based-Attendance-System-master
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your settings (optional)
```

### 5. Train the Model
```bash
# Add your training images to dataset/ folder
# Each person should have their own folder with 10+ images

# Run training
python simple_train.py
```

### 6. Run the Application
```bash
python run.py
```

Visit `http://localhost:5000` in your browser.

## Training Your Model

### Step 1: Prepare Dataset
Create folders for each person in the `dataset/` directory:
```
dataset/
├── person1/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ... (10+ images recommended)
├── person2/
│   └── ... (10+ images)
└── person3/
    └── ... (10+ images)
```

### Step 2: Train
```bash
python simple_train.py
```

This will:
1. Prepare your dataset
2. Detect and align faces
3. Train the classifier
4. Save the model

### Step 3: Test
```bash
python test_simple_model.py
```

For detailed training instructions, see [TRAINING_GUIDE.md](TRAINING_GUIDE.md)

## Project Structure
```
├── attendance/              # Main Flask application
│   ├── __init__.py         # App initialization with config
│   ├── routes.py           # URL routes and views
│   ├── models.py           # Database models
│   ├── forms.py            # WTForms
│   ├── templates/          # HTML templates
│   └── static/             # CSS, images
├── config/                  # Configuration management
│   ├── __init__.py
│   └── configuration_manager.py
├── services/                # Business logic services
├── models/                  # Domain models
├── utils/                   # Utility functions
├── dataset/                 # Training images
├── uploads/                 # Uploaded images
├── reports/                 # Generated reports
├── simple_train.py          # Model training script
├── test_simple_model.py     # Model testing script
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
└── run.py                   # Application entry point
```

## Configuration

The system uses environment variables for configuration. Edit `.env` file:

```env
# Database
DATABASE_URL=sqlite:///site.db

# Directories
UPLOAD_DIRECTORY=uploads
MODEL_DIRECTORY=attendance/facenet/src/20180402-114759
REPORTS_DIRECTORY=reports

# Security
SECRET_KEY=your-secret-key-here
MAX_FILE_SIZE=10485760

# Face Recognition
FACE_DETECTION_THRESHOLD=0.6
RECOGNITION_THRESHOLD=0.5

# Application
DEBUG=True
```

## Usage

### 1. Register/Login
- Create an account or login with existing credentials

### 2. Add Class Information
- Navigate to "Add Class"
- Enter class details and student information

### 3. Take Attendance
- Navigate to "Take Attendance"
- Upload a classroom image
- System will recognize faces and mark attendance
- Download the generated Excel report

## Improving Recognition Accuracy

For better results:
1. **Use 10+ diverse images per person**
2. **Include different angles and lighting**
3. **Ensure clear, high-quality images**
4. **Avoid blurry or dark photos**
5. **Retrain after adding new images**

See [TRAINING_IMPROVEMENT_GUIDE.md](TRAINING_IMPROVEMENT_GUIDE.md) for detailed tips.

## Troubleshooting

### Model Not Found
```bash
# Train the model first
python simple_train.py
```

### Low Recognition Accuracy
- Add more diverse training images
- Ensure good image quality
- Retrain the model

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Database Errors
```bash
# Delete old database and restart
rm site.db
python run.py
```

## Development

### Running Tests
```bash
pytest
```

### Code Style
```bash
# Format code
black .

# Lint code
flake8 .
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License
This project is for educational purposes.

## Acknowledgments
- Original FaceNet implementation
- OpenCV for face detection
- TensorFlow/Keras for deep learning
- Flask community

## References
- https://github.com/davidsandberg/facenet
- https://github.com/AISangam/Facenet-Real-time-face-recognition-using-deep-learning-Tensorflow
- https://github.com/abhijeet3922/Face_ID

## Support
For issues and questions, please create an issue in the repository.

---
Made with ❤️ for automated attendance tracking