# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, HiddenField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, Regexp

from server.models import User


class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    username = StringField('UserName', validators=[DataRequired(), Length(1, 9),
                                                   Regexp('^[a-zA-Z0-9]*$',
                                                          message='The username should contain only a-z, A-Z and 0-9.')])
    jobnumber = StringField('Job Number', validators=[DataRequired(), Length(1, 9),
                                                   Regexp('[0-9]',
                                                          message='The jobnumber should contain only 0-9.')])
    department = StringField('Department', validators=[DataRequired(), Length(1, 30)])
    level = StringField('Level', validators=[DataRequired(), Length(1, 2)])
    website = StringField('Website', validators=[Optional(), Length(0, 255)])
    location = StringField('Location', validators=[Optional(), Length(0, 50)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(0, 120)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('The username is already in use.')


class DownloadskForm(FlaskForm):
    submit = StringField()

class SetFileAttriForm(FlaskForm):
    time = StringField("Time", validators=[Optional(), Length(1, 254)])
    dept = StringField("Dept", validators=[DataRequired(), Length(1, 254)])
    name = StringField("Name")
    submit = SubmitField()


class UploadAvatarForm(FlaskForm):
    image = FileField('Upload', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'txt'], 'The file format should be .jpg or .png. or txt')
    ])
    submit = SubmitField()


class CropAvatarForm(FlaskForm):
    x = HiddenField()
    y = HiddenField()
    w = HiddenField()
    h = HiddenField()
    submit = SubmitField('Crop and Update')


class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('The email is already in use.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField()


class NotificationSettingForm(FlaskForm):
    receive_comment_notification = BooleanField('New comment')
    receive_follow_notification = BooleanField('New follower')
    receive_collect_notification = BooleanField('New collector')
    submit = SubmitField()


class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField('Public my collection')
    submit = SubmitField()


class DeleteAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username:
            raise ValidationError('Wrong username.')
