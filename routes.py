from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from forms import RegistrationForm, LoginForm, PDFRequestForm, PDFUploadForm, VocabularyForm, AnnouncementForm, CustomerSupportForm, SupportReplyForm
from models import User, PDFRequest, PDFResource, KoreanVocabulary, VocabularyWord, QuizScore, Notification, Announcement, FocusSession, CustomerSupport, SupportReply
from app import app, db, csrf
from werkzeug.utils import secure_filename
from flask import send_from_directory
import os
import secrets
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from flask import g
from flask_login import current_user

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('로그인되었습니다.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('잘못된 사용자명 또는 비밀번호입니다.', 'danger')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('회원가입이 완료되었습니다!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent activities
    recent_requests = PDFRequest.query.filter_by(user_id=current_user.id).order_by(PDFRequest.requested_at.desc()).limit(5).all()
    vocabulary_count = VocabularyWord.query.filter_by(user_id=current_user.id).count()
    recent_scores = QuizScore.query.filter_by(user_id=current_user.id).order_by(QuizScore.quiz_date.desc()).limit(3).all()

    # Get visible announcements for logged-in users
    all_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.priority.desc(), Announcement.created_at.desc()).all()
    visible_announcements = [ann for ann in all_announcements if ann.is_visible_to_user(current_user)]

    return render_template('dashboard.html', 
                         recent_requests=recent_requests,
                         vocabulary_count=vocabulary_count,
                         recent_scores=recent_scores,
                         current_user=current_user,
                         announcements=visible_announcements)

@app.route('/pdf-resources', methods=['GET', 'POST'])
@login_required
def pdf_resources():
    form = PDFRequestForm()

    # Get user's requests
    user_requests = PDFRequest.query.filter_by(user_id=current_user.id).order_by(PDFRequest.requested_at.desc()).all()

    # Get all available resources (통합)
    all_resources = PDFResource.query.order_by(PDFResource.upload_date.desc()).all()

    # Check if user can request today
    can_request_today = PDFRequest.can_user_request_today(current_user.id)
    today_request_count = PDFRequest.get_user_today_request_count(current_user.id)

    if request.method == 'POST' and form.validate_on_submit():
        # 일일 요청 제한 확인
        if not can_request_today:
            flash('하루에 한 번만 PDF 자료를 요청할 수 있습니다. 내일 다시 시도해주세요.', 'warning')
            return redirect(url_for('pdf_resources'))

        # 입력값 검증 및 정제
        subject = form.subject.data.strip()[:100]  # 길이 제한
        topic = form.topic.data.strip()[:200]
        description = form.description.data.strip()[:1000] if form.description.data else None

        # 빈 값 검증
        if not subject or not topic:
            flash('과목과 주제는 필수 입력 항목입니다.', 'danger')
            return redirect(url_for('pdf_resources'))

        # 스팸 방지: 같은 내용 중복 요청 확인
        recent_duplicate = PDFRequest.query.filter(
            PDFRequest.user_id == current_user.id,
            PDFRequest.subject == subject,
            PDFRequest.topic == topic,
            PDFRequest.requested_at >= datetime.now() - timedelta(days=7)
        ).first()

        if recent_duplicate:
            flash('최근 7일 내에 동일한 요청이 있었습니다.', 'warning')
            return redirect(url_for('pdf_resources'))

        try:
            pdf_request = PDFRequest()
            pdf_request.user_id = current_user.id
            pdf_request.subject = subject
            pdf_request.topic = topic
            pdf_request.description = description
            db.session.add(pdf_request)
            db.session.commit()
            flash('자료 요청이 제출되었습니다.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('요청 처리 중 오류가 발생했습니다. 다시 시도해주세요.', 'danger')
        
        return redirect(url_for('pdf_resources'))

    return render_template('pdf_resources.html', 
                         form=form,
                         user_requests=user_requests,
                         all_resources=all_resources,
                         can_request_today=can_request_today,
                         today_request_count=today_request_count)

@app.route('/suneung/korean')
@login_required
def suneung_korean():
    # Get Korean vocabulary for classical literature
    vocab_words = KoreanVocabulary.query.all()  # 모든 카테고리 포함
    vocab_words_dict = [word.to_dict() for word in vocab_words]
    
    # Get recent quiz scores
    recent_scores = QuizScore.query.filter_by(user_id=current_user.id).order_by(QuizScore.quiz_date.desc()).limit(3).all()
    
    return render_template('suneung_korean.html', vocab_words=vocab_words, vocab_words_dict=vocab_words_dict, recent_scores=recent_scores)

@app.route('/korean/vocabulary')
@login_required
def korean_vocabulary():
    # Get Korean vocabulary for classical literature
    vocab_words = KoreanVocabulary.query.filter_by(category='호칭').all()
    vocab_words_dict = [word.to_dict() for word in vocab_words]
    return render_template('korean_vocabulary.html', vocab_words=vocab_words, vocab_words_dict=vocab_words_dict)

@app.route('/korean/nonfiction')
@login_required
def korean_nonfiction():
    # Load nonfiction tests from files
    nonfiction_tests = load_nonfiction_tests()
    
    # Get recent scores (placeholder for now)
    recent_scores = []
    
    return render_template('korean_nonfiction.html', nonfiction_tests=nonfiction_tests, recent_scores=recent_scores)

@app.route('/korean/nonfiction/test/<test_id>')
@login_required
def korean_nonfiction_test(test_id):
    # Load test data from file
    test_data = load_nonfiction_test(test_id)
    
    if not test_data:
        flash('문제를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('korean_nonfiction'))
    
    return render_template('korean_nonfiction_test.html', test_data=test_data)

@app.route('/korean/nonfiction/submit/<test_id>', methods=['POST'])
@login_required
@csrf.exempt
def submit_nonfiction_test(test_id):
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        duration = data.get('duration', 0)
        
        # Load test data to check answers
        test_data = load_nonfiction_test(test_id)
        if not test_data:
            return jsonify({'success': False, 'message': '문제를 찾을 수 없습니다.'})
        
        # Calculate score
        correct_count = 0
        total_questions = len(test_data['questions'])
        
        for i, question in enumerate(test_data['questions'], 1):
            user_answer = answers.get(str(i))
            if user_answer == question['correct_answer']:
                correct_count += 1
        
        score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        
        # Save result to file
        result_id = save_nonfiction_result(current_user.id, test_id, answers, score, duration, test_data['title'])
        
        return jsonify({
            'success': True,
            'result_id': result_id,
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions
        })
        
    except Exception as e:
        print(f"Submit nonfiction test error: {str(e)}")
        return jsonify({'success': False, 'message': '제출 중 오류가 발생했습니다.'})

@app.route('/korean/nonfiction/result/<test_id>/<result_id>')
@login_required
def korean_nonfiction_result(test_id, result_id):
    # Load result data
    result_data = load_nonfiction_result(result_id)
    test_data = load_nonfiction_test(test_id)
    
    if not result_data or not test_data:
        flash('결과를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('korean_nonfiction'))
    
    # Calculate correct count
    correct_count = 0
    for i, question in enumerate(test_data['questions'], 1):
        user_answer = result_data['answers'].get(str(i))
        if user_answer == question['correct_answer']:
            correct_count += 1
    
    return render_template('korean_nonfiction_result.html', 
                         result_data=result_data, 
                         test_data=test_data, 
                         correct_count=correct_count)

@app.route('/korean/nonfiction/results')
@login_required
def korean_nonfiction_results():
    # Load user's all results
    user_results = load_user_nonfiction_results(current_user.id)
    return render_template('korean_nonfiction_results.html', user_results=user_results)

@app.route('/suneung/english')
@login_required
def suneung_english():
    # Get user's vocabulary words
    user_vocab = VocabularyWord.query.filter_by(user_id=current_user.id, language='en').order_by(VocabularyWord.added_at.desc()).all()
    form = VocabularyForm()

    return render_template('suneung_english.html', user_vocab=user_vocab, form=form)

@app.route('/naeshin')
@login_required
def naeshin():
    # Check if it's after mid-August (using current date)
    current_date = date.today()
    unlock_date = date(2024, 8, 15)  # Mid-August
    is_unlocked = current_date >= unlock_date

    if not is_unlocked:
        return render_template('naeshin.html', is_unlocked=False, unlock_date=unlock_date)

    # If unlocked, show 상모고 내신 resources
    naeshin_resources = PDFResource.query.filter_by(category='naeshin').order_by(PDFResource.upload_date.desc()).all()
    return render_template('naeshin.html', is_unlocked=True, naeshin_resources=naeshin_resources)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'danger')
        return redirect(url_for('dashboard'))

    # Get pending requests
    pending_requests = PDFRequest.query.filter_by(status='pending').order_by(PDFRequest.requested_at.desc()).all()

    # Get upload form
    upload_form = PDFUploadForm()

    # Get Korean vocabulary categories
    korean_vocab = KoreanVocabulary.query.all()
    categories = set([vocab.category for vocab in korean_vocab])

    # Get announcements
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    announcement_form = AnnouncementForm()

    # Get all uploaded resources
    uploaded_resources = PDFResource.query.order_by(PDFResource.upload_date.desc()).all()

    # Get all users for user management
    all_users = User.query.order_by(User.id.desc()).all()
    
    # Debug: Print user count
    print(f"Total users found: {len(all_users)}")
    for user in all_users:
        print(f"User: {user.username}, Admin: {user.is_admin}")

    return render_template('admin.html', 
                         pending_requests=pending_requests, 
                         upload_form=upload_form,
                         korean_vocab=korean_vocab,
                         categories=categories,
                         announcements=announcements,
                         announcement_form=announcement_form,
                         uploaded_resources=uploaded_resources,
                         all_users=all_users)

@app.route('/upload-pdf', methods=['POST'])
@login_required
def upload_pdf():
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'danger')
        return redirect(url_for('dashboard'))

    form = PDFUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            # Keep original filename for display purposes
            original_filename = file.filename

            # Create a safe filename for storage while preserving extension
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{secrets.token_hex(8)}{file_extension}"

            # Save file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            # Create database record
            pdf_resource = PDFResource()
            pdf_resource.title = form.title.data
            pdf_resource.subject = form.subject.data
            pdf_resource.category = form.category.data
            pdf_resource.filename = unique_filename
            pdf_resource.original_filename = original_filename  # 한국어 파일명 그대로 저장
            pdf_resource.file_size = os.path.getsize(file_path)
            pdf_resource.uploaded_by = current_user.id
            db.session.add(pdf_resource)
            db.session.commit()

            flash('PDF 파일이 업로드되었습니다.', 'success')
    else:
        flash('파일 업로드 중 오류가 발생했습니다.', 'danger')

    return redirect(url_for('admin'))

@app.route('/download/<int:resource_id>')
@login_required
def download_pdf(resource_id):
    resource = PDFResource.query.get_or_404(resource_id)

    # Increment download count
    resource.download_count += 1
    db.session.commit()

    return send_from_directory(app.config['UPLOAD_FOLDER'], resource.filename, 
                             as_attachment=True, download_name=resource.original_filename)

@app.route('/nonfiction-image/<path:image_path>')
@login_required
def serve_nonfiction_image(image_path):
    """비문학 모의고사 이미지 제공"""
    try:
        # 보안을 위해 경로 검증
        if '..' in image_path or image_path.startswith('/'):
            return "Invalid path", 404
        
        # 이미지 파일 경로
        full_path = os.path.join(os.getcwd(), image_path)
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        if not os.path.exists(full_path):
            return "Image not found", 404
        
        return send_from_directory(directory, filename)
        
    except Exception as e:
        print(f"Serve nonfiction image error: {str(e)}")
        return "Error serving image", 500

@app.route('/vocabulary/quiz/<quiz_type>')
@login_required
def vocabulary_quiz(quiz_type):
    if quiz_type == 'korean':
        words_query = KoreanVocabulary.query.all()  # 모든 카테고리 포함
        words = [{'word': w.word, 'meaning': w.meaning, 'category': w.category, 'id': w.id} for w in words_query]
    elif quiz_type == 'english':
        words_query = VocabularyWord.query.filter_by(user_id=current_user.id, language='en').all()
        words = [{'word': w.word, 'meaning': w.meaning, 'mastery_level': w.mastery_level, 'id': w.id} for w in words_query]
    else:
        flash('잘못된 퀴즈 유형입니다.', 'danger')
        return redirect(url_for('dashboard'))

    # Check minimum word count for quiz
    if len(words) < 3:
        if quiz_type == 'korean':
            flash('퀴즈를 시작하려면 최소 3개의 국어 고전어휘가 필요합니다. 관리자에게 문의하여 더 많은 어휘를 등록해주세요.', 'warning')
            return redirect(url_for('suneung_korean'))
        else:
            flash('퀴즈를 시작하려면 최소 3개의 영어 단어가 필요합니다. 단어장에 더 많은 단어를 추가해주세요.', 'warning')
            return redirect(url_for('english_dictionary'))

    return render_template('vocabulary_quiz.html', words=words, quiz_type=quiz_type)

@app.route('/english-dictionary')
@login_required
def english_dictionary():
    form = VocabularyForm()
    user_vocab = VocabularyWord.query.filter_by(user_id=current_user.id, language='en').order_by(VocabularyWord.added_at.desc()).all()

    return render_template('english_dictionary.html', form=form, user_vocab=user_vocab)

@app.route('/add-vocabulary', methods=['POST'])
@login_required
def add_vocabulary():
    form = VocabularyForm()
    if form.validate_on_submit():
        # Check if word already exists for user
        word_data = form.word.data.lower() if form.word.data else ''
        meaning_data = form.meaning.data if form.meaning.data else ''

        existing = VocabularyWord.query.filter_by(
            user_id=current_user.id,
            word=word_data,
            language='en'
        ).first()

        if not existing and word_data and meaning_data:
            vocab_word = VocabularyWord()
            vocab_word.user_id = current_user.id
            vocab_word.word = word_data
            vocab_word.meaning = meaning_data
            vocab_word.language = 'en'
            db.session.add(vocab_word)
            db.session.commit()
            flash('단어가 단어장에 추가되었습니다.', 'success')
        else:
            flash('이미 단어장에 있는 단어입니다.', 'warning')

    return redirect(url_for('english_dictionary'))

@app.route('/submit-quiz-score', methods=['POST'])
@login_required
def submit_quiz_score():
    data = request.get_json()

    quiz_score = QuizScore()
    quiz_score.user_id = current_user.id
    quiz_score.quiz_type = data['quiz_type']
    quiz_score.score = data['score']
    quiz_score.total_questions = data['total_questions']
    db.session.add(quiz_score)
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route('/admin/add-korean-vocab', methods=['POST'])
@login_required
@csrf.exempt
def add_korean_vocab():
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403

    data = request.get_json()
    vocab = KoreanVocabulary()
    vocab.word = data['word']
    vocab.meaning = data['meaning']
    vocab.category = data['category']
    db.session.add(vocab)
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route('/admin/delete-korean-vocab/<int:vocab_id>', methods=['DELETE'])
@login_required
@csrf.exempt
def delete_korean_vocab(vocab_id):
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403

    vocab = KoreanVocabulary.query.get_or_404(vocab_id)
    db.session.delete(vocab)
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route('/admin/announcements', methods=['GET', 'POST'])
@login_required
def admin_announcements():
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'danger')
        return redirect(url_for('dashboard'))

    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            visibility=form.visibility.data,
            priority=form.priority.data,
            created_by=current_user.id,
            expires_at=form.expires_at.data,
            is_active=form.is_active.data
        )
        db.session.add(announcement)
        db.session.commit()
        flash('공지사항이 작성되었습니다.', 'success')
        return redirect(url_for('admin_announcements'))

    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin_announcements.html', form=form, announcements=announcements)

@app.route('/admin/announcements/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_announcement(announcement_id):
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'danger')
        return redirect(url_for('dashboard'))

    announcement = Announcement.query.get_or_404(announcement_id)
    form = AnnouncementForm(obj=announcement)

    if form.validate_on_submit():
        form.populate_obj(announcement)
        announcement.updated_at = datetime.now()
        db.session.commit()
        flash('공지사항이 수정되었습니다.', 'success')
        return redirect(url_for('admin_announcements'))

    return render_template('edit_announcement.html', form=form, announcement=announcement)

@app.route('/admin/announcements/<int:announcement_id>/delete', methods=['POST'])
@login_required
@csrf.exempt
def delete_announcement(announcement_id):
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'danger')
        return redirect(url_for('dashboard'))

    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash('공지사항이 삭제되었습니다.', 'success')
    return redirect(url_for('admin_announcements'))

@app.route('/admin/announcements/<int:announcement_id>/toggle', methods=['POST'])
@login_required
@csrf.exempt
def toggle_announcement(announcement_id):
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403

    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = not announcement.is_active
    announcement.updated_at = datetime.now()
    db.session.commit()

    return jsonify({'status': 'success', 'is_active': announcement.is_active})

@app.route('/admin/delete-resource/<int:resource_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_resource(resource_id):
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': '관리자 권한이 필요합니다.'}), 403

        resource = PDFResource.query.get(resource_id)
        if not resource:
            return jsonify({'status': 'error', 'message': '파일을 찾을 수 없습니다.'}), 404

        # 실제 파일 삭제
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], resource.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # 데이터베이스에서 삭제
        db.session.delete(resource)
        db.session.commit()

        return jsonify({'status': 'success', 'message': '파일이 삭제되었습니다.'})

    except Exception as e:
        db.session.rollback()
        print(f"Delete resource error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/approve-request/<int:request_id>', methods=['POST'])
@login_required
@csrf.exempt
def approve_request(request_id):
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': '관리자 권한이 필요합니다.'}), 403

        request_obj = PDFRequest.query.get(request_id)
        if not request_obj:
            return jsonify({'status': 'error', 'message': '요청을 찾을 수 없습니다.'}), 404

        if request_obj.status != 'pending':
            return jsonify({'status': 'error', 'message': '이미 처리된 요청입니다.'}), 400

        request_obj.status = 'approved'
        request_obj.processed_at = datetime.now()

        db.session.commit()
        return jsonify({'status': 'success', 'message': '요청이 승인되었습니다.'})

    except Exception as e:
        db.session.rollback()
        print(f"Approve request error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'승인 처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/reject-request/<int:request_id>', methods=['POST'])
@login_required
@csrf.exempt
def reject_request(request_id):
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': '관리자 권한이 필요합니다.'}), 403

        request_obj = PDFRequest.query.get(request_id)
        if not request_obj:
            return jsonify({'status': 'error', 'message': '요청을 찾을 수 없습니다.'}), 404

        if request_obj.status != 'pending':
            return jsonify({'status': 'error', 'message': '이미 처리된 요청입니다.'}), 400

        request_obj.status = 'rejected'
        request_obj.processed_at = datetime.now()

        db.session.commit()
        return jsonify({'status': 'success', 'message': '요청이 거절되었습니다.'})

    except Exception as e:
        db.session.rollback()
        print(f"Reject request error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'거절 처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/toggle-user-role/<int:user_id>', methods=['POST'])
@login_required
@csrf.exempt
def toggle_user_role(user_id):
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': '관리자 권한이 필요합니다.'}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '사용자를 찾을 수 없습니다.'}), 404

        if user.id == current_user.id:
            return jsonify({'status': 'error', 'message': '본인의 권한은 변경할 수 없습니다.'}), 400

        user.is_admin = not user.is_admin
        db.session.commit()

        action = '관리자 권한이 부여' if user.is_admin else '관리자 권한이 해제'
        return jsonify({'status': 'success', 'message': f'{user.username}님의 {action}되었습니다.'})

    except Exception as e:
        db.session.rollback()
        print(f"Toggle user role error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'권한 변경 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/add-nonfiction-test', methods=['POST'])
@login_required
@csrf.exempt
def add_nonfiction_test():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '관리자 권한이 필요합니다.'}), 403
    
    try:
        # JSON 데이터 가져오기
        data = request.get_json()
        test_id = data.get('id')
        title = data.get('title')
        description = data.get('description', '')
        passage = data.get('passage')
        questions = data.get('questions', [])
        
        if not test_id or not title or not passage:
            return jsonify({'success': False, 'message': '문제 ID, 제목, 지문은 필수입니다.'})
        
        # 문제 ID 중복 확인
        tests_dir = '모의고사'
        os.makedirs(tests_dir, exist_ok=True)
        
        filepath = os.path.join(tests_dir, f"{test_id}.txt")
        if os.path.exists(filepath):
            return jsonify({'success': False, 'message': '이미 존재하는 문제 ID입니다.'})
        
        # 모의고사 데이터 저장
        test_data = {
            'id': test_id,
            'title': title,
            'description': description,
            'passage': passage,
            'questions': questions
        }
        
        if save_nonfiction_test(test_data):
            return jsonify({'success': True, 'message': '비문학 모의고사가 성공적으로 추가되었습니다.'})
        else:
            return jsonify({'success': False, 'message': '저장 중 오류가 발생했습니다.'})
        
    except Exception as e:
        print(f"Add nonfiction test error: {str(e)}")
        return jsonify({'success': False, 'message': '추가 중 오류가 발생했습니다.'})

@app.route('/admin/nonfiction-tests')
@login_required
def admin_nonfiction_tests():
    if not current_user.is_admin:
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
    
    tests = load_nonfiction_tests()
    return jsonify({'tests': tests})

@app.route('/admin/delete-nonfiction-test/<test_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_nonfiction_test(test_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '관리자 권한이 필요합니다.'}), 403
    
    try:
        tests_dir = '모의고사'
        filepath = os.path.join(tests_dir, f"{test_id}.txt")
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': '문제를 찾을 수 없습니다.'}), 404
        
        # 파일 삭제
        os.remove(filepath)
        
        # 관련 결과 파일들도 삭제 (선택사항)
        results_dir = os.path.join(tests_dir, 'results')
        if os.path.exists(results_dir):
            for filename in os.listdir(results_dir):
                if f'_{test_id}' in filename:
                    result_filepath = os.path.join(results_dir, filename)
                    try:
                        os.remove(result_filepath)
                    except:
                        pass  # 결과 파일 삭제 실패해도 계속 진행
        
        return jsonify({'success': True, 'message': '비문학 모의고사가 삭제되었습니다.'})
        
    except Exception as e:
        print(f"Delete nonfiction test error: {str(e)}")
        return jsonify({'success': False, 'message': '삭제 중 오류가 발생했습니다.'}), 500

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_user(user_id):
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': '관리자 권한이 필요합니다.'}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '사용자를 찾을 수 없습니다.'}), 404

        if user.id == current_user.id:
            return jsonify({'status': 'error', 'message': '본인 계정은 삭제할 수 없습니다.'}), 400

        username = user.username

        # 관련된 데이터도 함께 삭제
        VocabularyWord.query.filter_by(user_id=user_id).delete()
        QuizScore.query.filter_by(user_id=user_id).delete()
        PDFRequest.query.filter_by(user_id=user_id).delete()

        db.session.delete(user)
        db.session.commit()

        return jsonify({'status': 'success', 'message': f'{username}님의 계정이 삭제되었습니다.'})

    except Exception as e:
        db.session.rollback()
        print(f"Delete user error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'사용자 삭제 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/reset-user-requests/<int:user_id>', methods=['POST'])
@login_required
@csrf.exempt
def reset_user_requests(user_id):
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': '관리자 권한이 필요합니다.'}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '사용자를 찾을 수 없습니다.'}), 404

        # 오늘 날짜의 요청만 삭제 (일일 제한 초기화)
        from datetime import date
        today = date.today()
        today_requests = PDFRequest.query.filter(
            PDFRequest.user_id == user_id,
            db.func.date(PDFRequest.requested_at) == today
        ).delete()

        db.session.commit()

        return jsonify({'status': 'success', 'message': f'{user.username}님의 오늘 PDF 요청이 초기화되었습니다. ({today_requests}개 삭제)'})

    except Exception as e:
        db.session.rollback()
        print(f"Reset user requests error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'요청 초기화 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/admin/reset-all-requests', methods=['POST'])
@login_required
@csrf.exempt
def reset_all_requests():
    try:
        if not current_user.is_admin:
            return jsonify({'status': 'error', 'message': '관리자 권한이 필요합니다.'}), 403

        # 오늘 날짜의 모든 요청 삭제
        from datetime import date
        today = date.today()
        deleted_count = PDFRequest.query.filter(
            db.func.date(PDFRequest.requested_at) == today
        ).delete()

        db.session.commit()

        return jsonify({'status': 'success', 'message': f'오늘의 모든 PDF 요청이 초기화되었습니다. ({deleted_count}개 삭제)'})

    except Exception as e:
        db.session.rollback()
        print(f"Reset all requests error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'전체 요청 초기화 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/dictionary/<word>')
@login_required
def get_word_definition(word):
    try:
        # 다음 사전에서 단어 검색
        korean_meaning = search_daum_dictionary(word)

        if korean_meaning:
            # 품사별로 분리된 뜻을 파싱
            meanings_list = []

            if ' | ' in korean_meaning:
                # 품사별로 구분된 경우
                parts = korean_meaning.split(' | ')
                for part in parts:
                    if '[' in part and ']' in part:
                        # 품사 정보가 있는 경우
                        pos_end = part.find(']')
                        pos = part[1:pos_end]
                        definition = part[pos_end+1:].strip()
                        meanings_list.append({
                            'partOfSpeech': pos,
                            'partOfSpeechKorean': pos,
                            'definitions': [],
                            'koreanDefinitions': [definition] if definition else []
                        })
                    else:
                        # 품사 정보가 없는 경우
                        meanings_list.append({
                            'partOfSpeech': '',
                            'partOfSpeechKorean': '',
                            'definitions': [],
                            'koreanDefinitions': [part.strip()]
                        })
            else:
                # 단순한 뜻의 경우 쉼표로 분리
                definitions = [def_.strip() for def_ in korean_meaning.split(',')]
                meanings_list.append({
                    'partOfSpeech': '',
                    'partOfSpeechKorean': '',
                    'definitions': [],
                    'koreanDefinitions': definitions
                })

            # 메인 번역은 첫 번째 뜻 사용
            main_translation = korean_meaning.split(' | ')[0] if ' | ' in korean_meaning else korean_meaning
            if '[' in main_translation and ']' in main_translation:
                pos_end = main_translation.find(']')
                main_translation = main_translation[pos_end+1:].strip()

            return jsonify({
                'word': word,
                'meanings': meanings_list,
                'phonetics': [],
                'mainTranslation': main_translation
            })
        else:
            return jsonify({'error': '단어를 찾을 수 없습니다. 다시 시도해주세요.'}), 404

    except Exception as e:
        print(f"Dictionary API error: {str(e)}")
        return jsonify({'error': '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'}), 500

def save_ticket_to_file(ticket_data):
    """문의를 텍스트 파일로 저장"""
    try:
        # support_tickets 폴더 생성
        tickets_dir = 'support_tickets'
        os.makedirs(tickets_dir, exist_ok=True)
        
        # 파일명 생성 (타임스탬프 + 사용자ID)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ticket_{timestamp}_{ticket_data['user_id']}.txt"
        filepath = os.path.join(tickets_dir, filename)
        
        # 텍스트 파일로 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== 고객 문의 ===\n")
            f.write(f"문의 ID: {filename}\n")
            f.write(f"사용자: {ticket_data['username']} (ID: {ticket_data['user_id']})\n")
            f.write(f"제목: {ticket_data['subject']}\n")
            f.write(f"우선순위: {ticket_data['priority']}\n")
            f.write(f"문의일시: {ticket_data['created_at']}\n")
            f.write(f"상태: 대기중\n")
            f.write(f"\n=== 문의 내용 ===\n")
            f.write(f"{ticket_data['message']}\n")
            f.write(f"\n=== 답변 내역 ===\n")
            f.write(f"(답변 없음)\n")
        
        print(f"문의가 파일로 저장됨: {filepath}")
        
    except Exception as e:
        print(f"문의 저장 오류: {str(e)}")

def load_user_tickets(user_id):
    """사용자의 문의 파일들을 로드"""
    try:
        tickets_dir = 'support_tickets'
        if not os.path.exists(tickets_dir):
            return []
        
        user_tickets = []
        for filename in os.listdir(tickets_dir):
            if filename.endswith(f'_{user_id}.txt'):
                filepath = os.path.join(tickets_dir, filename)
                ticket_data = parse_ticket_file(filepath, filename)
                if ticket_data:
                    user_tickets.append(ticket_data)
        
        # 최신순으로 정렬
        user_tickets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return user_tickets
        
    except Exception as e:
        print(f"문의 로드 오류: {str(e)}")
        return []

def parse_ticket_file(filepath, filename):
    """문의 파일을 파싱하여 딕셔너리로 반환"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 기본 정보 추출
        lines = content.split('\n')
        ticket_data = {
            'id': filename.replace('.txt', ''),
            'filename': filename,
            'subject': '',
            'priority': 'normal',
            'created_at': '',
            'status': '대기중',
            'message': '',
            'replies_count': 0,
            'user_id': '',
            'username': ''
        }
        
        for line in lines:
            if line.startswith('제목: '):
                ticket_data['subject'] = line.replace('제목: ', '')
            elif line.startswith('우선순위: '):
                ticket_data['priority'] = line.replace('우선순위: ', '')
            elif line.startswith('문의일시: '):
                ticket_data['created_at'] = line.replace('문의일시: ', '')
            elif line.startswith('상태: '):
                ticket_data['status'] = line.replace('상태: ', '')
            elif line.startswith('사용자: '):
                user_info = line.replace('사용자: ', '')
                if '(ID: ' in user_info:
                    username = user_info.split(' (ID: ')[0]
                    user_id = user_info.split(' (ID: ')[1].replace(')', '')
                    ticket_data['username'] = username
                    ticket_data['user_id'] = user_id
        
        # 문의 내용 추출
        content_start = content.find('=== 문의 내용 ===')
        replies_start = content.find('=== 답변 내역 ===')
        if content_start != -1 and replies_start != -1:
            message_content = content[content_start:replies_start].replace('=== 문의 내용 ===\n', '').strip()
            ticket_data['message'] = message_content
        
        # 답변 개수 계산 및 답변 내용 추출
        replies_section = content[replies_start:] if replies_start != -1 else ''
        ticket_data['replies'] = []
        
        if '(답변 없음)' not in replies_section:
            # 답변이 있으면 개수 계산 및 내용 추출
            ticket_data['replies_count'] = replies_section.count('답변:')
            
            # 답변 내용들을 리스트로 추출
            replies_text = replies_section.replace('=== 답변 내역 ===\n', '').strip()
            if replies_text:
                # 각 답변을 분리
                reply_blocks = replies_text.split('\n답변:')
                for i, block in enumerate(reply_blocks):
                    if i == 0 and not block.startswith('답변:'):
                        continue
                    if i > 0:
                        block = '답변:' + block
                    ticket_data['replies'].append(block.strip())
        
        return ticket_data
        
    except Exception as e:
        print(f"파일 파싱 오류: {str(e)}")
        return None

def load_all_tickets():
    """모든 문의 파일들을 로드"""
    try:
        tickets_dir = 'support_tickets'
        if not os.path.exists(tickets_dir):
            return []
        
        all_tickets = []
        for filename in os.listdir(tickets_dir):
            if filename.startswith('ticket_') and filename.endswith('.txt'):
                filepath = os.path.join(tickets_dir, filename)
                ticket_data = parse_ticket_file(filepath, filename)
                if ticket_data:
                    all_tickets.append(ticket_data)
        
        # 최신순으로 정렬
        all_tickets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return all_tickets
        
    except Exception as e:
        print(f"전체 문의 로드 오류: {str(e)}")
        return []

def load_ticket_by_id(ticket_id):
    """특정 ID의 문의 파일을 로드"""
    try:
        tickets_dir = 'support_tickets'
        filename = f"{ticket_id}.txt"
        filepath = os.path.join(tickets_dir, filename)
        
        if os.path.exists(filepath):
            return parse_ticket_file(filepath, filename)
        return None
        
    except Exception as e:
        print(f"문의 로드 오류: {str(e)}")
        return None

def add_reply_to_ticket_file(ticket_id, username, message, is_admin_reply):
    """문의 파일에 답변 추가"""
    try:
        tickets_dir = 'support_tickets'
        filename = f"{ticket_id}.txt"
        filepath = os.path.join(tickets_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        # 기존 파일 내용 읽기
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 답변 추가
        reply_text = f"\n답변: {username} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
        if is_admin_reply:
            reply_text += "[관리자 답변]\n"
        reply_text += f"{message}\n"
        
        # (답변 없음) 제거하고 답변 추가
        if '(답변 없음)' in content:
            content = content.replace('(답변 없음)', reply_text.strip())
        else:
            content += reply_text
        
        # 상태 업데이트 (관리자가 답변한 경우)
        if is_admin_reply and '상태: 대기중' in content:
            content = content.replace('상태: 대기중', '상태: 답변완료')
        
        # 파일에 다시 쓰기
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"답변이 파일에 추가됨: {filepath}")
        return True
        
    except Exception as e:
        print(f"답변 추가 오류: {str(e)}")
        return False

def load_nonfiction_tests():
    """모의고사 폴더에서 문제 목록을 로드"""
    try:
        tests_dir = '모의고사'
        if not os.path.exists(tests_dir):
            os.makedirs(tests_dir, exist_ok=True)
            return []
        
        tests = []
        for filename in os.listdir(tests_dir):
            if filename.endswith('.txt'):
                test_id = filename.replace('.txt', '')
                test_data = load_nonfiction_test(test_id)
                if test_data:
                    tests.append({
                        'id': test_id,
                        'title': test_data['title'],
                        'description': test_data.get('description', ''),
                        'question_count': len(test_data['questions'])
                    })
        
        return sorted(tests, key=lambda x: x['title'])
        
    except Exception as e:
        print(f"Load nonfiction tests error: {str(e)}")
        return []

def load_nonfiction_test(test_id):
    """특정 모의고사 문제를 로드"""
    try:
        tests_dir = '모의고사'
        filepath = os.path.join(tests_dir, f"{test_id}.txt")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse test data
        lines = content.split('\n')
        test_data = {
            'id': test_id,
            'title': '',
            'description': '',
            'passage': '',
            'questions': []
        }
        
        current_section = ''
        current_question = None
        
        for line in lines:
            line = line.strip()
            # Remove any control characters
            line = ''.join(char for char in line if ord(char) >= 32 or char in '\t\n\r')
            if line.startswith('제목: '):
                test_data['title'] = line.replace('제목: ', '')
            elif line.startswith('설명: '):
                test_data['description'] = line.replace('설명: ', '')
            elif line == '=== 지문 ===':
                current_section = 'passage'
            elif line.startswith('=== 문제') and line.endswith('==='):
                current_section = 'question'
                try:
                    # 문제 번호 파싱 개선
                    parts = line.replace('===', '').strip().split()
                    if len(parts) >= 2:
                        question_num_str = parts[1].replace('번', '')
                        question_num = int(question_num_str)
                    else:
                        question_num = len(test_data['questions']) + 1
                except (ValueError, IndexError):
                    question_num = len(test_data['questions']) + 1
                
                current_question = {
                    'number': question_num,
                    'content': '',
                    'options': [],
                    'correct_answer': 1,
                    'explanation': ''
                }
            elif line.startswith('정답: '):
                if current_question:
                    try:
                        current_question['correct_answer'] = int(line.replace('정답: ', ''))
                    except ValueError:
                        current_question['correct_answer'] = 1
            elif line.startswith('해설: '):
                if current_question:
                    current_question['explanation'] = line.replace('해설: ', '')
                    test_data['questions'].append(current_question)
                    current_question = None
            elif current_section == 'passage':
                if line:
                    test_data['passage'] += line + '\n'
            elif current_section == 'question' and current_question:
                if line.startswith('①') or line.startswith('②') or line.startswith('③') or line.startswith('④') or line.startswith('⑤'):
                    current_question['options'].append(line[1:].strip())
                elif line and not line.startswith('='):
                    current_question['content'] += line + '\n'
        
        # 마지막 문제가 해설 없이 끝나는 경우 처리
        if current_question:
            test_data['questions'].append(current_question)
        
        test_data['question_count'] = len(test_data['questions'])
        return test_data
        
    except Exception as e:
        print(f"Load nonfiction test error: {str(e)}")
        return None

def save_nonfiction_result(user_id, test_id, answers, score, duration, test_title):
    """비문학 모의고사 결과를 파일로 저장"""
    try:
        results_dir = os.path.join('모의고사', 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate result ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_id = f"result_{timestamp}_{user_id}_{test_id}"
        
        result_data = {
            'result_id': result_id,
            'user_id': user_id,
            'test_id': test_id,
            'test_title': test_title,
            'answers': answers,
            'score': score,
            'duration': duration,
            'completed_at': datetime.now().isoformat()
        }
        
        filepath = os.path.join(results_dir, f"{result_id}.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== 비문학 모의고사 결과 ===\n")
            f.write(f"결과 ID: {result_id}\n")
            f.write(f"사용자 ID: {user_id}\n")
            f.write(f"문제 ID: {test_id}\n")
            f.write(f"문제 제목: {test_title}\n")
            f.write(f"점수: {score}점\n")
            f.write(f"소요시간: {duration}분\n")
            f.write(f"완료시간: {result_data['completed_at']}\n")
            f.write(f"\n=== 답안 ===\n")
            for question_num, answer in answers.items():
                f.write(f"문제 {question_num}: {answer}번\n")
        
        return result_id
        
    except Exception as e:
        print(f"Save nonfiction result error: {str(e)}")
        return None

def load_nonfiction_result(result_id):
    """비문학 모의고사 결과를 로드"""
    try:
        results_dir = os.path.join('모의고사', 'results')
        filepath = os.path.join(results_dir, f"{result_id}.txt")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse result data
        lines = content.split('\n')
        result_data = {
            'result_id': result_id,
            'answers': {}
        }
        
        for line in lines:
            if line.startswith('사용자 ID: '):
                result_data['user_id'] = int(line.replace('사용자 ID: ', ''))
            elif line.startswith('문제 ID: '):
                result_data['test_id'] = line.replace('문제 ID: ', '')
            elif line.startswith('문제 제목: '):
                result_data['test_title'] = line.replace('문제 제목: ', '')
            elif line.startswith('점수: '):
                result_data['score'] = int(line.replace('점수: ', '').replace('점', ''))
            elif line.startswith('소요시간: '):
                result_data['duration'] = int(line.replace('소요시간: ', '').replace('분', ''))
            elif line.startswith('완료시간: '):
                result_data['completed_at'] = line.replace('완료시간: ', '')
            elif line.startswith('문제 ') and ': ' in line:
                parts = line.split(': ')
                question_num = parts[0].replace('문제 ', '')
                answer = int(parts[1].replace('번', ''))
                result_data['answers'][question_num] = answer
        
        return result_data
        
    except Exception as e:
        print(f"Load nonfiction result error: {str(e)}")
        return None

def load_user_nonfiction_results(user_id):
    """사용자의 모든 비문학 모의고사 결과를 로드"""
    try:
        results_dir = os.path.join('모의고사', 'results')
        if not os.path.exists(results_dir):
            return []
        
        user_results = []
        for filename in os.listdir(results_dir):
            if filename.endswith(f'_{user_id}_') or filename.endswith(f'_{user_id}.txt'):
                result_data = load_nonfiction_result(filename.replace('.txt', ''))
                if result_data:
                    user_results.append(result_data)
        
        # Sort by completion time (newest first)
        user_results.sort(key=lambda x: x.get('completed_at', ''), reverse=True)
        return user_results
        
    except Exception as e:
        print(f"Load user nonfiction results error: {str(e)}")
        return []

def save_nonfiction_test_with_images(test_data):
    """이미지가 포함된 비문학 모의고사를 파일로 저장"""
    try:
        tests_dir = '모의고사'
        os.makedirs(tests_dir, exist_ok=True)
        
        test_id = test_data['id']
        filepath = os.path.join(tests_dir, f"{test_id}.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"제목: {test_data['title']}\n")
            f.write(f"설명: {test_data['description']}\n")
            f.write(f"지문이미지: {test_data['passage_image']}\n")
            f.write(f"\n=== 지문 ===\n")
            f.write(f"이미지 파일로 제공\n")
            
            for question in test_data['questions']:
                f.write(f"\n=== 문제 {question['number']}번 ===\n")
                f.write(f"문제이미지: {question['image_path']}\n")
                f.write(f"정답: {question['correct_answer']}\n")
                if question.get('explanation'):
                    f.write(f"해설: {question['explanation']}\n")
        
        return True
        
    except Exception as e:
        print(f"Save nonfiction test with images error: {str(e)}")
        return False

def save_nonfiction_test(test_data):
    """비문학 모의고사를 파일로 저장"""
    try:
        tests_dir = '모의고사'
        os.makedirs(tests_dir, exist_ok=True)
        
        test_id = test_data['id']
        filepath = os.path.join(tests_dir, f"{test_id}.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"제목: {test_data['title']}\n")
            f.write(f"설명: {test_data['description']}\n")
            f.write(f"\n=== 지문 ===\n")
            f.write(f"{test_data['passage']}\n")
            
            for i, question in enumerate(test_data['questions'], 1):
                f.write(f"\n=== 문제 {i}번 ===\n")
                f.write(f"{question['content']}\n")
                for j, option in enumerate(question['options'], 1):
                    f.write(f"{'①②③④⑤'[j-1]} {option}\n")
                f.write(f"정답: {question['correct_answer']}\n")
                if question.get('explanation'):
                    f.write(f"해설: {question['explanation']}\n")
        
        return True
        
    except Exception as e:
        print(f"Save nonfiction test error: {str(e)}")
        return False

def search_daum_dictionary(word):
    """다음 사전에서 영어 단어의 한국어 뜻을 검색합니다"""
    try:
        # 기본 단어 매핑 (빠른 검색을 위해)
        word_mappings = {
            'apple': '[명사] 사과', 'book': '[명사] 책', 'computer': '[명사] 컴퓨터', 
            'water': '[명사] 물', 'love': '[동사] 사랑하다 | [명사] 사랑', 
            'house': '[명사] 집, 가옥', 'school': '[명사] 학교', 'student': '[명사] 학생', 
            'teacher': '[명사] 선생님, 교사', 'friend': '[명사] 친구', 'family': '[명사] 가족',
            'food': '[명사] 음식, 식품', 'time': '[명사] 시간, 때', 'money': '[명사] 돈, 화폐',
            'work': '[동사] 일하다 | [명사] 일, 작업', 'study': '[동사] 공부하다 | [명사] 연구',
            'hello': '[감탄사] 안녕하세요', 'good': '[형용사] 좋은, 훌륭한', 
            'bad': '[형용사] 나쁜, 안 좋은', 'big': '[형용사] 큰', 'small': '[형용사] 작은',
            'beautiful': '[형용사] 아름다운, 예쁜', 'happy': '[형용사] 행복한, 기쁜',
            'help': '[동사] 돕다 | [명사] 도움', 'get': '[동사] 얻다, 받다', 'go': '[동사] 가다',
            'come': '[동사] 오다', 'see': '[동사] 보다', 'know': '[동사] 알다', 'think': '[동사] 생각하다',
            'world': '[명사] 세계, 세상', 'hope': '[동사] 희망하다 | [명사] 희망',
            'like': '[동사] 좋아하다 | [전치사] ~같은', 'make': '[동사] 만들다',
            'huge': '[형용사] 거대한, 매우 큰', 'tiny': '[형용사] 아주 작은',
            'amazing': '[형용사] 놀라운, 경이로운', 'wonderful': '[형용사] 훌륭한, 멋진',
            'important': '[형용사] 중요한', 'different': '[형용사] 다른, 차이나는',
            'difficult': '[형용사] 어려운, 힘든', 'easy': '[형용사] 쉬운, 간단한',
            'possible': '[형용사] 가능한', 'impossible': '[형용사] 불가능한',
            'remember': '[동사] 기억하다', 'forget': '[동사] 잊다', 'understand': '[동사] 이해하다',
            'explain': '[동사] 설명하다', 'describe': '[동사] 묘사하다', 'create': '[동사] 창조하다',
            'destroy': '[동사] 파괴하다', 'build': '[동사] 건설하다', 'break': '[동사] 부수다',
            'repair': '[동사] 수리하다', 'change': '[동사] 바꾸다 | [명사] 변화',
            'improve': '[동사] 개선하다', 'develop': '[동사] 개발하다', 'grow': '[동사] 자라다',
            'increase': '[동사] 증가하다', 'decrease': '[동사] 감소하다', 'start': '[동사] 시작하다',
            'finish': '[동사] 끝내다', 'continue': '[동사] 계속하다', 'stop': '[동사] 멈추다',
            'move': '[동사] 움직이다', 'travel': '[동사] 여행하다', 'visit': '[동사] 방문하다',
            'meet': '[동사] 만나다', 'leave': '[동사] 떠나다', 'arrive': '[동사] 도착하다',
            'return': '[동사] 돌아오다', 'stay': '[동사] 머물다', 'live': '[동사] 살다',
            'die': '[동사] 죽다', 'born': '[동사] 태어나다', 'grow': '[동사] 자라다',
            'learn': '[동사] 배우다', 'teach': '[동사] 가르치다', 'practice': '[동사] 연습하다',
            'try': '[동사] 시도하다', 'succeed': '[동사] 성공하다', 'fail': '[동사] 실패하다',
            'win': '[동사] 이기다', 'lose': '[동사] 지다', 'play': '[동사] 놀다, 연주하다',
            'watch': '[동사] 보다', 'listen': '[동사] 듣다', 'speak': '[동사] 말하다',
            'talk': '[동사] 이야기하다', 'tell': '[동사] 말하다', 'ask': '[동사] 묻다',
            'answer': '[동사] 대답하다 | [명사] 답', 'question': '[명사] 질문',
            'problem': '[명사] 문제', 'solution': '[명사] 해결책', 'idea': '[명사] 아이디어',
            'plan': '[명사] 계획 | [동사] 계획하다', 'decision': '[명사] 결정',
            'choice': '[명사] 선택', 'option': '[명사] 선택권', 'opportunity': '[명사] 기회',
            'chance': '[명사] 기회, 가능성', 'luck': '[명사] 운', 'success': '[명사] 성공',
            'failure': '[명사] 실패', 'mistake': '[명사] 실수', 'error': '[명사] 오류',
            'truth': '[명사] 진실', 'lie': '[명사] 거짓말 | [동사] 거짓말하다',
            'fact': '[명사] 사실', 'information': '[명사] 정보', 'knowledge': '[명사] 지식',
            'education': '[명사] 교육', 'experience': '[명사] 경험', 'skill': '[명사] 기술',
            'ability': '[명사] 능력', 'talent': '[명사] 재능', 'gift': '[명사] 선물, 재능',
            'strength': '[명사] 힘, 강점', 'weakness': '[명사] 약점', 'advantage': '[명사] 이점',
            'disadvantage': '[명사] 단점', 'benefit': '[명사] 이익', 'profit': '[명사] 이익',
            'loss': '[명사] 손실', 'cost': '[명사] 비용 | [동사] 비용이 들다',
            'price': '[명사] 가격', 'value': '[명사] 가치', 'worth': '[명사] 가치',
            'quality': '[명사] 품질', 'quantity': '[명사] 양', 'size': '[명사] 크기',
            'weight': '[명사] 무게', 'height': '[명사] 높이', 'length': '[명사] 길이',
            'width': '[명사] 너비', 'depth': '[명사] 깊이', 'distance': '[명사] 거리',
            'speed': '[명사] 속도', 'direction': '[명사] 방향', 'location': '[명사] 위치',
            'place': '[명사] 장소', 'position': '[명사] 위치', 'situation': '[명사] 상황',
            'condition': '[명사] 상태, 조건', 'environment': '[명사] 환경', 'atmosphere': '[명사] 분위기',
            'culture': '[명사] 문화', 'society': '[명사] 사회', 'community': '[명사] 공동체',
            'group': '[명사] 그룹', 'team': '[명사] 팀', 'organization': '[명사] 조직',
            'company': '[명사] 회사', 'business': '[명사] 사업', 'industry': '[명사] 산업',
            'economy': '[명사] 경제', 'market': '[명사] 시장', 'customer': '[명사] 고객',
            'service': '[명사] 서비스', 'product': '[명사] 제품', 'technology': '[명사] 기술',
            'science': '[명사] 과학', 'research': '[명사] 연구', 'experiment': '[명사] 실험',
            'method': '[명사] 방법', 'system': '[명사] 시스템', 'process': '[명사] 과정',
            'result': '[명사] 결과', 'effect': '[명사] 효과', 'influence': '[명사] 영향',
            'impact': '[명사] 영향, 충격', 'consequence': '[명사] 결과', 'outcome': '[명사] 결과'
        }

        # 기본 매핑에서 먼저 확인
        if word.lower() in word_mappings:
            return word_mappings[word.lower()]

        # 다음 사전 URL
        dic_url = f"http://dic.daum.net/search.do?q={word}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(dic_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 다음 사전 결과에서 한국어 뜻 추출
            korean_meanings = []

            # 다음 사전의 클래스명들 시도
            meaning_selectors = [
                '.list_search',           # 기본 검색 결과
                '.search_cleanword',      # 클린 검색 결과  
                '.txt_search',            # 검색 텍스트
                '.cleanword_type',        # 클린워드 타입
                '.list_mean',             # 의미 리스트
                '.txt_emph1',             #         강조 텍스트
                '.search_result',         # 검색 결과
                '.mean_list',             # 의미 목록
                '.word_class',            # 단어 클래스
                '.mean_item'              # 의미 항목
            ]

            for selector in meaning_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text().strip()
                    # 한국어가 포함되고 적당한 길이인 텍스트 찾기
                    if text and any('\uac00' <= char <= '\ud7af' for char in text):
                        if 2 < len(text) < 150:
                            # 불필요한 텍스트 제거
                            skip_words = ['다음', '사전', '검색', '결과', '목록', '페이지', '로그인', '회원가입']
                            if not any(skip in text for skip in skip_words):
                                # 줄바꿈을 쉼표로 변경하고 정리
                                cleaned_text = text.replace('\n', ', ').replace('\t', ' ')
                                cleaned_text = ' '.join(cleaned_text.split())
                                if cleaned_text and cleaned_text not in korean_meanings:
                                    korean_meanings.append(cleaned_text)

            # 특정 태그에서 한국어 텍스트 검색 (fallback)
            if not korean_meanings:
                all_elements = soup.find_all(['span', 'div', 'li', 'p', 'dd', 'dt'])
                for elem in all_elements:
                    text = elem.get_text().strip()
                    # 한국어가 포함되고 적당한 길이인 텍스트
                    if text and any('\uac00' <= char <= '\ud7af' for char in text):
                        if 3 < len(text) < 100:
                            # 광고나 네비게이션 텍스트 제외
                            skip_words = ['다음', '사전', '로그인', '회원가입', '메뉴', '검색', '광고', '배너']
                            if not any(skip in text for skip in skip_words):
                                cleaned_text = text.replace('\n', ' ').replace('\t', ' ')
                                cleaned_text = ' '.join(cleaned_text.split())
                                if cleaned_text and cleaned_text not in korean_meanings and len(cleaned_text) > 2:
                                    korean_meanings.append(cleaned_text)

            if korean_meanings:
                # 중복 제거 및 정리
                unique_meanings = []
                for meaning in korean_meanings[:8]:  # 상위 8개만 확인
                    if meaning not in unique_meanings and len(meaning) > 2:
                        # 너무 짧거나 의미없는 텍스트 제외
                        if not meaning.isdigit() and len(meaning.split()) > 1:
                            unique_meanings.append(meaning)

                if unique_meanings:
                    # 최대 3개 의미만 반환하되, 품사 정보가 있으면 우선
                    prioritized = []
                    others = []

                    for meaning in unique_meanings:
                        if '[' in meaning and ']' in meaning:
                            prioritized.append(meaning)
                        else:
                            others.append(meaning)

                    final_meanings = (prioritized + others)[:3]
                    return ' | '.join(final_meanings) if len(final_meanings) > 1 else final_meanings[0]

        return None

    except Exception as e:
        print(f"Daum dictionary error: {str(e)}")
        return None

@app.route('/delete-vocabulary/<int:word_id>', methods=['POST'])
@login_required
def delete_vocabulary(word_id):
    try:
        word = VocabularyWord.query.filter_by(id=word_id, user_id=current_user.id).first()
        if not word:
            return jsonify({'success': False, 'message': '단어를 찾을 수 없습니다.'}), 404

        db.session.delete(word)
        db.session.commit()
        return jsonify({'success': True, 'message': '단어가 삭제되었습니다.'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/toggle-auto-add', methods=['POST'])
@login_required
def toggle_auto_add():
    """자동 단어 추가 설정 토글"""
    try:
        data = request.get_json()
        auto_add_enabled = data.get('enabled', False)

        # 사용자 설정에 저장 (간단히 세션에 저장)
        from flask import session
        session['auto_add_enabled'] = auto_add_enabled

        return jsonify({'success': True, 'enabled': auto_add_enabled})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/auto-add-word', methods=['POST'])
@login_required
def auto_add_word():
    """단어 자동 추가"""
    try:
        from flask import session
        if not session.get('auto_add_enabled', False):
            return jsonify({'success': False, 'message': '자동 추가가 비활성화되어 있습니다.'})

        data = request.get_json()
        word = data.get('word', '').lower()

        if not word:
            return jsonify({'success': False, 'message': '단어가 없습니다.'})

        # 이미 존재하는지 확인
        existing = VocabularyWord.query.filter_by(
            user_id=current_user.id,
            word=word,
            language='en'
        ).first()

        if existing:
            return jsonify({'success': False, 'message': '이미 단어장에 있는 단어입니다.'})

        # 네이버 사전에서 뜻 찾기
        meaning = search_daum_dictionary(word)
        if not meaning:
            return jsonify({'success': False, 'message': '단어 뜻을 찾을 수 없습니다.'})

        # 단어장에 추가
        vocab_word = VocabularyWord()
        vocab_word.user_id = current_user.id
        vocab_word.word = word
        vocab_word.meaning = meaning
        vocab_word.korean_meaning = meaning
        vocab_word.language = 'en'

        db.session.add(vocab_word)
        db.session.commit()

        return jsonify({'success': True, 'message': f'"{word}" 단어가 자동으로 추가되었습니다.'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'자동 추가 중 오류: {str(e)}'}), 500

# Update user last seen
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# Initialize some sample Korean vocabulary if database is empty
def initialize_data():
    with app.app_context():
        # Create admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User()
            admin_user.username = 'admin'
            admin_user.email = 'admin@wackydocs.com'
            admin_user.is_admin = True
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("관리자 계정이 생성되었습니다: username=admin, password=admin123")

        # Add sample Korean vocabulary
        if KoreanVocabulary.query.count() == 0:
            sample_vocab = [
            ]

            for vocab in sample_vocab:
                db.session.add(vocab)

            db.session.commit()

# Call initialization function
initialize_data()

# PWA Routes
@app.route('/offline')
def offline():
    return render_template('offline.html')

@app.route('/mobile-app')
@login_required
def mobile_app_guide():
    return render_template('mobile_app_guide.html')

@app.route('/focus-timer')
@login_required
def focus_timer():
    return render_template('focus_timer.html')

@app.route('/profile')
@login_required
def profile():
    # username이 없을 경우 대비
    username = getattr(current_user, 'username', None)
    if not username:
        return "사용자 정보가 올바르지 않습니다.", 400
    return render_template('profile.html', user=current_user)

@app.route('/api/update-profile', methods=['POST'])
@login_required
@csrf.exempt
def update_profile():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()

        if not username or not email:
            return jsonify({'success': False, 'message': '사용자명과 이메일을 모두 입력해주세요.'}), 400

        # 중복 확인 (현재 사용자 제외)
        existing_user = User.query.filter(
            User.username == username,
            User.id != current_user.id
        ).first()

        if existing_user:
            return jsonify({'success': False, 'message': '이미 사용 중인 사용자명입니다.'}), 400

        existing_email = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_email:
            return jsonify({'success': False, 'message': '이미 사용 중인 이메일입니다.'}), 400

        # 프로필 업데이트
        current_user.username = username
        current_user.email = email
        db.session.commit()

        return jsonify({'success': True, 'message': '프로필이 성공적으로 업데이트되었습니다.'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/change-password', methods=['POST'])
@login_required
@csrf.exempt
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')

        if not current_password or not new_password:
            return jsonify({'success': False, 'message': '현재 비밀번호와 새 비밀번호를 모두 입력해주세요.'}), 400

        # 현재 비밀번호 확인
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'message': '현재 비밀번호가 올바르지 않습니다.'}), 400

        if len(new_password) < 8:
            return jsonify({'success': False, 'message': '새 비밀번호는 8자 이상이어야 합니다.'}), 400

        # 비밀번호 변경
        current_user.set_password(new_password)
        db.session.commit()

        return jsonify({'success': True, 'message': '비밀번호가 성공적으로 변경되었습니다.'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/save-focus-session', methods=['POST'])
@login_required
@csrf.exempt
def save_focus_session():
    try:
        from models import FocusSession
        from datetime import date

        data = request.get_json()
        session_date = date.fromisoformat(data.get('session_date', str(date.today())))
        focus_minutes = data.get('focus_minutes', 25)
        completed = data.get('completed', True)

        # 같은 날짜에 기존 세션이 있으면 추가, 없으면 새로 생성
        focus_session = FocusSession(
            user_id=current_user.id,
            session_date=session_date,
            focus_minutes=focus_minutes,
            completed=completed
        )

        db.session.add(focus_session)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/focus-stats')
@login_required
def get_focus_stats():
    try:
        from models import FocusSession
        from datetime import date, timedelta
        from sqlalchemy import func

        # 총 통계 계산
        total_sessions = FocusSession.query.filter_by(user_id=current_user.id, completed=True).count()
        total_focus_minutes = db.session.query(func.sum(FocusSession.focus_minutes)).filter_by(
            user_id=current_user.id, completed=True
        ).scalar() or 0

        # 활동 일수 계산
        active_days = db.session.query(func.count(func.distinct(FocusSession.session_date))).filter_by(
            user_id=current_user.id, completed=True
        ).scalar() or 0

        # 최장 연속 세션 계산 (간단한 버전)
        longest_streak = calculate_longest_streak(current_user.id)

        # 최근 7일 통계
        end_date = date.today()
        start_date = end_date - timedelta(days=6)

        daily_stats = []
        for i in range(7):
            check_date = start_date + timedelta(days=i)
            daily_minutes = db.session.query(func.sum(FocusSession.focus_minutes)).filter(
                FocusSession.user_id == current_user.id,
                FocusSession.session_date == check_date,
                FocusSession.completed == True
            ).scalar() or 0

            daily_stats.append({
                'date': check_date.isoformat(),
                'focus_minutes': daily_minutes
            })

        # 최근 세션 기록 (최대 10개)
        recent_sessions = FocusSession.query.filter_by(
            user_id=current_user.id, completed=True
        ).order_by(FocusSession.created_at.desc()).limit(10).all()

        return jsonify({
            'total_sessions': total_sessions,
            'total_focus_minutes': total_focus_minutes,
            'active_days': active_days,
            'longest_streak': longest_streak,
            'daily_stats': daily_stats,
            'recent_sessions': [session.to_dict() for session in recent_sessions]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_longest_streak(user_id):
    """사용자의 최장 연속 집중 세션 계산"""
    try:
        from models import FocusSession
        from datetime import date, timedelta

        # 모든 집중 세션 날짜 가져오기
        sessions = FocusSession.query.filter_by(
            user_id=user_id, completed=True
        ).with_entities(FocusSession.session_date).distinct().order_by(
            FocusSession.session_date
        ).all()

        if not sessions:
            return 0

        dates = [session.session_date for session in sessions]
        max_streak = 1
        current_streak = 1

        for i in range(1, len(dates)):
            if dates[i] - dates[i-1] == timedelta(days=1):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak

    except Exception:
        return 0

# 공지사항 전체공개 목록 (비회원도 접근 가능)
@app.route('/announcements')
def announcements():
    # 전체공개 공지사항만 조회
    public_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=public_announcements)

@app.route('/customer-support', methods=['GET', 'POST'])
@login_required
def customer_support():
    form = CustomerSupportForm()
    
    # 사용자의 문의 내역 (파일 기반)
    user_tickets = load_user_tickets(current_user.id)
    
    if form.validate_on_submit():
        # 파일로 문의 저장
        ticket_data = {
            'user_id': current_user.id,
            'username': current_user.username,
            'subject': form.subject.data,
            'message': form.message.data,
            'priority': form.priority.data,
            'created_at': datetime.now().isoformat()
        }
        save_ticket_to_file(ticket_data)
        flash('문의가 접수되었습니다. 빠른 시일 내에 답변드리겠습니다.', 'success')
        return redirect(url_for('customer_support'))
    
    return render_template('customer_support.html', form=form, tickets=user_tickets)

@app.route('/customer-support/<ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = load_ticket_by_id(ticket_id)
    
    if not ticket:
        flash('문의를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('customer_support'))
    
    # 본인 티켓이거나 관리자인 경우만 조회 가능
    if str(ticket['user_id']) != str(current_user.id) and not current_user.is_admin:
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('customer_support'))
    
    reply_form = SupportReplyForm()
    return render_template('view_ticket.html', ticket=ticket, reply_form=reply_form)

@app.route('/customer-support/<ticket_id>/reply', methods=['POST'])
@login_required
@csrf.exempt
def reply_ticket(ticket_id):
    ticket = load_ticket_by_id(ticket_id)
    
    if not ticket:
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404
    
    # 본인 티켓이거나 관리자인 경우만 답변 가능
    if str(ticket['user_id']) != str(current_user.id) and not current_user.is_admin:
        return jsonify({'success': False, 'message': '접근 권한이 없습니다.'}), 403
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'message': '메시지를 입력해주세요.'}), 400
    
    # 파일에 답변 추가
    add_reply_to_ticket_file(ticket_id, current_user.username, message, current_user.is_admin)
    
    return jsonify({'success': True, 'message': '답변이 등록되었습니다.'})

@app.route('/admin/support')
@login_required
def admin_support():
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'danger')
        return redirect(url_for('dashboard'))
    
    # 모든 티켓 조회 (파일 기반)
    tickets = load_all_tickets()
    
    return render_template('admin_support.html', tickets=tickets)