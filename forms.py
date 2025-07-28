from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, BooleanField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from models import User

class LoginForm(FlaskForm):
    username = StringField('사용자명', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('로그인')

class RegistrationForm(FlaskForm):
    username = StringField('사용자명', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('비밀번호 확인', 
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('회원가입')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('이미 사용중인 사용자명입니다.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('이미 등록된 이메일입니다.')

class PDFRequestForm(FlaskForm):
    subject = SelectField('과목', choices=[
        ('국어', '국어'),
        ('영어', '영어'), 
        ('수학', '수학'),
        ('과학', '과학'),
        ('사회', '사회'),
        ('기타', '기타')
    ], validators=[DataRequired()])
    topic = StringField('주제/단원', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('상세 설명')
    submit = SubmitField('자료 요청')

class PDFUploadForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(max=200)])
    subject = SelectField('과목', choices=[
        ('국어', '국어'),
        ('영어', '영어'),
        ('수학', '수학'),
        ('과학', '과학'),
        ('사회', '사회'),
        ('기타', '기타')
    ], validators=[DataRequired()])
    category = SelectField('카테고리', choices=[
        ('suneung', '수능'),
        ('naeshin', '내신')
    ], validators=[DataRequired()])
    file = FileField('PDF 파일', validators=[
        DataRequired(),
        FileAllowed(['pdf'], 'PDF 파일만 업로드 가능합니다.')
    ])
    submit = SubmitField('업로드')

class VocabularyForm(FlaskForm):
    word = StringField('단어', validators=[DataRequired(), Length(max=100)])
    meaning = TextAreaField('뜻', validators=[DataRequired()])
    submit = SubmitField('단어장에 추가')

class AnnouncementForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(min=1, max=200)])
    content = TextAreaField('내용', validators=[DataRequired()], render_kw={"rows": 8})
    visibility = SelectField('공개 범위', choices=[
        ('all', '모든 사용자'),
        ('members', '회원만'),
        ('non_members', '비회원만')
    ], default='all')
    priority = SelectField('우선순위', choices=[
        ('low', '낮음'),
        ('normal', '보통'),
        ('high', '높음'),
        ('urgent', '긴급')
    ], default='normal')
    is_active = BooleanField('활성화', default=True)
    expires_at = DateTimeLocalField('만료일시', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField('저장')

class CustomerSupportForm(FlaskForm):
    subject = StringField('제목', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('문의 내용', validators=[DataRequired(), Length(min=10, max=2000)])
    priority = SelectField('우선순위', choices=[
        ('normal', '일반'),
        ('high', '높음'),
        ('urgent', '긴급')
    ], default='normal')
    submit = SubmitField('문의하기')

class SupportReplyForm(FlaskForm):
    message = TextAreaField('답변', validators=[DataRequired(), Length(min=5, max=1000)])
    submit = SubmitField('답변하기')