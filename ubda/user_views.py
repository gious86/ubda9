from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User, Access_level, Access_point
from . import db
from datetime import datetime
import csv

user_views = Blueprint('user_views', __name__)


@user_views.route('/users')
@login_required
def users():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    access_levels = Access_level.query.all()
    access_level_names = {}
    for access_level in access_levels:
        access_level_names.update({access_level.id : access_level.name})
    users = current_user.created_users
    print (access_levels)
    return render_template("users.html", 
                            current_user = current_user, 
                            access_level_names = access_level_names, 
                            users = users )

@user_views.route('/reset_all_passwords')
@login_required
def reset_passwords():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    
    users = User.query.all()
    for user in users :
        user.password = generate_password_hash('11111111')
        db.session.add(user)
        db.session.commit()
    
    return redirect(url_for('vievs.home'))


@user_views.route('/new_user', methods=['GET', 'POST'])
@login_required
def new_user():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    if request.method == 'POST':
        user_name = request.form.get('userName')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        access_level = request.form.get('access_level')
        card_number = request.form.get('card_number')
        print('****')
        try:
            valid_thru = datetime.strptime(request.form.get('valid_thru'), '%Y-%m-%d')
        except:
            valid_thru = None
        user = User.query.filter_by(user_name=user_name).first()
        if user:
            flash('User already exists.', category='error')
        elif password1 != password2:
            flash("Passwords don't match.", category='error')
        else:
            new_user = User(user_name = user_name, 
                            first_name = first_name, 
                            password = generate_password_hash(password1),
                            access_level = access_level,
                            card_number = card_number,
                            valid_thru = valid_thru,
                            created_by = current_user.id)
            db.session.add(new_user)
            db.session.commit()
            flash('User added', category='success')
            return redirect(url_for('user_views.users'))
    accessLevels = Access_level.query.all()
    return render_template("new_user.html", user=current_user, accessLevels = accessLevels)


@user_views.route('/edit_user/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    user = User.query.filter_by(id=id).first()
    if not user :
        flash(f'No person with id:{id}', category='error')
        return redirect(url_for('views.personnel'))
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        access_level_id = request.form.get('access_level')
        card_number = request.form.get('card_number')
        try:
            valid_thru = datetime.strptime(request.form.get('valid_thru'), '%Y-%m-%d')
        except:
            valid_thru = None
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.access_level = access_level_id
        user.card_number = card_number
        user.valid_thru = valid_thru
        db.session.add(user)
        db.session.commit()
        flash('Person information updated', category='success')
        return redirect(url_for('user_views.users'))
    access_levels = Access_level.query.all() 
    return render_template("edit_user.html", current_user = current_user, 
                                            user = user, 
                                            access_levels = access_levels)


@user_views.route('/delete_user/<string:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    user = User.query.filter_by(id=id).first()
    if not user :
        flash(f'No user with id:{id}', category='error')
        return redirect(url_for('user_views.users'))
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()
        flash('Person deleted', category='success')
        return redirect(url_for('user_views.users'))
    return render_template("delete_user.html", current_user = current_user, user=user)


@user_views.route('/user_access_log/<string:id>')
@login_required
def user_access_log(id):
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    user = User.query.filter_by(id=id).first()
    if not user:
        flash(f'No user with id:{id}', category='error')
        return redirect(url_for('user_views.users'))
    else:
        aps = Access_point.query.all()
        ap_names = {}
        for ap in aps:
            ap_names.update({ap.id : ap.name})
        return render_template("user_access_log.html",
                                ap_names = ap_names, 
                                current_user = current_user, 
                                user = user)
    
@user_views.route('/import_users', methods=['GET', 'POST'])
@login_required
def import_users():
    if current_user.role != 'admin':    
        flash('Restricted area', category='error')
        return redirect(url_for('views.user_home'))
    if request.method == 'POST':
        f = request.files['file'] 
        access_level = request.form.get('access_level')
        filename=f.filename
        f.save(filename)
        with open(filename) as f:
            csvr = csv.reader(f, delimiter=',')
            for row in csvr:
                #print(f'\t{row[0]} - {row[1]} - {row[2]}.')
                new_user = User(user_name = row[0], 
                            first_name = row[1], 
                            password = generate_password_hash('11111111'),
                            access_level = access_level,
                            card_number = row[2],
                            created_by = current_user.id)
                db.session.add(new_user)
                db.session.commit()
    accessLevels = Access_level.query.all()
    return render_template("import_users.html", accessLevels=accessLevels)