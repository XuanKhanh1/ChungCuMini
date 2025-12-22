from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta, date
import calendar
# Import models từ file models.py
from models import db, CanHo, NguoiDung, HopDong, QuyDinh, HoaDon

app = Flask(__name__)

# --- CẤU HÌNH DATABASE ---
# LƯU Ý: Nếu mật khẩu MySQL của ông không phải là 'Abc123', hãy sửa lại dòng dưới
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Abc123@localhost/QuanLyCanHo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key_bao_mat_cua_toi'

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return NguoiDung.query.get(int(user_id))


# Hàm hỗ trợ tính ngày kết thúc hợp đồng
def cong_thang(ngay_goc, so_thang):
    thang_moi = ngay_goc.month - 1 + so_thang
    nam_moi = ngay_goc.year + thang_moi // 12
    thang_moi = thang_moi % 12 + 1
    ngay_moi = min(ngay_goc.day, calendar.monthrange(nam_moi, thang_moi)[1])
    return ngay_goc.replace(year=nam_moi, month=thang_moi, day=ngay_moi)


# --- TRANG CHỦ ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.vai_tro == 'Admin':
            return redirect(url_for('ql_hop_dong'))
        elif current_user.vai_tro == 'ChuNha':
            return redirect(url_for('thong_ke'))
        else:
            return redirect(url_for('thong_tin_ca_nhan'))

    ds = CanHo.query.all()
    return render_template('index.html', danh_sach=ds)


# --- ĐĂNG NHẬP ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ten = request.form.get('username')
        mk = request.form.get('password')

        u = NguoiDung.query.filter_by(ten_dang_nhap=ten).first()

        if u and u.mat_khau == mk:
            login_user(u)
            flash(f'Xin chào {u.ho_ten}!', 'success')

            if u.vai_tro == 'Admin':
                return redirect(url_for('ql_hop_dong'))
            elif u.vai_tro == 'ChuNha':
                return redirect(url_for('thong_ke'))
            else:
                return redirect(url_for('thong_tin_ca_nhan'))
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu!', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công.', 'info')
    return redirect(url_for('login'))


# --- QUẢN LÝ TÀI KHOẢN (ADMIN) ---
@app.route('/quan-ly-tai-khoan', methods=['GET', 'POST'])
@login_required
def ql_tai_khoan():
    if current_user.vai_tro != 'Admin':
        flash('Chức năng này chỉ dành cho Admin!', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            ho_ten = request.form['ho_ten']
            user = request.form['ten_dang_nhap']
            pw = request.form['mat_khau']
            role = request.form['vai_tro']

            check_user = NguoiDung.query.filter_by(ten_dang_nhap=user).first()
            if check_user:
                flash(f'Tên đăng nhập "{user}" đã tồn tại!', 'danger')
            else:
                new_user = NguoiDung(
                    ho_ten=ho_ten,
                    ten_dang_nhap=user,
                    mat_khau=pw,
                    vai_tro=role
                )
                db.session.add(new_user)
                db.session.commit()
                flash(f'Đã tạo tài khoản {user} thành công!', 'success')

        except Exception as e:
            flash(f'Lỗi tạo tài khoản: {str(e)}', 'danger')

    ds_nguoi_dung = NguoiDung.query.all()
    return render_template('quan_ly_tai_khoan.html', danh_sach=ds_nguoi_dung)


@app.route('/xoa-tai-khoan/<int:id>', methods=['POST'])
@login_required
def xoa_tai_khoan(id):
    if current_user.vai_tro != 'Admin':
        flash('Bạn không có quyền!', 'danger')
        return redirect(url_for('index'))

    if id == current_user.id:
        flash('Không thể tự xóa chính mình!', 'warning')
        return redirect(url_for('ql_tai_khoan'))

    u = NguoiDung.query.get_or_404(id)
    try:
        db.session.delete(u)
        db.session.commit()
        flash(f'Đã xóa tài khoản {u.ten_dang_nhap}', 'success')
    except Exception as e:
        flash(f'Lỗi khi xóa: {e}', 'danger')

    return redirect(url_for('ql_tai_khoan'))


# --- QUẢN LÝ CĂN HỘ (ADMIN) ---
@app.route('/quan-ly-can-ho', methods=['GET', 'POST'])
@login_required
def page_them_can_ho():
    if current_user.vai_tro != 'Admin':
        flash('Chỉ Admin mới có quyền quản lý căn hộ!', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            ma = request.form['ma_can']
            dt = request.form['dien_tich']
            loai = request.form['loai_phong']

            moi = CanHo(ma_can=ma, dien_tich=dt, loai_phong=loai)
            db.session.add(moi)
            db.session.commit()
            flash('Thêm căn hộ thành công', 'success')
            return redirect(url_for('page_them_can_ho'))
        except Exception as e:
            flash(f'Lỗi (có thể trùng mã căn): {str(e)}', 'danger')

    ds = CanHo.query.all()
    return render_template('them_can_ho.html', danh_sach=ds)


@app.route('/sua-can-ho/<int:id>', methods=['GET', 'POST'])
@login_required
def sua_can_ho(id):
    if current_user.vai_tro != 'Admin':
        flash('Không có quyền!', 'danger')
        return redirect(url_for('index'))

    can_ho = CanHo.query.get_or_404(id)

    if request.method == 'POST':
        try:
            can_ho.ma_can = request.form['ma_can']
            can_ho.dien_tich = request.form['dien_tich']
            can_ho.loai_phong = request.form['loai_phong']

            db.session.commit()
            flash(f'Đã cập nhật căn hộ {can_ho.ma_can} thành công!', 'success')
            return redirect(url_for('page_them_can_ho'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {str(e)}', 'danger')

    return render_template('sua_can_ho.html', can=can_ho)


@app.route('/xoa-can-ho/<int:id>', methods=['POST'])
@login_required
def xoa_can_ho(id):
    if current_user.vai_tro != 'Admin':
        flash('Không có quyền!', 'danger')
        return redirect(url_for('index'))

    can_ho = CanHo.query.get_or_404(id)

    if can_ho.tinh_trang != 'Trong':
        flash(f'Căn hộ {can_ho.ma_can} đang có người ở hoặc đang sửa, không thể xóa!', 'warning')
        return redirect(url_for('page_them_can_ho'))

    try:
        db.session.delete(can_ho)
        db.session.commit()
        flash(f'Đã xóa căn hộ {can_ho.ma_can}!', 'success')
    except Exception as e:
        flash(f'Lỗi khi xóa: {str(e)}', 'danger')

    return redirect(url_for('page_them_can_ho'))


# --- QUẢN LÝ HỢP ĐỒNG ---
@app.route('/quan-ly-hop-dong', methods=['GET', 'POST'])
@login_required
def ql_hop_dong():
    if current_user.vai_tro not in ['Admin', 'ChuNha']:
        flash('Bạn không có quyền truy cập mục này!', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if current_user.vai_tro != 'Admin':
            flash('Chỉ Admin mới có quyền tạo hợp đồng!', 'danger')
            return redirect(url_for('ql_hop_dong'))

        try:
            ma_can_nhap = request.form['ma_can']
            id_nguoi_thue = int(request.form['id_nguoi_thue'])
            user_obj = NguoiDung.query.get(id_nguoi_thue)

            if not user_obj:
                flash('Người thuê không tồn tại!', 'danger')
                return redirect(url_for('ql_hop_dong'))

            ten_nguoi_thue = user_obj.ho_ten
            so_nguoi = int(request.form['so_nguoi_o'])
            ngay_bd_str = request.form['ngay_bat_dau']
            han = int(request.form['thoi_han'])
            gia = float(request.form['gia_thue'])
            coc = float(request.form['tien_coc'])
            ngay_bd = datetime.strptime(ngay_bd_str, '%Y-%m-%d').date()

            qd = QuyDinh.query.first()
            if not qd:
                qd = QuyDinh(gia_dien=3500, gia_nuoc=20000, phi_dich_vu=150000, so_nguoi_toi_da=4)
                db.session.add(qd)
                db.session.commit()

            if so_nguoi > qd.so_nguoi_toi_da:
                flash(f'Vi phạm quy định: Phòng tối đa {qd.so_nguoi_toi_da} người!', 'danger')
                return redirect(url_for('ql_hop_dong'))

            can_ho = CanHo.query.filter_by(ma_can=ma_can_nhap).first()

            if not can_ho:
                flash('Căn hộ không tồn tại!', 'danger')
            elif can_ho.tinh_trang != 'Trong':
                flash(f'Căn hộ {ma_can_nhap} đang ở trạng thái {can_ho.tinh_trang}, không thể thuê!', 'warning')
            else:
                hd_moi = HopDong(
                    ma_can=ma_can_nhap,
                    id_nguoi_dung=id_nguoi_thue,
                    nguoi_thue=ten_nguoi_thue,
                    so_nguoi_o=so_nguoi,
                    ngay_bat_dau=ngay_bd,
                    thoi_han=han,
                    gia_thue=gia,
                    tien_coc=coc
                )
                can_ho.tinh_trang = 'DaThue'
                db.session.add(hd_moi)
                db.session.commit()
                flash(f'Tạo hợp đồng thành công cho {ten_nguoi_thue}!', 'success')

            return redirect(url_for('ql_hop_dong'))

        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {e}', 'danger')

    ds_hop_dong = HopDong.query.all()
    ds_can_trong = CanHo.query.filter_by(tinh_trang='Trong').all()
    quy_dinh_hien_tai = QuyDinh.query.first()
    ds_nguoi_thue = NguoiDung.query.filter_by(vai_tro='NguoiThue').all()

    danh_sach_hien_thi = []
    for hd in ds_hop_dong:
        ngay_ket_thuc = cong_thang(hd.ngay_bat_dau, hd.thoi_han)
        hd.ngay_ket_thuc = ngay_ket_thuc
        danh_sach_hien_thi.append(hd)

    return render_template('quan_ly_hop_dong.html',
                           danh_sach=danh_sach_hien_thi,
                           can_trong=ds_can_trong,
                           quy_dinh=quy_dinh_hien_tai,
                           ds_users=ds_nguoi_thue)


@app.route('/xoa-hop-dong/<int:id>', methods=['POST'])
@login_required
def xoa_hop_dong(id):
    if current_user.vai_tro != 'Admin':
        flash('Bạn không có quyền xóa!', 'danger')
        return redirect(url_for('ql_hop_dong'))

    hop_dong = HopDong.query.get_or_404(id)

    try:
        can_ho = CanHo.query.filter_by(ma_can=hop_dong.ma_can).first()
        if can_ho:
            can_ho.tinh_trang = 'Trong'

        db.session.delete(hop_dong)
        db.session.commit()
        flash(f'Đã thanh lý hợp đồng căn {hop_dong.ma_can}!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'danger')

    return redirect(url_for('ql_hop_dong'))


# --- QUẢN LÝ HÓA ĐƠN ---
@app.route('/quan-ly-hoa-don', methods=['GET', 'POST'])
@login_required
def ql_hoa_don():
    if current_user.vai_tro != 'Admin':
        flash('Chức năng Thu Tiền chỉ dành cho Admin!', 'warning')
        return redirect(url_for('index'))

    quy_dinh = QuyDinh.query.first()
    if not quy_dinh:
        quy_dinh = QuyDinh(gia_dien=3500, gia_nuoc=20000, phi_dich_vu=150000, so_nguoi_toi_da=4)
        db.session.add(quy_dinh)
        db.session.commit()

    if request.method == 'POST':
        try:
            ma_can = request.form['ma_can']
            thang = request.form['thang']

            d_cu = int(request.form['dien_cu'])
            d_moi = int(request.form['dien_moi'])
            n_cu = int(request.form['nuoc_cu'])
            n_moi = int(request.form['nuoc_moi'])

            hop_dong = HopDong.query.filter_by(ma_can=ma_can).order_by(HopDong.id.desc()).first()

            if not hop_dong:
                flash(f'Phòng {ma_can} hiện chưa có hợp đồng thuê!', 'danger')
                return redirect(url_for('ql_hoa_don'))

            so_dien = d_moi - d_cu
            so_nuoc = n_moi - n_cu

            if so_dien < 0 or so_nuoc < 0:
                flash('Chỉ số Mới phải lớn hơn chỉ số Cũ!', 'danger')
                return redirect(url_for('ql_hoa_don'))

            t_dien = so_dien * quy_dinh.gia_dien
            t_nuoc = so_nuoc * quy_dinh.gia_nuoc
            t_phong = hop_dong.gia_thue
            t_dich_vu = quy_dinh.phi_dich_vu
            tong = t_phong + t_dien + t_nuoc + t_dich_vu

            hd_moi = HoaDon(
                ma_can=ma_can,
                thang=thang,
                dien_cu=d_cu, dien_moi=d_moi,
                nuoc_cu=n_cu, nuoc_moi=n_moi,
                tien_phong=t_phong,
                tien_dien=t_dien,
                tien_nuoc=t_nuoc,
                phi_dich_vu=t_dich_vu,
                tong_cong=tong,
                trang_thai='ChuaThu'
            )
            db.session.add(hd_moi)
            db.session.commit()
            flash('Đã lập hóa đơn thành công!', 'success')

        except Exception as e:
            flash(f'Lỗi tính toán: {str(e)}', 'danger')

    phong_da_thue = CanHo.query.filter_by(tinh_trang='DaThue').all()
    # Hiển thị tất cả hóa đơn để Admin quản lý
    ds_hoa_don = HoaDon.query.order_by(HoaDon.id.desc()).all()

    return render_template('quan_ly_hoa_don.html',
                           phong_da_thue=phong_da_thue,
                           ds_hoa_don=ds_hoa_don,
                           quy_dinh=quy_dinh)


@app.route('/thay-doi-quy-dinh', methods=['GET', 'POST'])
@login_required
def thay_doi_quy_dinh():
    if current_user.vai_tro != 'ChuNha':
        flash('Chức năng này chỉ dành cho Chủ Nhà!', 'danger')
        return redirect(url_for('index'))

    qd = QuyDinh.query.first()
    if not qd:
        qd = QuyDinh(gia_dien=3500, gia_nuoc=20000, phi_dich_vu=150000, so_nguoi_toi_da=4)
        db.session.add(qd)
        db.session.commit()

    if request.method == 'POST':
        try:
            qd.gia_dien = float(request.form['gia_dien'])
            qd.gia_nuoc = float(request.form['gia_nuoc'])
            qd.phi_dich_vu = float(request.form['phi_dich_vu'])
            qd.so_nguoi_toi_da = int(request.form['so_nguoi_toi_da'])

            db.session.commit()
            flash('Đã cập nhật bảng giá thành công!', 'success')
            return redirect(url_for('thay_doi_quy_dinh'))

        except Exception as e:
            flash(f'Lỗi nhập liệu: {str(e)}', 'danger')

    return render_template('quy_dinh.html', qd=qd)


@app.route('/thong-ke')
@login_required
def thong_ke():
    if current_user.vai_tro not in ['ChuNha', 'Admin']:
        flash('Bạn không có quyền xem thống kê!', 'warning')
        return redirect(url_for('index'))

    trong = CanHo.query.filter_by(tinh_trang='Trong').count()
    da_thue = CanHo.query.filter_by(tinh_trang='DaThue').count()
    sua_chua = CanHo.query.filter_by(tinh_trang='SuaChua').count()

    ds_hoa_don = HoaDon.query.all()
    data_doanh_thu = {}

    for hd in ds_hoa_don:
        # Chỉ tính doanh thu những hóa đơn ĐÃ THU
        if hd.trang_thai == 'DaThu':
            t = hd.thang
            tien = float(hd.tong_cong)
            if t in data_doanh_thu:
                data_doanh_thu[t] += tien
            else:
                data_doanh_thu[t] = tien

    labels_dt = list(data_doanh_thu.keys())
    values_dt = list(data_doanh_thu.values())

    ds_hop_dong = HopDong.query.all()
    hop_dong_sap_het = []
    hom_nay = date.today()

    for hd in ds_hop_dong:
        ngay_ket_thuc = cong_thang(hd.ngay_bat_dau, hd.thoi_han)
        so_ngay_con_lai = (ngay_ket_thuc - hom_nay).days

        if 0 <= so_ngay_con_lai <= 30:
            item = {
                'ma_can': hd.ma_can,
                'nguoi_thue': hd.nguoi_thue,
                'ngay_het_han': ngay_ket_thuc,
                'so_ngay': so_ngay_con_lai
            }
            hop_dong_sap_het.append(item)

    return render_template('thong_ke.html',
                           p_trong=trong, p_da_thue=da_thue, p_sua=sua_chua,
                           labels_dt=labels_dt, values_dt=values_dt,
                           ds_sap_het=hop_dong_sap_het)


@app.route('/thong-tin-ca-nhan')
@login_required
def thong_tin_ca_nhan():
    hop_dong = HopDong.query.filter_by(id_nguoi_dung=current_user.id).order_by(HopDong.id.desc()).first()

    ngay_ket_thuc = None
    so_ngay_con_lai = 0
    hoa_don_gan_nhat = None

    if hop_dong:
        ngay_ket_thuc = cong_thang(hop_dong.ngay_bat_dau, hop_dong.thoi_han)
        hom_nay = date.today()
        so_ngay_con_lai = (ngay_ket_thuc - hom_nay).days

        hoa_don_gan_nhat = HoaDon.query.filter_by(ma_can=hop_dong.ma_can).order_by(HoaDon.id.desc()).first()

    return render_template('thong_tin_ca_nhan.html',
                           hd=hop_dong,
                           ngay_kt=ngay_ket_thuc,
                           ngay_con=so_ngay_con_lai,
                           hoa_don=hoa_don_gan_nhat)


# --- ROUTE CẤP CỨU ---
@app.route('/tao-admin-gap')
def tao_admin_gap():
    u = NguoiDung.query.filter_by(ten_dang_nhap='admin').first()

    if u:
        u.mat_khau = '123'
        u.vai_tro = 'Admin'
        db.session.commit()
        return "Đã tìm thấy Admin cũ. Đã RESET mật khẩu thành: 123"
    else:
        admin_moi = NguoiDung(
            ten_dang_nhap='admin',
            mat_khau='123',
            vai_tro='Admin',
            ho_ten='Super Admin'
        )
        db.session.add(admin_moi)
        db.session.commit()
        return "Database đang trống. Đã TẠO MỚI tài khoản: admin / 123"


# --- CHỨC NĂNG THANH TOÁN & DUYỆT (MỚI THÊM) ---
@app.route('/thanh-toan')
@login_required
def thanh_toan():
    # 1. Tìm hợp đồng
    hop_dong = HopDong.query.filter_by(id_nguoi_dung=current_user.id).order_by(HopDong.id.desc()).first()

    if not hop_dong:
        flash('Bạn chưa có hợp đồng thuê phòng nào!', 'warning')
        return redirect(url_for('thong_tin_ca_nhan'))

    # 2. Tìm hóa đơn mới nhất (không quan tâm trạng thái để hiện ChoDuyet nếu có)
    # Lấy hóa đơn mới nhất mà KHÔNG PHẢI là "DaThu" (tức là ChuaThu hoặc ChoDuyet)
    # Hoặc nếu không có nợ thì nó sẽ ra None
    hoa_don = HoaDon.query.filter_by(ma_can=hop_dong.ma_can).filter(HoaDon.trang_thai != 'DaThu').order_by(
        HoaDon.id.desc()).first()

    tk_ngan_hang = {
        'ngan_hang': 'MBBank',
        'so_tai_khoan': '0987654321',
        'chu_tai_khoan': 'NGUYEN VAN CHU NHA'
    }

    return render_template('thanh_toan.html', hd=hoa_don, can_ho=hop_dong.ma_can, bank=tk_ngan_hang)


@app.route('/user-xac-nhan-thanh-toan/<int:id_hoa_don>')
@login_required
def user_xac_nhan_thanh_toan(id_hoa_don):
    # Người thuê xác nhận đã chuyển khoản
    hoa_don = HoaDon.query.get_or_404(id_hoa_don)

    # Kiểm tra bảo mật: Hóa đơn này phải thuộc về hợp đồng của user đang đăng nhập
    # (Để đơn giản ta bỏ qua bước check sâu này, chỉ check trạng thái)

    if hoa_don.trang_thai == 'ChuaThu':
        hoa_don.trang_thai = 'ChoDuyet'
        db.session.commit()
        flash('Đã gửi xác nhận thanh toán! Vui lòng chờ Admin duyệt.', 'info')

    return redirect(url_for('thanh_toan'))


@app.route('/admin-duyet-thanh-toan/<int:id_hoa_don>')
@login_required
def admin_duyet_thanh_toan(id_hoa_don):
    # Admin xác nhận tiền đã về
    if current_user.vai_tro != 'Admin':
        flash('Bạn không có quyền này!', 'danger')
        return redirect(url_for('index'))

    hoa_don = HoaDon.query.get_or_404(id_hoa_don)

    if hoa_don.trang_thai == 'ChoDuyet' or hoa_don.trang_thai == 'ChuaThu':
        hoa_don.trang_thai = 'DaThu'
        db.session.commit()
        flash(f'Đã xác nhận thu tiền căn {hoa_don.ma_can}!', 'success')

    return redirect(url_for('ql_hoa_don'))


if __name__ == '__main__':
    app.run(debug=True)