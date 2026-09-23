# Road Accident & Collision Management System
## DBMS 
**Course Code:** 23UDSPCL3508 / 23UDSPCP3508 — Database Management Systems  
**Academic Year:** 2026–2027 | **Evaluation:** TAE 2 (Winter 2026)  
**Student Name:** Prerna Agrawal | **Roll Number:** P39 | **Registration No:** 24ACDS1101026 | **Section:** P  
**Department:** Computer Science & Engineering (Data Science)  
**Institute:** G H Raisoni College of Engineering and Management, Pune  
**Target RDBMS:** MySQL 8.0 (InnoDB Engine)  
**Dataset Source:** NYPD Motor Vehicle Collisions - Crashes Dataset (`Motor_Vehicle_Collisions_-_Crashes.csv`)  

---

## 📌 Project Overview
The **Road Accident & Collision Management System** is a normalized relational database designed to store, manage, and analyze road accident records, spatial accident locations, vehicle types involved, primary contributing factors, and casualty statistics. 

This project translates an approved 3NF/BCNF relational model into an executable database schema, populates it with real-world collision data, and implements advanced SQL features including multi-table joins, correlated subqueries, transactional stored procedures, dynamic triggers, virtual views, and B-Tree index optimization.

---

## 🏗️ Relational Schema (3NF / BCNF Normalized)

The database splits flat, unnormalized crash register data into **9 core relations** using natural keys and strict foreign key integrity constraints:

```
+----------------+       +------------------+       +-------------------+
|    BOROUGH     |----<  |     ZIP_CODE     |----<  |     LOCATION      |
+----------------+       +------------------+       +-------------------+
                                                              |
                                                              v
+----------------+       +------------------+       +-------------------+
|  VEHICLE_TYPE  |----<  | COLLISION_VEHICLE|----<  |     COLLISION     |
+----------------+       +------------------+       +-------------------+
                                                              | 1:1
+----------------+       +------------------+                 v
| CONTRIBUTING_F |----<  | COLLISION_FACTOR |----<  +-------------------+
+----------------+       +------------------+       |     CASUALTY      |
                                                    +-------------------+
```

1. **`BOROUGH`** `(BOROUGH [PK])` — Administrative NYC boroughs.
2. **`ZIP_CODE`** `(ZIP_CODE [PK], BOROUGH [FK])` — Postal codes linked to boroughs.
3. **`LOCATION`** `((LATITUDE, LONGITUDE) [PK], ON_STREET_NAME, CROSS_STREET_NAME, OFF_STREET_NAME, ZIP_CODE [FK])` — Street-level details and GPS coordinates.
4. **`COLLISION`** `(COLLISION_ID [PK], ACCIDENT_DATE, ACCIDENT_TIME, (LATITUDE, LONGITUDE) [FK])` — Core collision record.
5. **`VEHICLE_TYPE`** `(VEHICLE_TYPE_CODE [PK])` — Catalog of 8 vehicle categories (`Car/SUV`, `Truck/Bus`, `Motorcycle`, `Bicycle`, `Ebike`, `Escooter`, `ATV`, `Other`).
6. **`COLLISION_VEHICLE`** `((COLLISION_ID, VEHICLE_TYPE_CODE) [PK, FK])` — Associative entity for vehicle types involved.
7. **`CONTRIBUTING_FACTOR`** `(CONTRIBUTING_FACTOR_VEHICLE [PK])` — Catalog of crash causes.
8. **`COLLISION_FACTOR`** `((COLLISION_ID, CONTRIBUTING_FACTOR_VEHICLE) [PK, FK])` — Associative entity for contributing factors.
9. **`CASUALTY`** `(COLLISION_ID [PK, FK], NUMBER_OF_PERSONS_INJURED, NUMBER_OF_PERSONS_KILLED, ...)` — 1:1 casualty metrics.
10. **`COLLISION_AUDIT`** `(AUDIT_ID [PK], COLLISION_ID, ACTION_TYPE, ...)` — Audit trail for dynamic triggers.

---

## 📂 Repository Deliverables & Directory Structure

```
RoadAccident_DBMS_TAE2/
├── README.md               # Project documentation and setup guide
├── schema.sql              # Table creation DDL with constraints & cascades
├── data.sql                # Executable DML script (300+ real records from CSV)
├── queries.sql             # Multi-table joins, procedures, triggers, views & EXPLAIN
├── import_real_data.py     # Python ETL parser for Motor_Vehicle_Collisions_-_Crashes.csv
├── populate.py             # Synthetic dataset generator fallback script
└── Presentation_Deck.md    # 10-minute presentation guide & technical viva prep
```

---

## ⚡ Setup & Execution Guide (MySQL 8.0)

### Step 1: Clone / Open Project Directory
Open terminal or MySQL Workbench in the project directory:
```bash
cd C:\Users\prera\.gemini\antigravity\scratch\RoadAccident_DBMS_TAE2
```

### Step 2: Initialize Database Schema
Execute `schema.sql` in MySQL to create `road_accident_db` and create all tables:
```sql
SOURCE schema.sql;
```

### Step 3: Populate Database Records
Execute `data.sql` to insert 300+ clean real records extracted from the NYPD dataset:
```sql
SOURCE data.sql;
```

### Step 4: Execute Advanced Queries & Benchmarks
Execute `queries.sql` to run all joins, procedures, triggers, views, and `EXPLAIN` analysis:
```sql
SOURCE queries.sql;
```

---

## 📊 Summary of Advanced SQL Features Implemented

1. **Complex Multi-Table INNER JOIN:** Rejoins all 9 normalized entities to trace incidents from Borough down to vehicle types, factors, and injuries.
2. **Outer Joins (LEFT / RIGHT):** Identifies collisions without registered contributing factors and vehicle categories with zero crashes.
3. **Self Join:** Detects repeat accident locations matching exact GPS coordinates.
4. **Correlated Subquery:** Retrieves collisions with injuries strictly exceeding the borough-specific average.
5. **Transactional Stored Procedure (`sp_RegisterNewCollision`):** Handles atomic collision registration with `START TRANSACTION`, `COMMIT`, and `ROLLBACK`.
6. **Automated Business Rule Trigger (`trg_ValidateCasualtyCounts`):** Prevents insertion of casualty sub-counts exceeding total injured/killed totals.
7. **Dynamic Audit Trigger (`trg_AuditCollisionChanges`):** Records date modifications into `COLLISION_AUDIT`.
8. **Virtual Views (`vw_BoroughAccidentSummary`, `vw_HighRiskFactorAnalysis`):** Business reporting views.
9. **Performance Tuning (`EXPLAIN ANALYZE`):** B-Tree composite indexing (`idx_collision_date`, `idx_location_zip`, `idx_casualty_injured`) reducing query costs.

---

## 🤝 Authors & Acknowledgments
- **Student:** Prerna Agrawal (Roll P39)
- **Guided By:** Mr. Chinmay Mukim Sir
- **Department:** CSE (Data Science), GHRCEM, Pune
