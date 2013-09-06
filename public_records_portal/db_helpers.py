""" 
.. module:: db_helpers
	:synopsis: Functions that interact with the Postgres database via Flask-SQLAlchemy
.. modlueauthor:: Richa Agarwal <richa@codeforamerica.org>
"""


from public_records_portal import db, app
from models import *
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy import func


### @export "get_obj"
def get_obj(obj_type, obj_id):
	""" A wrapper to query the database for an object via its class/type (defined in models.py) and ID. """
	if not obj_id:
		return None
	# There has to be a better way of doing this
	if obj_type == "User":
		return User.query.get(obj_id)
	elif obj_type == "Request":
		return Request.query.get(obj_id)
	elif obj_type == "Owner":
		return Owner.query.get(obj_id)
	elif obj_type == "Note":
		return Note.query.get(obj_id)
	elif obj_type == "QA":
		return QA.query.get(obj_id)
	elif obj_type == "Subscriber":
		return Subscriber.query.get(obj_id)
	return None

### @export "get_objs"
def get_objs(obj_type):
	""" A wrapper to query the database for all objects of a certain class/type (defined in models.py) """
	# There has to be a better way of doing this
	if obj_type == "User":
		return User.query.all()
	elif obj_type == "Request":
		return Request.query.all()
	elif obj_type == "Owner":
		return Owner.query.all()
	elif obj_type == "Note":
		return Note.query.all()
	elif obj_type == "QA":
		return QA.query.all()
	elif obj_type == "Subscriber":
		return Subscriber.query.all()
	return None

### @export "get_request_by_owner"
def get_request_by_owner(owner_id):
	""" Return the request that a particular owner belongs to """
	if not owner_id:
		return None
	return Request.query.filter_by(current_owner = owner_id).first()

### @export "get_owners_by_user_id"
def get_owners_by_user_id(user_id):
	""" Return the queryset of owners for a particular user. (A user can be associated with multiple owners)."""
	if not user_id:
		return None
	return Owner.query.filter_by(user_id = user_id)

### @export "put_obj"
def put_obj(obj):
	""" Add and commit the object to the database. Return true if successful. """
	if obj:
		db.session.add(obj)
		db.session.commit()
		return True
	return False

def get_attribute(attribute, obj_id = None, obj_type = None, obj = None):
	""" Obtain the object by obj_id and obj_type if obj is not provided, and return the specified attribute for that object. """
	if obj_id and obj_type:
		obj = get_obj(obj_type, obj_id)
	if obj:
		try:
			return getattr(obj, attribute)
		except:
			return None
	return None


def update_obj(attribute, val, obj_type = None, obj_id = None, obj = None):
	""" Obtain the object by obj_id and obj_type if obj is not provided, and update the specified attribute for that object. Return true if successful. """
	if obj_id and obj_type:
		obj = get_obj(obj_type, obj_id)
	if obj:
		try:
			setattr(obj, attribute, val)
			db.session.add(obj)
			db.session.commit()
			return True
		except:
			return False
	return False

def create_QA(request_id, question, owner_id):
	""" Create a QA object and return the ID. """
	qa = QA(request_id = request_id, question = question, owner_id = owner_id)
	db.session.add(qa)
	db.session.commit()
	return qa.id

def create_request(text, user_id):
	""" Create a Request object and return the ID. """
	req = Request(text = text, creator_id = user_id)
	db.session.add(req)
	db.session.commit()
	return req.id

def create_subscriber(request_id, user_id):
	""" Create a Subscriber object and return the ID. """
	subscriber = Subscriber(request_id = request_id, user_id = user_id)
	db.session.add(subscriber)
	db.session.commit()
	return subscriber.id

def create_note(request_id, text, user_id):
	""" Create a Note object and return the ID. """
	try:
		note = Note(request_id = request_id, text = text, user_id = user_id)
		put_obj(note)
		return note.id
	except:
		return None

def create_record(request_id, user_id, description, doc_id = None, filename = None, access = None, url = None):
	# try:
		record = Record(doc_id = doc_id, request_id = request_id, user_id = user_id, description = description, filename = filename, url = url, access = access)
		put_obj(record)
		return record.id
	# except:
		# return None

def remove_obj(obj_type, obj_id):
	obj = get_obj(obj_type, obj_id)
	db.session.delete(obj)
	db.session.commit()

def create_answer(qa_id, subscriber_id, answer):
	qa = get_obj("QA", qa_id)
	qa.subscriber_id = subscriber_id
	qa.answer = answer
	db.session.add(qa)
	db.session.commit()
	return qa.request_id

def create_or_return_user(email, alias = None, phone = None, department = None, not_id = False):
	user = User.query.filter(func.lower(User.email) == func.lower(email)).first() 
	if not user:
		user = User(email = email, alias = alias, phone = phone, department = department, password = app.config['ADMIN_PASSWORD'])
	else:
		if alias:
			user.alias = alias
		if phone:
			user.phone = phone
		if department:
			user.department = department
	if not user.password:
		user.password = app.config['ADMIN_PASSWORD']
	db.session.add(user)
	db.session.commit()
	if not_id:
		return user
	return user.id

def create_owner(request_id, reason, email = None, user_id = None):
	""" Adds a staff member to the request without assigning them as current owner. (i.e. "participant")
	Useful for multidepartmental requests."""
	if not user_id:
		user_id = create_or_return_user(email = email)
	participant = Owner(request_id = request_id, user_id = user_id, reason = reason)
	db.session.add(participant)
	db.session.commit()
	return participant.id

def change_request_status(request_id, status):
	req = get_obj("Request", request_id)
	req.status = status
	req.status_updated = datetime.now().isoformat()
	db.session.add(req)
	db.session.commit()

def find_request(text):
	req = Request.query.filter_by(text = text).first()
	if req:
		return req.id
	return None

def find_owner(request_id, user_id):
	owner = Owner.query.filter_by(request_id = request_id, user_id = user_id).first() 
	if owner:
		return owner.id
	return None

def add_staff_participant(request_id, user_id):
	participant = Owner.query.filter_by(request_id = request_id, user_id = user_id)
	if not participant:
		participant = Owner(request_id = request_id, user_id = user_id, reason = "Participant")
		db.session.add(participant)
		db.session.commit()
		return participant.id
	else:
		return None

def authenticate_login(email, password):
	if email:
		user = create_or_return_user(email=email, not_id = True)
		if user.password == password:
			return user
	return None







