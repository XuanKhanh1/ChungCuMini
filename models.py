from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func

db = SQLAlchemy()


class NguoiDung(UserMixin, db.Model):
    __tablename__ = 'NguoiDung'
    id = db.Column(db.Integer, primary_key=True)
    ten_dang_nhap = db.Column(db.String(100), unique=True, nullable=False)
    mat_khau = db.Column(db.String(255), nullable=False)
    vai_tro = db.Column(db.Enum('Admin', 'ChuNha', 'NguoiThue'), nullable=False)
    ho_ten = db.Column(db.String(100))


class CanHo(db.Model):
    __tablename__ = 'CanHo'
    id = db.Column(db.Integer, primary_key=True)
    ma_can = db.Column(db.String(20), unique=True, nullable=False)
    dien_tich = db.Column(db.Numeric(5, 2), nullable=False)
    loai_phong = db.Column(db.String(50))
    tinh_trang = db.Column(db.Enum('Trong', 'DaThue', 'SuaChua'), default='Trong')


class QuyDinh(db.Model):
    __tablename__ = 'QuyDinh'
    id = db.Column(db.Integer, primary_key=True)
    gia_dien = db.Column(db.Numeric(10, 2), nullable=False)
    gia_nuoc = db.Column(db.Numeric(10, 2), nullable=False)
    phi_dich_vu = db.Column(db.Numeric(15, 2), default=0)
    so_nguoi_toi_da = db.Column(db.Integer, default=4)


class HopDong(db.Model):
    __tablename__ = 'HopDong'
    id = db.Column(db.Integer, primary_key=True)
    ma_can = db.Column(db.String(20), nullable=False)

    # --- MỚI THÊM: Liên kết ID để tránh trùng tên ---
    # nullable=True để tránh lỗi nếu lỡ xóa user nhưng vẫn muốn giữ hợp đồng lưu trữ
    id_nguoi_dung = db.Column(db.Integer, db.ForeignKey('NguoiDung.id'), nullable=True)
    # ------------------------------------------------

    nguoi_thue = db.Column(db.String(100), nullable=False)  # Vẫn giữ tên để hiển thị nhanh
    so_nguoi_o = db.Column(db.Integer, nullable=False, default=1)

    ngay_bat_dau = db.Column(db.Date, nullable=False)
    thoi_han = db.Column(db.Integer, nullable=False)
    gia_thue = db.Column(db.Numeric(15, 2), nullable=False)
    tien_coc = db.Column(db.Numeric(15, 2), nullable=False)


class HoaDon(db.Model):
    __tablename__ = 'HoaDon'
    id = db.Column(db.Integer, primary_key=True)
    ma_can = db.Column(db.String(20), nullable=False)
    thang = db.Column(db.String(10), nullable=False)

    dien_cu = db.Column(db.Integer, nullable=False)
    dien_moi = db.Column(db.Integer, nullable=False)
    nuoc_cu = db.Column(db.Integer, nullable=False)
    nuoc_moi = db.Column(db.Integer, nullable=False)

    tien_phong = db.Column(db.Numeric(15, 2), nullable=False)
    tien_dien = db.Column(db.Numeric(15, 2), nullable=False)
    tien_nuoc = db.Column(db.Numeric(15, 2), nullable=False)
    phi_dich_vu = db.Column(db.Numeric(15, 2), nullable=False)

    tong_cong = db.Column(db.Numeric(15, 2), nullable=False)
    trang_thai = db.Column(db.String(20), default='ChuaThu')
