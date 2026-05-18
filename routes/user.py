from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_db_connection

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.before_request
def require_login():
    if 'user_id' not in session or session.get('role') != 'user':
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

@user_bp.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Using JOIN to get booking details along with vehicle details
    query = """
        SELECT b.booking_id, v.vehicle_number, v.model, b.start_time, b.end_time, b.total_rent, b.status
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        WHERE b.user_id = %s
        ORDER BY b.created_at DESC
    """
    cursor.execute(query, (session['user_id'],))
    bookings = cursor.fetchall()
    conn.close()
    
    return render_template('user_dashboard.html', bookings=bookings)

@user_bp.route('/vehicles')
def list_vehicles():
    filter_type = request.args.get('type')
    search_model = request.args.get('model')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM vehicles WHERE 1=1"
    params = []
    
    if filter_type:
        query += " AND type = %s"
        params.append(filter_type)
        
    if search_model:
        query += " AND model LIKE %s"
        params.append(f"%{search_model}%")
        
    cursor.execute(query, tuple(params))
    vehicles = cursor.fetchall()
    conn.close()
    
    return render_template('vehicle_list.html', vehicles=vehicles)

@user_bp.route('/book/<int:vehicle_id>', methods=['GET', 'POST'])
def book_vehicle(vehicle_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        
        try:
            # Calling the stored procedure to handle booking
            cursor.callproc('sp_create_booking', (session['user_id'], vehicle_id, start_time, end_time))
            conn.commit()
            
            # Retrieve output from stored procedure
            for result in cursor.stored_results():
                msg = result.fetchone()
                if msg:
                    flash(f"Booking successful! Total Rent: ${msg['rent']}", 'success')
            
            return redirect(url_for('user.dashboard'))
        except Exception as e:
            conn.rollback()
            flash(str(e), 'danger')
        finally:
            conn.close()
            
    cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
    vehicle = cursor.fetchone()
    conn.close()
    
    return render_template('book_vehicle.html', vehicle=vehicle)
