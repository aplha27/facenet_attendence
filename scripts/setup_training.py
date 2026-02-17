#!/usr/bin/env python3
"""
Setup script for FaceNet training environment
"""

import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        ('tensorflow', 'tensorflow'),
        ('opencv-python', 'cv2'),
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('pillow', 'PIL'),
        ('scikit-learn', 'sklearn')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            logger.info(f"✓ {package_name}")
        except ImportError:
            logger.error(f"✗ {package_name}")
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_directory_structure():
    """Check if required directories exist"""
    logger.info("Checking directory structure...")
    
    project_root = Path(__file__).parent
    required_dirs = [
        "dataset",
        "attendance/facenet/src",
        "attendance/facenet/src/align",
        "attendance/facenet/src/20180402-114759",
        "attendance/facenet/dataset"
    ]
    
    missing_dirs = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            logger.info(f"✓ {dir_path}")
        else:
            logger.error(f"✗ {dir_path}")
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        logger.error(f"Missing directories: {', '.join(missing_dirs)}")
        return False
    
    return True

def check_model_files():
    """Check if FaceNet model files exist"""
    logger.info("Checking FaceNet model files...")
    
    project_root = Path(__file__).parent
    model_dir = project_root / "attendance/facenet/src/20180402-114759"
    
    required_files = [
        "20180402-114759.pb",
        "model-20180402-114759.ckpt-275.data-00000-of-00001",
        "model-20180402-114759.ckpt-275.index",
        "model-20180402-114759.ckpt-275.meta"
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = model_dir / file_name
        if file_path.exists():
            logger.info(f"✓ {file_name}")
        else:
            logger.warning(f"? {file_name}")
            missing_files.append(file_name)
    
    if missing_files:
        logger.warning("Some model files are missing. The training might still work if you have the .pb file.")
        logger.info("If training fails, download the pre-trained model from:")
        logger.info("https://drive.google.com/drive/folders/1pwQ3H4aJ8a6yyJHZkTwtjcL4wYWQb7bn")
    
    return len(missing_files) < len(required_files)  # At least some files exist

def check_dataset():
    """Check dataset structure"""
    logger.info("Checking dataset...")
    
    project_root = Path(__file__).parent
    dataset_dir = project_root / "dataset"
    
    if not dataset_dir.exists():
        logger.error("Dataset directory not found!")
        return False
    
    person_folders = [d for d in dataset_dir.iterdir() if d.is_dir()]
    
    if not person_folders:
        logger.error("No person folders found in dataset!")
        logger.info("Create folders for each person and add their images")
        return False
    
    total_images = 0
    for person_folder in person_folders:
        images = list(person_folder.glob("*.jpg")) + list(person_folder.glob("*.jpeg")) + list(person_folder.glob("*.png"))
        total_images += len(images)
        logger.info(f"✓ {person_folder.name}: {len(images)} images")
        
        if len(images) < 5:
            logger.warning(f"  Warning: {person_folder.name} has only {len(images)} images. Recommend at least 10 images per person.")
    
    logger.info(f"Total images: {total_images}")
    return total_images > 0

def create_missing_directories():
    """Create missing directories"""
    logger.info("Creating missing directories...")
    
    project_root = Path(__file__).parent
    dirs_to_create = [
        "attendance/facenet/dataset/raw",
        "attendance/facenet/dataset/aligned",
        "attendance/facenet/dataset/test-images",
        "reports",
        "uploads"
    ]
    
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Created: {dir_path}")

def main():
    logger.info("Setting up FaceNet training environment...")
    logger.info("="*50)
    
    # Create missing directories
    create_missing_directories()
    
    # Check everything
    checks = [
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Model Files", check_model_files),
        ("Dataset", check_dataset)
    ]
    
    all_good = True
    
    for check_name, check_func in checks:
        logger.info(f"\n{check_name}:")
        logger.info("-" * 30)
        if not check_func():
            all_good = False
    
    logger.info("\n" + "="*50)
    
    if all_good:
        logger.info("🎉 Setup completed successfully!")
        logger.info("You can now run: python train_model.py")
    else:
        logger.error("❌ Setup incomplete. Please fix the issues above.")
        logger.info("\nCommon solutions:")
        logger.info("1. Install missing packages: pip install tensorflow opencv-python numpy scipy pillow scikit-learn")
        logger.info("2. Add more images to your dataset folders (at least 10 per person)")
        logger.info("3. Download the pre-trained FaceNet model if missing")

if __name__ == "__main__":
    main()