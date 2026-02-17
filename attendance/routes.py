from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from flask import render_template,url_for,flash,redirect,request,jsonify,abort,make_response
from attendance import app, db
from attendance.forms import RegistrationForm, LoginForm, AddForm, EditForm
from attendance.models import User,Add
from flask_login import login_user, current_user, logout_user, login_required

import os
import pickle
import sys
import time
import cv2
import numpy as np
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
# from scipy import misc
from PIL import Image
import attendance.facenet.src.facenet as facenet
from attendance.facenet.src.align import detect_face
# from keras.models import load_model
from flask_httpauth import HTTPBasicAuth
import sqlite3
import xlsxwriter
import datetime
import requests
from werkzeug.utils import secure_filename

auth = HTTPBasicAuth()

# Initialize FaceNet resources
print("Loading FaceNet models...")
# Paths
basedir = os.path.abspath(os.path.dirname(__file__))
# Correct path to model directory relative to routes.py (attendance/)
model_dir = os.path.join(basedir, 'facenet', 'src', '20180402-114759')
classifier_path = os.path.join(model_dir, 'my_classifier.pkl')
npy_path = os.path.join(basedir, 'facenet', 'src', 'align')

# Global TensorFlow Session
graph = tf.Graph()
sess = tf.Session(graph=graph)

with graph.as_default():
    with sess.as_default():
        # Load MTCNN
        print('Loading MTCNN...')
        pnet, rnet, onet = detect_face.create_mtcnn(sess, npy_path)
        
        # Load FaceNet Model
        print(f'Loading FaceNet from {model_dir}...')
        # Point to pb file explicitly if needed, or dir
        facenet.load_model(os.path.join(model_dir, '20180402-114759.pb'))
        
        # Get tensors
        images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
        embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
        phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
        embedding_size = embeddings.get_shape()[1]

# Load Classifier
with open(classifier_path, 'rb') as infile:
    (model, class_names) = pickle.load(infile)
print(f'Loaded classifier: {class_names}')

def recognize_face_helper(image_path):
    print(f"Processing {image_path}")
    img_list = []
    
    try:
        img = np.array(Image.open(image_path))
    except Exception as e:
        print(f"Error opening image: {e}")
        return []

    if img.ndim == 2:
        img = facenet.to_rgb(img)
    img = img[:,:,0:3]

    minsize = 20
    threshold = [0.6, 0.7, 0.7]
    factor = 0.709

    with graph.as_default():
        with sess.as_default():
            bounding_boxes, _ = detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold, factor)
    
    nrof_faces = bounding_boxes.shape[0]
    print(f"Detected {nrof_faces} faces")
    
    if nrof_faces > 0:
        det = bounding_boxes[:,0:4]
        img_size = np.asarray(img.shape)[0:2]
        
        cropped_images = []
        
        for i in range(nrof_faces):
            bb = np.zeros(4, dtype=np.int32)
            margin = 32 # Consistent with aligned dataset
            bb[0] = np.maximum(det[i][0]-margin/2, 0)
            bb[1] = np.maximum(det[i][1]-margin/2, 0)
            bb[2] = np.minimum(det[i][2]+margin/2, img_size[1])
            bb[3] = np.minimum(det[i][3]+margin/2, img_size[0])
            cropped = img[bb[1]:bb[3],bb[0]:bb[2],:]
            
            # aligned = misc.imresize(cropped, (160, 160), interp='bilinear') # Deprecated
            aligned = np.array(Image.fromarray(cropped).resize((160, 160), Image.BILINEAR))
            
            prewhitened = facenet.prewhiten(aligned)
            cropped_images.append(prewhitened)
            
        images_array = np.stack(cropped_images)
        
        with graph.as_default():
            with sess.as_default():
                feed_dict = { images_placeholder: images_array, phase_train_placeholder: False }
                emb_array = sess.run(embeddings, feed_dict=feed_dict)
                
        predictions = model.predict_proba(emb_array)
        best_class_indices = np.argmax(predictions, axis=1)
        best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
        
        results = []
        for i in range(len(best_class_indices)):
            name = class_names[best_class_indices[i]]
            prob = best_class_probabilities[i]
            print(f"Recognized: {name} ({prob})")
            if prob > 0.75: # Threshold updated to 75% accuracy
                # Convert name (e.g. 'vivek_n') to expected format if needed
                results.append(name.replace('_', ' '))
        
        return results
    return []

@app.route("/")
@app.route("/home")
def home():
	return redirect(url_for('take'))

@app.route("/about")
def about():
	return render_template('about.html',title='About')

@app.route("/register", methods=['GET','POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		# TODO: Re-enable password hashing when bcrypt is available
		# hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		hashed_password = form.password.data  # Temporary: store plain text password
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash('Your account has been created! You are now able to Log In', 'success')
		return redirect(url_for('login'))
	return render_template('register.html',title='Register',form=form)

@app.route("/login", methods=['GET','POST'])	
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		# TODO: Re-enable password hashing when bcrypt is available
		# if user and bcrypt.check_password_hash(user.password, form.password.data):
		if user and user.password == form.password.data:  # Temporary: plain text comparison
			login_user(user, remember=form.remember.data)
			flash('You have been logged in!','success')
			next_page = request.args.get('next')
			if next_page:
				return redirect(next_page) 
			else:
				return redirect(url_for('home'))
		else:
			flash('Login Unsuccessful. Please check Email and Password','danger')	
	return render_template('login.html',title='Login',form=form)

@app.route("/add", methods=['GET','POST'])
@login_required
def add():
	form = AddForm()
	if form.validate_on_submit():
		new = Add(classname=form.classname.data, coordinator=form.coordinator.data, co_email=form.co_email.data, stuname=form.stuname_1.data, regno=form.regno_1.data, mobileno=form.mobileno_1.data)
		db.session.add(new)
		new = Add(stuname=form.stuname_2.data, regno=form.regno_2.data, mobileno=form.mobileno_2.data)
		db.session.add(new)
		new = Add(stuname=form.stuname_3.data, regno=form.regno_3.data, mobileno=form.mobileno_3.data)
		db.session.add(new)		
		new = Add(stuname=form.stuname_4.data, regno=form.regno_4.data, mobileno=form.mobileno_4.data)
		db.session.add(new)
		new = Add(stuname=form.stuname_5.data, regno=form.regno_5.data, mobileno=form.mobileno_5.data)						
		db.session.add(new)
		db.session.commit()
		flash('A new class has been created!','success')
		return redirect(url_for('home'))
	return render_template('add.html',title='Adding Class',form=form)

@app.route("/edit",methods=['GET','POST'])
@login_required
def edit():
	form = EditForm()
	if form.validate_on_submit():
		db.session.commit()
		flash('The existing class has been updated!','success')
		return redirect(url_for('home'))
	return render_template('edit.html',title='Editing Class',form=form)	

@app.route("/take")
def take():
	return render_template('take.html',title="Take Attendance")		

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('home'))

@app.route("/recognition")
def recognition():
	return render_template('recog.html',title="Recognized students")
	
@app.route("/face_recog", methods=['GET','POST'])
def face_recog():
	if request.method == "POST":
		# Use new secure file handling system
		if 'image' not in request.files:
			flash('No image file provided', 'danger')
			return render_template('take.html', title="Take Attendance")
		
		file = request.files['image']
		if file.filename == '':
			flash('No image file selected', 'danger')
			return render_template('take.html', title="Take Attendance")
		
		# Process upload securely
		from utils.file_security_utils import upload_helper
		upload_result = upload_helper.process_upload(file, 'images')
		
		if not upload_result['success']:
			error_msg = upload_result['error']
			if 'details' in upload_result:
				error_msg += ': ' + '; '.join(upload_result['details'])
			flash(f'File upload failed: {error_msg}', 'danger')
			return render_template('take.html', title="Take Attendance")
		
		# Get secure file path
		file_info = upload_result['file_info']
		img_path = file_info['file_path']
		
		# Show warnings if any
		if upload_result.get('warnings'):
			for warning in upload_result['warnings']:
				flash(f'Warning: {warning}', 'warning')
	
		# Perform recognition
		recognized_names = recognize_face_helper(img_path)
		
		if recognized_names:
			flash(f'Recognized: {", ".join(recognized_names)}', 'success')
			
			# Generate Excel Report
			try:
				report_folder = os.path.join(app.root_path, '..', 'reports')
				if not os.path.exists(report_folder):
					os.makedirs(report_folder)
					
				filename = 'Report_for_' + datetime.datetime.now().strftime("%Y_%m_%d-%H_%M") + '.xlsx'
				filepath = os.path.join(report_folder, filename)
				
				workbook = xlsxwriter.Workbook(filepath)
				worksheet = workbook.add_worksheet()
				
				# Get students from DB
				# Note: Assuming 'add' table structure from original code
				# Using direct sqlite for simplicity as in original code, or models
				conn = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
				c = conn.cursor()
				students_cursor = c.execute("SELECT stuname FROM 'add'")
				
				worksheet.write(0, 0, 'Student Name')
				worksheet.write(0, 1, 'Status')
				worksheet.write(0, 2, 'Time')
				
				row = 1
				for db_row in students_cursor:
					student_name = db_row[0]
					worksheet.write(row, 0, student_name)
					
					# Simple check - modify regex or matching to be robust
					is_present = False
					for rec_name in recognized_names:
						if rec_name.lower() in student_name.lower() or student_name.lower() in rec_name.lower():
							is_present = True
							break
					
					if is_present:
						worksheet.write(row, 1, 'Present')
						worksheet.write(row, 2, datetime.datetime.now().strftime("%H:%M:%S"))
					else:
						worksheet.write(row, 1, 'Absent')
					row += 1
					
				workbook.close()
				conn.close()
				flash(f'Attendance report generated: {filename}', 'info')
				
			except Exception as e:
				flash(f'Error generating report: {e}', 'warning')
				print(e)

		else:
			flash('No faces recognized or low confidence.', 'warning')

	return render_template('take.html', title="Take Attendance")	                   

@app.route("/mark", methods=['GET','POST'])
def mark():
	#workbook = xlsxwriter.Workbook('C:\\Users\\Dell\\Attendance\\Reports\\Report_for_'+ datetime.datetime.now().strftime("%Y_%m_%d-%H")+'.xlsx')
	#worksheet = workbook.add_worksheet()
	#conn = sqlite3.connect('C:\\Users\\Dell\\Attendance\\attendance\\site.db')
	#c = conn.cursor()
	#students = c.execute("SELECT stuname FROM 'add'")
	#name = face_recog()
	#for i, row in enumerate(students):
		#for j, value in enumerate(row):
			#worksheet.write_string(i,j, str(value))
			#if name == value:
				#worksheet.write_string(i,j+1,'Present') 
			#else:
				#worksheet.write_string(i,j+1, 'Absent')
	#workbook.close()
	return render_template('take.html',title="Take Attendance")

@app.route("/sms", methods=['GET','POST'])
def sms():	
	return render_template('take.html',title="Take Attendance")
