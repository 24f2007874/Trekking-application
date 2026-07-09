from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date, datetime ,timezone

db = SQLAlchemy()

class Admin(db.Model, UserMixin):
    __tablename__ ="admins"
    id=db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="admin")
    def get_id(self):
        return self.user_id
    
class user(db.Model,UserMixin):
    __tablename__ = "trekkers"
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    blocklisted = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="trekker")
    bookings = db.relationship('Booking', backref='trekker', lazy=True)
    def get_id(self):
        return str(self.user_id)
    
class staff(db.Model,UserMixin):
    __tablename__="staff"
    user_id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=True) 
    name = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="staff")
    assigned_treks = db.relationship('trek', backref='lead_staff', lazy=True)

    def get_id(self):
        return str(self.user_id)
    
class trek(db.Model,UserMixin):
    __tablename__="trek"
    id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(50)) # Easy, Moderate, Hard
    total_slots = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False) #keeps decreasing
    status = db.Column(db.String(20), default='Pending')
    # FOREIGN KEY: Links the trek to an assigned staff member [2, 3]
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('staff.user_id'), nullable=True)
    # RELATIONSHIP: backref 'event' injected into Booking model.
    # Essential for staff to view lists of registered users per trek [5, 7, 8].
    registrations = db.relationship('Booking', backref='event', lazy=True)


class Booking(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    booking_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='Booked')
    user_id = db.Column(db.Integer, db.ForeignKey('trekkers.user_id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)