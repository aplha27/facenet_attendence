#!/usr/bin/env python3
"""
Script to help improve training data and retrain the model
"""

import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_dataset():
    """Analyze the current dataset"""
    logger.info("Analyzing current dataset...")
    
    dataset_dir = Path("dataset")
    
    for person_folder in dataset_dir.iterdir():
        if not person_folder.is_dir():
            continue
        
        logger.info(f"\n{person_folder.name}:")
        logger.info("-" * 30)
        
        image_files = list(person_folder.glob("*.jpg")) + list(person_folder.glob("*.jpeg")) + list(person_folder.glob("*.png"))
        
        logger.info(f"Total images: {len(image_files)}")
        
        # Check for duplicate-looking filenames
        base_names = set()
        duplicates = []
        
        for img_file in image_files:
            # Remove common suffixes like " - Copy (2)"
            base_name = img_file.stem
            for suffix in [" - Copy", " - Copy (2)", " - Copy (3)", " - Copy (4)"]:
                base_name = base_name.replace(suffix, "")
            
            if base_name in base_names:
                duplicates.append(img_file.name)
            else:
                base_names.add(base_name)
        
        if duplicates:
            logger.warning(f"Potential duplicates detected: {duplicates}")
            logger.warning("Consider adding more diverse images for better recognition")
        
        unique_images = len(base_names)
        logger.info(f"Unique base images: {unique_images}")
        
        if len(image_files) < 10:
            logger.warning(f"Recommendation: Add more images (current: {len(image_files)}, recommended: 10+)")
        
        if unique_images < 5:
            logger.warning(f"Recommendation: Add more diverse images (current unique: {unique_images}, recommended: 5+)")

def create_training_guide():
    """Create a guide for better training data"""
    guide = """
# Training Data Improvement Guide

## Current Issues:
- Limited training data (5 images per person)
- Possible duplicate/similar images
- Model confusion between people

## Recommendations:

### 1. Add More Diverse Images
For each person, add images with:
- Different facial expressions (smiling, neutral, serious)
- Different angles (front, slight left, slight right)
- Different lighting conditions (bright, dim, natural light)
- Different backgrounds
- With/without glasses (if applicable)
- Different clothing/hairstyles

### 2. Image Quality Guidelines
- Use clear, high-resolution images
- Ensure face is clearly visible
- Avoid blurry or dark images
- Face should be at least 100x100 pixels
- One person per image (for training)

### 3. Recommended Dataset Structure
```
dataset/
├── viswas/
│   ├── viswas_front_1.jpg      # Front facing, smiling
│   ├── viswas_front_2.jpg      # Front facing, neutral
│   ├── viswas_left_1.jpg       # Slight left angle
│   ├── viswas_right_1.jpg      # Slight right angle
│   ├── viswas_bright_1.jpg     # Bright lighting
│   ├── viswas_dim_1.jpg        # Dim lighting
│   ├── viswas_glasses_1.jpg    # With glasses (if applicable)
│   ├── viswas_outdoor_1.jpg    # Outdoor photo
│   ├── viswas_indoor_1.jpg     # Indoor photo
│   └── viswas_casual_1.jpg     # Different clothing
├── vivek/
│   └── [similar variety for vivek]
└── new_person/                 # Add more people as needed
    └── [10+ diverse images]
```

### 4. After Adding Images
1. Run: python simple_train.py
2. Test: python test_simple_model.py
3. Check accuracy and add more images if needed

### 5. Adding New People
1. Create a new folder in dataset/ with the person's name
2. Add 10+ diverse images of that person
3. Retrain the model
"""
    
    with open("TRAINING_IMPROVEMENT_GUIDE.md", "w") as f:
        f.write(guide)
    
    logger.info("Created TRAINING_IMPROVEMENT_GUIDE.md")

def main():
    logger.info("Training Data Analysis and Improvement")
    logger.info("=" * 50)
    
    analyze_dataset()
    create_training_guide()
    
    logger.info("\n" + "=" * 50)
    logger.info("RECOMMENDATIONS:")
    logger.info("1. Add more diverse images to your dataset folders")
    logger.info("2. Read TRAINING_IMPROVEMENT_GUIDE.md for detailed tips")
    logger.info("3. After adding images, retrain with: python simple_train.py")
    logger.info("4. Test improved model with: python test_simple_model.py")

if __name__ == "__main__":
    main()