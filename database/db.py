import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',  # Default password, user can change this
    'database': 'vehicle_rental'
}

def get_db_connection():
    """Returns a new database connection."""
    try:
        conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_MYSQL_PASSWORD",
    database="vehicle_rental"
)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None
