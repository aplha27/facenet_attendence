from datetime import datetime
from attendance import app, db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(db.Model,UserMixin):
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(20),unique=True,nullable=False)
	email = db.Column(db.String(120),unique=True,nullable=False)
	password = db.Column(db.String(60),nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	
	def __repr__(self):
		return f"User('{self.username}','{self.email}')"

class Student(db.Model):
	"""Student model with improved structure"""
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	registration_number = db.Column(db.String(50), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=True)
	phone = db.Column(db.String(20), nullable=True)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	
	def __repr__(self):
		return f"Student('{self.name}', '{self.registration_number}')"

class Class(db.Model):
	"""Class model with improved structure"""
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	coordinator = db.Column(db.String(100), nullable=False)
	coordinator_email = db.Column(db.String(120), nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	
	def __repr__(self):
		return f"Class('{self.name}', '{self.coordinator}')"

class ClassEnrollment(db.Model):
	"""Many-to-many relationship between students and classes"""
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
	class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
	enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
	
	def __repr__(self):
		return f"ClassEnrollment(student_id={self.student_id}, class_id={self.class_id})"

# Legacy model for backward compatibility
class Add(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	classname = db.Column(db.String(20),unique=True)
	coordinator = db.Column(db.String(30), unique=True)
	co_email = db.Column(db.String(30),unique=True)
	stuname = db.Column(db.String(30),unique=True)
	regno = db.Column(db.Integer,unique=True)
	mobileno = db.Column(db.Integer,unique=True)
	
	def __repr__(self):
		return f"Add('{self.classname}','{self.coordinator}','{self.co_email}','{self.stuname}','{self.regno}','{self.mobileno}')"