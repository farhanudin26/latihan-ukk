from datetime import date, datetime
from io import BytesIO
import io
import os
from flask_bcrypt import Bcrypt  # Mengimpor bcrypt dari flask_bcrypt
from flask import Blueprint, current_app, flash, jsonify, make_response, redirect, render_template, request, send_file, session, url_for
from flask_login import current_user, login_required
import pandas as pd
from models.models import User, Product, Customer, Sale, DetailSale  # Model yang digunakan
from models import db
from sqlalchemy import func
from werkzeug.utils import secure_filename
from xhtml2pdf import pisa

# Inisialisasi Bcrypt
bcrypt = Bcrypt()

api_bp = Blueprint("api_bp", __name__)


@api_bp.route("/api/sales_per_day")
def get_sales_per_day():
    sales_per_day = db.session.query(
        func.date(Sale.created_at).label('sale_day'),
        func.sum(Sale.total_price).label('total_sales')
    ).group_by(func.date(Sale.created_at)).all()

    result = [{'sale_day': str(sale[0]), 'total_sales': sale[1]} for sale in sales_per_day]

    return jsonify(result)

#################### user ######################

@api_bp.route('/users')
def users():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))  # Pastikan rujukan ke login sesuai

    users = User.query.all()
    return render_template('user/users.html', users=users)

# Create a new user
@api_bp.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))  # Pastikan user login terlebih dahulu

    if request.method == 'POST':
        name = request.form['name'].strip()
        password = request.form['password']
        role = request.form['role']

        # Validasi input user
        if not name or not password or not role:
            flash("Semua field harus diisi!", "warning")
            return redirect(url_for('api_bp.add_user'))

        # Cek apakah nama sudah digunakan
        existing_user = User.query.filter_by(name=name).first()
        if existing_user:
            flash("Nama user sudah digunakan. Silakan pilih nama lain.", "danger")
            return redirect(url_for('api_bp.add_user'))

        # Simpan user baru
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Menggunakan bcrypt instance
        new_user = User(name=name, password=hashed_password, role=role)

        db.session.add(new_user)
        db.session.commit()

        flash("User berhasil ditambahkan!", "success")
        return redirect(url_for('api_bp.users'))

    return render_template('user/add_user.html')


# Edit a user
@api_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    user = User.query.get_or_404(id)

    # Hitung total admin
    admin_count = User.query.filter_by(role='admin').count()

    # Cek apakah role harus dikunci (hanya 1 admin & sedang edit admin itu)
    disable_role_edit = (user.role == 'admin' and admin_count == 1)

    if request.method == 'POST':
        name = request.form['name'].strip()

        # Validasi: Pastikan nama tidak kosong dan tidak ada yang menggunakan nama yang sama
        if not name:
            flash("Nama tidak boleh kosong.", "warning")
            return redirect(url_for('api_bp.edit_user', id=id))
        
        # Cek apakah nama sudah digunakan oleh user lain
        existing_user = User.query.filter(User.name == name, User.id != user.id).first()
        if existing_user:
            flash("Nama user sudah digunakan oleh user lain!", "danger")
            return redirect(url_for('api_bp.edit_user', id=id))

        # Update nama
        user.name = name

        # Update password jika diisi
        password = request.form['password']
        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Role hanya diubah jika tidak dikunci
        if not disable_role_edit:
            user.role = request.form['role']

        db.session.commit()
        flash("User berhasil diperbarui!", "success")
        return redirect(url_for('api_bp.users'))

    return render_template('user/edit_user.html', user=user, disable_role_edit=disable_role_edit)

# Delete a user
@api_bp.route('/users/delete/<int:id>')
def delete_user(id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    user = User.query.get_or_404(id)

    # Jika user yang akan dihapus adalah admin
    if user.role == 'admin':
        total_admin = User.query.filter_by(role='admin').count()
        if total_admin <= 1:
            flash('Tidak dapat menghapus user admin terakhir!', 'danger')
            return redirect(url_for('api_bp.users'))

    db.session.delete(user)
    db.session.commit()
    flash('User berhasil dihapus.', 'success')
    return redirect(url_for('api_bp.users'))


################################# product ######################

# Fungsi untuk memeriksa ekstensi file gambar
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@api_bp.route('/products')
def products():
    products = Product.query.all()
    return render_template('product/products.html', products=products)

@api_bp.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        stock = request.form['stock']

        image = request.files.get('image')  # Mendapatkan file gambar
        image_filename = None

        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)  # Menyimpan file gambar ke folder yang ditentukan

        new_product = Product(name=name, price=price, stock=stock, image=image_filename)
        db.session.add(new_product)
        db.session.commit()

        flash("Produk berhasil ditambahkan!", "success")
        return redirect(url_for('api_bp.products'))

    return render_template('product/add_product.html')

@api_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']
        product.stock = request.form['stock']

        image = request.files.get('image')  # Mendapatkan file gambar
        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)  # Menyimpan file gambar baru
            product.image = image_filename  # Mengupdate nama gambar di database

        db.session.commit()

        flash("Produk berhasil diperbarui!", "success")
        return redirect(url_for('api_bp.products'))

    return render_template('product/edit_product.html', product=product)

@api_bp.route('/product/<int:id>/update-stock', methods=['GET', 'POST'])
def update_product_stock(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        try:
            new_stock = int(request.form['stock'])
            product.stock = new_stock
            db.session.commit()
            flash('Stok berhasil diperbarui!', 'success')
            return redirect(url_for('api_bp.products'))
        except ValueError:
            flash('Input stok tidak valid.', 'danger')

    return render_template('product/update_stock_product.html',product=product)


@api_bp.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash("Produk berhasil dihapus!", "success")
    except Exception as e:
        db.session.rollback()  # Untuk membatalkan perubahan jika terjadi kesalahan
        flash("Terjadi kesalahan saat menghapus produk.", "danger")
    
    return redirect(url_for('api_bp.products'))

################# sale ####################

# Tampilkan daftar penjualan
@api_bp.route('/sales', endpoint='sales')
@login_required
def sales():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('sales/sales.html', sales=sales)

@api_bp.route('/api/sale', methods=['POST'])
def create_sale():
    customer_phone = request.form['no_hp']
    points_used = int(request.form['points_used'])

    # Dapatkan data pelanggan berdasarkan nomor HP
    customer = Customer.query.filter_by(phone=customer_phone).first()

    if customer:
        if customer.points < points_used:
            return jsonify({'success': False, 'message': 'Poin tidak cukup'}), 400

        # Kurangi poin pelanggan
        customer.points -= points_used
        db.session.commit()

        # Simpan data penjualan
        sale = Sale(
            customer_id=customer.id,
            total_price=request.form['total_pay'],
            points_used=points_used
        )
        db.session.add(sale)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Penjualan berhasil'}), 200

    return jsonify({'success': False, 'message': 'Pelanggan tidak ditemukan'}), 404

@api_bp.route('/sales/add', methods=['GET', 'POST'], endpoint='add_sale')
@login_required
def add_sale():
    if request.method == 'POST':
        sale_date = request.form.get('sale_date')
        selected_products = request.form.getlist('products[]')
        quantities = [request.form.get(f'quantities_{product_id}') for product_id in selected_products]
        
        total_price = 0
        valid_products = []

        for product_id, qty in zip(selected_products, quantities):
            try:
                qty_int = int(qty)
            except (ValueError, TypeError):
                qty_int = 0

            product = Product.query.get(int(product_id))
            if product and qty_int > 0 and product.stock >= qty_int:
                total_price += product.price * qty_int
                valid_products.append((product_id, qty))

        if valid_products:
            session['sale_data'] = {
                'sale_date': sale_date,
                'products': [p for p, _ in valid_products],
                'quantities': [q for _, q in valid_products],
                'total_price': total_price
            }
            return redirect(url_for('api_bp.confirm_sale'))

    products = Product.query.all()
    today = date.today().isoformat()
    return render_template('sales/add_sale.html', products=products, today=today)

@api_bp.route('/sales/confirm', methods=['GET', 'POST'], endpoint='confirm_sale')
@login_required
def confirm_sale():
    sale_data = session.get('sale_data')
    if not sale_data:
        return redirect(url_for('api_bp.add_sale'))

    products = []
    for pid, qty in zip(sale_data['products'], sale_data['quantities']):
        product = Product.query.get(int(pid))
        if product:
            products.append({
                'product': product,
                'quantity': int(qty),
                'subtotal': product.price * int(qty)
            })

    if request.method == 'POST':
        customer_status = request.form.get("customer_status")
        customer_name = request.form.get("customer_name")
        no_hp = request.form.get("no_hp")
        customer_point = int(request.form.get("customer_point") or 0)
        use_point = request.form.get("use_point")
        total_pay = int(request.form.get("total_pay") or 0)
        total_return = int(request.form.get("total_return") or 0)

        is_member = customer_status == "member"
        customer = None

        if is_member:
            customer = Customer.query.filter_by(no_hp=no_hp).first()
            if not customer:
                customer = Customer(name=customer_name, no_hp=no_hp, point=customer_point)
                db.session.add(customer)
                db.session.commit()
            else:
                customer.point += customer_point
                db.session.commit()

        final_point = 0
        if is_member and use_point and customer and customer.point > 0:
            final_point = min(customer.point, customer_point)
            
            # Pastikan semua poin terpakai dan diset ke 0
            customer.point = 0
            db.session.commit()


        sale = Sale(
            sale_date=datetime.strptime(sale_data['sale_date'], '%Y-%m-%d'),
            total_price=sale_data['total_price'],
            total_pay=total_pay,
            total_return=total_return,
            user_id=current_user.id,
            customer_id=customer.id if customer else None,
            point=final_point,
            total_point=final_point
        )
        db.session.add(sale)
        db.session.commit()

        for pid, qty in zip(sale_data['products'], sale_data['quantities']):
            product = Product.query.get(int(pid))
            qty = int(qty)
            subtotal = product.price * qty

            detail = DetailSale(
                sale_id=sale.id,
                product_id=product.id,
                amount=qty,
                subtotal=subtotal
            )
            db.session.add(detail)
            product.stock -= qty
        db.session.commit()

        session.pop('sale_data', None)
        flash("Penjualan berhasil disimpan.", "success")
        return redirect(url_for('api_bp.sales_invoice', sale_id=sale.id))

    return render_template('sales/confirm_sale.html', products=products, total_price=sale_data['total_price'])

@api_bp.route('/customer/points/<string:phone>', methods=['GET'])
def get_customer_points(phone):
    customer = Customer.query.filter_by(no_hp=phone).first()
    if customer:
        return jsonify({
            'success': True,
            'points': customer.point
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Customer not found'
        }), 404
        
@api_bp.route('/sales/invoice/<int:sale_id>', methods=['GET'], endpoint='sales_invoice')
@login_required
def sales_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    customer = Customer.query.get(sale.customer_id) if sale.customer_id else None
    cashier = User.query.get(sale.user_id)
    details = DetailSale.query.filter_by(sale_id=sale_id).all()

    return render_template('sales/sales_invoice.html', sale=sale, customer=customer, cashier=cashier, details=details,)

@api_bp.route('/sales/complete', methods=['POST'])
def complete_sale():
    # Ambil data dari form
    customer_phone = request.form['no_hp']
    total_pay = float(request.form['total_pay'])
    points_used = int(request.form['point_used'])

    # Cari customer berdasarkan no_hp
    customer = Customer.query.filter_by(no_hp=customer_phone).first()
    
    if customer:
        # Verifikasi bahwa poin yang digunakan tidak melebihi poin yang dimiliki
        if points_used > customer.point:
            return jsonify({'success': False, 'message': 'Poin yang digunakan melebihi poin yang dimiliki'}), 400
        
        # Update jumlah poin customer setelah transaksi
        customer.point -= points_used
        db.session.commit()

        # Simpan penjualan ke database
        sale = Sale(
            customer_id=customer.id,
            total_price=total_pay,
            points_used=points_used
        )
        db.session.add(sale)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Penjualan berhasil disimpan'})
    else:
        return jsonify({'success': False, 'message': 'Customer tidak ditemukan'}), 404
    
    
@api_bp.route('/sales/export_excel')
def export_sales_excel():
    sales = Sale.query.all()
    data = []
    for sale in sales:
        data.append({
            "Nama Pelanggan": sale.customer.name if sale.customer else "Customer",
            "Tanggal Penjualan": sale.sale_date.strftime('%Y-%m-%d'),
            "Total Harga": sale.total_price,
            "Total Bayar": sale.total_pay,
            "Kasir": sale.user.name if sale.user else ""
        })

    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data Penjualan')
    output.seek(0)

    return send_file(output, download_name="data_penjualan.xlsx", as_attachment=True)

@api_bp.route('/sales/invoice/pdf/<int:sale_id>')
def sales_invoice_pdf(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    customer = Customer.query.get(sale.customer_id) if sale.customer_id else None
    cashier = User.query.get(sale.user_id)
    details = DetailSale.query.filter_by(sale_id=sale_id).all()

    rendered = render_template('sales/sales_invoice_pdf.html', sale=sale, customer=customer, cashier=cashier, details=details)

    pdf_buffer = BytesIO()

    pisa_status = pisa.CreatePDF(rendered, dest=pdf_buffer)

    if pisa_status.err:
        return "Terjadi kesalahan saat membuat PDF", 500

    pdf_buffer.seek(0)

    # Buat response dengan PDF
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="invoice_{sale.id}.pdf"'

    return response

@api_bp.route('/sales/export_all_pdf')
def export_all_sales_pdf():
    sales = Sale.query.all()
    html = render_template('sales/sales_pdf.html', sales=sales)
    pdf_file = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=pdf_file)
    pdf_file.seek(0)
    return send_file(pdf_file, download_name="semua_penjualan.pdf", as_attachment=True)
