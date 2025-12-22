from app import app, db

with app.app_context():
    db.create_all()
    print(">>> ĐÃ TẠO BẢNG HỢP ĐỒNG THÀNH CÔNG! <<<")
