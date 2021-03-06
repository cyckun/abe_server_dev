# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask import render_template, flash, redirect, url_for, current_app, request, Blueprint, send_from_directory
from flask_login import login_required, current_user, fresh_login_required, logout_user

from server.decorators import confirm_required, permission_required
from server.emails import send_change_email_email
from server.extensions import db, avatars
from server.forms.user import EditProfileForm, DownloadskForm, UploadAvatarForm, CropAvatarForm, ChangeEmailForm, \
    ChangePasswordForm, NotificationSettingForm, PrivacySettingForm, DeleteAccountForm, SetFileAttriForm
from server.models import User, Photo, Collect, File
from server.notifications import push_follow_notification
from server.settings import Operations
from server.utils import generate_token, validate_token, redirect_back, flash_errors
from server.blueprints.cpabe_usrkey import cpabe_usrkey
import time
from server.blueprints.cpabe_enc import cpabe_enc_cli

user_bp = Blueprint('user', __name__)


@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user and user.locked:
        flash('Your account is locked.', 'danger')

    if user == current_user and not user.active:
        logout_user()

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ABE_PHOTO_PER_PAGE']
    pagination = Photo.query.with_parent(user).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items
    return render_template('user/index.html', user=user, pagination=pagination, photos=photos)


@user_bp.route('/<username>/collections')
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ABE_PHOTO_PER_PAGE']
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('user/collections.html', user=user, pagination=pagination, collects=collects)


@user_bp.route('/<username>/files')
def show_files(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ABE_PHOTO_PER_PAGE']
    pagination = File.query.with_parent(user).order_by(File.timestamp.desc()).paginate(page, per_page)
    files = pagination.items
    return render_template('user/files.html', user=user, pagination=pagination, files=files)

@user_bp.route('/show_fileattri/<filename>', methods=['GET', 'POST'])
@login_required
def show_file_attri(filename):

    file = File.query.filter_by(filename=filename).first_or_404()
    return render_template('user/file_attri.html', user=current_user, file=file)

@user_bp.route('/dec_file/<filename>', methods=['GET', 'POST'])
@login_required
def dec_file(filename):  # not used yet
    #deal lator

    file = File.query.filter_by(filename=filename).first_or_404()
    return render_template('user/file_attri.html', user=current_user, file=file)


@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
@confirm_required
@permission_required('FOLLOW')
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        flash('Already followed.', 'info')
        return redirect(url_for('.index', username=username))

    current_user.follow(user)
    flash('User followed.', 'success')
    if user.receive_follow_notification:
        push_follow_notification(follower=current_user, receiver=user)
    return redirect_back()


@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        flash('Not follow yet.', 'info')
        return redirect(url_for('.index', username=username))

    current_user.unfollow(user)
    flash('User unfollowed.', 'info')
    return redirect_back()


@user_bp.route('/<username>/followers')
def show_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ABE_USER_PER_PAGE']
    pagination = user.followers.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/followers.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/<username>/following')
def show_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ABE_USER_PER_PAGE']
    pagination = user.following.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/following.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.department = form.department.data
        current_user.jobnumber = form.jobnumber.data
        current_user.level = form.level.data
        current_user.bio = form.bio.data
        current_user.website = form.website.data
        current_user.location = form.location.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.name.data = current_user.name
    form.username.data = current_user.username
    form.bio.data = current_user.bio
    form.website.data = current_user.website
    form.location.data = current_user.location
    return render_template('user/settings/edit_profile.html', form=form)

def set_file_policy(dept="", time=0, name=""):
    # (Dept:SecurityResearch)
    policy = ""
    if dept != "":
        policy = "Dept:"+dept
    if time != 0:
        #time_begin = time.time()
        pass
    if name != "":
        policy = "Name:"+name
    return policy

@user_bp.route('/settings/accesspolicy/<filename>', methods=['GET', 'POST'])
@login_required
def set_file_acp(filename):
    print("test,enter fileattri.")
    form = SetFileAttriForm()
    if form.validate_on_submit():
        name = form.name.data
        dept = form.dept.data
        time = form.time.data
        policy = set_file_policy(dept, time, name)
        file_path = current_app.config['ABE_UPLOAD_PATH']
        file_path += "/"
        file_path += filename
        with open(file_path, "rb") as f:
            buffer = f.read()
            f.close()

        # modify it lator.
        ct = ""
        if len(buffer) > 0:ct = cpabe_enc_cli(buffer, policy)   # should user grpc to call enc service, as init cpabe is wastful;
        else:pass
        with open(file_path+".enc", "wb") as f:
            f.write(ct)
            f.close()
        file = File.query.filter_by(filename=filename).first_or_404()
        file.enc_flag = True
        file.enc_policy = policy
        db.session.commit()

        return redirect(url_for('.index', username=current_user.username))

    return render_template('user/settings/edit_fileattri.html', form=form)

def set_userattri():
    print("jobnumber:", current_user.jobnumber)
    print(current_user.jobnumber == None)
    if current_user.jobnumber != None:
        attri = "Name:"
        attri += current_user.name + "|"
        attri += "Dept:" + current_user.department + "|"
        attri += "Level:" + current_user.level
        return attri
    else:
        return ""


@user_bp.route('/settings/download_sk', methods=['GET', 'POST'])
@login_required
def download_sk():
    form = DownloadskForm()
    # if form.validate_on_submit():
    '''
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.website = form.website.data
        current_user.location = form.location.data
        db.session.commit()
    '''
    attri = set_userattri()
    if attri == "": return "set profile first"

    print("test attri:", attri)
    ret = cpabe_usrkey(attri)

    flash('sk updated.', 'success')
    # filename = current_user.jobnumber
    # return redirect(url_for('.index', username=current_user.username))
    return send_from_directory(current_app.config['ABE_UPLOAD_PATH'], filename="sk.txt", as_attachment=True)
    # return render_template('user/settings/edit_profile.html', form=form)
    # return "download sk OK "


@user_bp.route('/settings/avatar')
@login_required
@confirm_required
def change_avatar():
    upload_form = UploadAvatarForm()
    crop_form = CropAvatarForm()
    return render_template('user/settings/change_avatar.html', upload_form=upload_form, crop_form=crop_form)


@user_bp.route('/settings/avatar/upload', methods=['POST'])
@login_required
@confirm_required
def upload_avatar():
    form = UploadAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = avatars.save_avatar(image)
        current_user.avatar_raw = filename
        db.session.commit()
        flash('Image uploaded, please crop.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar'))


@user_bp.route('/settings/avatar/crop', methods=['POST'])
@login_required
@confirm_required
def crop_avatar():
    form = CropAvatarForm()
    if form.validate_on_submit():
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        filenames = avatars.crop_avatar(current_user.avatar_raw, x, y, w, h)
        current_user.avatar_s = filenames[0]
        current_user.avatar_m = filenames[1]
        current_user.avatar_l = filenames[2]
        db.session.commit()
        flash('Avatar updated.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar'))


@user_bp.route('/settings/change-password', methods=['GET', 'POST'])
@fresh_login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.validate_password(form.old_password.data):
            current_user.set_password(form.password.data)
            db.session.commit()
            flash('Password updated.', 'success')
            return redirect(url_for('.index', username=current_user.username))
        else:
            flash('Old password is incorrect.', 'warning')
    return render_template('user/settings/change_password.html', form=form)


@user_bp.route('/settings/change-email', methods=['GET', 'POST'])
@fresh_login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = generate_token(user=current_user, operation=Operations.CHANGE_EMAIL, new_email=form.email.data.lower())
        send_change_email_email(to=form.email.data, user=current_user, token=token)
        flash('Confirm email sent, check your inbox.', 'info')
        return redirect(url_for('.index', username=current_user.username))
    return render_template('user/settings/change_email.html', form=form)


@user_bp.route('/change-email/<token>')
@login_required
def change_email(token):
    if validate_token(user=current_user, token=token, operation=Operations.CHANGE_EMAIL):
        flash('Email updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    else:
        flash('Invalid or expired token.', 'warning')
        return redirect(url_for('.change_email_request'))


@user_bp.route('/settings/notification', methods=['GET', 'POST'])
@login_required
def notification_setting():
    form = NotificationSettingForm()
    if form.validate_on_submit():
        current_user.receive_collect_notification = form.receive_collect_notification.data
        current_user.receive_comment_notification = form.receive_comment_notification.data
        current_user.receive_follow_notification = form.receive_follow_notification.data
        db.session.commit()
        flash('Notification settings updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.receive_collect_notification.data = current_user.receive_collect_notification
    form.receive_comment_notification.data = current_user.receive_comment_notification
    form.receive_follow_notification.data = current_user.receive_follow_notification
    return render_template('user/settings/edit_notification.html', form=form)


@user_bp.route('/settings/privacy', methods=['GET', 'POST'])
@login_required
def privacy_setting():
    form = PrivacySettingForm()
    if form.validate_on_submit():
        current_user.public_collections = form.public_collections.data
        db.session.commit()
        flash('Privacy settings updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.public_collections.data = current_user.public_collections
    return render_template('user/settings/edit_privacy.html', form=form)


@user_bp.route('/settings/account/delete', methods=['GET', 'POST'])
@fresh_login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        db.session.delete(current_user._get_current_object())
        db.session.commit()
        flash('Your are free, goodbye!', 'success')
        return redirect(url_for('main.index'))
    return render_template('user/settings/delete_account.html', form=form)
