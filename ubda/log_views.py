from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Access_log, User, Access_point


log_views = Blueprint('log_views', __name__)


@log_views.route('/access_log')
@login_required
def access_log():
    log = Access_log.query.all()
    users = User.query.all()
    aps = Access_point.query.all()
    ap_names = {}
    user_names = {}
    for user in users:
        user_names.update({user.id : f'{user.user_name}({user.first_name} {user.last_name})'})
    for ap in aps:
        ap_names.update({ap.id : ap.name})
    return render_template("access_log.html", 
                            current_user = current_user, 
                            user_names = user_names,
                            ap_names = ap_names,
                            log=log)


@log_views.route('/system_log')
@login_required
def sys_log():
    return render_template("system_log.html", current_user = current_user)


