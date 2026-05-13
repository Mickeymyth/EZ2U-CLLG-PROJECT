from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="soterisalone"
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        print("Login attempt received")
        print("Username:", username)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute(
                "SELECT * FROM public.users2 WHERE username=%s AND password=%s",
                (username, password)
            )

            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                session['user_id'] = user['id']
                session['username'] = username
                session['role'] = user.get('role', 'Employee')
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid username or password')

        except Exception as e:
            return render_template('login.html', error=f'Database error: {str(e)}')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_role = session.get('role', 'Employee')
    username = session.get('username', 'User')
    return render_template('pktdash.html', user_role=user_role, username=username)


@app.route('/dcmodule')
def dcmodule():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_role = session.get('role', 'Employee')
    username = session.get('username', 'User')
    return render_template('dcmodule.html', user_role=user_role, username=username)


@app.route('/fssmodule')
def fssmodule():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_role = session.get('role', 'Employee')
    username = session.get('username', 'User')
    return render_template('fssmodule.html', user_role=user_role, username=username)

@app.route('/vendormodule')
def vendormodule():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_role = session.get('role', 'Employee')
    username = session.get('username', 'User')
    if user_role != 'Admin':
        return redirect(url_for('dashboard'))
    return render_template('vendormodule.html', user_role=user_role, username=username)

@app.route('/addvendor', methods=['GET', 'POST'])
def addvendor():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_role = session.get('role', 'Employee')
    if user_role != 'Admin':
        return redirect(url_for('dashboard'))

    message = None
    error = None

    if request.method == 'POST':
        name = request.form.get('receiver_name')
        address = request.form.get('receiver_address')
        gst = request.form.get('receiver_gst')
        phone = request.form.get('receiver_phone')
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.receiver (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    address TEXT,
                    gst TEXT,
                    phone TEXT
                )
            """)
            cur.execute("""
                INSERT INTO public.receiver (name, address, gst, phone)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    address = EXCLUDED.address,
                    gst = EXCLUDED.gst,
                    phone = EXCLUDED.phone
            """, (name, address, gst, phone))
            conn.commit()
            cur.close()
            conn.close()
            message = "Vendor saved successfully."
        except Exception as e:
            error = f"Error saving vendor: {str(e)}"

    return render_template('addvendor.html', user_role=user_role, message=message, error=error)

@app.route('/managevendor', methods=['GET', 'POST'])
def managevendor():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_role = session.get('role', 'Employee')
    if user_role != 'Admin':
        return redirect(url_for('dashboard'))

    message = None
    error = None
    vendors = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.receiver (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                address TEXT,
                gst TEXT,
                phone TEXT
            )
        """)
        if request.method == 'POST':
            action = request.form.get('action')
            name = request.form.get('vendor_name')
            if action == 'update':
                address = request.form.get('vendor_address')
                gst = request.form.get('vendor_gst')
                phone = request.form.get('vendor_phone')
                cur.execute("""
                    UPDATE public.receiver
                    SET address = %s, gst = %s, phone = %s
                    WHERE name = %s
                """, (address, gst, phone, name))
                conn.commit()
                message = "Vendor updated successfully."
            elif action == 'delete':
                cur.execute("DELETE FROM public.receiver WHERE name = %s", (name,))
                conn.commit()
                if cur.rowcount > 0:
                    message = "Vendor deleted successfully."
                else:
                    error = "Vendor not found."

        cur.execute("SELECT name FROM public.receiver ORDER BY name")
        vendors = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
    except Exception as e:
        error = f"Error loading vendors: {str(e)}"

    return render_template('managevendor.html', user_role=user_role, vendors=vendors, message=message, error=error)

@app.route('/createdc', methods=['GET', 'POST'])
def createdc():
    if 'username' not in session:
        return redirect(url_for('login'))

    sender = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.sender (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                address TEXT,
                gst TEXT,
                phone TEXT
            )
        """)
        cur.execute("SELECT name, address, gst, phone FROM public.sender ORDER BY id ASC LIMIT 1")
        sender = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error loading sender: {str(e)}")

    if request.method == 'POST':
        if not sender:
            flash("Sender details not configured. Please add sender in the database first.", 'error')
            return redirect(url_for('createdc'))
        sender_name = sender.get('name')
        sender_address = sender.get('address')
        sender_gst = sender.get('gst')
        sender_phone = sender.get('phone')

        receiver_name = request.form.get('receiver_name')
        receiver_address = request.form.get('receiver_address')
        receiver_gst = request.form.get('receiver_gst')
        receiver_phone = request.form.get('receiver_phone')

        department = request.form.get('department')
        dispatch_method = request.form.get('dispatch_method')
        expected_return_date = request.form.get('expected_return_date') or None
        remarks = request.form.get('remarks')

        # collect items from form arrays
        item_names = request.form.getlist('item_name[]')
        item_hsns = request.form.getlist('item_hsn[]')
        item_qtys = request.form.getlist('item_qty[]')
        item_units = request.form.getlist('item_unit[]')
        item_prices = request.form.getlist('item_price[]')
        item_descs = request.form.getlist('item_desc[]')

        created_by = session['username']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # ensure dc table has remarks column
            cur.execute("ALTER TABLE public.dc ADD COLUMN IF NOT EXISTS remarks text")
            # ensure dc table has expected return date column
            cur.execute("ALTER TABLE public.dc ADD COLUMN IF NOT EXISTS expected_return_date DATE")
            # ensure dc table has sender phone column
            cur.execute("ALTER TABLE public.dc ADD COLUMN IF NOT EXISTS sender_phone TEXT")
            # ensure sender table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.sender (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    address TEXT,
                    gst TEXT,
                    phone TEXT
                )
            """)
            # ensure receiver table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.receiver (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    address TEXT,
                    gst TEXT,
                    phone TEXT
                )
            """)
            # ensure items table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.dc_items (
                    id SERIAL PRIMARY KEY,
                    dc_id INTEGER REFERENCES public.dc(id),
                    item_name TEXT,
                    hsn TEXT,
                    quantity INTEGER,
                    unit TEXT,
                    price DECIMAL(10,2),
                    description TEXT
                )
            """)
            # Add columns if not exist
            cur.execute("ALTER TABLE public.dc_items ADD COLUMN IF NOT EXISTS hsn TEXT")
            cur.execute("ALTER TABLE public.dc_items ADD COLUMN IF NOT EXISTS price DECIMAL(10,2)")

            # Generate unique DC number
            cur.execute("SELECT COUNT(*) FROM public.dc")
            dc_count = cur.fetchone()[0] + 1
            dc_number = f"PKT-{dc_count}"

            cur.execute("""
                INSERT INTO public.dc (
                    dc_number, sender_name, sender_address, sender_gst, sender_phone,
                    receiver_name, receiver_address, receiver_gst, receiver_phone,
                    department, dispatch_method, expected_return_date, remarks, created_by
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (
                dc_number, sender_name, sender_address, sender_gst, sender_phone,
                receiver_name, receiver_address, receiver_gst, receiver_phone,
                department, dispatch_method, expected_return_date, remarks, created_by
            ))

            dc_id = cur.fetchone()[0]  # newly created DC id

            # upsert receiver record
            if receiver_name:
                cur.execute("""
                    INSERT INTO public.receiver (name, address, gst, phone)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        address = EXCLUDED.address,
                        gst = EXCLUDED.gst,
                        phone = EXCLUDED.phone
                """, (receiver_name, receiver_address, receiver_gst, receiver_phone))

            # insert item rows if any
            for name, hsn, qty, unit, price, desc in zip(item_names, item_hsns, item_qtys, item_units, item_prices, item_descs):
                if name and qty:
                    cur.execute(
                        "INSERT INTO public.dc_items (dc_id, item_name, hsn, quantity, unit, price, description) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (dc_id, name, hsn, qty, unit, price, desc)
                    )

            conn.commit()
            cur.close()
            conn.close()

            flash(f"Delivery Challan '{dc_number}' submitted successfully!", 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f"Error saving DC: {str(e)}", 'error')
            return redirect(url_for('createdc'))

    # Generate preview DC number for display on form load
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM public.dc")
        dc_count = cur.fetchone()[0] + 1
        preview_dc_number = f"PKT-{dc_count}"
        cur.close()
        conn.close()
    except:
        preview_dc_number = "PKT-1"

    return render_template('createdc.html', dc_number=preview_dc_number, sender=sender)

@app.route('/api/sender')
def get_sender():
    if 'username' not in session:
        return {}, 401

    name = request.args.get('name')
    if not name:
        return {}, 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT name, address, gst, phone FROM public.sender WHERE name ILIKE %s LIMIT 1",
            (name,)
        )
        sender = cur.fetchone()
        cur.close()
        conn.close()
        if not sender:
            return {}, 404
        return sender
    except Exception as e:
        print(f"Error fetching sender: {str(e)}")
        return {}, 500

@app.route('/api/receiver')
def get_receiver():
    if 'username' not in session:
        return {}, 401

    name = request.args.get('name')
    if not name:
        return {}, 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT name, address, gst, phone FROM public.receiver WHERE name ILIKE %s LIMIT 1",
            (name,)
        )
        receiver = cur.fetchone()
        cur.close()
        conn.close()
        if not receiver:
            return {}, 404
        return receiver
    except Exception as e:
        print(f"Error fetching receiver: {str(e)}")
        return {}, 500

@app.route('/api/sender-names')
def get_sender_names():
    if 'username' not in session:
        return [], 401
    q = request.args.get('q', '').strip()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if q:
            cur.execute(
                "SELECT name FROM public.sender WHERE name ILIKE %s ORDER BY name LIMIT 25",
                (f"%{q}%",)
            )
        else:
            cur.execute("SELECT name FROM public.sender ORDER BY name LIMIT 25")
        names = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return names
    except Exception as e:
        print(f"Error fetching sender names: {str(e)}")
        return [], 500

@app.route('/api/receiver-names')
def get_receiver_names():
    if 'username' not in session:
        return [], 401
    q = request.args.get('q', '').strip()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if q:
            cur.execute(
                "SELECT name FROM public.receiver WHERE name ILIKE %s ORDER BY name LIMIT 25",
                (f"%{q}%",)
            )
        else:
            cur.execute("SELECT name FROM public.receiver ORDER BY name LIMIT 25")
        names = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return names
    except Exception as e:
        print(f"Error fetching receiver names: {str(e)}")
        return [], 500

@app.route('/addfss', methods=['GET', 'POST'], strict_slashes=False)
def addfss():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        design = request.form.get('design')
        color = request.form.get('color')
        customer = request.form.get('customer')
        created_by = session['username']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO public.fss (design, color, customer, created_by)
                VALUES (%s, %s, %s, %s)
            """, (design, color, customer, created_by))

            conn.commit()
            cur.close()
            conn.close()

            flash(f"FSS with design '{design}' submitted successfully!", 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f"Error saving FSS: {str(e)}", 'error')
            return redirect(url_for('addfss'))

    return render_template('addfss.html')


@app.route('/users', methods=['GET', 'POST'])
def users():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('role', 'Employee')
    # Only Admin can access user management
    if user_role != 'Admin':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            if action == 'create':
                cur.execute(
                    "INSERT INTO public.users2 (username, password, role) VALUES (%s, %s, %s)",
                    (username, password, role)
                )
                conn.commit()
                flash(f"User '{username}' with role '{role}' created successfully!", 'success')
            
            elif action == 'delete':
                cur.execute(
                    "DELETE FROM public.users2 WHERE username=%s AND password=%s",
                    (username, password)
                )
                conn.commit()
                if cur.rowcount > 0:
                    flash(f"User '{username}' deleted successfully!", 'success')
                else:
                    flash(f"User '{username}' not found!", 'error')
            
            cur.close()
            conn.close()
            
            return redirect(url_for('users'))
        
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('users'))
    
    return render_template('users.html', user_role=user_role)

@app.route('/managedc', methods=['GET', 'POST'])
def managedc():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('role', 'Employee')
    # Only Admin and Manager can access manage DC
    if user_role == 'Employee':
        return redirect(url_for('dashboard'))
    
    message = None
    error = None
    search_results = None
    pending_dcs = None

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if request.method == 'POST':
            action = request.form.get('action')

            # Search DC
            if action == 'search':
                search_date = request.form.get('search_date')
                search_return_date = request.form.get('search_return_date')
                search_receiver = request.form.get('search_receiver')
                search_dc_number = request.form.get('search_dc_number')

                query = "SELECT * FROM public.dc WHERE 1=1"
                params = []

                if search_date:
                    query += " AND DATE(created_at) = %s"
                    params.append(search_date)

                if search_return_date:
                    query += " AND expected_return_date = %s"
                    params.append(search_return_date)

                if search_receiver:
                    query += " AND receiver_name ILIKE %s"
                    params.append(f"%{search_receiver}%")

                if search_dc_number:
                    query += " AND dc_number = %s"
                    params.append(search_dc_number)

                cur.execute(query, params)
                search_results = cur.fetchall()

                if not search_results:
                    flash("No delivery challans found matching your search criteria", 'info')

            # Approve DC
            elif action == 'approve':
                dc_id = request.form.get('dc_id')
                cur.execute(
                    "UPDATE public.dc SET status=%s WHERE id=%s",
                    ('Approved', dc_id)
                )
                conn.commit()
                flash("DC approved successfully!", 'success')

            # Reject DC
            elif action == 'reject':
                dc_id = request.form.get('dc_id')
                cur.execute(
                    "UPDATE public.dc SET status=%s WHERE id=%s",
                    ('Rejected', dc_id)
                )
                conn.commit()
                flash("DC rejected successfully!", 'error')

            # Delete DC
            elif action == 'delete':
                delete_dc_number = request.form.get('delete_dc_number')
                cur.execute(
                    "DELETE FROM public.dc WHERE dc_number=%s",
                    (delete_dc_number,)
                )
                conn.commit()

                if cur.rowcount > 0:
                    flash(f"DC '{delete_dc_number}' deleted successfully!", 'success')
                else:
                    flash(f"DC '{delete_dc_number}' not found!", 'error')

        # Fetch all pending DCs
        cur.execute("SELECT * FROM public.dc WHERE status IS NULL OR status = 'Pending' ORDER BY created_at DESC")
        pending_dcs = cur.fetchall()

        cur.close()
        conn.close()

    except Exception as e:
        flash(f"Error: {str(e)}", 'error')

    return render_template('managedc.html', 
                         search_results=search_results,
                         pending_dcs=pending_dcs,
                         user_role=user_role)

@app.route('/managefss', methods=['GET', 'POST'])
def managefss():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('role', 'Employee')
    # Only Admin and Manager can access manage FSS
    if user_role == 'Employee':
        return redirect(url_for('dashboard'))
    
    message = None
    error = None
    search_results = None

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if request.method == 'POST':
            action = request.form.get('action')

            # Search FSS
            if action == 'search':
                search_design = request.form.get('search_design')
                search_customer = request.form.get('search_customer')
                search_date = request.form.get('search_date')

                query = "SELECT * FROM public.fss WHERE 1=1"
                params = []

                if search_design:
                    query += " AND design ILIKE %s"
                    params.append(f"%{search_design}%")

                if search_customer:
                    query += " AND customer ILIKE %s"
                    params.append(f"%{search_customer}%")

                if search_date:
                    query += " AND DATE(created_at) = %s"
                    params.append(search_date)

                cur.execute(query, params)
                search_results = cur.fetchall()

                if not search_results:
                    flash("No FSS records found matching your search criteria", 'info')

            # Delete FSS
            elif action == 'delete':
                delete_fss_id = request.form.get('delete_fss_id')
                cur.execute(
                    "DELETE FROM public.fss WHERE id=%s",
                    (delete_fss_id,)
                )
                conn.commit()

                if cur.rowcount > 0:
                    flash(f"FSS ID '{delete_fss_id}' deleted successfully!", 'success')
                else:
                    flash(f"FSS ID '{delete_fss_id}' not found!", 'error')

        cur.close()
        conn.close()

    except Exception as e:
        flash(f"Error: {str(e)}", 'error')

    return render_template('managefss.html', 
                         search_results=search_results,
                         user_role=user_role)

@app.route('/api/dc/<dc_number>')
def get_dc(dc_number):
    # returns JSON with full details of a delivery challan, including sender/receiver and items
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM public.dc WHERE dc_number=%s", (dc_number,))
        dc = cur.fetchone()
        cur.close()
        conn.close()
        if not dc:
            return {}, 404
        # attempt to fetch items
        items = []
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT item_name AS name, hsn, quantity, unit, price, description FROM public.dc_items WHERE dc_id=%s", (dc['id'],))
            items = cur.fetchall()
            cur.close()
            conn.close()
        except Exception:
            items = []
        dc['items'] = items
        return dc
    except Exception as e:
        print(f"API error: {e}")
        return {}, 500


@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f"Logged out successfully! Goodbye {username}.", 'success')
    return redirect(url_for('index'))

@app.route('/api/dashboard-stats')
def dashboard_stats():
    if 'username' not in session:
        return {'total_dcs': 0, 'total_fss': 0}
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get total DCs created today
        cur.execute("""
            SELECT COUNT(*) FROM public.dc 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        total_dcs = cur.fetchone()[0]
        
        # Get total FSS records
        cur.execute("SELECT COUNT(*) FROM public.fss")
        total_fss = cur.fetchone()[0]

        # Get total goods returning today (expected return date)
        cur.execute("""
            SELECT COUNT(*) FROM public.dc
            WHERE expected_return_date = CURRENT_DATE
        """)
        total_returns = cur.fetchone()[0]
        
        # Get total users
        try:
            conn2 = get_db_connection()
            cur2 = conn2.cursor()
            cur2.execute("SELECT COUNT(*) FROM public.users2")
            total_users = cur2.fetchone()[0]
            cur2.close()
            conn2.close()
        except Exception:
            total_users = 0

        # Get total vendors (receivers)
        cur.execute("SELECT COUNT(*) FROM public.receiver")
        total_vendors = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return {
            'total_dcs': total_dcs,
            'total_fss': total_fss,
            'total_users': total_users,
            'total_returns': total_returns,
            'total_vendors': total_vendors
        }
    
    except Exception as e:
        print(f"Error fetching stats: {str(e)}")
        return {'total_dcs': 0, 'total_fss': 0, 'total_returns': 0, 'total_vendors': 0}

@app.route('/download_dc/<int:dc_id>')
def download_dc(dc_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Get DC data
        cur.execute("SELECT * FROM public.dc WHERE id = %s", (dc_id,))
        dc = cur.fetchone()
        if not dc:
            flash("DC not found", 'error')
            return redirect(url_for('managedc'))
        # Get items
        cur.execute("SELECT * FROM public.dc_items WHERE dc_id = %s", (dc_id,))
        items = cur.fetchall()
        cur.close()
        conn.close()

        # Prepare shared data
        company_name = dc['sender_name']
        company_address = dc['sender_address']
        company_gstin = dc['sender_gst']
        dc_number = dc['dc_number']
        customer_name = dc['receiver_name']
        customer_address = dc['receiver_address']
        customer_phone = dc['receiver_phone']
        customer_gstin = dc['receiver_gst']
        challan_date = dc.get('created_at', '').strftime('%Y-%m-%d') if dc.get('created_at') else "N/A"
        department = dc.get('department', 'N/A')
        dispatch_method = dc.get('dispatch_method', 'N/A')
        expected_return_date = dc.get('expected_return_date')
        expected_return_date = expected_return_date.strftime('%Y-%m-%d') if expected_return_date else "N/A"
        notes = dc.get('remarks', "")

        # Build HTML rows for template-driven PDF
        items_rows = ""
        for idx, item in enumerate(items, start=1):
            item_name = item.get('item_name', '')
            hsn = item.get('hsn', '')
            qty = item.get('quantity', '')
            unit = item.get('unit', '')
            price = item.get('price', '')
            desc = item.get('description', '')
            items_rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{item_name}</td>
                    <td>{hsn}</td>
                    <td>{qty}</td>
                    <td>{unit}</td>
                    <td>{price}</td>
                    <td>{desc}</td>
                </tr>
            """

        # Primary path: render HTML template to PDF
        try:
            html = render_template(
                'dc_pdf_template.html',
                company_name=company_name,
                company_address=company_address,
                company_gstin=company_gstin,
                dc_number=dc_number,
                customer_name=customer_name,
                customer_address=customer_address,
                customer_phone=customer_phone,
                customer_gstin=customer_gstin,
                challan_date=challan_date,
                department=department,
                dispatch_method=dispatch_method,
                expected_return_date=expected_return_date,
                notes=notes,
                items_rows=items_rows
            )

            from weasyprint import HTML
            pdf_data = HTML(string=html, base_url=request.url_root).write_pdf()
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename={dc_number}.pdf'
            return response
        except Exception:
            # If WeasyPrint isn't available, keep current reportlab behavior.
            pass

        # Fallback path: generate PDF using reportlab
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Logo
        logo_path = os.path.join(app.static_folder, 'lightmood_logo.jpeg')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=1.5*inch, height=0.5*inch)
            story.append(logo)
            story.append(Spacer(1, 12))

        # Title
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, textColor=colors.HexColor('#19a44b'))
        story.append(Paragraph("DELIVERY CHALLAN", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Delivery Challan# - {dc_number}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Company info
        story.append(Paragraph(f"Company Name: {company_name}", styles['Normal']))
        story.append(Paragraph(f"Address: {company_address}", styles['Normal']))
        story.append(Paragraph(f"GSTIN: {company_gstin}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Details
        details_data = [
            [Paragraph("<b>Bill To:</b>", styles['Normal']), Paragraph(f"Challan Date: {challan_date}", styles['Normal'])],
            [f"{customer_name}", f"Department: {department}"],
            [f"{customer_address}", f"Dispatch Method: {dispatch_method}"],
            [f"Phone: {customer_phone}", f"Expected Return Date: {expected_return_date}"],
            [f"GSTIN: {customer_gstin}", ""]
        ]
        details_table = Table(details_data, colWidths=[3*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 12))

        # Items table
        items_data = [['SR NO', 'ITEM DESCRIPTION', 'HSN/SAC', 'QTY', 'UNIT', 'PRICE', 'DESCRIPTION']]
        sr_no = 1
        for item in items:
            price = float(item.get('price', 0))
            hsn = item.get('hsn', 'N/A')
            items_data.append([
                str(sr_no),
                item['item_name'],
                hsn,
                str(item['quantity']),
                item['unit'],
                f"{price:.2f}",
                item.get('description', '')
            ])
            sr_no += 1
        items_table = Table(items_data, colWidths=[0.5*inch, 1.5*inch, 1*inch, 0.5*inch, 0.5*inch, 0.8*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0a83b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 12))

        # Notes
        if notes:
            story.append(Paragraph(f"Notes: {notes}", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()

        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={dc_number}.pdf'
        return response
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", 'error')
        return redirect(url_for('managedc'))

@app.route('/print_fss_label/<int:fss_id>')
def print_fss_label(fss_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM public.fss WHERE id = %s", (fss_id,))
        fss = cur.fetchone()
        cur.close()
        conn.close()

        if not fss:
            flash("FSS record not found", 'error')
            return redirect(url_for('managefss'))

        return render_template('fss_label_print.html', fss=fss)
    except Exception as e:
        flash(f"Error preparing label: {str(e)}", 'error')
        return redirect(url_for('managefss'))

if __name__ == '__main__':
    app.run(debug=True)
