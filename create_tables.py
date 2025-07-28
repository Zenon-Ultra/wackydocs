
from app import app, db

with app.app_context():
    db.create_all()
    print("모든 데이터베이스 테이블이 생성되었습니다.")
