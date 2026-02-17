#!/usr/bin/env python3
"""
Simplified FaceNet Training Script
This script trains a face recognition model using your dataset
"""

import os
import sys
import shutil
import logging
import cv2
import numpy as np
import pickle
from pathlib import Path
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import tensorflow as tf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleFaceTrainer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dataset_dir = self.project_root / "dataset"
        self.raw_dir = self.project_root / "attendance/facenet/dataset/raw"
        self.aligned_dir = self.project_root / "attendance/facenet/dataset/aligned"
        self.model_dir = self.project_root / "attendance/facenet/src/20180402-114759"
        self.classifier_path = self.model_dir / "my_classifier.pkl"
        
        # Face detection using OpenCV (simpler than MTCNN)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def prepare_dataset(self):
        """Copy and prepare dataset"""
        logger.info("Preparing dataset...")
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.aligned_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy dataset
        for person_folder in self.dataset_dir.iterdir():
            if person_folder.is_dir():
                dest_folder = self.raw_dir / person_folder.name
                
                if dest_folder.exists():
                    shutil.rmtree(dest_folder)
                
                shutil.copytree(person_folder, dest_folder)
                logger.info(f"Copied {person_folder.name} dataset")
        
        return True
    
    def detect_and_align_faces(self):
        """Detect and align faces using OpenCV"""
        logger.info("Detecting and aligning faces...")
        
        for person_folder in self.raw_dir.iterdir():
            if not person_folder.is_dir():
                continue
                
            aligned_person_folder = self.aligned_dir / person_folder.name
            aligned_person_folder.mkdir(exist_ok=True)
            
            image_files = list(person_folder.glob("*.jpg")) + list(person_folder.glob("*.jpeg")) + list(person_folder.glob("*.png"))
            
            for i, image_file in enumerate(image_files):
                try:
                    # Read image
                    img = cv2.imread(str(image_file))
                    if img is None:
                        continue
                    
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # Detect faces
                    faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                    
                    if len(faces) > 0:
                        # Take the largest face
                        face = max(faces, key=lambda x: x[2] * x[3])
                        x, y, w, h = face
                        
                        # Add some margin
                        margin = 20
                        x = max(0, x - margin)
                        y = max(0, y - margin)
                        w = min(img.shape[1] - x, w + 2 * margin)
                        h = min(img.shape[0] - y, h + 2 * margin)
                        
                        # Extract and resize face
                        face_img = img[y:y+h, x:x+w]
                        face_img = cv2.resize(face_img, (160, 160))
                        
                        # Save aligned face
                        output_path = aligned_person_folder / f"{person_folder.name}_{i:03d}.png"
                        cv2.imwrite(str(output_path), face_img)
                        
                except Exception as e:
                    logger.warning(f"Error processing {image_file}: {e}")
                    continue
            
            aligned_count = len(list(aligned_person_folder.glob("*.png")))
            logger.info(f"Aligned {aligned_count} faces for {person_folder.name}")
        
        return True
    
    def extract_features(self):
        """Extract features from aligned faces using a simple CNN"""
        logger.info("Extracting features...")
        
        # Simple feature extraction using pre-trained MobileNet
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(160, 160, 3),
            include_top=False,
            weights='imagenet'
        )
        
        # Add global average pooling
        model = tf.keras.Sequential([
            base_model,
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu')
        ])
        
        features = []
        labels = []
        
        for person_folder in self.aligned_dir.iterdir():
            if not person_folder.is_dir():
                continue
                
            person_name = person_folder.name
            image_files = list(person_folder.glob("*.png"))
            
            for image_file in image_files:
                try:
                    # Load and preprocess image
                    img = cv2.imread(str(image_file))
                    if img is None:
                        continue
                    
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = img.astype(np.float32) / 255.0
                    img = np.expand_dims(img, axis=0)
                    
                    # Extract features
                    feature = model.predict(img, verbose=0)
                    features.append(feature.flatten())
                    labels.append(person_name)
                    
                except Exception as e:
                    logger.warning(f"Error extracting features from {image_file}: {e}")
                    continue
        
        return np.array(features), np.array(labels)
    
    def train_classifier(self):
        """Train SVM classifier"""
        logger.info("Training classifier...")
        
        # Extract features
        features, labels = self.extract_features()
        
        if len(features) == 0:
            logger.error("No features extracted!")
            return False
        
        logger.info(f"Extracted {len(features)} features from {len(set(labels))} people")
        
        # Encode labels
        label_encoder = LabelEncoder()
        encoded_labels = label_encoder.fit_transform(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, encoded_labels, test_size=0.2, random_state=42, stratify=encoded_labels
        )
        
        # Train SVM
        svm_model = SVC(kernel='rbf', probability=True, random_state=42)
        svm_model.fit(X_train, y_train)
        
        # Test accuracy
        y_pred = svm_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Training accuracy: {accuracy:.3f}")
        
        # Save model and label encoder
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.classifier_path, 'wb') as f:
            pickle.dump((svm_model, label_encoder.classes_), f)
        
        logger.info(f"Model saved to {self.classifier_path}")
        return True
    
    def full_training_pipeline(self):
        """Run complete training pipeline"""
        logger.info("Starting simplified training pipeline...")
        
        steps = [
            ("Preparing dataset", self.prepare_dataset),
            ("Detecting and aligning faces", self.detect_and_align_faces),
            ("Training classifier", self.train_classifier)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*50}")
            logger.info(f"STEP: {step_name}")
            logger.info(f"{'='*50}")
            
            if not step_func():
                logger.error(f"Failed at step: {step_name}")
                return False
        
        logger.info(f"\n{'='*50}")
        logger.info("🎉 TRAINING COMPLETED SUCCESSFULLY! 🎉")
        logger.info(f"{'='*50}")
        logger.info(f"Classifier saved to: {self.classifier_path}")
        
        return True

def main():
    trainer = SimpleFaceTrainer()
    trainer.full_training_pipeline()

if __name__ == "__main__":
    main()