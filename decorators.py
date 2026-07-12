from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user, login_required
# creating a right now , we require function to strict/tighten the access
# creating a right now , we require function to strict/tighten the access
def rn_required(role):
    # used  @rn_required('admin'), @rn_required('staff'), or @rn_required('user')
    def wrapper(fn):
        @wraps(fn)
        @login_required
        def gatekeeper(*args, **kwargs):
            # Check core role requirement [5]
            if current_user.role != role:
                flash("Unauthorized access!", "danger")
                return redirect(url_for("login"))
            # Additional logic: Admin skips status checks, as they are the pre-existing superuser [1, 2]
            if current_user.role != 'admin':
                #Staff must be 'Approved' to login
                if role == 'staff' and current_user.status != 'Approved':
                    flash("Access Denied:pending Admin approval.", "warning")
                    return redirect(url_for("home"))
                if current_user.status == 'Blacklisted':
                    flash("Your account has been blacklisted by the Admin.", "danger")
                    return redirect(url_for("logout"))
            return fn(*args, **kwargs)
        return gatekeeper
    return wrapper
# 2 --: for Trekkers (Users)
def trekker_only(fn):
    @wraps(fn)
    @login_required
    def gatekeeper(user_id, *args, **kwargs):
        if current_user.role != 'user' or str(current_user.user_id) != str(user_id):
            flash("Unauthorized access to this profile.", "danger")
            return redirect(url_for("home"))
        return fn(user_id, *args, **kwargs)
    return gatekeeper
# 3-->for Trek Staff
def assigned_staff_only(fn):
    @wraps(fn)
    @login_required
    def gatekeeper(trek_id, *args, **kwargs):
        # logic is :-->verify if current_user.user_id == trek.assigned_staff_id
        if current_user.role != 'staff' or current_user.status != 'Approved':
            flash("Unauthorized access.", "danger")
            return redirect(url_for("home"))
        return fn(trek_id, *args, **kwargs)
    return gatekeeper