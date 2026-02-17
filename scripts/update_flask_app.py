#!/usr/bin/env python3
"""
Update Flask app to use the new trained model
"""

import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_original_routes():
    """Backup the original routes file"""
    routes_file = Path("attendance/routes.py")
    backup_file = Path("attendance/routes_original.py")
    
    if routes_file.exists() and not backup_file.exists():
        shutil.copy2(routes_file, backup_file)
        logger.info("Backed up original routes.py to routes_original.py")

def create_updated_routes():
    """Create updated routes that use the new model"""
    routes_content = '''"""
Updated routes using the new simplified face recognition model
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from flask import render_template, url_for, flash, redirect, request, jsonify, abort, make_response
from attendance import app, db, bcrypt
from attendance.forms import RegistrationForm, LoginForm, AddForm, EditForm
from attendance.models import User, Add
from flask_login import login_user, current_user, logout_user, login_required

import os
import pickle
import sys
import time
import cv2
import numpy as np
import tensorflow as tf
import sqlite3
import xlsxwriter
import datetime
import requests
from werkzeug.utils import secure_filename
from pathlib import Path

# Import the new configuration manager
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.configuration_manager import config_manager

# Initialize the face recognition components
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Feature extraction model (same as training)
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(160, 160, 3),
    include_top=False,
    weights='imagenet'
)

feature_model = tf.keras.Sequential([
    base_model,
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(64, activation='relu')
])

# Load the trained classifier
classifier_path = Path("attendance/facenet/src/20180402-114759/my_classifier.pkl")
classifier = None
class_names = None

if classifier_path.exists():
    with open(classifier_path, 'rb') as f:
        classifier, class_names = pickle.load(f)
    print(f"Loaded classifier with classes: {list(class_names)}")
else:
    print("Warning: Classifier not found. Please train the model first.")

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/register", methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to Log In', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET','POST'])    
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('You have been logged in!','success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page) 
            else:
                return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check Email and Password','danger')    
    return render_template('login.html', title='Login', form=form)

@app.route("/add", methods=['GET','POST'])
@login_required
def add():
    form = AddForm()
    if form.validate_on_submit():
        # Create class entry
        new = Add(
            classname=form.classname.data, 
            coordinator=form.coordinator.data, 
            co_email=form.co_email.data, 
            stuname=form.stuname_1.data, 
            regno=form.regno_1.data, 
            mobileno=form.mobileno_1.data
        )
        db.session.add(new)
        
        # Add other students
        students = [
            (form.stuname_2.data, form.regno_2.data, form.mobileno_2.data),
            (form.stuname_3.data, form.regno_3.data, form.mobileno_3.data),
            (form.stuname_4.data, form.regno_4.data, form.mobileno_4.data),
            (form.stuname_5.data, form.regno_5.data, form.mobileno_5.data)
        ]
        
        for stuname, regno, mobileno in students:
            if stuname and regno and mobileno:  # Only add if all fields are filled
                new_student = Add(stuname=stuname, regno=regno, mobileno=mobileno)
                db.session.add(new_student)
        
        db.session.commit()
        flash('A new class has been created!','success')
        return redirect(url_for('home'))
    return render_template('add.html', title='Adding Class', form=form)

@app.route("/edit", methods=['GET','POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        db.session.commit()
        flash('The existing class has been updated!','success')
        return redirect(url_for('home'))
    return render_template('edit.html', title='Editing Class', form=form)    

@app.route("/take")
@login_required
def take():
    return render_template('take.html', title="Take Attendance")        

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/recognition")
def recognition():
    return render_template('recog.html', title="Recognized students")

def recognize_faces_in_image(image_path):
    """Recognize faces using the new trained model"""
    if classifier is None:
        return []
    
    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        return []
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    recognized_names = []
    
    for (x, y, w, h) in faces:
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
            features = feature_model.predict(face_img, verbose=0)
            features = features.flatten().reshape(1, -1)
            
            # Predict
            prediction = classifier.predict(features)[0]
            probabilities = classifier.predict_proba(features)[0]
            confidence = max(probabilities)
            
            # Only accept high confidence predictions
            if confidence > 0.5:  # Adjust threshold as needed
                person_name = class_names[prediction]
                recognized_names.append(person_name)
                print(f"Recognized: {person_name} (confidence: {confidence:.3f})")
            
        except Exception as e:
            print(f"Error processing face: {e}")
            continue
    
    return recognized_names

@app.route("/face_recog", methods=['GET','POST'])
def face_recog():
    if request.method == "POST":
        try:
            file = request.files["image"]
            if not file:
                flash('No file uploaded!', 'error')
                return render_template('take.html', title="Take Attendance")
            
            filename = secure_filename(file.filename)
            
            # Save uploaded file
            upload_dir = config_manager.get_upload_directory()
            upload_dir.mkdir(exist_ok=True)
            
            img_path = upload_dir / filename
            file.save(str(img_path))
            
            # Recognize faces
            recognized_names = recognize_faces_in_image(img_path)
            
            if not recognized_names:
                flash('No faces recognized in the uploaded image!', 'warning')
                return render_template('take.html', title="Take Attendance")
            
            # Generate attendance report
            report_dir = config_manager.get_reports_directory()
            report_dir.mkdir(exist_ok=True)
            
            report_filename = f'Report_for_{datetime.datetime.now().strftime("%Y_%m_%d-%H_%M")}.xlsx'
            report_path = report_dir / report_filename
            
            workbook = xlsxwriter.Workbook(str(report_path))
            worksheet = workbook.add_worksheet()
            
            # Write headers
            worksheet.write(0, 0, 'Student Name')
            worksheet.write(0, 1, 'Attendance Status')
            worksheet.write(0, 2, 'Date')
            worksheet.write(0, 3, 'Time')
            
            # Get all students from database
            conn = sqlite3.connect(config_manager.get_database_url().replace('sqlite:///', ''))
            c = conn.cursor()
            students = c.execute("SELECT DISTINCT stuname FROM 'add' WHERE stuname IS NOT NULL").fetchall()
            conn.close()
            
            # Write attendance data
            row = 1
            for student_row in students:
                student_name = student_row[0]
                if student_name in recognized_names:
                    status = 'Present'
                else:
                    status = 'Absent'
                
                worksheet.write(row, 0, student_name)
                worksheet.write(row, 1, status)
                worksheet.write(row, 2, datetime.datetime.now().strftime("%Y-%m-%d"))
                worksheet.write(row, 3, datetime.datetime.now().strftime("%H:%M:%S"))
                row += 1
            
            workbook.close()
            
            flash(f'Attendance processed successfully! {len(recognized_names)} faces recognized. Report saved as {report_filename}', 'success')
            
        except Exception as e:
            flash(f'Error processing attendance: {str(e)}', 'error')
            print(f"Error in face_recog: {e}")
    
    return render_template('take.html', title="Take Attendance")

@app.route("/mark", methods=['GET','POST'])
def mark():
    return render_template('take.html', title="Take Attendance")

@app.route("/sms", methods=['GET','POST'])
def sms():    
    return render_template('take.html', title="Take Attendance")
'''
    
    with open("attendance/routes_updated.py", "w", encoding='utf-8') as f:
        f.write(routes_content)
    
    logger.info("Created updated routes file: attendance/routes_updated.py")

def main():
    logger.info("Updating Flask application to use new model...")
    
    backup_original_routes()
    create_updated_routes()
    
    logger.info("\n" + "=" * 50)
    logger.info("UPDATE COMPLETE!")
    logger.info("=" * 50)
    logger.info("Files created:")
    logger.info("- attendance/routes_original.py (backup)")
    logger.info("- attendance/routes_updated.py (new version)")
    logger.info("\nTo use the new model:")
    logger.info("1. Replace attendance/routes.py with attendance/routes_updated.py")
    logger.info("2. Or manually integrate the changes")
    logger.info("3. Run your Flask app and test the attendance feature")

if __name__ == "__main__":
    main()