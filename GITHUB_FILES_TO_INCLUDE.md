# Files to Include in GitHub

## ✅ INCLUDE These Files/Folders:

### Core Application Files
```
attendance/
├── __init__.py
├── routes.py (or routes_updated.py)
├── models.py
├── forms.py
├── detect.py
├── excel.py
├── templates/
│   └── *.html (all HTML files)
├── static/
│   ├── *.css
│   ├── *.png
│   └── *.jpg
└── facenet/
    └── src/
        ├── *.py (all Python files)
        └── align/
            └── *.py
```

### Configuration & Setup Files
```
config/
├── __init__.py
└── configuration_manager.py

services/
├── __init__.py
└── (any service files you create)

models/
└── __init__.py

utils/
└── __init__.py
```

### Training Scripts
```
simple_train.py
test_simple_model.py
setup_training.py
improve_training.py
update_flask_app.py
train_model.py
test_model.py
```

### Configuration Files
```
.env.example          (YES - example only)
config.ini.example    (YES - example only)
requirements.txt
.gitignore
```

### Documentation
```
README.md (or README_NEW.md)
TRAINING_GUIDE.md
TRAINING_IMPROVEMENT_GUIDE.md
TRAINING_COMPLETE.md
GIT_GUIDE.md
```

### Entry Point
```
run.py
```

### Empty Directories (with .gitkeep)
```
uploads/.gitkeep
reports/.gitkeep
```

---

## ❌ DO NOT INCLUDE:

### Virtual Environments
```
venv/
venv_std/
env/
.venv/
```

### Database Files
```
*.db
*.sqlite
*.sqlite3
site.db
attendance.db
```

### Environment Files (with secrets)
```
.env                  (NO - contains secrets)
config.ini            (NO - if it has secrets)
```

### Dataset & Training Data
```
dataset/              (NO - images are large)
attendance/facenet/dataset/raw/
attendance/facenet/dataset/aligned/
attendance/facenet/dataset/test-images/
```

### Model Files (large binary files)
```
*.pkl                 (NO - trained models are large)
*.h5
*.pb
*.ckpt*
attendance/facenet/src/20180402-114759/*.pkl
```

### Generated/Uploaded Files
```
uploads/*             (NO - except .gitkeep)
reports/*             (NO - except .gitkeep)
output/
```

### Python Cache
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
```

### IDE Files
```
.vscode/
.idea/
*.swp
.DS_Store
Thumbs.db
```

### Backup Files
```
*_original.py
*_backup.py
*.bak
```

### Logs
```
*.log
logs/
```

---

## 📝 Your .gitignore File

Make sure your `.gitignore` includes:

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
venv/
venv_std/
*.egg-info/

# Database
*.db
*.sqlite
*.sqlite3
site.db

# Environment
.env
config.ini

# Dataset & Models
dataset/
attendance/facenet/dataset/raw/
attendance/facenet/dataset/aligned/
attendance/facenet/dataset/test-images/
*.pkl
*.h5
*.pb
*.ckpt*

# Uploads & Reports
uploads/*
!uploads/.gitkeep
reports/*
!reports/.gitkeep

# IDE
.vscode/
.idea/
*.swp
.DS_Store

# Logs
*.log

# Backup
*_original.py
*_backup.py
```

---

## 🚀 Quick GitHub Upload Steps:

1. **Create .gitignore** (already done ✓)

2. **Initialize Git:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: FaceNet Attendance System"
   ```

3. **Create GitHub Repository:**
   - Go to GitHub.com
   - Click "New Repository"
   - Name it (e.g., "facenet-attendance-system")
   - Don't initialize with README (you already have one)

4. **Push to GitHub:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

---

## 📋 Summary:

**INCLUDE:**
- ✅ All Python code files (.py)
- ✅ HTML templates
- ✅ CSS and static assets
- ✅ Documentation (.md files)
- ✅ requirements.txt
- ✅ .gitignore
- ✅ .env.example (example only)
- ✅ Empty folders with .gitkeep

**EXCLUDE:**
- ❌ Virtual environments (venv/)
- ❌ Database files (*.db)
- ❌ Dataset images (dataset/)
- ❌ Trained models (*.pkl)
- ❌ Uploaded files (uploads/*)
- ❌ Generated reports (reports/*)
- ❌ .env file (has secrets)
- ❌ Python cache (__pycache__/)

**Total Size:** Should be under 10-20 MB (mostly code and docs)