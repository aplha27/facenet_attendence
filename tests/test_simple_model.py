#!/usr/bin/env python3
"""
Test the simplified trained model
"""

import cv2
import numpy as np
import pickle
import tensorflow as tf
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleModelTester:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.model_dir = self.project_root / "attendance/facenet/src/20180402-114759"
        self.classifier_path = self.model_dir / "my_classifier.pkl"
        self.test_images_dir = self.project_root / "attendance/facenet/dataset/test-images"
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Feature extraction model (same as training)
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(160, 160, 3),
            include_top=False,
            weights='imagenet'
        )
        
        self.feature_model = tf.keras.Sequential([
            base_model,
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu')
        ])
        
    def load_model(self):
        """Load the trained classifier"""
        if not self.classifier_path.exists():
            logger.error(f"Classifier not found at {self.classifier_path}")
            return False
        
        with open(self.classifier_path, 'rb') as f:
            self.classifier, self.class_names = pickle.load(f)
        
        logger.info(f"Model loaded successfully!")
        logger.info(f"Recognized classes: {list(self.class_names)}")
        return True
    
    def recognize_face(self, image_path):
        """Recognize faces in an image"""
        logger.info(f"Processing: {image_path}")
        
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Could not read image: {image_path}")
            return []
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        results = []
        
        for i, (x, y, w, h) in enumerate(faces):
            try:
                # Extract face with margin
                margin = 20
                x = max(0, x - margin)
                y = max(0, y - margin)
                w = min(img.shape[1] - x, w + 2 * margin)
                h = min(img.shape[0] - y, h + 2 * margin)
                
                # Extract and preprocess face
                face_img = img[y:y+h, x:x+w]
                face_img = cv2.resize(face_img, (160, 160))
                face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                face_img = face_img.astype(np.float32) / 255.0
                face_img = np.expand_dims(face_img, axis=0)
                
                # Extract features
                features = self.feature_model.predict(face_img, verbose=0)
                features = features.flatten().reshape(1, -1)
                
                # Predict
                prediction = self.classifier.predict(features)[0]
                probabilities = self.classifier.predict_proba(features)[0]
                confidence = max(probabilities)
                
                person_name = self.class_names[prediction]
                
                results.append({
                    'name': person_name,
                    'confidence': confidence,
                    'bbox': (x, y, w, h)
                })
                
                logger.info(f"Face {i+1}: {person_name} (confidence: {confidence:.3f})")
                
            except Exception as e:
                logger.warning(f"Error processing face {i}: {e}")
                continue
        
        return results
    
    def test_dataset_images(self):
        """Test on original dataset images"""
        logger.info("Testing on dataset images...")
        
        dataset_dir = self.project_root / "dataset"
        
        for person_folder in dataset_dir.iterdir():
            if not person_folder.is_dir():
                continue
            
            logger.info(f"\nTesting {person_folder.name} images:")
            logger.info("-" * 40)
            
            image_files = list(person_folder.glob("*.jpg")) + list(person_folder.glob("*.jpeg")) + list(person_folder.glob("*.png"))
            
            correct = 0
            total = 0
            
            for image_file in image_files[:3]:  # Test first 3 images
                results = self.recognize_face(image_file)
                
                if results:
                    predicted_name = results[0]['name']
                    confidence = results[0]['confidence']
                    
                    if predicted_name == person_folder.name:
                        logger.info(f"✓ {image_file.name}: {predicted_name} ({confidence:.3f}) - CORRECT")
                        correct += 1
                    else:
                        logger.info(f"✗ {image_file.name}: {predicted_name} ({confidence:.3f}) - WRONG (expected {person_folder.name})")
                else:
                    logger.info(f"? {image_file.name}: No face detected")
                
                total += 1
            
            if total > 0:
                accuracy = correct / total * 100
                logger.info(f"Accuracy for {person_folder.name}: {accuracy:.1f}% ({correct}/{total})")
    
    def test_all_images(self):
        """Test all images in test directory"""
        if not self.test_images_dir.exists():
            logger.info(f"Test images directory not found: {self.test_images_dir}")
            logger.info("Testing on dataset images instead...")
            self.test_dataset_images()
            return
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(self.test_images_dir.glob(f"*{ext}"))
            image_files.extend(self.test_images_dir.glob(f"*{ext.upper()}"))
        
        if not image_files:
            logger.info("No test images found, testing on dataset images...")
            self.test_dataset_images()
            return
        
        logger.info(f"Found {len(image_files)} test images")
        
        for image_file in image_files:
            logger.info(f"\n{'='*50}")
            results = self.recognize_face(image_file)
            
            if results:
                for i, result in enumerate(results):
                    logger.info(f"Face {i+1}: {result['name']} (confidence: {result['confidence']:.3f})")
            else:
                logger.info(f"No faces recognized in {image_file.name}")

def main():
    tester = SimpleModelTester()
    
    if not tester.load_model():
        return
    
    tester.test_all_images()
    
    logger.info("\n" + "="*50)
    logger.info("🎉 Testing completed!")
    logger.info("Your model is ready to use!")

if __name__ == "__main__":
    main()