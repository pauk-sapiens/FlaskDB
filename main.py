from flask import Flask, render_template, redirect, url_for, request, session
import config
import pyodbc
import string
import service

app = Flask(__name__)
app.secret_key = b'_5#2L"F4Q8z\n\xec]/'


def validate_string(s):
    if not s:
        return False
    if len(s) > 50:
        return False
    for c in s:
        if c not in string.ascii_letters and c not in service.Glagolitsa and c not in "0123456789 '-!":
            return False
    return True


def validate_num(num):
    if not num:
        return False
    if len(num) > 10:
        return False
    flag = False
    for c in '123456789':
        if num.startswith(c):
            flag = True
    if not flag:
        return flag
    k = 0
    for c in num:
        if c not in string.digits and c != '.':
            return False
        if c == '.':
            k += 1
    if k > 1:
        return False
    return True

def validate_id(id):
    if not id:
        return False
    for c in id:
        if c not in string.digits:
            return False
    return True

def validate_date(date):
    if not date:
        return False
    date = date.split('-')
    if len(date) != 3:
        return False
    if len(date[0]) != 4:
        return False
    if len(date[1]) != 2:
        return False
    if len(date[2]) != 2:
        return False
    for c in date[0]:
        if c not in string.digits:
            return False
    for c in date[1]:
        if c not in string.digits:
            return False
    for c in date[2]:
        if c not in string.digits:
            return False
    if int(date[1]) > 12:
        return False
    if int(date[2]) > 31:
        return False
    if int(date[1]) == 2 and int(date[2]) > 29:
        return False
    return True

def validate_contact(contact):
    contact = contact.split('-')
    if len(contact) != 3:
        return False
    if len(contact[0]) != 2 or len(contact[1]) != 2 or len(contact[2]) != 2:
        return False
    for num in contact:
        for c in num:
            if c not in string.digits:
                return False
    return True
def connection():
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};' + f'SERVER={config.host};DATABASE={config.db_name};Trusted_Connection=yes'
    conn = pyodbc.connect(cstr)
    return conn


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin' or request.form['username'] == 'user' and request.form['password'] == 'user':
            session['username'] = request.form['username']
            return redirect(url_for('tables'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/tables', methods=['GET'])
def tables():
    if session.get('username') == 'admin':
        return render_template('tables_admin.html')
    elif session.get('username') == 'user':
        return render_template('tables_admin.html')
    else:
        return 'вы не авторизованы'


@app.route('/dishes', methods=['GET'])
def dishes():
    dishes = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from dishes')
    for row in cursor.fetchall():
        dishes.append({'id':row[0], 'name':row[1], 'price':row[2],'type':row[3]})
    conn.close()
    if session.get('username') == 'user':
        return render_template('dishes_user.html', dishes=dishes)
    if session.get('username') == 'admin':
        return render_template('dishes_admin.html', dishes=dishes)
    return 'вы не авторизованы'


@app.route('/add_dish', methods=['GET', 'POST'])
def add_dish():
    if session.get('username') == 'admin':
        err = None
        if request.method == 'GET':
            return render_template('add_dish.html', error=err)
        if request.method == 'POST':
            name = request.form["name"]
            price = request.form["price"]
            type = request.form["type"]
            ids = set()
            names = set()
            conn = connection()
            cursor = conn.cursor()
            cursor.execute('select * from dishes')
            for row in cursor.fetchall():
                ids.add((row[0]))
                names.add(row[1])
            if name not in names and validate_string(name) and validate_string(type) and validate_num(price):
                price = float(price)
                cursor.execute("INSERT INTO dishes VALUES (?, ?, ?, ?)", max(ids)+1, name, price, type)
                conn.commit()
                conn.close()
                return redirect(url_for('dishes'))
            elif name in names:
                err = 'Dish Already Exists'
                conn.close()
                return render_template('add_dish.html', error=err)
            else:
                err = 'Invalid Values: '
                if not validate_num(price):
                    err += ' price'
                if not validate_string(type):
                    err += ' type'
                if not validate_string(name):
                    err += ' name'
            return render_template('add_dish.html', error=err)
    return 'вы не авторизованы'


@app.route('/update_dish', methods=['GET', 'POST'])
def update_dish():
    if session.get('username') == 'admin':
        err = None
        names = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from dishes')
        for row in cursor.fetchall():
            names.add(row[1])
        if request.method == 'GET':
            return render_template('update_dish.html', error=err, dishs=names)
        if request.method == 'POST':
            name = request.form["name"]
            price = request.form["price"]
            type = request.form["type"]
            if name in names and validate_string(name) and validate_string(type) and validate_num(price):
                price = float(price)
                cursor.execute(f"update dishes set cost_price = {price}, type_dish = '{type}' where name ='{name}'")
                conn.commit()
                conn.close()
                return redirect(url_for('dishes'))
            elif name not in names:
                err = "Dish Does Not Exist"
                conn.close()
                return render_template('update_dish.html', error=err, dishs=names)
            else:
                err = 'Invalid Values: '
                if not validate_num(price):
                    err += ' price'
                if not validate_string(type):
                    err += ' type'
                if not validate_string(name):
                    err += ' name'
            return render_template('update_dish.html', error=err, dishs=names)
    return 'вы не авторизованы'


@app.route('/delete_dish', methods=['GET', 'POST'])
def delete_dish():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from dishes')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        if request.method == 'GET':
            return render_template('delete_dish.html', error=err, dishs=ids)
        if request.method == 'POST':
            name = request.form["name"]
            if name in ids and validate_string(name):
                cursor.execute("select dish_id FROM dishes WHERE name = ?", name)
                dish_id = int(cursor.fetchone()[0])
                cursor.execute("DELETE FROM employee_dishes WHERE dish_id = ?", dish_id)
                cursor.execute("DELETE FROM dishes WHERE name = ?", name)
                conn.commit()
                conn.close()
                return redirect(url_for('dishes'))
            else:
                err = 'No Such Dish'
                conn.commit()
                conn.close()
            return render_template('delete_dish.html', error=err, dishs=ids)
    return 'вы не авторизованы'


@app.route('/orders', methods=['GET'])
def orders():
    orders = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from orders')
    for row in cursor.fetchall():
        orders.append({'id':row[5], 'date':row[1], 'status':row[2],'total_amount':row[3], 'payment_type': row[4]})
    conn.close()
    if session.get('username') == 'admin':
        return render_template('orders_admin.html', orders=orders)
    if session.get('username') =='user':
        return render_template('orders_user.html', orders=orders)
    return 'вы не авторизованы'


@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    if session.get('username') == 'admin':
        err = None
        if request.method == 'GET':
            return render_template('add_order.html', error=err)
        if request.method == 'POST':
            id = request.form['id']
            date = request.form["date"]
            status = request.form["status"]
            payment = request.form['payment']
            ids = set()
            m = set()
            conn = connection()
            cursor = conn.cursor()
            cursor.execute('select * from orders')
            for row in cursor.fetchall():
                ids.add(str(row[5]))
                m.add(row[0])
            if validate_id(id) and id not in ids and validate_string(status) and validate_string(payment) and validate_date(date):
                id = int(id)
                cursor.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",max(m)+1 , date, status,0, payment, id)
                conn.commit()
                conn.close()
                return redirect(url_for('orders'))
            elif id in ids:
                err = 'Order already exists'
                conn.close()
                return render_template('add_order.html', error=err)
            else:
                err = 'Invalid Values: '
                if not validate_id(id):
                    err += 'id '
                if not validate_date(date):
                    err += 'date '
                if not validate_string(status):
                    err += 'status '
                if not validate_string(payment):
                    err += 'payment'
            return render_template('add_order.html', error=err)
    return 'вы не авторизованы'


@app.route('/delete_order', methods=['GET', 'POST'])
def delete_order():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from orders')
        for row in cursor.fetchall():
            ids.add(str(row[5]))
        if request.method == 'GET':
            return render_template('delete_order.html', error=err, orders=ids)
        if request.method == 'POST':
            id = request.form["id"]

            if id in ids and validate_id(id):
                id = int(id)
                cursor.execute("DELETE FROM orders WHERE order_number = ?", id)
                conn.commit()
                conn.close()
                return redirect(url_for('orders'))
            else:
                err = 'No Such Order'
                conn.commit()
                conn.close()
            return render_template('delete_order.html', error=err, orders=ids)
    return 'вы не авторизованы'


@app.route('/update_order', methods=['GET', 'POST'])
def update_order():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from orders')
        for row in cursor.fetchall():
            ids.add(str(row[5]))
        if request.method == 'GET':
            return render_template('update_order.html', error=err, orders=ids)
        if request.method == 'POST':
            id = request.form['id']
            date = request.form["date"]
            status = request.form["status"]
            price = '10'
            payment = request.form['payment']
            if id in ids and validate_string(status) and validate_string(payment) and validate_num(price) and validate_id(id) and validate_date(date):
                price = float(price)
                id = int(id)
                cursor.execute(f"update orders set payment_type = '{payment}', date = '{date}', status = '{status}' where order_number = '{id}'")
                conn.commit()
                conn.close()
                return redirect(url_for('orders'))
            elif id not in ids:
                err = 'Order does not exist'
                conn.close()
                return render_template('update_order.html', error=err, orders=ids)
            else:
                err = 'Invalid Values: '
                if not validate_id(id):
                    err += 'id '
                if not validate_date(date):
                    err += 'date '
                if not validate_string(status):
                    err += 'status '
                if not validate_num(price):
                    err += 'price '
                if not validate_string(payment):
                    err += 'payment'
            return render_template('update_order.html', error=err, orders=ids)
    return 'вы не авторизованы'


@app.route('/employee', methods=['GET'])
def employee():
    employee = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from employee')
    for row in cursor.fetchall():
        employee.append({'name':row[1], 'age':row[2],'order_id':row[3], 'role': row[4], 'type_employee_id': row[5]})
    for i in range(len(employee)):
        cursor.execute('select order_number from orders where order_id = ?', employee[i]['order_id'])
        employee[i]['order_id'] = cursor.fetchone()[0]
        cursor.execute('select type_name from type_employee where type_employee_id = ?', employee[i]['type_employee_id'])
        employee[i]['type_employee_id'] = cursor.fetchone()[0]
    conn.close()
    if session.get('username') == 'admin':
        return render_template('employee_admin.html', employee=employee)
    if session.get('username') =='user':
        return render_template('employee_user.html', employee=employee)
    return 'вы не авторизованы'


@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        order_ids = set()
        type_ids = set()
        m = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from employee')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
            m.add(row[0])
        cursor.execute('select * from orders')
        for row in cursor.fetchall():
            order_ids.add(str(row[5]))
        cursor.execute('select * from type_employee')
        for row in cursor.fetchall():
            type_ids.add(str(row[1]))
        if request.method == 'GET':
            return render_template('add_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
        if request.method == 'POST':
            name = request.form["name"]
            age = request.form["age"]
            order_id = request.form["order_id"]
            role = 'челик'
            type_id = request.form['type_id']
            if validate_string(name) and name not in ids and type_id in type_ids and order_id in order_ids and validate_string(role) and validate_num(age) and validate_id(order_id) and validate_string(type_id):
                age = int(age)
                cursor.execute('select order_id from orders where order_number = ?', order_id)
                order_ins = cursor.fetchone()[0]
                order_ins = int(order_ins)
                cursor.execute('select type_employee_id from type_employee where type_name = ?', type_id)
                type_ins = cursor.fetchone()[0]
                type_ins = int(type_ins)
                cursor.execute("INSERT INTO View_Employee_flask VALUES (?, ?, ?, ?, ?, ?)", max(m)+1, name, age, order_ins, role, type_ins)
                conn.commit()
                conn.close()
                return redirect(url_for('employee'))
            elif name in ids:
                err = 'Employee already exists'
                conn.close()
                return render_template('add_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
            elif order_id not in order_ids:
                err = 'Order № does not exist'
                conn.close()
                return render_template('add_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
            elif type_id not in type_ids:
                err = 'Employee Type does not exist'
                conn.close()
                return render_template('add_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
            else:
                err = 'Invalid Values: '
                if not validate_string(name):
                    err += 'name '
                if not validate_string(role):
                    err += 'role '
                if not validate_num(age):
                    err += 'age '
                if not validate_id(order_id):
                    err += 'order № '
                if not validate_string(type_id):
                    err += 'employee type'
            return render_template('add_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
    return 'вы не авторизованы'


@app.route('/update_employee', methods=['GET', 'POST'])
def update_employee():
    if session.get('username') == 'admin':
        err = None
        ids = []
        order_ids = []
        type_ids = set()
        m = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from employee')
        for row in cursor.fetchall():
            ids.append(str(row[1]))
            m.add(row[0])
        cursor.execute('select * from orders')
        for row in cursor.fetchall():
            order_ids.append(str(row[5]))
        cursor.execute('select * from type_employee')
        for row in cursor.fetchall():
            type_ids.add(str(row[1]))
        if request.method == 'GET':
            return render_template('update_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
        if request.method == 'POST':
            name = request.form["name"]
            age = request.form["age"]
            order_id = request.form["order_id"]
            role = 'челик'
            type_id = request.form['type_id']
            if validate_string(name) and name in ids and type_id in type_ids and order_id in order_ids and validate_string(role) and validate_num(age) and validate_id(order_id) and validate_string(type_id):
                age = int(age)
                cursor.execute('select order_id from orders where order_number = ?', order_id)
                order_ins = cursor.fetchone()[0]
                order_ins = int(order_ins)
                cursor.execute('select type_employee_id from type_employee where type_name = ?', type_id)
                type_ins = cursor.fetchone()[0]
                type_ins = int(type_ins)
                cursor.execute(f"update View_Employee_flask set age = {age}, job_role = '{role}', order_id = {order_ins}, type_employee_id = {type_ins} where name = '{name}'")
                conn.commit()
                conn.close()
                return redirect(url_for('employee'))
            elif name not in ids:
                err = 'Employee does not exist'
                conn.close()
                return render_template('update_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
            elif order_id not in order_ids:
                err = 'Order № does not exist'
                conn.close()
                return render_template('update_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
            elif type_id not in type_ids:
                err = 'Employee Type does not exist'
                conn.close()
                return render_template('update_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
            else:
                err = 'Invalid Values: '
                if not validate_string(name):
                    err += 'name '
                if not validate_string(role):
                    err += 'role '
                if not validate_num(age):
                    err += 'age '
                if not validate_id(order_id):
                    err += 'order id'
                if not validate_string(type_id):
                    err += 'employee type'
            return render_template('update_employee.html', error=err, orders=order_ids, employees=ids, tis=type_ids)
    return 'вы не авторизованы'


@app.route('/delete_employee', methods=['GET', 'POST'])
def delete_employee():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from employee')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        if request.method == 'GET':
            return render_template('delete_employee.html', error=err, employees=ids)
        if request.method == 'POST':
            id = request.form["id"]
            if id in ids and validate_string(id):
                cursor.execute("select employee_id FROM View_Employee_flask WHERE name = ?", id)
                emid = cursor.fetchone()[0]
                cursor.execute("DELETE FROM View_Employee_Dishes_flask  WHERE employee_id = ?", emid)
                cursor.execute("DELETE FROM View_Employee_flask WHERE name = ?", id)
                conn.commit()
                conn.close()
                return redirect(url_for('employee'))
            else:
                err = 'No Such Employee'
                conn.commit()
                conn.close()
            return render_template('delete_employee.html', error=err, employees=ids)
    return 'вы не авторизованы'


@app.route('/products', methods=['GET'])
def products():
    products = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from products')
    for row in cursor.fetchall():
        products.append({'name':row[1], 'category':row[2],'price':row[3], 'supplier_id': row[4], 'storage_id': row[5]})
    for i in range(len(products)):
        cursor.execute('select storage_number from storage where storage_id = ?', products[i]['storage_id'])
        products[i]['storage_id'] = cursor.fetchone()[0]
        cursor.execute('select name from suppliers where supplier_id = ?',
                       products[i]['supplier_id'])
        products[i]['supplier_id'] = cursor.fetchone()[0]
    conn.close()
    if session.get('username') == 'admin':
        return render_template('products_admin.html', products=products)
    if session.get('username') == 'user':
        return render_template('products_user.html', products=products)
    return 'вы не авторизованы'

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        m = set()
        supplier_ids = set()
        storage_ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from products')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
            m.add(row[0])
        cursor.execute('select * from suppliers')
        for row in cursor.fetchall():
            supplier_ids.add(str(row[1]))
        cursor.execute('select * from storage')
        for row in cursor.fetchall():
            storage_ids.add(str(row[4]))
        if request.method == 'GET':
            return render_template('add_product.html', error=err, products=ids, suppliers=supplier_ids, storages=storage_ids)
        if request.method == 'POST':
            name = request.form["name"]
            price = request.form["price"]
            supplier_id = request.form['supplier_id']
            storage_id = request.form['storage_id']
            category = supplier_id
            if name not in ids and supplier_id in supplier_ids and storage_id in storage_ids and validate_string(name) and validate_string(category) and validate_num(price) and validate_string(supplier_id) and validate_id(storage_id):
                price = float(price)
                cursor.execute('select storage_id from storage where storage_number = ?', storage_id)
                storage_ins = cursor.fetchone()[0]
                storage_ins = int(storage_ins)
                cursor.execute('select supplier_id from suppliers where name = ?', supplier_id)
                supplier_ins = cursor.fetchone()[0]
                supplier_ins = int(supplier_ins)
                cursor.execute("INSERT INTO View_Products_flask VALUES (?, ?, ?, ?, ?, ?)", max(m)+1, name, category, price, supplier_ins, storage_ins)
                conn.commit()
                conn.close()
                return redirect(url_for('products'))
            elif name in ids:
                err = 'Product already exists'
                conn.close()
                return render_template('add_product.html', error=err, products=ids, suppliers=supplier_ids,
                                       storages=storage_ids)
            elif supplier_id not in supplier_ids:
                err = 'Supplier does not exist'
                conn.close()
                return render_template('add_product.html', error=err, products=ids, suppliers=supplier_ids,
                                       storages=storage_ids)
            elif storage_id not in storage_ids:
                err = 'Storage does not exist'
                conn.close()
                return render_template('add_product.html', error=err, products=ids, suppliers=supplier_ids,
                                       storages=storage_ids)
            else:
                err = 'Invalid Values: '
                if not validate_string(name):
                    err += 'name '
                if not validate_string(category):
                    err += 'category '
                if not validate_num(price):
                    err += 'price '
                if not validate_string(supplier_id):
                    err += 'supplier name'
                if not validate_id(storage_id):
                    err += 'storage №'
            return render_template('add_product.html', error=err, products=ids, suppliers=supplier_ids, storages=storage_ids)
    return 'вы не авторизованы'


@app.route('/update_product', methods=['GET', 'POST'])
def update_product():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        m = set()
        supplier_ids = set()
        storage_ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from products')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
            m.add(row[0])
        cursor.execute('select * from suppliers')
        for row in cursor.fetchall():
            supplier_ids.add(str(row[1]))
        cursor.execute('select * from storage')
        for row in cursor.fetchall():
            storage_ids.add(str(row[4]))
        if request.method == 'GET':
            return render_template('update_product.html', error=err, products=ids, suppliers=supplier_ids, storages=storage_ids)
        if request.method == 'POST':
            name = request.form["name"]
            category = 'вкусняшка'
            price = request.form["price"]
            supplier_id = request.form['supplier_id']
            storage_id = request.form['storage_id']
            if name in ids and supplier_id in supplier_ids and storage_id in storage_ids and validate_string(name) and validate_string(category) and validate_num(price) and validate_string(supplier_id) and validate_id(storage_id):
                price = float(price)
                cursor.execute('select storage_id from storage where storage_number = ?', storage_id)
                storage_ins = cursor.fetchone()[0]
                storage_ins = int(storage_ins)
                cursor.execute('select supplier_id from suppliers where name = ?', supplier_id)
                supplier_ins = cursor.fetchone()[0]
                supplier_ins = int(supplier_ins)
                cursor.execute(f"update View_Products_flask set price = {price}, category = '{category}', supplier_id = {supplier_ins}, storage_id = {storage_ins} where name = '{name}'")
                conn.commit()
                conn.close()
                return redirect(url_for('products'))
            elif name not in ids:
                err = 'Product does not exist'
                conn.close()
                return render_template('update_product.html', error=err, products=ids, suppliers=supplier_ids,
                                       storages=storage_ids)
            elif supplier_id not in supplier_ids:
                err = 'Supplier does not exist'
                conn.close()
                return render_template('update_product.html', error=err, products=ids, suppliers=supplier_ids,
                                       storages=storage_ids)
            elif storage_id not in storage_ids:
                err = 'Storage does not exist'
                conn.close()
                return render_template('update_product.html', error=err, products=ids, suppliers=supplier_ids,
                                       storages=storage_ids)
            else:
                err = 'Invalid Values: '
                if not validate_string(name):
                    err += 'name '
                if not validate_string(category):
                    err += 'category '
                if not validate_num(price):
                    err += 'price '
                if not validate_string(supplier_id):
                    err += 'supplier name '
                if not validate_id(storage_id):
                    err += 'storage №'
            return render_template('update_product.html', error=err, products=ids, suppliers=supplier_ids, storages=storage_ids)
    return 'вы не авторизованы'


@app.route('/delete_product', methods=['GET', 'POST'])
def delete_product():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from products')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        if request.method == 'GET':
            return render_template('delete_product.html', error=err, products=ids)
        if request.method == 'POST':
            id = request.form["id"]
            if id in ids and validate_string(id):
                cursor.execute('select product_id from products where name = ?', id)
                pid = cursor.fetchone()[0]
                cursor.execute('delete from recipes where product_id = ?', pid)
                cursor.execute("DELETE FROM View_Products_flask WHERE name = ?", id)
                conn.commit()
                conn.close()
                return redirect(url_for('products'))
            else:
                err = 'No Such Product'
                conn.commit()
                conn.close()
            return render_template('delete_product.html', error=err, products=ids)
    return 'вы не авторизованы'

@app.route('/suppliers', methods=['GET'])
def suppliers():
    supplier = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from suppliers')
    for row in cursor.fetchall():
        supplier.append({'name':row[1], 'contact':row[2],'rate':row[3]})
    conn.close()
    if session.get('username') == 'user':
        return render_template('suppliers_user.html', suppliers=supplier)
    if session.get('username') == 'admin':
        return render_template('suppliers_admin.html', suppliers=supplier)
    return 'вы не авторизованы'

@app.route('/add_supplier', methods=['GET', 'POST'])
def add_supplier():
    if session.get('username') == 'admin':
        err = None
        if request.method == 'GET':
            return render_template('add_supplier.html', error=err)
        if request.method == 'POST':
            name = request.form["name"]
            contact = request.form["contact"]
            rate = request.form["rate"]
            ids = set()
            m = set()
            conn = connection()
            cursor = conn.cursor()
            cursor.execute('select * from suppliers')
            for row in cursor.fetchall():
                ids.add(str(row[1]))
                m.add(row[0])
            if name not in ids and validate_string(name) and validate_contact(contact) and validate_num(rate):
                rate = int(rate)
                cursor.execute("INSERT INTO suppliers VALUES (?, ?, ?, ?)", max(m)+1, name, contact, rate)
                conn.commit()
                conn.close()
                return redirect(url_for('suppliers'))
            elif name in ids:
                err = 'Supplier Already Exists'
                conn.close()
                return render_template('add_supplier.html', error=err)
            else:
                err = 'Invalid Values: '
                if not validate_string(name):
                    err += ' name'
                if not validate_contact(contact):
                    err += ' contact'
                if not validate_num(rate):
                    err += ' rate'
            return render_template('add_supplier.html', error=err)
    return 'вы не авторизованы'


@app.route('/update_supplier', methods=['GET', 'POST'])
def update_supplier():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from suppliers')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        if request.method == 'GET':
            return render_template('update_supplier.html', error=err, suppliers=ids)
        if request.method == 'POST':
            name = request.form["name"]
            contact = request.form["contact"]
            rate = request.form["rate"]
            if name in ids and validate_string(name) and validate_contact(contact) and validate_num(rate):
                rate = int(rate)
                cursor.execute(f"update suppliers set rating = ?, contact_details = ? where name = ?", rate, contact, name)
                conn.commit()
                conn.close()
                return redirect(url_for('suppliers'))
            elif name not in ids:
                err = "Supplier Does Not Exist"
                conn.close()
                return render_template('update_supplier.html', error=err, suppliers=ids)
            else:
                err = 'Invalid Values: '
                if not validate_string(name):
                    err += ' name'
                if not validate_contact(contact):
                    err += ' contact'
                if not validate_num(rate):
                    err += ' rate'
            return render_template('update_supplier.html', error=err, suppliers=ids)
    return 'вы не авторизованы'


@app.route('/delete_supplier', methods=['GET', 'POST'])
def delete_supplier():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from suppliers')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        if request.method == 'GET':
            return render_template('delete_supplier.html', error=err, suppliers=ids)
        if request.method == 'POST':
            id = request.form["id"]
            if id in ids and validate_string(id):
                cursor.execute("select supplier_id FROM suppliers WHERE name = ?", id)
                sid = cursor.fetchone()[0]
                cursor.execute('select product_id from products where supplier_id = ?', sid)
                res = cursor.fetchall()
                if res:
                    for pid1 in res:
                        cursor.execute('delete from recipes where product_id = ?', pid1)
                cursor.execute("DELETE FROM products WHERE supplier_id = ?", sid)
                cursor.execute("DELETE FROM suppliers WHERE name = ?", id)
                conn.commit()
                conn.close()
                return redirect(url_for('suppliers'))
            else:
                err = 'No Such Supplier'
                conn.commit()
                conn.close()
            return render_template('delete_supplier.html', error=err, suppliers=ids)
    return 'вы не авторизованы'



@app.route('/storage', methods=['GET'])
def storage():
    storages = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from storage')
    for row in cursor.fetchall():
        storages.append({'id':row[4], 'date':row[1], 'exdate':row[2],'qtt':row[3]})
    conn.close()
    if session.get('username') == 'user':
        return render_template('storage_user.html', storages=storages)
    if session.get('username') == 'admin':
        return render_template('storage_admin.html', storages=storages)
    return 'вы не авторизованы'

@app.route('/add_storage', methods=['GET', 'POST'])
def add_storage():
    if session.get('username') == 'admin':
        err = None
        if request.method == 'GET':
            return render_template('add_storage.html', error=err)
        if request.method == 'POST':
            id = request.form["id"]
            date = request.form["date"]
            exdate = request.form["exdate"]
            qtt = request.form["qtt"]
            ids = set()
            conn = connection()
            cursor = conn.cursor()
            m = set()
            cursor.execute('select * from storage')
            for row in cursor.fetchall():
                ids.add(str(row[4]))
                m.add(row[0])
            if id not in ids and validate_date(date) and validate_date(exdate) and validate_num(qtt) and validate_id(id):
                qtt = int(qtt)
                id = int(id)
                cursor.execute("INSERT INTO storage VALUES (?, ?, ?, ?, ?)", max(m)+1, date, exdate, qtt, id)
                conn.commit()
                conn.close()
                return redirect(url_for('storage'))
            elif id in ids:
                err = 'Storage Already Exists'
                conn.close()
                return render_template('add_storage.html', error=err)
            else:
                err = 'Invalid Values: '
                if not validate_id(id):
                    err += 'storage №'
                if not validate_date(date):
                    err += ' date'
                if not validate_date(exdate):
                    err += ' exdate'
                if not validate_num(qtt):
                    err += ' quantity'
            return render_template('add_storage.html', error=err)
    return 'вы не авторизованы'


@app.route('/update_storage', methods=['GET', 'POST'])
def update_storage():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from storage')
        for row in cursor.fetchall():
            ids.add(str(row[4]))
        if request.method == 'GET':
            return render_template('update_storage.html', error=err, storages=ids)
        if request.method == 'POST':
            id = request.form["id"]
            date = request.form["date"]
            exdate = request.form["exdate"]
            qtt = request.form["qtt"]
            if id in ids and validate_date(date) and validate_date(exdate) and validate_num(qtt) and validate_id(id):
                qtt = int(qtt)
                id = int(id)
                cursor.execute(f"update storage set production_date ='{date}', expiry_date = '{exdate}', unit_quantity = {qtt} where storage_number = {id}")
                conn.commit()
                conn.close()
                return redirect(url_for('storage'))
            elif id not in ids:
                err = "Storage Does Not Exist"
                conn.close()
                return render_template('update_storage.html', error=err, storages=ids)
            else:
                err = 'Invalid Values: '
                if not validate_id(id):
                    err += 'storage №'
                if not validate_date(date):
                    err += ' date'
                if not validate_date(exdate):
                    err += ' exdate'
                if not validate_num(qtt):
                    err += ' quantity'
            return render_template('update_storage.html', error=err, storages=ids)
    return 'вы не авторизованы'


@app.route('/delete_storage', methods=['GET', 'POST'])
def delete_storage():
    if session.get('username') == 'admin':
        err = None
        ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from storage')
        for row in cursor.fetchall():
            ids.add(str(row[4]))
        if request.method == 'GET':
            return render_template('delete_storage.html', error=err, storages=ids)
        if request.method == 'POST':
            id = request.form["id"]
            if id in ids and validate_id(id):
                id = int(id)
                cursor.execute("select storage_id FROM storage WHERE storage_number = ?", id)
                sid = cursor.fetchone()[0]
                cursor.execute('select product_id from products where storage_id = ?', sid)
                res = cursor.fetchall()
                if res:
                    for pid1 in res:
                        cursor.execute('delete from recipes where product_id = ?', pid1)
                cursor.execute("DELETE FROM products WHERE storage_id = ?", sid)
                cursor.execute("DELETE FROM storage WHERE storage_number = ?", id)
                conn.commit()
                conn.close()
                return redirect(url_for('storage'))
            else:
                err = 'No Such Storage'
                conn.commit()
                conn.close()
            return render_template('delete_storage.html', error=err, storages=ids)
    return 'вы не авторизованы'


@app.route('/recipes', methods=['GET'])
def recipes():
    recipes_admin = []
    recipes_user = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from recipes')
    for row in cursor.fetchall():
        recipes_admin.append({'dish_id':row[0], 'product_id':row[1], 'qtt':row[2]})
    for i in recipes_admin:
        dish_id = i['dish_id']
        cursor.execute(f'select name from dishes where dish_id = {dish_id}')
        dish_name = cursor.fetchone()[0]
        product_id = i['product_id']
        cursor.execute(f'select name from products where product_id = {product_id}')
        product_name = cursor.fetchone()[0]
        qtt = i['qtt']
        recipes_user.append({'product_name':product_name, 'dish_name':dish_name, 'qtt':qtt})
    conn.close()
    if session.get('username') == 'admin':
        return render_template('recipes_admin.html', recipes=recipes_user)
    if session.get('username') =='user':
        return render_template('recipes_user.html', recipes=recipes_user)
    return 'вы не авторизованы'


@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if session.get('username') == 'admin':
        err = None
        pks = []
        ids = set()
        product_ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from dishes')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        cursor.execute('select * from products')
        for row in cursor.fetchall():
            product_ids.add(str(row[1]))
        cursor.execute('select * from recipes')
        for row in cursor.fetchall():
            pks.append([row[0], row[1]])
        for i in range(len(pks)):
            cursor.execute('select name from dishes where dish_id = ?', pks[i][0])
            pks[i][0] = cursor.fetchone()[0]
            cursor.execute('select name from products where product_id = ?', pks[i][1])
            pks[i][1] = cursor.fetchone()[0]
        if request.method == 'GET':
            return render_template('update_recipe.html', error=err, dishes=ids,products=product_ids)
        if request.method == 'POST':
            id = request.form['id']
            product_id = request.form['product_id']
            qtt = request.form["qtt"]
            pk = [id, product_id]
            if pk not in pks and validate_string(id) and id in ids and product_id in product_ids and validate_num(qtt) and validate_string(product_id):
                qtt = int(qtt)
                cursor.execute('select dish_id from dishes where name = ?', id)
                id_ins = cursor.fetchone()[0]
                id_ins = int(id_ins)
                cursor.execute('select product_id from products where name = ?', product_id)
                product_ins = cursor.fetchone()[0]
                product_ins = int(product_ins)
                cursor.execute("INSERT INTO recipes VALUES (?, ?, ?)", id_ins, product_ins, qtt)
                conn.commit()
                conn.close()
                return redirect(url_for('recipes'))
            elif id not in ids:
                err = 'Dish does not exist'
                conn.close()
                return render_template('update_recipe.html', error=err, dishes=ids, products=product_ids)
            elif product_id not in product_ids:
                err = 'Product does not exist'
                conn.close()
                return render_template('update_recipe.html', error=err, dishes=ids, products=product_ids)
            elif pk in pks:
                err = 'Recipe already exists'
                conn.close()
                return render_template('update_recipe.html', error=err, dishes=ids, products=product_ids)
            else:
                err = 'Invalid Values: '
                if not validate_string(id):
                    err += 'dish name '
                if not validate_num(qtt):
                    err += 'quantity '
                if not validate_string(product_id):
                    err += 'product name'
            return render_template('update_recipe.html', error=err, dishes=ids,products=product_ids)
    return 'вы не авторизованы'


@app.route('/update_recipe', methods=['GET', 'POST'])
def update_recipe():
    if session.get('username') == 'admin':
        err = None
        pks = []
        sdish = set()
        sprod = set()
        ids = set()
        product_ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from dishes')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        cursor.execute('select * from products')
        for row in cursor.fetchall():
            product_ids.add(str(row[1]))
        cursor.execute('select * from recipes')
        for row in cursor.fetchall():
            pks.append([row[0], row[1]])
        for i in range(len(pks)):
            cursor.execute('select name from dishes where dish_id = ?', pks[i][0])
            ds = cursor.fetchone()[0]
            pks[i][0] = ds
            sdish.add(ds)
            cursor.execute('select name from products where product_id = ?', pks[i][1])
            ds = cursor.fetchone()[0]
            pks[i][1] = ds
            sprod.add(ds)
        if request.method == 'GET':
            return render_template('update_recipe.html', error=err, dishes=sdish,products=sprod)
        if request.method == 'POST':
            id = request.form['id']
            product_id = request.form['product_id']
            qtt = request.form["qtt"]
            pk = [id, product_id]
            if pk in pks and validate_string(id) and id in ids and product_id in product_ids and validate_num(
                    qtt) and validate_string(product_id):
                qtt = int(qtt)
                cursor.execute('select dish_id from dishes where name = ?', id)
                id_ins = cursor.fetchone()[0]
                id_ins = int(id_ins)
                cursor.execute('select product_id from products where name = ?', product_id)
                product_ins = cursor.fetchone()[0]
                product_ins = int(product_ins)
                cursor.execute(f"update recipes set quantity = {qtt} where dish_id = {id_ins} and product_id = {product_ins}")
                conn.commit()
                conn.close()
                return redirect(url_for('recipes'))
            elif id not in ids:
                err = 'Dish does not exist'
                conn.close()
                return render_template('update_recipe.html', error=err, dishes=sdish, products=sprod)
            elif product_id not in product_ids:
                err = 'Product does not exist'
                conn.close()
                return render_template('update_recipe.html', error=err, dishes=sdish, products=sprod)
            elif pk not in pks:
                err = 'Recipe does not exist'
                conn.close()
                return render_template('update_recipe.html', error=err, dishes=sdish, products=sprod)
            else:
                err = 'Invalid Values: '
                if not validate_string(id):
                    err += 'dish name '
                if not validate_num(qtt):
                    err += 'quantity '
                if not validate_string(product_id):
                    err += 'product name'
            return render_template('update_recipe.html', error=err, dishes=sdish,products=sprod)
    return 'вы не авторизованы'


@app.route('/delete_recipe', methods=['GET', 'POST'])
def delete_recipe():
    if session.get('username') == 'admin':
        err = None
        pks = []
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from recipes')
        dishes = set()
        products = set()
        for row in cursor.fetchall():
            pks.append([row[0], row[1]])
        for i in range(len(pks)):
            cursor.execute('select name from dishes where dish_id = ?', pks[i][0])
            ds = cursor.fetchone()[0]
            pks[i][0] = ds
            dishes.add(ds)
            cursor.execute('select name from products where product_id = ?', pks[i][1])
            ps = cursor.fetchone()[0]
            pks[i][1] = ps
            products.add(ps)
        if request.method == 'GET':
            return render_template('delete_recipe.html', error=err, dishes=dishes, products=products)
        if request.method == 'POST':
            id = request.form['id']
            product_id = request.form['product_id']
            pk = [id, product_id]
            if pk in pks and validate_string(id) and validate_string(product_id):
                cursor.execute('select dish_id from dishes where name = ?', id)
                id_ins = cursor.fetchone()[0]
                id_ins = int(id_ins)
                cursor.execute('select product_id from products where name = ?', product_id)
                product_ins = cursor.fetchone()[0]
                product_ins = int(product_ins)
                cursor.execute("DELETE FROM recipes WHERE dish_id = ? and product_id = ?", id_ins, product_ins)
                conn.commit()
                conn.close()
                return redirect(url_for('recipes'))
            else:
                err = 'No Such Recipe'
                conn.commit()
                conn.close()
            return render_template('delete_recipe.html', error=err, dishes=dishes, products=products)
    return 'вы не авторизованы'


@app.route('/diary_orders', methods=['GET'])
def diary_orders():
    dos_admin = []
    dos_user = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from diary_orders')
    for row in cursor.fetchall():
        dos_admin.append({'dish_id':row[0], 'order_id':row[1], 'qtt':row[2]})
    for i in dos_admin:
        dish_id = i['dish_id']
        cursor.execute(f'select name from dishes where dish_id = {dish_id}')
        dish_name = cursor.fetchone()[0]
        order_id = i['order_id']
        cursor.execute(f'select order_number from orders where order_id = {order_id}')
        order_status = cursor.fetchone()[0]
        qtt = i['qtt']
        dos_user.append({'order_status':order_status, 'dish_name':dish_name, 'qtt':qtt})
    conn.close()
    if session.get('username') == 'admin':
        return render_template('do_admin.html', dos=dos_user)
    if session.get('username') =='user':
        return render_template('do_user.html', dos=dos_user)
    return 'вы не авторизованы'


@app.route('/add_do', methods=['GET', 'POST'])
def add_do():
    if session.get('username') == 'admin':
        err = None
        pks = []
        ids = set()
        product_ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from dishes')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        cursor.execute('select * from orders')
        for row in cursor.fetchall():
            product_ids.add(str(row[5]))
        cursor.execute('select * from diary_orders')
        for row in cursor.fetchall():
            pks.append([row[0], row[1]])
        for i in range(len(pks)):
            cursor.execute('select name from dishes where dish_id = ?', pks[i][0])
            pks[i][0] = cursor.fetchone()[0]
            cursor.execute('select order_number from orders where order_id = ?', pks[i][1])
            pks[i][1] = str(cursor.fetchone()[0])
        if request.method == 'GET':
            return render_template('add_do.html', error=err, dishes=ids, orders=product_ids)
        if request.method == 'POST':
            id = request.form['id']
            product_id = request.form['product_id']
            qtt = request.form["qtt"]
            pk = [id, product_id]
            if pk not in pks and validate_string(id) and id in ids and product_id in product_ids and validate_num(
                    qtt) and validate_id(product_id):
                qtt = int(qtt)
                cursor.execute('select dish_id from dishes where name = ?', id)
                id_ins = cursor.fetchone()[0]
                id_ins = int(id_ins)
                cursor.execute('select order_id from orders where order_number = ?', product_id)
                product_ins = cursor.fetchone()[0]
                product_ins = int(product_ins)
                cursor.execute("select total_amount from orders where order_id = ?", product_ins)
                pred_amount = cursor.fetchone()[0]
                cursor.execute("INSERT INTO View_Diary_Orders_flask VALUES (?, ?, ?)", id_ins, product_ins, qtt)
                cursor.execute("select sum(cost_price*quantity) from dishes join diary_orders on dishes.dish_id = diary_orders.dish_id where diary_orders.order_id = ?", product_ins)
                res = cursor.fetchone()[0]
                pred_amount += res
                cursor.execute('update orders set total_amount = ? where order_id =?', pred_amount, product_ins)
                conn.commit()
                conn.close()
                return redirect(url_for('diary_orders'))
            elif id not in ids:
                err = 'Dish does not exist'
                conn.close()
                return render_template('add_do.html', error=err, dishes=ids, orders=product_ids)
            elif product_id not in product_ids:
                err = 'Order does not exist'
                conn.close()
                return render_template('add_do.html', error=err, dishes=ids, orders=product_ids)
            elif pk in pks:
                err = 'Diary Order already exists'
                conn.close()
                return render_template('add_do.html', error=err, dishes=ids, orders=product_ids)
            else:
                err = 'Invalid Values: '
                if not validate_string(id):
                    err += 'dish name '
                if not validate_num(qtt):
                    err += 'quantity '
                if not validate_id(product_id):
                    err += 'order number'
            return render_template('add_do.html', error=err, dishes=ids, orders=product_ids)
    return 'вы не авторизованы'


@app.route('/update_do', methods=['GET', 'POST'])
def update_do():
    if session.get('username') == 'admin':
        err = None
        pks = []
        ids = set()
        product_ids = set()
        sdish = set()
        sorders = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from dishes')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        cursor.execute('select * from orders')
        for row in cursor.fetchall():
            product_ids.add(str(row[5]))
        cursor.execute('select * from diary_orders')
        for row in cursor.fetchall():
            pks.append([row[0], row[1]])
        for i in range(len(pks)):
            cursor.execute('select name from dishes where dish_id = ?', pks[i][0])
            ds = cursor.fetchone()[0]
            pks[i][0] = ds
            sdish.add(ds)
            cursor.execute('select order_number from orders where order_id = ?', pks[i][1])
            ds = cursor.fetchone()[0]
            pks[i][1] = str(ds)
            sorders.add(ds)
        if request.method == 'GET':
            return render_template('add_do.html', error=err, dishes=sdish, orders=sorders)
        if request.method == 'POST':
            id = request.form['id']
            product_id = request.form['product_id']
            qtt = request.form["qtt"]
            pk = [id, product_id]
            if pk in pks and validate_string(id) and id in ids and product_id in product_ids and validate_num(
                    qtt) and validate_id(product_id):
                qtt = int(qtt)
                cursor.execute('select dish_id from dishes where name = ?', id)
                id_ins = cursor.fetchone()[0]
                id_ins = int(id_ins)
                cursor.execute('select order_id from orders where order_number = ?', product_id)
                product_ins = cursor.fetchone()[0]
                product_ins = int(product_ins)
                cursor.execute("select total_amount from orders where order_id = ?", product_ins)
                pred_amount = cursor.fetchone()[0]
                cursor.execute("select quantity from diary_orders where dish_id = ? and order_id = ?",id_ins, product_ins)
                pred_qtt = cursor.fetchone()[0]
                cursor.execute("update View_Diary_Orders_flask set quantity = ? where dish_id = ? and order_id = ?", qtt, id_ins, product_ins)
                qtt -= pred_qtt
                cursor.execute("select cost_price from dishes join diary_orders on dishes.dish_id = diary_orders.dish_id where diary_orders.dish_id = ? and diary_orders.order_id = ?", id_ins, product_ins)
                multi = cursor.fetchone()[0]
                print(qtt, pred_amount, multi)
                cursor.execute('update orders set total_amount =?+?*? where order_id = ?', pred_amount, qtt, multi, product_ins)
                conn.commit()
                conn.close()
                return redirect(url_for('diary_orders'))
            elif id not in ids:
                err = 'Dish does not exist'
                conn.close()
                return render_template('add_do.html', error=err, dishes=sdish, orders=sorders)
            elif product_id not in product_ids:
                err = 'Order does not exist'
                conn.close()
                return render_template('add_do.html', error=err, dishes=sdish, orders=sorders)
            elif pk not in pks:
                err = 'Diary Order does not exists'
                conn.close()
                return render_template('add_do.html', error=err, dishes=sdish, orders=sorders)
            else:
                err = 'Invalid Values: '
                if not validate_string(id):
                    err += 'dish name '
                if not validate_num(qtt):
                    err += 'quantity '
                if not validate_id(product_id):
                    err += 'order number'
            return render_template('add_do.html', error=err, dishes=sdish, orders=sorders)
    return 'вы не авторизованы'


@app.route('/delete_do', methods=['GET', 'POST'])
def delete_do():
    if session.get('username') == 'admin':
        err = None
        pks = []
        sdish = set()
        sorder = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from diary_orders')
        for row in cursor.fetchall():
            pks.append([row[0], row[1]])
        for i in range(len(pks)):
            cursor.execute('select name from dishes where dish_id = ?', pks[i][0])
            ds = cursor.fetchone()[0]
            pks[i][0] = ds
            sdish.add(ds)
            cursor.execute('select order_number from orders where order_id = ?', pks[i][1])
            ds = cursor.fetchone()[0]
            pks[i][1] = str(ds)
            sorder.add(ds)
        if request.method == 'GET':
            return render_template('delete_do.html', error=err, dishes=sdish, orders=sorder)
        if request.method == 'POST':
            id = request.form['id']
            product_id = request.form['product_id']
            pk = [id, product_id]
            print(pk, pks)
            if pk in pks and validate_string(id) and validate_id(product_id):
                cursor.execute('select dish_id from dishes where name = ?', id)
                id_ins = cursor.fetchone()[0]
                id_ins = int(id_ins)
                cursor.execute('select order_id from orders where order_number = ?', product_id)
                product_ins = cursor.fetchone()[0]
                product_ins = int(product_ins)
                cursor.execute("select total_amount from orders where order_id = ?", product_ins)
                pred_amount = cursor.fetchone()[0]
                cursor.execute(
                    "select cost_price from dishes join diary_orders on dishes.dish_id = diary_orders.dish_id where diary_orders.dish_id = ? and diary_orders.order_id = ?",
                    id_ins, product_ins)
                multi = cursor.fetchone()[0]
                cursor.execute('select quantity from diary_orders where dish_id = ? and order_id = ?', id_ins, product_ins)
                qtt = cursor.fetchone()[0]
                cursor.execute('update orders set total_amount =?-?*? where order_id = ?', pred_amount, qtt, multi, product_ins)
                cursor.execute("DELETE FROM View_Diary_Orders_flask WHERE dish_id = ? and order_id = ?", id_ins, product_ins)
                conn.commit()
                conn.close()
                return redirect(url_for('diary_orders'))
            else:
                err = 'No Such Diary Order'
                conn.commit()
                conn.close()
            return render_template('delete_do.html', error=err, dishes=sdish, orders=sorder)

@app.route('/type_employee', methods=['GET'])
def type_employee():
    dishes = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from type_employee')
    for row in cursor.fetchall():
        dishes.append({'id':row[0], 'name':row[1]})
    conn.close()
    if session.get('username') == 'user':
        return render_template('te_user.html', dishes=dishes)
    if session.get('username') == 'admin':
        return render_template('te_admin.html', dishes=dishes)
    return 'вы не авторизованы'


@app.route('/add_te', methods=['GET', 'POST'])
def add_te():
    if session.get('username') == 'admin':
        err = None
        if request.method == 'GET':
            return render_template('add_te.html', error=err)
        if request.method == 'POST':
            name = request.form["name"]
            ids = set()
            names = set()
            conn = connection()
            cursor = conn.cursor()
            cursor.execute('select * from type_employee')
            for row in cursor.fetchall():
                ids.add((row[0]))
                names.add(row[1])
            if name not in names and validate_string(name):
                cursor.execute("INSERT INTO type_employee VALUES (?, ?)", max(ids)+1, name)
                conn.commit()
                conn.close()
                return redirect(url_for('type_employee'))
            elif name in names:
                err = 'Type Already Exists'
                conn.close()
                return render_template('add_te.html', error=err)
            else:
                err = 'Invalid Values: '
                if not validate_string(name):
                    err += ' name'
            return render_template('add_te.html', error=err)
    return 'вы не авторизованы'


@app.route('/delete_te', methods=['GET', 'POST'])
def delete_te():
    if session.get('username') == 'admin':
        err = None
        if request.method == 'GET':
            return render_template('delete_te.html', error=err)
        if request.method == 'POST':
            name = request.form["name"]
            ids = set()
            conn = connection()
            cursor = conn.cursor()
            cursor.execute('select * from type_employee')
            for row in cursor.fetchall():
                ids.add(str(row[1]))
            if name in ids and validate_string(name):
                cursor.execute('select type_employee_id from type_employee where type_name = ?', name)
                pid = cursor.fetchone()[0]
                cursor.execute('select employee_id from employee where type_employee_id = ?', pid)
                res = cursor.fetchall()
                if res:
                    for pid1 in res:
                        cursor.execute('delete from employee_dishes where employee_id = ?', pid1)
                cursor.execute('delete from employee where type_employee_id = ?', pid)
                cursor.execute("DELETE FROM type_employee WHERE type_name = ?", name)
                conn.commit()
                conn.close()
                return redirect(url_for('type_employee'))
            else:
                err = 'No Such Type'
                conn.commit()
                conn.close()
            return render_template('delete_te.html', error=err)
    return 'вы не авторизованы'


@app.route('/employee_dishes', methods=['GET'])
def employee_dishes():
    recipes_admin = []
    recipes_user = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('select * from employee_dishes')
    for row in cursor.fetchall():
        recipes_admin.append({'product_id':row[0], 'dish_id':row[1]})
    for i in recipes_admin:
        dish_id = i['dish_id']
        cursor.execute(f'select name from dishes where dish_id = {dish_id}')
        dish_name = cursor.fetchone()[0]
        product_id = i['product_id']
        cursor.execute(f'select name from employee where employee_id = {product_id}')
        product_name = cursor.fetchone()[0]
        recipes_user.append({'product_name':product_name, 'dish_name':dish_name})
    conn.close()
    if session.get('username') == 'admin':
        return render_template('ed_admin.html', recipes=recipes_user)
    if session.get('username') =='user':
        return render_template('ed_user.html', recipes=recipes_user)
    return 'вы не авторизованы'


@app.route('/add_ed', methods=['GET', 'POST'])
def add_ed():
    if session.get('username') == 'admin':
        err = None
        pks = []
        ids = set()
        product_ids = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from dishes')
        for row in cursor.fetchall():
            ids.add(str(row[1]))
        cursor.execute('select * from employee')
        for row in cursor.fetchall():
            product_ids.add(str(row[1]))
        cursor.execute('select * from employee_dishes')
        for row in cursor.fetchall():
            pks.append([row[1], row[0]])
        for i in range(len(pks)):
            cursor.execute('select name from dishes where dish_id = ?', pks[i][0])
            pks[i][0] = cursor.fetchone()[0]
            cursor.execute('select name from employee where employee_id = ?', pks[i][1])
            pks[i][1] = cursor.fetchone()[0]
        if request.method == 'GET':
            return render_template('add_ed.html', error=err, employees=product_ids, dishes=ids)
        if request.method == 'POST':
            id = request.form['id']
            product_id = request.form['product_id']
            pk = [id, product_id]
            if pk not in pks and validate_string(id) and id in ids and product_id in product_ids and validate_string(product_id):
                cursor.execute('select dish_id from dishes where name = ?', id)
                id_ins = cursor.fetchone()[0]
                id_ins = int(id_ins)
                cursor.execute('select employee_id from employee where name = ?', product_id)
                product_ins = cursor.fetchone()[0]
                product_ins = int(product_ins)
                cursor.execute("INSERT INTO View_Employee_Dishes_flask VALUES (?, ?)", product_ins, id_ins)
                conn.commit()
                conn.close()
                return redirect(url_for('employee_dishes'))
            elif id not in ids:
                err = 'Dish does not exist'
                conn.close()
                return render_template('add_ed.html', error=err, employees=product_ids, dishes=ids)
            elif product_id not in product_ids:
                err = 'Employee does not exist'
                conn.close()
                return render_template('add_ed.html', error=err, employees=product_ids, dishes=ids)
            elif pk in pks:
                err = 'Employee dish already exists'
                conn.close()
                return render_template('add_ed.html', error=err, employees=product_ids, dishes=ids)
            else:
                err = 'Invalid Values: '
                if not validate_string(id):
                    err += 'dish name '
                if not validate_string(product_id):
                    err += 'employee name'
            return render_template('add_ed.html', error=err, employees=product_ids, dishes=ids)
    return 'вы не авторизованы'


@app.route('/delete_ed', methods=['GET', 'POST'])
def delete_ed():
    if session.get('username') == 'admin':
        err = None
        pks = []
        s1 = set()
        s2 = set()
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select * from employee_dishes')
        for row in cursor.fetchall():
            pks.append([row[1], row[0]])
        for i in range(len(pks)):
            cursor.execute('select name from dishes where dish_id = ?', pks[i][0])
            ds = cursor.fetchone()[0]
            pks[i][0] = ds
            s1.add(ds)
            cursor.execute('select name from employee where employee_id = ?', pks[i][1])
            ds = cursor.fetchone()[0]
            pks[i][1] = ds
            s2.add(ds)
        if request.method == 'GET':
            return render_template('delete_ed.html', error=err, employees=s2, dishes=s1)
        if request.method == 'POST':
            id = request.form['id']
            product_id = request.form['product_id']
            pk = [id, product_id]
            if pk in pks and validate_string(id) and validate_string(product_id):
                cursor.execute('select dish_id from dishes where name = ?', id)
                id_ins = cursor.fetchone()[0]
                id_ins = int(id_ins)
                cursor.execute('select employee_id from employee where name = ?', product_id)
                product_ins = cursor.fetchone()[0]
                product_ins = int(product_ins)
                cursor.execute("DELETE FROM View_Employee_Dishes_flask WHERE dish_id = ? and employee_id = ?", id_ins, product_ins)
                conn.commit()
                conn.close()
                return redirect(url_for('employee_dishes'))
            else:
                err = 'No Such Employee Dish'
                conn.commit()
                conn.close()
            return render_template('delete_ed.html', error=err, employees=s2, dishes=s1)
    return 'вы не авторизованы'

@app.route('/supplier_product', methods=['GET', 'POST'])
def supplier_product():
    if session.get('username') == 'admin' or session.get('username') == 'user':
        products = []
        suppliers = []
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select name from suppliers')
        err = None
        for row in cursor.fetchall():
            suppliers.append({'name': row[0]})
        if request.method == 'GET':
            return render_template('supplier_product.html', products=products, suppliers=suppliers, err=err)
        if request.method == 'POST':
            name = request.form.get('name')
            aut ={'name':name}
            if validate_string(name) and aut in suppliers:
                swap = suppliers.pop(suppliers.index(aut))
                suppliers.insert(0, swap)
                cursor.execute('select supplier_id from suppliers where name = ?', name)
                supplier_id = cursor.fetchone()[0]
                cursor.execute('select * from products where supplier_id = ?', supplier_id)
                for row in cursor.fetchall():
                    products.append({'name': row[1], 'category': row[2], 'price': row[3],
                                     'storage_id': row[5]})
                for i in range(len(products)):
                    cursor.execute('select storage_number from storage where storage_id = ?', products[i]['storage_id'])
                    products[i]['storage_id'] = cursor.fetchone()[0]
                conn.close()
                return render_template('supplier_product.html', products=products, suppliers=suppliers)
            else:
                err = 'Invalid supplier'
                conn.close()
                return render_template('supplier_product.html', products=products, suppliers=suppliers)
        return 'вы не авторизованы'

@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
    if session.get('username') == 'admin' or session.get('username') == 'user':
        err = None
        conn = connection()
        cursor = conn.cursor()
        supplier_storage = {}
        cursor.execute('EXEC ProductCount')
        product_amount = cursor.fetchone()
        cursor.execute("DECLARE @maxRating INT EXEC MaxSupplierRating @rating = @maxRating Output select 'Максимальная оценка поставщика' = @maxRating")
        maxrate = cursor.fetchone()[0]
        products = []
        suppliers = []
        productd = {}
        veg_amount = 0
        cursor.execute('select name from products')
        for row in cursor.fetchall():
            products.append({'name':row[0]})
        cursor.execute('select name from suppliers')
        for row in cursor.fetchall():
            suppliers.append({'name':row[0]})
        if request.method == 'GET':
            return render_template('monitor.html', veg_amount=veg_amount, err=err,
                                   product_amount=product_amount, products=products,
                                   supplier_storage=supplier_storage, suppliers=suppliers, productd=productd, maxrate=maxrate)
        if request.method == 'POST':
            if {'name': request.form.get('product')} in products:
                product = request.form['product']
                if validate_string(product):
                    cursor.execute('select product_id from products where name = ?', product)
                    product_id = cursor.fetchone()[0]
                    cursor.execute('EXEC ProductSupplierStorageDetails ?', product_id)
                    row = cursor.fetchone()
                    supplier_storage = {'pname':row[0], 'sname':row[1], 'pdate':row[2], 'edate':row[3], 'qtt':row[4]}
                    conn.close()
                    return render_template('monitor.html', veg_amount=veg_amount, err=err,
                                           product_amount=product_amount, products=products,
                                           supplier_storage=supplier_storage, suppliers=suppliers, productd=productd,
                                           maxrate=maxrate)

                else:
                    err = 'invalid product'
                    conn.close()
                    return render_template('monitor.html', veg_amount=veg_amount, err=err,
                                           product_amount=product_amount, products=products,
                                           supplier_storage=supplier_storage, suppliers=suppliers, productd=productd,
                                           maxrate=maxrate)

            if {'name': request.form.get('supplier')} in suppliers:
                supplier = request.form['supplier']
                if validate_string(supplier):
                    cursor.execute('select supplier_id from suppliers where name = ?', supplier)
                    supplier_id = cursor.fetchone()[0]
                    cursor.execute("DECLARE @result INT EXEC @result = ExistSupplier ? SELECT 'TotalVegetablesAndSpices' = @result", supplier_id)
                    row = cursor.fetchone()
                    veg_amount = row[0]
                    conn.close()
                    return render_template('monitor.html', veg_amount=veg_amount, err=err,
                                           product_amount=product_amount, products=products,
                                           supplier_storage=supplier_storage, suppliers=suppliers, productd=productd,
                                           maxrate=maxrate)
                else:
                    err = 'invalid supplier'
                    conn.close()
                    return render_template('monitor.html', veg_amount=veg_amount, err=err,
                                           product_amount=product_amount, products=products,
                                           supplier_storage=supplier_storage, suppliers=suppliers, productd=productd,
                                           maxrate=maxrate)

            if {'name': request.form.get('productd')} in products:
                product = request.form['productd']
                if validate_string(product):
                    cursor.execute('select product_id from products where name = ?', product)
                    product_id = cursor.fetchone()[0]
                    cursor.execute('EXEC GetProductInformationByIdWithCursor ?', product_id)
                    row = cursor.fetchone()
                    productd = {'pname':row[0], 'cat':row[1], 'price':row[2], 'sname':row[3], 'rate':row[4]}
                    conn.close()
                    return render_template('monitor.html', veg_amount=veg_amount, err=err,
                                           product_amount=product_amount, products=products,
                                           supplier_storage=supplier_storage, suppliers=suppliers, productd=productd,
                                           maxrate=maxrate)
            return render_template('monitor.html', veg_amount=veg_amount, err=err,
                                   product_amount=product_amount, products=products,
                                   supplier_storage=supplier_storage, suppliers=suppliers, productd=productd,
                                   maxrate=maxrate)

        return 'вы не авторизованы'


@app.route('/search_form', methods=['GET', 'POST'])
def search_form():
    if session.get('username') == 'admin' or session.get('username') == 'user':
        res = []
        employees = []
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('select name from employee')
        err = None
        for row in cursor.fetchall():
            employees.append({'name': row[0]})
        if request.method == 'GET':
            return render_template('search_form.html', employees=employees, res=res, err=err)
        if request.method == 'POST':
            name = request.form.get('name')
            aut ={'name':name}
            if validate_string(name) and aut in employees:
                swap = employees.pop(employees.index(aut))
                employees.insert(0, swap)
                cursor.execute('SELECT employee.name, employee.age, employee.job_role, dishes.name, dishes.type_dish FROM employee JOIN employee_dishes ON employee.employee_id = employee_dishes.employee_id JOIN dishes ON employee_dishes.dish_id = dishes.dish_id where employee.name = ?', name)
                for row in cursor.fetchall():
                    res.append({'ename': row[0], 'age': row[1], 'jr': row[2],
                                     'dname': row[3], 'dt':row[4]})
                conn.close()
                return render_template('search_form.html', employees=employees, res=res, err=err)
            else:
                err = 'Invalid Employee'
                conn.close()
                return render_template('search_form.html', employees=employees, res=res, err=err)
        return 'вы не авторизованы'

if __name__ == '__main__':
    app.run()
