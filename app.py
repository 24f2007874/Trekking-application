from flask import Flask , flash , render_template ,request,redirect,url_for
from models import db ,Admin,user,staff,Booking,trek
from decorators import rn_required ,trekker_only ,assigned_staff_only
from datetime import date , datetime
from flask_login import LoginManager ,current_user , login_user , login_required ,logout_user
import re
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key="super_secret_key_2112"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prakruthi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def create_admin():
    db.create_all()
    if not Admin.query.filter_by(user_id="admin").first():
        admin = Admin(user_id="admin",password=generate_password_hash("admin123"),role="admin")
        db.session.add(admin)
        db.session.commit()
        print("Admin created successfully ! " )
""" or else = current_user will be empty after the first request
will not be able to check current_user.role or id ..blah blah.."""

@login_manager.user_loader
def load_user(User_id):
    admin=Admin.query.filter_by(user_id=User_id).first()
    if admin:
        return admin
    cuser = user.query.filter_by(user_id=User_id).first()
    if cuser:
        return cuser
    try:
        cstaff = staff.query.get(int(User_id))
        if cstaff:
            return cstaff
    except ValueError:
        pass
    return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method=="POST":
        name=request.form["name"]
        email=request.form["email"]
        user_id=request.form["user_id"]
        password=request.form["password"]
        MAIL_REGEX=r'^[^@]+@[^@]+\.[^@]+$'
        if not re.match(MAIL_REGEX,email):
            flash("Invalid mail .","danger")
            return render_template("register_user.html")
        hashed_pw=generate_password_hash(password)
        new_user=user(name=name,email=email,user_id=user_id,password=hashed_pw,role="user")
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register_user.html")

@app.route('/register_staff', methods=['GET', 'POST'])
def register_staff():
    if request.method=="POST":
        name=request.form["name"]
        email = request.form["email"]
        phone=request.form["phone"]
        user_id=request.form["user_id"]
        password = request.form["password"]
        MAIL_REGEX=r'^[^@]+@[^@]+\.[^@]+$'
        if not re.match(MAIL_REGEX,email):
            flash("Invalid mail .","danger")
            return render_template("reg_company.html")
        hashed_pw = generate_password_hash(password)
        preferred_region=request.form.get('preferred_region')
        new_staff=staff(name=name,email=email,phone=phone,user_id=user_id,password=hashed_pw,preferred_region=preferred_region,approved=False,role="staff")
        db.session.add(new_staff)
        db.session.commit()
        flash("Staff registered . awaiting admin approval..... ","success")
        return redirect(url_for("login"))
    return render_template('register_staff.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user_id_input = request.form.get("user_id")
        password = request.form.get("password")
#1st check Admin 
        admin_record = Admin.query.filter_by(user_id=user_id_input).first()
        if admin_record and check_password_hash(admin_record.password, password):
            login_user(admin_record)
            print("DEBUG: Logged in as Admin ->", current_user.user_id, "| role:", current_user.role)
            return redirect(url_for("admin_dashboard"))
# convert to integer ,becoz form gets str and user/staff- int userid
        if user_id_input.isdigit():
            int_user_id = int(user_id_input)
# orrr   user  
            trekker_record = user.query.filter_by(user_id=int_user_id).first()
            if trekker_record and check_password_hash(trekker_record.password, password):
                login_user(trekker_record)
                return redirect(url_for("user_dashboard", user_id=trekker_record.user_id))
# elseee staff  --avoid shadowing here (huge mistake!!!)
            staff_record = staff.query.filter_by(user_id=int_user_id).first() 
            if staff_record and check_password_hash(staff_record.password, password):
                if not staff_record.approved:
                    flash("Staff/lead NOT yet approved by admin, please wait", "warning")
                    return render_template("login.html")                
                login_user(staff_record)
                flash("Logging in..", "success")
                return redirect(url_for("staff_dashboard", user_id=staff_record.user_id))           
        flash("Invalid User ID or password!", "danger")         
    return render_template("login.html")

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/browse_treks')
def browse_treks():
    region = request.args.get('region')
    difficulty = request.args.get('difficulty')
    query = trek.query.filter_by(status='Open')
    if region:
        query = query.filter(trek.region == region)
    if difficulty:
        query = query.filter(trek.difficulty == difficulty)
    treks = query.all()
    return render_template('browse_treks.html', treks=treks)
@app.route('/view-trek/<int:trek_id>')
def view_trek(trek_id):
    trek_m= trek.query.get_or_404(trek_id)
    assigned_staff = staff.query.get(trek_m.assigned_staff_id) if trek_m.assigned_staff_id else None
    return render_template('view_trek.html', trek=trek_m, assigned_staff=assigned_staff)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@rn_required('admin')
def admin_dashboard():
    stats = {
        'total_treks': trek.query.count(),
        'total_users': user.query.filter_by(role='user').count(),
        'total_staff': staff.query.count(),
        'total_bookings': Booking.query.count()}
    pending_staff = staff.query.filter(staff.approved !=True).all()
#for pie
    all_treks = trek.query.all()
    region_summary = {}
    for t in all_treks:
        region_summary[t.region] = region_summary.get(t.region, 0) + 1
    region_labels = list(region_summary.keys())
    region_counts = list(region_summary.values())
# for bar
    trek_names = [t.trek_name for t in all_treks]
    total_slots_data = [t.total_slots for t in all_treks]
    available_slots_data = [t.available_slots for t in all_treks]
    return render_template('admin_dashboard.html', stats=stats, pending_staff=pending_staff,region_labels=region_labels,
                           region_counts=region_counts,
                           trek_names=trek_names,
                           total_slots_data=total_slots_data,
                           available_slots_data=available_slots_data)
@app.route("/admin/approve_user/<int:current_id>", methods=["POST"])
@rn_required('admin')
def approve_user(current_id):
    target = staff.query.get(current_id)
    if not target:
        target = user.query.get_or_404(current_id)
    target.approved = True
    db.session.commit()
    flash(f"{target.name} has been approved/restored.", "success")
    return redirect(request.referrer or url_for('admin_dashboard'))
@app.route("/admin/reject_staff/<int:staff_id>",methods=["POST"])
def reject_staff(staff_id):
    staff_m=staff.query.get_or_404(staff_id)
    db.session.delete(staff_m)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))
# if u reject a person - u r deleting their application permnently ...they'll have to register again
#blocklisting them is AFTER approval , but block 'em.. CAN approve them again without new reg
@app.route("/admin/blocklist_user/<int:current_id>", methods=["POST"])
@rn_required('admin')
def blocklist_user(current_id):
    target = staff.query.get(current_id)
    if not target:
        target = user.query.get_or_404(current_id)
    target.approved = False
    db.session.commit()
    flash(f"{target.name} access has been revoked (Blacklisted).", "warning")
    return redirect(request.referrer or url_for('admin_dashboard'))
@app.route('/admin/search')
@rn_required('admin')
def admin_search():
    search_query = request.args.get('query', '')
#searching treks by name/id
    trek_results = trek.query.filter((trek.trek_name.ilike(f'%{search_query}%')) | 
    (trek.id == search_query if search_query.isdigit() else False)).all()
#searching staff by same
    staff_results = staff.query.filter((staff.name.ilike(f'%{search_query}%')) | 
        (staff.user_id.ilike(f'%{search_query}%'))).all()
#same with user obj logic
    user_results = user.query.filter((user.name.ilike(f'%{search_query}%')) | 
    (user.user_id.ilike(f'%{search_query}%'))).all()
    return render_template('search_results.html', query=search_query, treks=trek_results, 
                           staff=staff_results, users=user_results)
@app.route('/admin/create_trek', methods=['GET', 'POST'])
@rn_required('admin') #@login_required
def create_trek():
    if request.method == 'POST':
        #have to convert HTML date str to py-date-objs for the model
        s_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        e_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        new_trek = trek(trek_name=request.form.get('name'),
            location=request.form.get('location'),region=request.form.get('region'),
            duration=int(request.form.get('duration')),difficulty=request.form.get('difficulty'),
            total_slots=int(request.form.get('slots')),
            available_slots=int(request.form.get('slots')), #same 
            start_date=s_date,
            end_date=e_date,
            status='Open', # default
            assigned_staff_id=request.form.get('staff_id'),
            description=request.form.get('description'),
            image_file=request.form.get('image_file'))
        db.session.add(new_trek)
        db.session.commit()
        flash(f"Trek '{new_trek.trek_name}' initialized successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    # GET --- do not forget !! 
    approved_staff = staff.query.filter_by(approved=True).all()
    available_images = ['hampta.jpg', 'kudremukh.jpg', 'valley_of_flowers.jpg', 'parson_valley.jpg','nagtiba.jpg']
    return render_template('create_trek.html', staff=approved_staff, trek=None,images=available_images)
@app.route('/admin/manage_treks')
@rn_required('admin')
def manage_treks():
    all_treks = trek.query.all()
    trek_ratings = {}
    for t in all_treks:
        avg_val = db.session.query(func.avg(Booking.rating)).filter(Booking.trek_id == t.id).scalar()        
        trek_ratings[t.id] = round(avg_val, 1) if avg_val else "New"    
    return render_template('manage_treks.html', treks=all_treks, trek_ratings=trek_ratings)
    
@app.route('/admin/edit_trek/<int:trek_id>', methods=['GET', 'POST'])
@rn_required('admin')
def edit_trek(trek_id):
    trek_to_edit = trek.query.get_or_404(trek_id)
    if request.method == 'POST':
        trek_to_edit.trek_name = request.form.get('name')
        trek_to_edit.location = request.form.get('location')
        trek_to_edit.region = request.form.get('region')
        trek_to_edit.duration = int(request.form.get('duration'))
        trek_to_edit.difficulty = request.form.get('difficulty')
        trek_to_edit.total_slots = int(request.form.get('slots'))
        trek_to_edit.description = request.form.get('description')
        trek_to_edit.image_file = request.form.get('image_file')
        trek_to_edit.status = request.form.get('status')
        trek_to_edit.assigned_staff_id = request.form.get('staff_id')
        trek_to_edit.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        trek_to_edit.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        trek_to_edit.image_file = request.form.get('image_file')
        db.session.commit()
        flash(f"Trek '{trek_to_edit.trek_name}' updated successfully.", "success")
        return redirect(url_for('manage_treks'))
    approved_staff = staff.query.filter_by(approved=True).all()
    available_images = ['hampta.jpg', 'kudremukh.jpg', 'valley_of_flowers.jpg', 'parson_valley.jpg','nagtiba.jpg']
    return render_template('create_trek.html', staff=approved_staff, trek=trek_to_edit, images=available_images)
@app.route('/admin/delete_trek/<int:trek_id>', methods=['POST','GET'])
@rn_required('admin')
def delete_trek(trek_id):
    trek_to_remove = trek.query.get_or_404(trek_id)
    Booking.query.filter_by(trek_id=trek.id).delete(synchronize_session=False)
    db.session.delete(trek_to_remove)
    db.session.commit()
    flash(f"Trek '{trek_to_remove.trek_name}' has been successfully removed.", "info")
    return redirect(url_for('browse_treks'))
@app.route('/admin/staff_manage')
@rn_required('admin')
def staff_manage():
    pending = staff.query.filter(staff.approved != 'True', staff.approved != 'Blacklisted').all()
    approved = staff.query.filter_by(approved='True').all()
    blacklisted = staff.query.filter_by(approved='Blacklisted').all()
    return render_template('staff_manage.html', pending=pending, approved=approved, blacklisted=blacklisted)
@app.route('/admin/user_registry')
@rn_required('admin')
def user_registry():
    all_users = user.query.filter_by(role='user').all()
    return render_template('user_registry.html', users=all_users)

@app.route('/user_dashboard/<int:user_id>')
@rn_required('user')
def user_dashboard(user_id):
    trekker_record = user.query.get_or_404(user_id)
#study this---------
    active_bookings = db.session.query(Booking.status, trek.trek_name, trek.location, trek.start_date, 
                                trek.id.label('trek_id'),staff.email.label('lead_mail'),staff.name.label('lead_name')).join(trek, Booking.trek_id == trek.id)\
     .outerjoin(staff, trek.assigned_staff_id == staff.user_id)\
     .filter(Booking.user_id == user_id, trek.status == 'Open' ).all() #Booking.status == 'Booked').all()
    history_bookings = db.session.query(trek.trek_name, trek.start_date, Booking.status,Booking.id.label('booking_id'),
                trek.id.label('trek_id'),Booking.rating.label('user_rating')).join(trek, Booking.trek_id == trek.id)\
     .filter(Booking.user_id == user_id, trek.status=='Closed').all() # Booking.status == 'Completed',
    trek_ratings = {}
    for t in history_bookings :
        avg_val = db.session.query(func.avg(Booking.rating)).filter(Booking.trek_id == t.trek_id).scalar()
        trek_ratings[t.trek_id] = round(avg_val, 1) if avg_val else "New"
    return render_template('user_dashboard.html', trekker=trekker_record, active_bookings=active_bookings, history_bookings=history_bookings,trek_ratings=trek_ratings)
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():  #user not staff , staff is seprately built
#tried dynamic changes here--dont forget to tell this in viva
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        current_user.name = name
        current_user.email = email
        if password:
            current_user.password = password
        db.session.commit()
        flash("Profile Updated Successfully!", "success")
        return redirect(url_for('user_dashboard', user_id=current_user.id))
    return render_template('edit_profile.html', user=current_user)   
@app.route('/book_trek/<int:trek_id>', methods=['POST'])
@login_required
def book_trek(trek_id):
    target_trek = trek.query.get_or_404(trek_id)
    existing = Booking.query.filter_by(user_id=current_user.user_id, trek_id=trek_id).first()
    if existing:
        flash("System indicates you are already registered for this trail.", "info")
        return redirect(url_for('user_dashboard', user_id=current_user.user_id))
    target_trek.available_slots -= 1 
    new_booking = Booking(user_id=current_user.user_id,trek_id=trek_id,status='Booked')
    db.session.add(new_booking)
    db.session.commit() 
    flash(f"Slot Confirmed: {target_trek.trek_name} added to your registry.", "success")
    return redirect(url_for('user_dashboard', user_id=current_user.user_id))
@app.route('/submit_rating/<int:booking_id>', methods=['POST','GET'])
@rn_required('user')
def submit_rating(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    rating_value = request.form.get('rating')
    print(f"DEBUG: Status is '{booking.status}', Rating is '{rating_value}'")
    if booking.status == 'Completed' and rating_value:
        booking.rating = int(rating_value)
        db.session.commit()
        print("DEBUG: Successfully committed to DB")
    else:
        print("DEBUG: Condition not met - Commit skipped")
    return redirect(url_for('user_dashboard',user_id=current_user.user_id))


@app.route('/staff/dashboard/<int:user_id>',methods=['POST','GET'])
#@rn_required('staff')
def staff_dashboard(user_id):
    all_my_treks = trek.query.filter_by(assigned_staff_id=user_id).all()
    current_treks = [t for t in all_my_treks if t.status != 'Closed'] # orrr...-> only open treks
    past_treks = [t for t in all_my_treks if t.status == 'Closed']

    trek_ratings = {}
    for t in past_treks:
        avg_val = db.session.query(func.avg(Booking.rating)).filter(Booking.trek_id == t.id).scalar()
        trek_ratings[t.id] = round(avg_val, 1) if avg_val else "New"
    return render_template('staff_dashboard.html', current_treks=current_treks, past_treks=past_treks,trek_ratings=trek_ratings)
@app.route('/staff/close_trek/<int:trek_id>',methods=['POST','GET'])
@rn_required('staff')
def close_trek(trek_id):
    t = trek.query.get_or_404(trek_id)
    t.status = 'Closed'
    Booking.query.filter_by(trek_id=trek.id, status='Booked').update({Booking.status: 'Completed'})
    db.session.commit()
    flash(f" {t.trek_name} has been Closed ", "warning")
    return redirect(url_for('staff_dashboard',user_id=current_user.user_id))
@app.route('/staff/edit_staff_profile', methods=['GET', 'POST'])
@rn_required('staff')#@login_required #
def edit_staff_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.email = request.form.get('email')        
        current_user.phone = request.form.get('phone')
        current_user.preferred_region = request.form.get('preferred_region')
        new_pass = request.form.get('password')
        if new_pass:
            current_user.password = generate_password_hash(new_pass)
        db.session.commit() 
        flash("Operational Profile Updated Successfully.", "success")
        return redirect(url_for('staff_dashboard',user_id=current_user.user_id))
    return render_template('edit_staff_profile.html', staff=current_user)
@app.route('/staff/view_participants/<int:trek_id>',methods=['GET','POST'])
@login_required # not @rn_required('staff') coz admin uses too 
def view_participants(trek_id):
    target_trek = trek.query.get_or_404(trek_id)
    participants = target_trek.registrations 
    return render_template('view_participants.html',trek=target_trek, participants=participants)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)