import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_str(val):
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if s == '' or s.upper() == 'NAN' or s.upper() == 'NULL' or s.upper() == 'UNSPECIFIED':
        return None
    # Escape single quotes for SQL
    return s.replace("'", "''")

def map_vehicle_type(raw_val):
    if not raw_val:
        return 'Other'
    v = raw_val.upper()
    if any(k in v for k in ['SEDAN', 'SPORT UTILITY', 'SUV', 'STATION WAGON', 'PASSENGER', 'TAXI', 'CONVERTIBLE', 'COUPE', 'VAN', 'MINIVAN', 'PK', 'PICK-UP']):
        return 'Car/SUV'
    elif any(k in v for k in ['TRUCK', 'BUS', 'TRACTOR', 'TRAILER', 'GARBAGE', 'DUMP', 'FLAT BED', 'BOX']):
        return 'Truck/Bus'
    elif any(k in v for k in ['MOTORCYCLE', 'SCOOTER', 'MOPED', 'MOTORBIKE']):
        return 'Motorcycle'
    elif any(k in v for k in ['BICYCLE', 'BIKE', 'CYCL']):
        return 'Bicycle'
    elif any(k in v for k in ['E-BIKE', 'EBIKE', 'ELECTRONIC BIKE']):
        return 'Ebike'
    elif any(k in v for k in ['E-SCOOTER', 'ESCOOTER']):
        return 'Escooter'
    elif any(k in v for k in ['ATV', 'ALL TERRAIN']):
        return 'ATV'
    else:
        return 'Other'

def process_csv():
    csv_path = r'C:\Users\prera\Downloads\Motor_Vehicle_Collisions_-_Crashes.csv'
    print("Reading CSV dataset...")
    # Read first 1500 valid rows to get a pristine, rich, high-quality subset with >100 rows per table
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Filter rows that have valid LATITUDE, LONGITUDE, BOROUGH, and ZIP CODE
    df_clean = df.dropna(subset=['COLLISION_ID', 'CRASH DATE', 'CRASH TIME', 'LATITUDE', 'LONGITUDE', 'BOROUGH', 'ZIP CODE']).copy()
    
    # Restrict to NYC Lat/Long bounds
    df_clean = df_clean[(df_clean['LATITUDE'] >= 40.4) & (df_clean['LATITUDE'] <= 40.95) & 
                        (df_clean['LONGITUDE'] >= -74.3) & (df_clean['LONGITUDE'] <= -73.6)].copy()
    
    print(f"Total valid clean records available: {len(df_clean)}")
    
    # Take top 300 clean records for optimum database performance and quick execution
    df_sub = df_clean.head(300).copy()

    sql_lines = []
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- REAL DATA POPULATION SCRIPT (data.sql)")
    sql_lines.append("-- Source: NYPD Motor Vehicle Collisions - Crashes Dataset")
    sql_lines.append(f"-- Transformed automatically for DBMS TAE 2 Evaluation ({len(df_sub)} Collision Records)")
    sql_lines.append("-- ============================================================================\n")
    sql_lines.append("USE road_accident_db;\n")
    sql_lines.append("SET FOREIGN_KEY_CHECKS = 0;\n")

    # 1. BOROUGH
    boroughs = sorted([b for b in df_sub['BOROUGH'].dropna().unique() if str(b).strip() != ''])
    sql_lines.append("-- 1. Insert BOROUGH records")
    b_vals = ", ".join([f"('{b.strip().upper()}')" for b in boroughs])
    sql_lines.append(f"INSERT INTO BOROUGH (BOROUGH) VALUES\n{b_vals}\nON DUPLICATE KEY UPDATE BOROUGH=VALUES(BOROUGH);\n")

    # 2. ZIP_CODE
    zip_pairs = set()
    for _, row in df_sub.iterrows():
        b = str(row['BOROUGH']).strip().upper()
        z = str(row['ZIP CODE']).split('.')[0].strip()
        if z and b:
            zip_pairs.add((z.zfill(5), b))
    
    sql_lines.append("-- 2. Insert ZIP_CODE records")
    z_vals = ", ".join([f"('{z}', '{b}')" for z, b in sorted(zip_pairs)])
    sql_lines.append(f"INSERT INTO ZIP_CODE (ZIP_CODE, BOROUGH) VALUES\n{z_vals}\nON DUPLICATE KEY UPDATE BOROUGH=VALUES(BOROUGH);\n")

    # 3. LOCATION
    locations_dict = {}
    for _, row in df_sub.iterrows():
        lat = round(float(row['LATITUDE']), 7)
        lng = round(float(row['LONGITUDE']), 7)
        key = (lat, lng)
        if key not in locations_dict:
            on_st = clean_str(row.get('ON STREET NAME'))
            cross_st = clean_str(row.get('CROSS STREET NAME'))
            off_st = clean_str(row.get('OFF STREET NAME'))
            z = str(row['ZIP CODE']).split('.')[0].strip().zfill(5)
            locations_dict[key] = (on_st, cross_st, off_st, z)

    sql_lines.append(f"-- 3. Insert LOCATION records ({len(locations_dict)} unique geographic locations)")
    loc_vals = []
    for (lat, lng), (on_st, cross_st, off_st, z) in locations_dict.items():
        on_str_val = f"'{on_st}'" if on_st else "NULL"
        cross_str_val = f"'{cross_st}'" if cross_st else "NULL"
        off_str_val = f"'{off_st}'" if off_st else "NULL"
        zip_val = f"'{z}'" if z else "NULL"
        loc_vals.append(f"({lat}, {lng}, {on_str_val}, {cross_str_val}, {off_str_val}, {zip_val})")
    
    sql_lines.append("INSERT INTO LOCATION (LATITUDE, LONGITUDE, ON_STREET_NAME, CROSS_STREET_NAME, OFF_STREET_NAME, ZIP_CODE) VALUES\n" + ",\n".join(loc_vals) + "\nON DUPLICATE KEY UPDATE ZIP_CODE=VALUES(ZIP_CODE);\n")

    # 4. COLLISION
    sql_lines.append(f"-- 4. Insert COLLISION records ({len(df_sub)} Collisions)")
    col_vals = []
    collision_ids = []
    for _, row in df_sub.iterrows():
        cid = int(row['COLLISION_ID'])
        collision_ids.append(cid)
        
        # Parse date
        c_date_raw = str(row['CRASH DATE']).split()[0]
        try:
            c_date = datetime.strptime(c_date_raw, '%m/%d/%Y').strftime('%Y-%m-%d')
        except:
            c_date = '2025-01-01'
            
        # Parse time
        c_time_raw = str(row['CRASH TIME']).strip()
        if ':' in c_time_raw:
            parts = c_time_raw.split(':')
            c_time = f"{int(parts[0]):02d}:{int(parts[1]):02d}:00"
        else:
            c_time = "12:00:00"
            
        lat = round(float(row['LATITUDE']), 7)
        lng = round(float(row['LONGITUDE']), 7)
        col_vals.append(f"({cid}, '{c_date}', '{c_time}', {lat}, {lng})")
        
    sql_lines.append("INSERT INTO COLLISION (COLLISION_ID, ACCIDENT_DATE, ACCIDENT_TIME, LATITUDE, LONGITUDE) VALUES\n" + ",\n".join(col_vals) + "\nON DUPLICATE KEY UPDATE ACCIDENT_DATE=VALUES(ACCIDENT_DATE);\n")

    # 5. VEHICLE_TYPE
    vehicle_categories = ['ATV', 'Bicycle', 'Car/SUV', 'Ebike', 'Escooter', 'Truck/Bus', 'Motorcycle', 'Other']
    sql_lines.append("-- 5. Insert VEHICLE_TYPE lookup records")
    v_vals = ", ".join([f"('{vt}')" for vt in vehicle_categories])
    sql_lines.append(f"INSERT INTO VEHICLE_TYPE (VEHICLE_TYPE_CODE) VALUES\n{v_vals}\nON DUPLICATE KEY UPDATE VEHICLE_TYPE_CODE=VALUES(VEHICLE_TYPE_CODE);\n")

    # 6. COLLISION_VEHICLE
    sql_lines.append("-- 6. Insert COLLISION_VEHICLE records (Unpivoted M:N)")
    cv_pairs = set()
    for _, row in df_sub.iterrows():
        cid = int(row['COLLISION_ID'])
        for col_idx in range(1, 6):
            v_raw = row.get(f'VEHICLE TYPE CODE {col_idx}')
            if pd.notna(v_raw) and str(v_raw).strip() != '':
                mapped_v = map_vehicle_type(str(v_raw).strip())
                cv_pairs.add((cid, mapped_v))
                
    cv_vals = [f"({cid}, '{v}')" for cid, v in sorted(cv_pairs)]
    sql_lines.append("INSERT INTO COLLISION_VEHICLE (COLLISION_ID, VEHICLE_TYPE_CODE) VALUES\n" + ",\n".join(cv_vals) + "\nON DUPLICATE KEY UPDATE VEHICLE_TYPE_CODE=VALUES(VEHICLE_TYPE_CODE);\n")

    # 7. CONTRIBUTING_FACTOR & 8. COLLISION_FACTOR
    cf_factors = set()
    col_factors = set()
    for _, row in df_sub.iterrows():
        cid = int(row['COLLISION_ID'])
        for col_idx in range(1, 6):
            f_raw = clean_str(row.get(f'CONTRIBUTING FACTOR VEHICLE {col_idx}'))
            if f_raw and f_raw.upper() != 'UNSPECIFIED':
                cf_factors.add(f_raw)
                col_factors.add((cid, f_raw))
                
    # Always include 'Unspecified' in CONTRIBUTING_FACTOR table
    cf_factors.add('Unspecified')

    sql_lines.append("-- 7. Insert CONTRIBUTING_FACTOR records")
    f_vals = ", ".join([f"('{f}')" for f in sorted(cf_factors)])
    sql_lines.append(f"INSERT INTO CONTRIBUTING_FACTOR (CONTRIBUTING_FACTOR_VEHICLE) VALUES\n{f_vals}\nON DUPLICATE KEY UPDATE CONTRIBUTING_FACTOR_VEHICLE=VALUES(CONTRIBUTING_FACTOR_VEHICLE);\n")

    sql_lines.append("-- 8. Insert COLLISION_FACTOR records (Unpivoted M:N)")
    cf_pair_vals = [f"({cid}, '{f}')" for cid, f in sorted(col_factors)]
    sql_lines.append("INSERT INTO COLLISION_FACTOR (COLLISION_ID, CONTRIBUTING_FACTOR_VEHICLE) VALUES\n" + ",\n".join(cf_pair_vals) + "\nON DUPLICATE KEY UPDATE CONTRIBUTING_FACTOR_VEHICLE=VALUES(CONTRIBUTING_FACTOR_VEHICLE);\n")

    # 9. CASUALTY
    sql_lines.append("-- 9. Insert CASUALTY records (1:1 with COLLISION)")
    cas_vals = []
    for _, row in df_sub.iterrows():
        cid = int(row['COLLISION_ID'])
        inj = int(row.get('NUMBER OF PERSONS INJURED', 0) if pd.notna(row.get('NUMBER OF PERSONS INJURED')) else 0)
        kil = int(row.get('NUMBER OF PERSONS KILLED', 0) if pd.notna(row.get('NUMBER OF PERSONS KILLED')) else 0)
        
        p_inj = int(row.get('NUMBER OF PEDESTRIANS INJURED', 0) if pd.notna(row.get('NUMBER OF PEDESTRIANS INJURED')) else 0)
        p_kil = int(row.get('NUMBER OF PEDESTRIANS KILLED', 0) if pd.notna(row.get('NUMBER OF PEDESTRIANS KILLED')) else 0)
        
        c_inj = int(row.get('NUMBER OF CYCLIST INJURED', 0) if pd.notna(row.get('NUMBER OF CYCLIST INJURED')) else 0)
        c_kil = int(row.get('NUMBER OF CYCLIST KILLED', 0) if pd.notna(row.get('NUMBER OF CYCLIST KILLED')) else 0)
        
        m_inj = int(row.get('NUMBER OF MOTORIST INJURED', 0) if pd.notna(row.get('NUMBER OF MOTORIST INJURED')) else 0)
        m_kil = int(row.get('NUMBER OF MOTORIST KILLED', 0) if pd.notna(row.get('NUMBER OF MOTORIST KILLED')) else 0)

        # Sanity check: Ensure sub-counts don't exceed total counts due to raw data typos
        if (p_inj + c_inj + m_inj) > inj:
            inj = p_inj + c_inj + m_inj
        if (p_kil + c_kil + m_kil) > kil:
            kil = p_kil + c_kil + m_kil

        cas_vals.append(f"({cid}, {inj}, {kil}, {p_inj}, {p_kil}, {c_inj}, {c_kil}, {m_inj}, {m_kil})")

    sql_lines.append(
        "INSERT INTO CASUALTY (\n"
        "    COLLISION_ID, NUMBER_OF_PERSONS_INJURED, NUMBER_OF_PERSONS_KILLED,\n"
        "    NUMBER_OF_PEDESTRIANS_INJURED, NUMBER_OF_PEDESTRIANS_KILLED,\n"
        "    NUMBER_OF_CYCLIST_INJURED, NUMBER_OF_CYCLIST_KILLED,\n"
        "    NUMBER_OF_MOTORIST_INJURED, NUMBER_OF_MOTORIST_KILLED\n"
        ") VALUES\n" + ",\n".join(cas_vals) + "\nON DUPLICATE KEY UPDATE NUMBER_OF_PERSONS_INJURED=VALUES(NUMBER_OF_PERSONS_INJURED);\n"
    )

    sql_lines.append("SET FOREIGN_KEY_CHECKS = 1;\n")
    sql_lines.append("-- END OF REAL DATA POPULATION SCRIPT")

    target_sql = r'C:\Users\prera\.gemini\antigravity\scratch\RoadAccident_DBMS_TAE2\data.sql'
    with open(target_sql, 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_lines))

    print(f"SUCCESS: Transformed real CSV dataset into {target_sql}!")

if __name__ == '__main__':
    process_csv()
