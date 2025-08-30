from flask import Flask, render_template, redirect, url_for,jsonify, request
from psycopg2 import pool
import webview # Это окно которое открывается при запуске приложения на Распберри
import atexit
import threading
import serial
import time
import psycopg2
import logging                           
from logging.handlers import RotatingFileHandler

# Create an event object to stop threads
stop_event = threading.Event()

# Set up rotating log files
handler = RotatingFileHandler('app.log', maxBytes=1024, backupCount=5)  # 5 MB per file, 5 backups
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Set up logging level to only log important events (Currently testing)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)

	# Connection with Arduino
try:
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout = 0.5)
    #ser.timeout = 0.5  # Установка таймаута ожидания данных (в секундах)

except serial.SerialException as e:
    logging.error(f"Ошибка при подключении к Arduino: {e}")
    ser = None  # Не ломаем код, а работаем без Arduino

redirect_to_scan_page = False
redirect_to_hello_page = False

# List to store scanned laptop UIDs temporarily
scanned_laptops = []

# Connection pool DB
db_pool = pool.SimpleConnectionPool(
    1, 10,  # Минимум 1, максимум 10 соединений
    dbname='SmartCart_db',
    user='postgres',
    password='hell0W0r1d',
    host='152.70.63.166',
    port='5432'
)

def get_db_connection():
    return db_pool.getconn()

def release_db_connection(conn):
    db_pool.putconn(conn)

def is_uid_allowed(uid):
    """Check if the given UID is allowed by querying the database."""
    conn = get_db_connection()
    try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE uid = %s LIMIT 1;", (uid,))
                return cur.fetchone() is not None  # True if UID is found, otherwise False
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)
        return False
    finally:
        release_db_connection(conn)

current_user_uid = None  # Global variable to store the current user's UID
laptop_status = "7/7"  # Global variable to store the laptop status
def arduino_thread():
        global current_user_uid, redirect_to_scan_page, redirect_to_hello_page, laptop_status, ser  # Use global variables
        while not stop_event.is_set():  # Check stoppage
            try:
                if ser and ser.is_open:
                    data = ser.readline().strip()
                    if data:
                        # Decode the data from bytes to string
                        data = data.decode().replace(" ", "").upper()  # Convert bytes to string and remove spaces
                        print("Received:", data)  # Log the data

                        # Handle RFID UID data
                        if data.startswith("UID:"):
                            uid = data[4:]  # Extract the UID (strip "UID:" prefix)
                            print("Received UID:", uid)

                            if is_uid_allowed(uid):
                                if current_user_uid is None:  # Only update if there's no active session
                                    current_user_uid = uid  # Store the UID of the current user
                                    print(f"Valid UID, stored as current user: {current_user_uid}")
                                    redirect_to_hello_page = True
                                else:
                                    print(f"New UID {uid} scanned, but a session is already active with UID {current_user_uid}. Ignoring.")
                            else:
                                print("UID not allowed.")

                        # Handle motion sensor data
                        elif data.endswith('/7'):
                            laptop_status = data  # Update the global laptop status
                time.sleep(0.1)  # Small sleep to optimize CPU
            except serial.SerialException:
                logging.warning("Arduino disconnected. Attempting to reconnect...")
            except Exception as e:
                print(f"Arduino thread error: {e}")

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=True,use_reloader=False, threaded=True)
@app.route('/submit_scan', methods=['POST'])
def submit_scan():
    global current_user_uid, redirect_to_hello_page  # Access the global user UID

    # Check if the UID was set by the RFID scan
    if not current_user_uid:
        return jsonify({'success': False, 'message': 'No valid user UID detected. Please scan your card.'}), 400

    data = request.json
    barcodes = data.get('barcodes')

    # Log the parsed UID and barcodes
    print(f"UID: {current_user_uid}")
    print(f"Barcodes: {barcodes}")

    if not barcodes:
        return jsonify({'success': False, 'message': 'No scanned barcodes provided.'}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for barcode in barcodes:

            cursor.execute("SELECT status FROM laptops WHERE name = %s;", (barcode,))
            result = cursor.fetchone()

            if not result:
                return jsonify({'success': False, 'message': f'Laptop {barcode} not found in the system.'}), 400

            if result[0] == 'unavailable':
                return jsonify(
                    {'success': False, 'message': f'Laptop {barcode} is already booked by another user.'}), 400

            # Set the laptop status to unavailable in the laptops table
            cursor.execute("""
                UPDATE laptops
                SET status = 'unavailable'
                WHERE name = %s
            """, (barcode,))

            # Insert the booking into the laptop_bookings table using current_user_uid
            cursor.execute("""
                INSERT INTO laptop_bookings (uid, laptop_name)
                VALUES (%s, %s)
            """, (current_user_uid, barcode))  # Use current_user_uid instead of uid

            # Optionally, log the return into laptop_history table
            cursor.execute("""
                INSERT INTO laptop_history (uid, laptop_name, action)
                VALUES (%s, %s, 'booked')
            """, (current_user_uid, barcode))

        conn.commit()

        # Clear the global UID to end the session
        current_user_uid = None
        redirect_to_hello_page = False  # Clear the hello page redirection
        return jsonify({'success': True, 'redirect_url': url_for('index')})  # Return a redirect URL to the home page

    except Exception as e:
        conn.rollback()
        logging.error(f"Ошибка при бронировании: {e}")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

    finally:
        release_db_connection(conn)
@app.route('/clear_session', methods=['POST'])
def clear_session():
    global current_user_uid, redirect_to_hello_page  # Use the global user UID

    # Clear the current user session
    current_user_uid = None
    redirect_to_hello_page = False  # Clear any redirection flags

    print("Session cleared.")

    return jsonify({'success': True})  # Send success response
@app.route('/check_laptop', methods=['POST'])
def check_laptop():
    data = request.json
    barcode = data.get('barcode')

    if not barcode:
        return jsonify({'success': False, 'message': 'No barcode provided'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the laptop exists in the database
            cursor.execute("SELECT COUNT(*) FROM laptops WHERE name = %s;", (barcode,))
            result = cursor.fetchone()[0]

            if result > 0:
                return jsonify({'success': True, 'message': 'Laptop found'})
            else:
                return jsonify({'success': False, 'message': 'Laptop not found'})

    except Exception as e:
        print(f"Error during laptop check: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

    finally:
        release_db_connection(conn)
@app.route('/get_laptop_status', methods=['GET'])
def get_laptop_status():
    global laptop_status
    return jsonify({'laptop_count': laptop_status})
@app.route('/')
def index():
    global current_user_uid, redirect_to_scan_page, redirect_to_hello_page, laptop_status

    if redirect_to_scan_page:
        redirect_to_scan_page = False
        return redirect(url_for('scan_page'))
    if redirect_to_hello_page:
        redirect_to_hello_page = False
        return redirect(url_for('hello_page'))
    current_user_uid = None
    
    return render_template('index.html', laptop_count=laptop_status)

@app.route('/scan_page')
def scan_page():
    return render_template('scan_page.html')

@app.route('/hello_page')
def hello_page():
    return render_template('hello_page.html')

@app.route('/return_page')
def return_page():
    return render_template('return_page.html')

@app.route('/check-redirect')
def check_redirect():
    global redirect_to_hello_page
    return jsonify({
        'redirect': redirect_to_hello_page
    })

@app.route('/check_user_laptops', methods=['POST'])
def check_user_laptops():
    global current_user_uid

    # Check if a valid user is set
    if not current_user_uid:
        return jsonify({'success': False, 'message': 'No valid user UID detected.'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Query the database to check if the user has borrowed any laptops
            cursor.execute("SELECT COUNT(*) FROM laptop_bookings WHERE uid = %s;", (current_user_uid,))
            result = cursor.fetchone()[0]

            if result > 0:
                return jsonify({'success': True, 'message': 'User has borrowed laptops.'})
            else:
                return jsonify({'success': False, 'message': 'User has not borrowed any laptops.'})

    except Exception as e:
        print(f"Error checking user laptops: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while checking the user\'s laptops.'}), 500

    finally:
        release_db_connection(conn)  # Возвращаем соединение в пул

@app.route('/return_laptops', methods=['POST'])
def return_laptops():
    global current_user_uid, redirect_to_hello_page  # Access the current user UID

    # Check if the UID was set by the RFID scan
    if not current_user_uid:
        return jsonify({'success': False, 'message': 'No valid user UID detected. Please scan your card.'}), 400

    data = request.json
    barcodes = data.get('barcodes')

    # Log the parsed UID and barcodes
    print(f"UID: {current_user_uid}")
    print(f"Barcodes: {barcodes}")

    if not barcodes:
        return jsonify({'success': False, 'message': 'No scanned barcodes provided.'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            not_borrowed_laptops = []  # To track laptops that weren't borrowed by the current user
            borrowed_laptops = []  # To track laptops that were borrowed by the current user

        # First pass: Verify which laptops were borrowed by the current user
            for barcode in barcodes:
                cursor.execute("""
                SELECT COUNT(*) FROM laptop_bookings WHERE uid = %s AND laptop_name = %s;
                """, (current_user_uid, barcode))
                booking_exists = cursor.fetchone()[0]

                if booking_exists > 0:
                    borrowed_laptops.append(barcode)
                else:
                    not_borrowed_laptops.append(barcode)

            # If there are laptops that weren't borrowed by the user, return an error
            if not_borrowed_laptops:
                return jsonify({
                    'success': False,
                    'message': f'The following laptops were not borrowed by the current user: {", ".join(not_borrowed_laptops)}'
                }), 400

            # Second pass: Proceed with returning the laptops only if all were borrowed
            for barcode in borrowed_laptops:
                # Set the laptop status to available in the laptops table
                cursor.execute("""
                    UPDATE laptops
                    SET status = 'available'
                    WHERE name = %s AND status = 'unavailable'
                """, (barcode,))

                # Remove the booking from the laptop_bookings table
                cursor.execute("""
                    DELETE FROM laptop_bookings WHERE uid = %s AND laptop_name = %s;
                """, (current_user_uid, barcode))

            # Optionally, log the return into laptop_history table
                cursor.execute("""
                    INSERT INTO laptop_history (uid, laptop_name, action)
                    VALUES (%s, %s, 'returned')
                """, (current_user_uid, barcode))

            conn.commit()

            redirect_to_hello_page = False  # Clear the hello page redirection
            return jsonify({'success': True, 'message': 'Laptops successfully returned and set to available.'})

    except Exception as e:
        conn.rollback()
        print(f"Error during return: {e}")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

    finally:
        release_db_connection(conn)

@app.route('/send_arduino_signal', methods=['POST'])
def send_arduino_signal():
    try:
        if ser and ser.is_open:
            ser.write(b'0\n')  # Отправка сигнала в Arduino
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Arduino not connected"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/send_arduino_signal_on', methods=['POST'])
def send_arduino_signal_on():
    try:
        if ser and ser.is_open:
            ser.write(b'1\n')  # Отправка сигнала в Arduino
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Arduino not connected"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def cleanup():
    print("Cleaning up resources...")

    # Stopping the threads
    stop_event.set()  # Signal to thread to stop
    time.sleep(0.2)  # Small sleep

    # Close DB
    if db_pool:
        db_pool.closeall()
        print("Database connection pool closed.")

    # Close connection with serial Arduino
    if ser and ser.is_open:
        ser.close()
        print("Serial connection closed.")

    print("Cleanup complete.")

# Cleanup program
atexit.register(cleanup)

if __name__ == '__main__':
    arduino_thread_instance = threading.Thread(target=arduino_thread, daemon=True)
    arduino_thread_instance.start()

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    try:
        time.sleep(2)

        webview.create_window("SmartCart", "http://0.0.0.0:5000", fullscreen=True)
        webview.start(gui='qt')
    except KeyboardInterrupt:
        print("Shutting down server.")