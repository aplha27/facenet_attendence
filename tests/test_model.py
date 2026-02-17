#!/usr/bin/env python3
"""
Test the trained FaceNet model
"""

import os
import sys
import pickle
import cv2
import numpy as np
import tensorflow as tf
from pathlib import Path
import logging

# Add the facenet src to path
sys.path.append('attendance/facenet/src')

try:
    import facenet
    from align import detect_face
except ImportError as e:
    print(f"Error importing facenet modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTester:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.model_dir = self.project_root / "attendance/facenet/src/20180402-114759"
        self.classifier_path = self.model_dir / "my_classifier.pkl"
        self.test_images_dir = self.project_root / "attendance/facenet/dataset/test-images"
        
    def load_model(self):
        """Load the trained model and classifier"""
        logger.info("Loading FaceNet model and classifier...")
        
        # Check if classifier exists
        if not self.classifier_path.exists():
            logger.error(f"Classifier not found at {self.classifier_path}")
            logger.error("Please train the model first using: python train_model.py")
            return False
        
        # Load TensorFlow session
        self.sess = tf.Session()
        
        # Load MTCNN for face detection
        npy = ""
        self.pnet, self.rnet, self.onet = detect_face.create_mtcnn(self.sess, npy)
        
        # Load FaceNet model
        facenet.load_model(str(self.model_dir))
        
        # Get input and output tensors
        self.images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
        self.embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
        self.phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
        
        # Load classifier
        with open(self.classifier_path, 'rb') as infile:
            self.model, self.class_names = pickle.load(infile)
        
        logger.info(f"Model loaded successfully!")
        logger.info(f"Recognized classes: {self.class_names}")
        
        return True
    
    def recognize_face(self, image_path):
        """Recognize faces in an image"""
        logger.info(f"Processing image: {image_path}")
        
        # Read image
        frame = cv2.imread(str(image_path))
        if frame is None:
            logger.error(f"Could not read image: {image_path}")
            return []
        
        # Convert to RGB
        if frame.ndim == 2:
            frame = facenet.to_rgb(frame)
        frame = frame[:, :, 0:3]
        
        # Detect faces
        minsize = 20
        threshold = [0.6, 0.7, 0.7]
        factor = 0.709
        
        bounding_boxes, _ = detect_face.detect_face(frame, minsize, self.pnet, self.rnet, self.onet, threshold, factor)
        nrof_faces = bounding_boxes.shape[0]
        
        logger.info(f"Detected {nrof_faces} faces")
        
        results = []
        
        if nrof_faces > 0:
            det = bounding_boxes[:, 0:4]
            img_size = np.asarray(frame.shape)[0:2]
            
            for i in range(nrof_faces):
                # Extract face region
                bb = det[i].astype(int)
                
                # Check bounds
                if bb[0] <= 0 or bb[1] <= 0 or bb[2] >= frame.shape[1] or bb[3] >= frame.shape[0]:
                    logger.warning(f"Face {i} is too close to image boundary, skipping")
                    continue
                
                # Crop and preprocess face
                cropped = frame[bb[1]:bb[3], bb[0]:bb[2], :]
                cropped = facenet.flip(cropped, False)
                
                # Resize to 160x160
                scaled = cv2.resize(cropped, (160, 160), interpolation=cv2.INTER_CUBIC)
                scaled = facenet.prewhiten(scaled)
                scaled = scaled.reshape(-1, 160, 160, 3)
                
                # Get embedding
                feed_dict = {self.images_placeholder: scaled, self.phase_train_placeholder: False}
                emb_array = self.sess.run(self.embeddings, feed_dict=feed_dict)
                
                # Classify
                predictions = self.model.predict_proba(emb_array)
                best_class_indices = np.argmax(predictions, axis=1)
                best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
                
                # Get result
                class_name = self.class_names[best_class_indices[0]]
                confidence = best_class_probabilities[0]
                
                results.append({
                    'name': class_name,
                    'confidence': confidence,
                    'bbox': bb
                })
                
                logger.info(f"Face {i}: {class_name} (confidence: {confidence:.3f})")
        
        return results
    
    def test_all_images(self):
        """Test all images in the test directory"""
        logger.info("Testing all images in test directory...")
        
        if not self.test_images_dir.exists():
            logger.error(f"Test images directory not found: {self.test_images_dir}")
            return
        
        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(self.test_images_dir.glob(f"*{ext}"))
            image_files.extend(self.test_images_dir.glob(f"*{ext.upper()}"))
        
        if not image_files:
            logger.warning("No test images found!")
            logger.info(f"Please add test images to: {self.test_images_dir}")
            return
        
        logger.info(f"Found {len(image_files)} test images")
        
        for image_file in image_files:
            logger.info(f"\n{'='*50}")
            results = self.recognize_face(image_file)
            
            if results:
                logger.info(f"Recognition results for {image_file.name}:")
                for i, result in enumerate(results):
                    logger.info(f"  Face {i+1}: {result['name']} (confidence: {result['confidence']:.3f})")
            else:
                logger.info(f"No faces recognized in {image_file.name}")

def main():
    tester = ModelTester()
    
    if not tester.load_model():
        return
    
    # Test all images
    tester.test_all_images()
    
    logger.info("\nTesting completed!")

if __name__ == "__main__":
    main()