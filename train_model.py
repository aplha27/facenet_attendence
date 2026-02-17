#!/usr/bin/env python3
"""
FaceNet Model Training Script
Comprehensive script to train the face recognition model for attendance system
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FaceNetTrainer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dataset_dir = self.project_root / "dataset"
        self.raw_dir = self.project_root / "attendance/facenet/dataset/raw"
        self.aligned_dir = self.project_root / "attendance/facenet/dataset/aligned"
        self.model_dir = self.project_root / "attendance/facenet/src/20180402-114759"
        self.classifier_path = self.model_dir / "my_classifier.pkl"
        
    def prepare_dataset(self):
        """Copy dataset from main dataset folder to facenet raw folder"""
        logger.info("Preparing dataset...")
        
        # Create raw directory if it doesn't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy each person's folder from dataset to raw
        for person_folder in self.dataset_dir.iterdir():
            if person_folder.is_dir():
                dest_folder = self.raw_dir / person_folder.name
                
                # Remove existing folder if it exists
                if dest_folder.exists():
                    shutil.rmtree(dest_folder)
                
                # Copy the folder
                shutil.copytree(person_folder, dest_folder)
                logger.info(f"Copied {person_folder.name} dataset to {dest_folder}")
                
                # Count images
                image_count = len(list(dest_folder.glob("*.jpg"))) + len(list(dest_folder.glob("*.jpeg"))) + len(list(dest_folder.glob("*.png")))
                logger.info(f"  - {image_count} images found for {person_folder.name}")
        
        logger.info("Dataset preparation completed!")
        return True
        
    def align_faces(self):
        """Align faces using MTCNN"""
        logger.info("Starting face alignment with MTCNN...")
        
        # Create aligned directory
        self.aligned_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to alignment script
        align_script = self.project_root / "attendance/facenet/src/align/align_dataset_mtcnn.py"
        
        if not align_script.exists():
            logger.error(f"Alignment script not found at {align_script}")
            return False
            
        # Run alignment command
        cmd = [
            sys.executable,
            str(align_script),
            str(self.raw_dir),
            str(self.aligned_dir),
            "--image_size", "160",
            "--margin", "32"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root / "attendance") + os.pathsep + env.get("PYTHONPATH", "")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root), env=env)
            
            if result.returncode == 0:
                logger.info("Face alignment completed successfully!")
                logger.info(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"Face alignment failed with return code {result.returncode}")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running face alignment: {e}")
            return False
    
    def train_classifier(self):
        """Train the SVM classifier"""
        logger.info("Starting classifier training...")
        
        # Path to classifier script
        classifier_script = self.project_root / "attendance/facenet/src/classifier.py"
        
        if not classifier_script.exists():
            logger.error(f"Classifier script not found at {classifier_script}")
            return False
        
        # Run training command
        cmd = [
            sys.executable,
            str(classifier_script),
            "TRAIN",
            str(self.aligned_dir),
            str(self.model_dir / "20180402-114759.pb"),
            str(self.classifier_path),
            "--batch_size", "1000",
            "--min_nrof_images_per_class", "5",
            "--nrof_train_images_per_class", "10",
            "--use_split_dataset"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root / "attendance") + os.pathsep + env.get("PYTHONPATH", "")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root), env=env)
            
            if result.returncode == 0:
                logger.info("Classifier training completed successfully!")
                logger.info(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"Classifier training failed with return code {result.returncode}")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running classifier training: {e}")
            return False
    
    def verify_training(self):
        """Verify that training was successful"""
        logger.info("Verifying training results...")
        
        # Check if classifier file exists
        if self.classifier_path.exists():
            logger.info(f"✓ Classifier file created: {self.classifier_path}")
            logger.info(f"  File size: {self.classifier_path.stat().st_size} bytes")
        else:
            logger.error(f"✗ Classifier file not found: {self.classifier_path}")
            return False
        
        # Check aligned faces
        aligned_count = 0
        for person_folder in self.aligned_dir.iterdir():
            if person_folder.is_dir():
                images = list(person_folder.glob("*.png")) + list(person_folder.glob("*.jpg"))
                aligned_count += len(images)
                logger.info(f"  {person_folder.name}: {len(images)} aligned faces")
        
        logger.info(f"Total aligned faces: {aligned_count}")
        
        if aligned_count > 0:
            logger.info("✓ Training verification completed successfully!")
            return True
        else:
            logger.error("✗ No aligned faces found!")
            return False
    
    def full_training_pipeline(self):
        """Run the complete training pipeline"""
        logger.info("Starting full training pipeline...")
        
        steps = [
            ("Preparing dataset", self.prepare_dataset),
            ("Aligning faces", self.align_faces),
            ("Training classifier", self.train_classifier),
            ("Verifying training", self.verify_training)
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
        logger.info("You can now use the trained model for attendance recognition!")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Train FaceNet model for attendance system")
    parser.add_argument("--step", choices=["prepare", "align", "train", "verify", "all"], 
                       default="all", help="Which step to run")
    
    args = parser.parse_args()
    
    trainer = FaceNetTrainer()
    
    if args.step == "prepare":
        trainer.prepare_dataset()
    elif args.step == "align":
        trainer.align_faces()
    elif args.step == "train":
        trainer.train_classifier()
    elif args.step == "verify":
        trainer.verify_training()
    elif args.step == "all":
        trainer.full_training_pipeline()

if __name__ == "__main__":
    main()