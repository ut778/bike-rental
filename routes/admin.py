from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def require_admin_login():
    if 'admin_id' not in session or session.get('role') != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('auth.login'))

@admin_bp.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Analytics using Aggregate functions
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute("SELECT COUNT(*) as total_bookings FROM bookings")
    total_bookings = cursor.fetchone()['total_bookings']
    
    cursor.execute("SELECT COALESCE(SUM(total_rent), 0) as total_revenue FROM bookings WHERE status = 'completed'")
    total_revenue = cursor.fetchone()['total_revenue']
    
    cursor.execute("SELECT COUNT(*) as active_rentals FROM bookings WHERE status = 'active'")
    active_rentals = cursor.fetchone()['active_rentals']
    
    # Complex query: Most rented vehicle
    most_rented_query = """
        SELECT v.model, COUNT(b.booking_id) as rent_count
        FROM vehicles v
        JOIN bookings b ON v.vehicle_id = b.vehicle_id
        GROUP BY v.vehicle_id
        ORDER BY rent_count DESC
        LIMIT 1
    """
    cursor.execute(most_rented_query)
    most_rented = cursor.fetchone()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                           total_users=total_users, 
                           total_bookings=total_bookings,
                           total_revenue=total_revenue,
                           active_rentals=active_rentals,
                           most_rented=most_rented)

@admin_bp.route('/vehicles')
def manage_vehicles():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()
    conn.close()
    return render_template('admin_vehicles.html', vehicles=vehicles)

@admin_bp.route('/vehicles/add', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        vehicle_number = request.form['vehicle_number']
        model = request.form['model']
        v_type = request.form['type']
        rent_per_hour = request.form['rent_per_hour']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO vehicles (vehicle_number, model, type, rent_per_hour) VALUES (%s, %s, %s, %s)",
                           (vehicle_number, model, v_type, rent_per_hour))
            conn.commit()
            flash('Vehicle added successfully', 'success')
            return redirect(url_for('admin.manage_vehicles'))
        except Exception as e:
            conn.rollback()
            flash('Error adding vehicle', 'danger')
        finally:
            conn.close()
            
    return render_template('add_vehicle.html')

@admin_bp.route('/vehicles/delete/<int:vehicle_id>')
def delete_vehicle(vehicle_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
        conn.commit()
        flash('Vehicle deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash('Cannot delete vehicle due to foreign key constraint (existing bookings).', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('admin.manage_vehicles'))
