import fastf1
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
import numpy as np # Import numpy to check for its types
import time

# Configure FastF1 cache
fastf1.Cache.enable_cache('cache/')

# MySQL connection details from environment variables
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'database': os.getenv('MYSQL_DATABASE', 'f1_data'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'password')
}



def connect_db(max_retries=10, delay=5): # <--- MODIFIED: Added retry parameters
    """Establishes and returns a database connection with retries."""
    for i in range(max_retries):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            if conn.is_connected():
                # print(f"Connected to MySQL database after {i+1} attempts.")
                return conn
        except Error as e:
            print(f"Attempt {i+1}/{max_retries}: Error connecting to MySQL: {e}")
            if i < max_retries - 1: # Don't delay after the last attempt
                # print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Could not connect to MySQL.")
    return None # Return None if connection fails after all retries


def create_tables_if_not_exists(cursor):
    """Creates necessary tables if they don't exist."""
    print("Ensuring database tables exist...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INT PRIMARY KEY AUTO_INCREMENT,
            year INT NOT NULL,
            gp_name VARCHAR(255) NOT NULL,
            session_type VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            round_number INT NOT NULL,
            CONSTRAINT uc_session UNIQUE (year, gp_name, session_type, round_number)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS laps (
            lap_id INT PRIMARY KEY AUTO_INCREMENT,
            session_id INT NOT NULL,
            driver VARCHAR(10) NOT NULL,
            lap_number INT NOT NULL,
            lap_time_ms INT,
            sector1_time_ms INT,
            sector2_time_ms INT,
            sector3_time_ms INT,
            speed_trap_kmh INT,
            tyre_compound VARCHAR(50),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            CONSTRAINT uc_lap UNIQUE (session_id, driver, lap_number)
        )
    """)
    print("Tables checked/created.")


def insert_session(cursor, session_data):
    """Inserts session data and returns the session_id."""
    sql = """
    INSERT INTO sessions (year, gp_name, session_type, date, round_number)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        session_id=LAST_INSERT_ID(session_id)
    """
    try:
        # Ensure year and round_number are standard Python int
        year = int(session_data['year'])
        round_number = int(session_data['round_number'])

        cursor.execute(sql, (
            year, # Cast to int
            session_data['gp_name'],
            session_data['session_type'],
            session_data['date'],
            round_number # Cast to int
        ))
        return cursor.lastrowid
    except Error as e:
        print(f"Error inserting session: {e}")
        return None

def insert_lap_data(cursor, session_id, lap_data):
    """Inserts lap data."""
    sql = """
    INSERT INTO laps (session_id, driver, lap_number, lap_time_ms, sector1_time_ms, sector2_time_ms, sector3_time_ms, speed_trap_kmh, tyre_compound)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        lap_time_ms=VALUES(lap_time_ms),
        sector1_time_ms=VALUES(sector1_time_ms),
        sector2_time_ms=VALUES(sector2_time_ms),
        sector3_time_ms=VALUES(sector3_time_ms),
        speed_trap_kmh=VALUES(speed_trap_kmh),
        tyre_compound=VALUES(tyre_compound)
    """
    try:
        # Convert timedelta to milliseconds, handling NaN and ensuring int type
        lap_time_ms = int(lap_data['LapTime'].total_seconds() * 1000) if pd.notna(lap_data['LapTime']) else None
        s1_time_ms = int(lap_data['Sector1Time'].total_seconds() * 1000) if pd.notna(lap_data['Sector1Time']) else None
        s2_time_ms = int(lap_data['Sector2Time'].total_seconds() * 1000) if pd.notna(lap_data['Sector2Time']) else None
        s3_time_ms = int(lap_data['Sector3Time'].total_seconds() * 1000) if pd.notna(lap_data['Sector3Time']) else None

        # Convert numpy.int64/float64 to standard Python int, handling NaN/None
        # Use a helper function for robustness
        def convert_to_int_or_none(value):
            if pd.isna(value) or value is None:
                return None
            # Check if it's a numpy numeric type before converting
            if isinstance(value, (np.integer, np.floating)):
                return int(value)
            return value # Already a standard Python int, float, or other type

        lap_number = convert_to_int_or_none(lap_data.get('LapNumber')) # Use .get()
        speed_trap_kmh = convert_to_int_or_none(lap_data.get('SpeedTrap')) # Use .get()
        tyre_compound = lap_data.get('Compound') # Use .get() for string, then check pd.notna if needed

        # Ensure Driver is handled if it could be missing or NaN (less common but safe)
        driver = lap_data.get('Driver')
        if pd.isna(driver):
            driver = None

        cursor.execute(sql, (
            session_id,
            driver, # Use new driver variable
            lap_number,
            lap_time_ms,
            s1_time_ms,
            s2_time_ms,
            s3_time_ms,
            speed_trap_kmh,
            tyre_compound if pd.notna(tyre_compound) else None # Apply pd.notna check after .get()
        ))
    except Error as e:
        print(f"Error inserting lap data for driver {lap_data.get('Driver')} lap {lap_data.get('LapNumber')}: {e}")

def get_f1_data_and_store(year, gp, session_type):
    """Fetches F1 data and stores it in MySQL."""
    conn = connect_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        create_tables_if_not_exists(cursor)

        print(f"Loading session: {year} {gp} {session_type}")
        session = fastf1.get_session(year, gp, session_type)
        session.load()

        session_data = {
            'year': year,
            'gp_name': session.event['EventName'],
            'session_type': session_type,
            'date': session.date.date(),
            'round_number': session.event['RoundNumber']
        }
        session_id = insert_session(cursor, session_data)
        if not session_id:
            # If session already exists, get its ID to proceed with lap data
            cursor.execute("SELECT session_id FROM sessions WHERE year = %s AND gp_name = %s AND session_type = %s AND round_number = %s",
                           (year, session_data['gp_name'], session_type, session_data['round_number']))
            existing_session = cursor.fetchone()
            if existing_session:
                session_id = existing_session[0]
            else:
                raise Exception("Failed to get session_id for lap insertion. Session might not have been inserted or found.")
        print(f"Session {session.event['EventName']} ({session_id}) processed.")


        laps = session.laps
        print(f"Processing {len(laps)} laps...")
        for index, lap in laps.iterrows():
            insert_lap_data(cursor, session_id, lap)

        conn.commit()
        print(f"Data for {year} {gp} {session_type} successfully stored.")

    except Exception as e:
        conn.rollback()
        print(f"An error occurred during data ingestion: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("Starting F1 data ingestion...")
    get_f1_data_and_store(2023, 'Monaco', 'Race')
    get_f1_data_and_store(2023, 'Bahrain', 'Race')
    print("F1 data ingestion finished.")
