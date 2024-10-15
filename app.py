import base64
import json
import requests
import bcrypt
from flask import Flask, jsonify, request, send_from_directory
from flask_mysqldb import MySQL
from flask_cors import CORS
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

load_dotenv()

mysql = MySQL(app)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')


@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory(os.path.join(os.getcwd(), 'front-end-capstone-project'), 'index.html')


@app.route('/')
def home():
    return jsonify({
        'message': {
            '/upload_image': 'Upload images for product (POST)',
            '/products': 'Create new product (POST)',
            '/products': 'Get all products o products by category (GET)',
            '/product/<int:product_id>': 'Get a unique product by its id (GET)',
            '/products/<int:product_id>': 'Updated the product by its id (PATCH)',
            '/products/<int:product_id>': 'Delete the product by its id (DELETE)',
            '/customers': 'Create a new customer account (POST)',
            '/administrators': 'Create a new admin account (POST)',
            '/login': 'Log into the system (POST)',
            '/customers/update_email': 'Update email for customer (PATCH)',
            '/customers/verify_password': 'Verify password for customer (POST)',
            '/customers/update_password': 'Update password for customer (PATCH)',
            '/customers/update_phone': 'Update phone number for customer (PATCH)',
            '/administrators/update_email': 'Update email for admin (PATCH)',
            '/administrators/verify_password': 'Verify password for admin (POST)',
            '/administrators/update_password': 'Update password for admin (PATCH)',
            '/administrators/<int:admin_id>': 'Delete account for admin  (DELETE)',
            '/customers/<int:customer_id>': 'Delete account for customer (DELETE)',
            '/customers/<int:customer_id>': 'Get data for customers (GET)',
            '/customers/<int:customer_id>/addresses': 'Get all addresses for customer (GET)',
            '/addresses/<int:address_id>': 'Get address for customer by id (GET)',
            '/update_address': 'Update address for customer (PATCH)',
            '/add_address': 'Add new address for customer (POST)',
            '/delete_address/<int:address_id>': 'Delete address for customer (DELETE)',
            '/orders': 'Create order (POST)',
            '/orders/user/<int:user_id>': 'Get all orders for customer (GET)',
            '/orders/user/number/<string:order_number>': 'Get order details for customer (GET)',
            '/orders/admin': 'Get all orders (GET)',
            '/orders/mark-seen/<string:order_number>': 'Update column seen for orders (PATCH)',
            '/orders/admin/number/<string:order_number>': 'Get all orders (GET)',
            '/admin/customers': 'Get all customers (GET)',
            '/transactions': 'Save transactions in the database (POST)'
        }})


@app.route('/upload_image', methods=['POST'])
def upload_image():
    products_id = request.form.get('products_id')
    images = [request.files.get(f'image_product_{i}') for i in range(3)]  

    if not products_id:
        return jsonify({"message": "Product ID is required"}), 400

    CLIENT_ID = '3f7e2edaa33b9c8'
    
    for image_product in images:
        if image_product:
            image_data = base64.b64encode(image_product.read()).decode('utf-8')
            image_product.seek(0)

            headers = {'Authorization': f'Client-ID {CLIENT_ID}'}
            response = requests.post("https://api.imgur.com/3/image", headers=headers, data={'image': image_data})

            if response.status_code == 200:
                img_url = json.loads(response.text)['data']['link']

                cursor = mysql.connection.cursor()
                cursor.execute("INSERT INTO images (images_url, images_products_id) VALUES (%s, %s)", (img_url, products_id))
                mysql.connection.commit()
                cursor.close()
            else:
                return jsonify({"message": "Image upload failed", "error": response.text}), response.status_code
        
    return jsonify({"message": "Images uploaded successfully"}), 200


@app.route('/products', methods=['POST'])
def add_product():
    data = request.form
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO products (products_name, products_category, products_description, products_material, products_quantity, products_price) VALUES (%s, %s, %s, %s, %s, %s)",
                (data['products_name'], data['products_category'], data['products_description'], data['products_material'], data['products_quantity'], data['products_price']))
    mysql.connection.commit()
    products_id = cur.lastrowid  
    cur.close()
    
    return jsonify({'message': 'Product added', 'products_id': products_id}), 201


@app.route('/products', methods=['GET'])
def get_products():
    category = request.args.get('category')
    page = request.args.get('page', default=1, type=int) 
    limit = 20  
    offset = (page - 1) * limit 
    cur = mysql.connection.cursor()

    query = """
    SELECT p.products_id, p.products_name, p.products_category, p.products_description,
           p.products_material, p.products_quantity, p.products_price,
           p.products_price_discounted_10, p.products_price_discounted_20,
           i.images_url
    FROM products p
    LEFT JOIN images i ON p.products_id = i.images_products_id
    """

    if category:
        query += " WHERE p.products_category = %s ORDER BY p.products_id DESC LIMIT %s OFFSET %s"
        cur.execute(query, (category, limit, offset))
    else:
        query += " ORDER BY p.products_id DESC LIMIT %s OFFSET %s"
        cur.execute(query, (limit, offset))

    result = cur.fetchall()
    cur.close()

    products = {}
    for row in result:
        product_id = row[0]
        if product_id not in products:
            products[product_id] = {
                'products_id': row[0],
                'products_name': row[1],
                'products_category': row[2],
                'products_description': row[3],
                'products_material': row[4],
                'products_quantity': row[5],
                'products_price': row[6],
                'products_price_discounted_10': row[7],
                'products_price_discounted_20': row[8],
                'image_product': []
            }

        if row[9] is not None:
            products[product_id]['image_product'].append(row[9])

    products_list = list(products.values())

    cur = mysql.connection.cursor()
    total_query = "SELECT COUNT(*) FROM products"
    if category:
        total_query += " WHERE products_category = %s"
        cur.execute(total_query, (category,))
    else:
        cur.execute(total_query)

    total_count = cur.fetchone()[0]
    cur.close()
    
    return jsonify({'products': products_list, 'total': total_count})



@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    cur = mysql.connection.cursor()
   
    query = """
        SELECT p.*, i.images_url 
        FROM products p 
        LEFT JOIN images i ON p.products_id = i.images_products_id 
        WHERE p.products_id = %s
    """
    cur.execute(query, (product_id,))
    rows = cur.fetchall()
    cur.close()
    
    if rows:
        product = {
            'products_id': rows[0][0],
            'products_name': rows[0][1],
            'products_category': rows[0][2],
            'products_description': rows[0][3],
            'products_material': rows[0][4],
            'products_quantity': rows[0][5],
            'products_price': rows[0][6],
            'products_price_discounted_10': rows[0][7],
            'products_price_discounted_20': rows[0][8],
            'image_product': []
        }
        
        for row in rows:
            if row[9]:  
                product['image_product'].append(row[9])
        
        return jsonify({'product': product})
    
    return jsonify({'message': 'Product not found'}), 404


@app.route('/products/<int:product_id>', methods=['PATCH'])
def update_product(product_id):
    data = request.form
    cur = mysql.connection.cursor()

    update_fields = []
    update_values = []
    valid_fields = [
        'products_name', 
        'products_category', 
        'products_description', 
        'products_material', 
        'products_quantity', 
        'products_price'
    ]

    for key in valid_fields:
        if key in data:
            update_fields.append(f"{key} = %s")
            update_values.append(data[key])

    if update_fields:
        update_query = ", ".join(update_fields)
        cur.execute(f"UPDATE products SET {update_query} WHERE products_id = %s", (*update_values, product_id))
        mysql.connection.commit()

    existing_images = []
    cur.execute("SELECT images_url FROM images WHERE images_products_id = %s", (product_id,))
    existing_images = cur.fetchall()
    existing_images_urls = {img[0] for img in existing_images}

    for i in range(3):  
        image_file = request.files.get(f'image_product_{i}')
        if image_file:
            if image_file.mimetype in ['image/jpeg', 'image/png']:
                image_data = image_file.read()

                CLIENT_ID = '3f7e2edaa33b9c8'
                headers = {'Authorization': f'Client-ID {CLIENT_ID}'}
                response = requests.post("https://api.imgur.com/3/image", headers=headers, files={'image': image_data})

                if response.status_code == 200:
                    img_url = json.loads(response.text)['data']['link']

                    if img_url not in existing_images_urls:
                        cur.execute("INSERT INTO images (images_url, images_products_id) VALUES (%s, %s)", (img_url, product_id))
                        mysql.connection.commit()
                else:
                    return jsonify({"message": "Image upload failed", "error": response.text}), response.status_code
            else:
                return jsonify({"message": "Unsupported file type!"}), 400

    cur.close()
    return jsonify({'message': 'Product updated'}), 200


@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM products WHERE products_id = %s", (product_id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Product deleted successfully'}), 200



@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.json
    first_name = data['first_name']
    surname = data['surname']
    email = data['email']
    password = data['password']

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    street_one = data['address']['street_one']
    street_two = data['address']['street_two']
    city = data['address']['city']
    province = data['address']['province']
    country = data['address']['country']
    postal_code = data['address']['postal_code']
    
    phone_number = data['contact']['phone_number']

    try:
        cur = mysql.connection.cursor()

        cur.execute('SELECT * FROM customers WHERE customers_email = %s', (email,))
        if cur.fetchone():
            return jsonify({'error': 'Email already exists'}), 409
        
        cur.execute('INSERT INTO customers (customers_first_name, customers_surname, customers_email, customers_password) VALUES (%s, %s, %s, %s)', (first_name, surname, email, hashed_password))
        customer_id = cur.lastrowid
        
        cur.execute('INSERT INTO addresses (addresses_street_one, addresses_street_two, addresses_city, addresses_province, addresses_country, addresses_postal_code, addresses_customers_id) VALUES (%s, %s, %s, %s, %s, %s, %s)', (street_one, street_two, city, province, country, postal_code, customer_id))
        
        cur.execute('INSERT INTO contacts (contacts_phone_number, contacts_customers_id) VALUES (%s, %s)', (phone_number, customer_id))

        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Customer added successfully', 'customer_id': customer_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/administrators', methods=['POST'])
def add_administrator():
    data = request.json
    first_name = data['first_name']
    surname = data['surname']
    email = data['email']
    password = data['password']

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cur = mysql.connection.cursor()

        cur.execute('SELECT * FROM administrators WHERE administrators_email = %s', (email,))
        if cur.fetchone():
            return jsonify({'error': 'Email already exists'}), 409

        cur.execute('INSERT INTO administrators (administrators_first_name, administrators_surname, administrators_email, administrators_password) VALUES (%s, %s, %s, %s)', (first_name, surname, email, hashed_password))
        admin_id = cur.lastrowid

        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Administrator added successfully', 'admin_id': admin_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM customers WHERE customers_email = %s', (email,))
    customer = cur.fetchone()

    if customer and bcrypt.checkpw(password.encode('utf-8'), customer[4].encode('utf-8')):  
        return jsonify({
            'role': 'USER',
            'first_name': customer[1],  
            'id': customer[0]         
        }), 200

    cur.execute('SELECT * FROM administrators WHERE administrators_email = %s', (email,))
    admin = cur.fetchone()

    if admin and bcrypt.checkpw(password.encode('utf-8'), admin[4].encode('utf-8')):  
        return jsonify({
            'role': 'ADMIN',
            'first_name': admin[1],     
            'id': admin[0]              
        }), 200

    return jsonify({'error': 'Invalid login credentials'}), 401

@app.route('/customers/update_email', methods=['PATCH'])
def update_customer_email():
    data = request.get_json()

    customer_id = data.get('customers_id')
    email = data.get('customers_email')

    if not customer_id or not email:
        return jsonify({'error': 'Missing customer_id or customers_email'}), 400

    try:
        cur = mysql.connection.cursor()
        
        cur.execute("""
            UPDATE customers 
            SET customers_email = %s 
            WHERE customers_id = %s
        """, (email, customer_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Customer not found'}), 404

        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Customer email updated successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400
    
@app.route('/customers/verify_password', methods=['POST'])
def verify_customer_password():
    data = request.get_json()
    customers_id = data.get('customers_id')
    entered_password = data.get('customers_password')

    if not customers_id or not entered_password:
        return jsonify({'isValid': False, 'message': 'ID or password not provided.'}), 400

    cursor = mysql.connection.cursor()
    
    cursor.execute("SELECT customers_password FROM customers WHERE customers_id = %s", (customers_id,))
    user = cursor.fetchone()

    if user is None:
        return jsonify({'isValid': False, 'message': 'User not found.'}), 404

    stored_password_hash = user[0]
    
    if bcrypt.checkpw(entered_password.encode('utf-8'), stored_password_hash.encode('utf-8')):
        return jsonify({'isValid': True}), 200
    else:
        return jsonify({'isValid': False, 'message': 'Invalid password.'}), 401

@app.route('/customers/update_password', methods=['PATCH'])
def update_customer_password():
    data = request.get_json()

    customer_id = data.get('customers_id')
    password = data.get('customers_password')

    if not customer_id or not password:
        return jsonify({'error': 'Missing customers_id or customers_password'}), 400

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cur = mysql.connection.cursor()
        
        cur.execute("""
            UPDATE customers 
            SET customers_password = %s 
            WHERE customers_id = %s
        """, (hashed_password, customer_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Customer not found'}), 404

        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Customer password updated successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400
    
@app.route('/customers/update_phone', methods=['PATCH'])
def update_customer_phone():
    data = request.get_json()

    customer_id = data.get('customers_id')
    phone_number = data.get('customers_phone_number')

    if not customer_id or not phone_number:
        return jsonify({'error': 'Missing customers_id or customers_phone_number'}), 400

    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            UPDATE contacts 
            SET contacts_phone_number = %s 
            WHERE contacts_customers_id = %s
        """, (phone_number, customer_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Customer not found or phone number not updated'}), 404

        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Customer phone number updated successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400
    
@app.route('/administrators/update_email', methods=['PATCH'])
def update_administrator_email():
    data = request.get_json()

    administrator_id = data.get('administrators_id')
    email = data.get('administrators_email')

    if not administrator_id or not email:
        return jsonify({'error': 'Missing administrators_id or administrators_email'}), 400

    try:
        cur = mysql.connection.cursor()
        
        cur.execute("""
            UPDATE administrators 
            SET administrators_email = %s 
            WHERE administrators_id = %s
        """, (email, administrator_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Administrator not found'}), 404

        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Administrator email updated successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/administrators/verify_password', methods=['POST'])
def verify_administrator_password():
    data = request.get_json()
    administrators_id = data.get('administrators_id')
    entered_password = data.get('administrators_password')

    if not administrators_id or not entered_password:
        return jsonify({'isValid': False, 'message': 'ID or password not provided.'}), 400

    cursor = mysql.connection.cursor()
    
    cursor.execute("SELECT administrators_password FROM administrators WHERE administrators_id = %s", (administrators_id,))
    user = cursor.fetchone()

    if user is None:
        return jsonify({'isValid': False, 'message': 'User not found.'}), 404

    stored_password_hash = user[0]
    
    if bcrypt.checkpw(entered_password.encode('utf-8'), stored_password_hash.encode('utf-8')):
        return jsonify({'isValid': True}), 200
    else:
        return jsonify({'isValid': False, 'message': 'Invalid password.'}), 401
    
@app.route('/administrators/update_password', methods=['PATCH'])
def update_administrator_password():
    data = request.get_json()

    administrator_id = data.get('administrators_id')
    password = data.get('administrators_password')

    if not administrator_id or not password:
        return jsonify({'error': 'Missing administrators_id or administrators_password'}), 400

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cur = mysql.connection.cursor()
        
        cur.execute("""
            UPDATE administrators 
            SET administrators_password = %s 
            WHERE administrators_id = %s
        """, (hashed_password, administrator_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Administrator not found'}), 404

        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Administrator password updated successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/administrators/<int:admin_id>', methods=['DELETE'])
def delete_administrator(admin_id):
    try:
        cur = mysql.connection.cursor()
        
        cur.execute('DELETE FROM administrators WHERE administrators_id = %s', (admin_id,))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Administrator deleted successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        cur = mysql.connection.cursor()
        
        cur.execute('DELETE FROM customers WHERE customers_id = %s', (customer_id,))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Customer deleted successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400
    

@app.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    cur = mysql.connection.cursor()
    
    query = """
    SELECT c.customers_id, c.customers_first_name, c.customers_surname, c.customers_email,
           ct.contacts_phone_number
    FROM customers c
    LEFT JOIN contacts ct ON c.customers_id = ct.contacts_customers_id
    WHERE c.customers_id = %s
    """
    cur.execute(query, (customer_id,))
    result = cur.fetchone()
    cur.close()
    
    if result:
        customer = {
            'customer_id': result[0],
            'first_name': result[1],
            'surname': result[2],
            'email': result[3],
            'contact': {
                'phone_number': result[4]
            }
        }
        return jsonify({'customer': customer}), 200
    else:
        return jsonify({'message': 'Customer not found'}), 404
    
@app.route('/customers/<int:customer_id>/addresses', methods=['GET'])
def get_addresses(customer_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM addresses WHERE addresses_customers_id = %s", (customer_id,))
        addresses = cur.fetchall()
        cur.close()

        address_list = []
        for address in addresses:
            address_list.append({
                'id': address[0],
                'street_one': address[1],
                'street_two': address[2],
                'city': address[3],
                'province': address[4],
                'country': address[5],
                'postal_code': address[6],
                'customer_id': address[7],
            })

        return jsonify({'addresses': address_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/addresses/<int:address_id>', methods=['GET'])
def get_address(address_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM addresses WHERE addresses_id = %s", (address_id,))
        address = cur.fetchone()
        cur.close()

        if address:
            return jsonify({
                'id': address[0],
                'street_one': address[1],
                'street_two': address[2],
                'city': address[3],
                'province': address[4],
                'country': address[5],
                'postal_code': address[6],
                'customer_id': address[7],
            }), 200
        else:
            return jsonify({'error': 'Address not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/update_address', methods=['PATCH'])
def update_address():
    data = request.get_json()

    address_id = data.get('address_id')  
    street_one = data.get('addresses_street_one')
    street_two = data.get('addresses_street_two')
    city = data.get('addresses_city')
    province = data.get('addresses_province')
    country = data.get('addresses_country')
    postal_code = data.get('addresses_postal_code')

    try:
        cur = mysql.connection.cursor()
        
        cur.execute(""" 
            UPDATE addresses 
            SET addresses_street_one = %s, addresses_street_two = %s, 
                addresses_city = %s, addresses_province = %s, 
                addresses_country = %s, addresses_postal_code = %s 
            WHERE addresses_id = %s  -- Додайте умову для адреси
        """, (street_one, street_two, city, province, country, postal_code, address_id))

        mysql.connection.commit()
        
        cur.close()
        
        return jsonify({'message': 'Address updated successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/add_address', methods=['POST'])
def add_address():
    data = request.get_json()

    street_one = data.get('addresses_street_one')
    street_two = data.get('addresses_street_two')
    city = data.get('addresses_city')
    province = data.get('addresses_province')
    country = data.get('addresses_country')
    postal_code = data.get('addresses_postal_code')
    customer_id = data.get('customers_id')  

    try:
        cur = mysql.connection.cursor()
        
        cur.execute(""" 
            INSERT INTO addresses (addresses_street_one, addresses_street_two, 
                                   addresses_city, addresses_province, 
                                   addresses_country, addresses_postal_code, 
                                   addresses_customers_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (street_one, street_two, city, province, country, postal_code, customer_id))

        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Address added successfully!'}), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400
    
@app.route('/delete_address/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("""
            DELETE FROM addresses 
            WHERE addresses_id = %s
        """, (address_id,))

        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Address deleted successfully!'}), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    orders_number = data['orders_number']
    orders_products_id = data['orders_products_id']
    orders_product_quantity = data['orders_product_quantity']
    orders_customers_id = data['orders_customers_id']
    orders_addresses_id = data['orders_addresses_id']
    orders_total_price = data['orders_total_price']
    orders_transactions_id = data['orders_transactions_id']

    cur = mysql.connection.cursor()

    for product_id, quantity in zip(orders_products_id, orders_product_quantity):
        cur.execute("""
            INSERT INTO orders (orders_number, orders_products_id, orders_product_quantity, orders_customers_id, orders_addresses_id, orders_total_price, orders_transactions_id, orders_date, orders_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (orders_number, product_id, quantity, orders_customers_id, orders_addresses_id, orders_total_price, orders_transactions_id, 0))

        cur.execute("""
            UPDATE products 
            SET products_quantity = products_quantity - %s 
            WHERE products_id = %s
        """, (quantity, product_id))

    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Order created successfully!'}), 201

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 15
        offset = (page - 1) * per_page

        cur = mysql.connection.cursor()
        query = """
            SELECT 
                orders_number, 
                orders_total_price, 
                orders_date
            FROM 
                orders
            WHERE 
                orders_customers_id = %s
            GROUP BY 
                orders_number, orders_total_price, orders_date
            ORDER BY 
                orders_date DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (user_id, per_page, offset))
        orders = cur.fetchall()
        cur.close()

        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(DISTINCT orders_number) FROM orders WHERE orders_customers_id = %s", (user_id,))
        total = cur.fetchone()[0]
        cur.close()

        return jsonify({
            'orders': [{
                'order_number': order[0],
                'total_price': order[1],
                'date': order[2].isoformat()
            } for order in orders],
            'total': total
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/orders/user/number/<string:order_number>', methods=['GET'])
def get_order_details_by_number(order_number):
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT orders_id, orders_total_price, orders_addresses_id
            FROM orders
            WHERE orders_number = %s
        """, (order_number,))
        orders = cur.fetchall()
        
        if not orders:
            return jsonify({'error': 'Order not found'}), 404
        
        address_id = orders[0][2]
        
        cur.execute("SELECT * FROM addresses WHERE addresses_id = %s", (address_id,))
        address = cur.fetchone()
        
        products = []
        for order in orders:
            order_id = order[0]
            cur.execute("""
                SELECT products.products_id, products.products_name, products.products_price, orders.orders_product_quantity
                FROM products
                JOIN orders ON products.products_id = orders.orders_products_id
                WHERE orders.orders_id = %s
            """, (order_id,))
            products.extend(cur.fetchall())
        
        cur.close()
        
        return jsonify({
            'order_number': order_number,
            'total_price': orders[0][1],  
            'address': {
                'id': address[0],
                'street_one': address[1],
                'street_two': address[2],
                'city': address[3],
                'province': address[4],
                'country': address[5],
                'postal_code': address[6]
            },
            'products': [{
                'id': product[0],
                'name': product[1],
                'price': product[2],
                'quantity': product[3]
            } for product in products]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/orders/admin', methods=['GET'])
def get_all_orders():
    try:
        page = request.args.get('page', 1, type=int)  
        per_page = 15  
        offset = (page - 1) * per_page  

        cur = mysql.connection.cursor()
        cur.execute(f"""
            SELECT orders_number, orders_total_price, orders_date, orders_seen
            FROM orders
            GROUP BY orders_number, orders_total_price, orders_date, orders_seen
            ORDER BY orders_date DESC
            LIMIT {per_page} OFFSET {offset}
        """)
        orders = cur.fetchall()
        cur.close()

        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(DISTINCT orders_number) FROM orders")
        total = cur.fetchone()[0]
        cur.close()

        return jsonify({
            'orders': [{
                'order_number': order[0],
                'total_price': order[1],
                'date': order[2].isoformat(),
                'seen': order[3]
            } for order in orders],
            'total': total
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400




@app.route('/orders/mark-seen/<string:order_number>', methods=['PATCH'])
def mark_order_as_seen(order_number):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE orders
            SET orders_seen = TRUE  # Виправлено на orders_seen
            WHERE orders_number = %s
        """, (order_number,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Order marked as seen'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/orders/admin/number/<string:order_number>', methods=['GET'])
def get_order_details_by_number_for_admin(order_number):
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT orders_id, orders_total_price, orders_addresses_id, orders_customers_id, orders_transactions_id
            FROM orders
            WHERE orders_number = %s
        """, (order_number,))
        orders = cur.fetchall()
        
        if not orders:
            return jsonify({'error': 'Order not found'}), 404
        
        order_id = orders[0][0]
        address_id = orders[0][2]
        customer_id = orders[0][3]
        transaction_id = orders[0][4]
        
        cur.execute("SELECT * FROM addresses WHERE addresses_id = %s", (address_id,))
        address = cur.fetchone()
        
        cur.execute("SELECT customers_first_name, customers_surname, customers_email FROM customers WHERE customers_id = %s", (customer_id,))
        customer = cur.fetchone()
        
        cur.execute("SELECT contacts_phone_number FROM contacts WHERE contacts_customers_id = %s", (customer_id,))
        contact = cur.fetchone()
        
        cur.execute("""
            SELECT products.products_id, products.products_name, products.products_price, orders.orders_product_quantity
            FROM orders
            JOIN products ON products.products_id = orders.orders_products_id
            WHERE orders.orders_number = %s
        """, (order_number,))
        products = cur.fetchall()
        
        cur.close()
        
        return jsonify({
            'order_number': order_number,
            'total_price': orders[0][1],
            'customer': {
                'first_name': customer[0],
                'surname': customer[1],
                'email': customer[2]
            },
            'contact': {
                'phone_number': contact[0] if contact else None
            },
            'transaction': {
                'number': transaction_id,
                'amount': orders[0][1]
            },
            'address': {
                'id': address[0],
                'street_one': address[1],
                'street_two': address[2],
                'city': address[3],
                'province': address[4],
                'country': address[5],
                'postal_code': address[6]
            },
            'products': [{
                'id': product[0],
                'name': product[1],
                'price': product[2],
                'quantity': product[3]
            } for product in products]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/admin/customers', methods=['GET'])
def get_customers():
    page = request.args.get('page', default=1, type=int)  
    limit = 20  
    offset = (page - 1) * limit  

    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT 
                c.customers_id,
                c.customers_first_name,
                c.customers_surname,
                c.customers_email,
                con.contacts_phone_number,
                COUNT(DISTINCT o.orders_number) AS order_count,
                SUM(o.orders_total_price) AS total_spent
            FROM customers AS c
            LEFT JOIN contacts AS con ON c.customers_id = con.contacts_customers_id
            LEFT JOIN orders AS o ON c.customers_id = o.orders_customers_id
            GROUP BY 
                c.customers_id,
                c.customers_first_name, 
                c.customers_surname, 
                c.customers_email,
                con.contacts_phone_number
            ORDER BY c.customers_first_name, c.customers_surname
            LIMIT %s OFFSET %s
        """, (limit, offset))

        customers = cur.fetchall()

        result = []
        for row in customers:
            customer_info = {
                'full_name': f"{row[1]} {row[2]}",
                'email': row[3],
                'phone_number': row[4],
                'order_count': row[5] or 0,
                'total_spent': float(row[6]) if row[6] is not None else 0.0  
            }
            
            cur.execute("""
                SELECT 
                    CONCAT(addresses_street_one, ', ', addresses_street_two, ', ', addresses_city, ', ', addresses_province, ', ', addresses_country, ', ', addresses_postal_code) AS full_address
                FROM addresses 
                WHERE addresses_customers_id = %s
            """, (row[0],))
            addresses = cur.fetchall()
            customer_info['address'] = '<br />'.join([addr[0] for addr in addresses]) if addresses else ""

            result.append(customer_info)

        cur.close()
        
        cur = mysql.connection.cursor()
        total_query = "SELECT COUNT(*) FROM customers"
        cur.execute(total_query)
        total_count = cur.fetchone()[0]
        cur.close()
        
        return jsonify({'customers': result, 'total': total_count}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@app.route('/transactions', methods=['POST'])
def create_payment():
    data = request.json

    payer_name = data.get('payer_name')
    payer_email = data.get('payer_email')
    transaction_id = data.get('transaction_id')
    amount = data.get('amount')

    cursor = mysql.connection.cursor()
    cursor.execute('''INSERT INTO transactions (transactions_payer_name, transactions_payer_email, transactions_number, transactions_amount)
                      VALUES (%s, %s, %s, %s)''',
                   (payer_name, payer_email, transaction_id, amount))

    mysql.connection.commit()
    transaction_id_db = cursor.lastrowid  
    cursor.close()

    return jsonify({"success": True, "transaction_id": transaction_id_db}), 201  


if __name__ == '__main__':
    app.run(debug=True)


