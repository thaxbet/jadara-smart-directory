# -*- coding: utf-8 -*-
"""
ملف إنشاء وتجهيز قاعدة البيانات (SQLite Database Schema & Approved Seed Data)
مشروع: دليل الساعات المكتبية ومواقع الدكاترة الذكي — جامعة جدارا (كلية تكنولوجيا المعلومات)
إعداد الطالب: ثابت قيس محمد قواسمة (202220020)
إشراف: د. معن مروان علي الزعبي
ملاحظة: مطابق 100% لملف البيانات المعتمد (doctors.xlsx) الذي يضم 20 دكتوراً (101 - 120).
"""

import sqlite3
import os

DB_FILENAME = "database.db"

# البيانات المعتمدة كاملة من ملف doctors.xlsx (20 دكتوراً)
APPROVED_DOCTORS = [
    (101, "د. أحمد إبراهيم خليل", "أستاذ مشارك", "هندسة البرمجيات", "كلية تكنولوجيا المعلومات", "الطابق الثاني", "IT-204", "a.khalil@jadara.edu.jo", "Sun/Tue/Thu 10:00 - 11:00"),
    (102, "د. رانيا محمود القضاة", "أستاذ مساعد", "علم الحاسوب", "كلية تكنولوجيا المعلومات", "الطابق الأول", "IT-108", "r.qudah@jadara.edu.jo", "Mon/Wed 11:00 - 12:30"),
    (103, "أ.د. طارق زياد العبدالله", "أستاذ دكتور", "الذكاء الاصطناعي", "مجمع الكليات العلمية", "الطابق الثالث", "SC-312", "t.abdallah@jadara.edu.jo", "Sun/Tue/Thu 12:00 - 01:00"),
    (104, "د. هبة سامي الخطيب", "أستاذ مساعد", "الأمن السيبراني", "كلية تكنولوجيا المعلومات", "الطابق الثاني", "IT-215", "h.khatib@jadara.edu.jo", "Mon/Wed 09:30 - 11:00"),
    (105, "د. حسام عمر التميمي", "أستاذ مشارك", "نظم المعلومات الحاسوبية", "كلية الأعمال وتكنولوجيا المعلومات", "الطابق الأرضي", "BI-005", "h.tamimi@jadara.edu.jo", "Sun/Tue/Thu 09:00 - 10:00"),
    (106, "د. يزن مصطفى العزام", "أستاذ مساعد", "هندسة البرمجيات", "كلية تكنولوجيا المعلومات", "الطابق الثاني", "IT-206", "y.azzam@jadara.edu.jo", "Mon/Wed 12:30 - 02:00"),
    (107, "د. منى فؤاد الروسان", "أستاذ مشارك", "علم الحاسوب", "كلية تكنولوجيا المعلومات", "الطابق الأول", "IT-112", "m.rousan@jadara.edu.jo", "Sun/Tue/Thu 11:00 - 12:00"),
    (108, "د. حمزة علي الجراح", "أستاذ مساعد", "الذكاء الاصطناعي", "مجمع الكليات العلمية", "الطابق الثالث", "SC-305", "h.jarrah@jadara.edu.jo", "Sun/Tue/Thu 01:00 - 02:00"),
    (109, "د. ليلى حسن بني هاني", "أستاذ مساعد", "الأمن السيبراني", "كلية تكنولوجيا المعلومات", "الطابق الثاني", "IT-220", "l.banihani@jadara.edu.jo", "Mon/Wed 10:00 - 11:30"),
    (110, "د. فراس ناصر الزعبي", "أستاذ دكتور", "علم الحاسوب", "كلية تكنولوجيا المعلومات", "الطابق الأول", "IT-101", "f.zoubi@jadara.edu.jo", "Sun/Tue/Thu 08:30 - 09:30"),
    (111, "د. دانية عبد الله الشبول", "أستاذ مساعد", "نظم المعلومات الحاسوبية", "كلية الأعمال وتكنولوجيا المعلومات", "الطابق الأول", "BI-104", "d.shboul@jadara.edu.jo", "Mon/Wed 08:30 - 10:00"),
    (112, "د. خالد وليد الطعاني", "أستاذ مشارك", "هندسة البرمجيات", "كلية تكنولوجيا المعلومات", "الطابق الثاني", "IT-202", "k.taani@jadara.edu.jo", "Sun/Tue/Thu 10:00 - 11:00"),
    (113, "د. سميرة عدنان العمري", "أستاذ مساعد", "علم الحاسوب", "كلية تكنولوجيا المعلومات", "الطابق الأول", "IT-115", "s.omari@jadara.edu.jo", "Mon/Wed 01:00 - 02:30"),
    (114, "د. مجد توفيق مقابلة", "أستاذ مشارك", "الذكاء الاصطناعي", "مجمع الكليات العلمية", "الطابق الثالث", "SC-318", "m.muqableh@jadara.edu.jo", "Sun/Tue/Thu 11:00 - 12:00"),
    (115, "د. عمر بشير غرايبة", "أستاذ مساعد", "الأمن السيبراني", "كلية تكنولوجيا المعلومات", "الطابق الثاني", "IT-218", "o.gharaibeh@jadara.edu.jo", "Sun/Tue/Thu 12:00 - 01:00"),
    (116, "د. ولاء محمود البطاينة", "مدرس", "نظم المعلومات الحاسوبية", "كلية الأعمال وتكنولوجيا المعلومات", "الطابق الأرضي", "BI-009", "w.bataineh@jadara.edu.jo", "Mon/Wed 11:30 - 01:00"),
    (117, "د. بشار كمال الهنداوي", "أستاذ مشارك", "هندسة البرمجيات", "كلية تكنولوجيا المعلومات", "الطابق الثاني", "IT-210", "b.hindawi@jadara.edu.jo", "Sun/Tue/Thu 09:00 - 10:00"),
    (118, "د. نادين سمير عبيدات", "أستاذ مساعد", "علم الحاسوب", "كلية تكنولوجيا المعلومات", "الطابق الأول", "IT-105", "n.obeidat@jadara.edu.jo", "Mon/Wed 10:00 - 11:30"),
    (119, "د. معتز نضال الخصاونة", "أستاذ مساعد", "الذكاء الاصطناعي", "مجمع الكليات العلمية", "الطابق الثالث", "SC-301", "m.khasawneh@jadara.edu.jo", "Sun/Tue/Thu 02:00 - 03:00"),
    (120, "د. إيناس كمال مريان", "أستاذ مساعد", "هندسة البرمجيات", "كلية تكنولوجيا المعلومات", "الطابق الثاني", "IT-208", "e.maryan@jadara.edu.jo", "Mon/Wed 12:00 - 01:30"),
]


def create_and_seed_database(db_path: str = DB_FILENAME) -> None:
    """ينشئ الجداول الخمسة الأساسية في قاعدة البيانات ويغذيها بالـ 20 دكتوراً المعتمدين في doctors.xlsx."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode = MEMORY;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. جدول الأقسام الأكاديمية (Departments)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Departments (
        department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        department_name TEXT NOT NULL UNIQUE
    );
    """)

    # 2. جدول المباني الجامعية (Buildings)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Buildings (
        building_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        building_code TEXT NOT NULL UNIQUE,
        building_name TEXT NOT NULL UNIQUE
    );
    """)

    # 3. جدول أعضاء الهيئة التدريسية (FacultyMembers) - مطابق لأعمدة doctors.xlsx
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FacultyMembers (
        doctor_id     INTEGER PRIMARY KEY,
        name          TEXT NOT NULL,
        rank          TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        building_id   INTEGER NOT NULL,
        floor         TEXT NOT NULL,
        office_number TEXT NOT NULL,
        email         TEXT NOT NULL UNIQUE,
        FOREIGN KEY (department_id) REFERENCES Departments(department_id) ON DELETE RESTRICT,
        FOREIGN KEY (building_id)   REFERENCES Buildings(building_id)     ON DELETE RESTRICT
    );
    """)

    # 4. جدول الساعات المكتبية (OfficeHours)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS OfficeHours (
        schedule_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id    INTEGER NOT NULL,
        days         TEXT NOT NULL,
        start_time   TEXT NOT NULL,
        end_time     TEXT NOT NULL,
        raw_schedule TEXT NOT NULL,
        FOREIGN KEY (doctor_id) REFERENCES FacultyMembers(doctor_id) ON DELETE CASCADE
    );
    """)

    # 5. جدول المستخدمين وصلاحيات الإدارة (Users / Admins)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role          TEXT NOT NULL CHECK(role IN ('Admin', 'Faculty', 'Secretary')),
        doctor_id     INTEGER,
        FOREIGN KEY (doctor_id) REFERENCES FacultyMembers(doctor_id) ON DELETE SET NULL
    );
    """)

    # إدخال الأقسام الخمسة المعتمدة في doctors.xlsx
    departments = [
        ("هندسة البرمجيات",),
        ("علم الحاسوب",),
        ("الذكاء الاصطناعي",),
        ("الأمن السيبراني",),
        ("نظم المعلومات الحاسوبية",),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO Departments (department_name) VALUES (?);",
        departments
    )

    # إدخال المباني الثلاثة المعتمدة في doctors.xlsx
    buildings = [
        ("IT", "كلية تكنولوجيا المعلومات"),
        ("SC", "مجمع الكليات العلمية"),
        ("BI", "كلية الأعمال وتكنولوجيا المعلومات"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO Buildings (building_code, building_name) VALUES (?, ?);",
        buildings
    )

    # جلب أرقام الأقسام والمباني للربط العلائقي (Foreign Keys)
    cursor.execute("SELECT department_name, department_id FROM Departments;")
    dept_map = dict(cursor.fetchall())

    cursor.execute("SELECT building_name, building_id FROM Buildings;")
    bldg_map = dict(cursor.fetchall())

    # مسح الساعات القديمة عند إعادة التهيئة لمنع التكرار
    cursor.execute("DELETE FROM OfficeHours;")

    # إدخال جميع الدكاترة الـ 20 وساعاتهم المكتبية
    for doc_id, name, rank, dept_name, bldg_name, floor, office_num, email, oh_str in APPROVED_DOCTORS:
        dept_id = dept_map[dept_name]
        bldg_id = bldg_map[bldg_name]

        cursor.execute("""
            INSERT OR REPLACE INTO FacultyMembers
            (doctor_id, name, rank, department_id, building_id, floor, office_number, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (doc_id, name, rank, dept_id, bldg_id, floor, office_num, email))

        # تفكيك الساعات المكتبية (مثال: "Sun/Tue/Thu 10:00 - 11:00")
        parts = oh_str.split(" ", 1)
        days_part = parts[0]
        times_part = parts[1].split("-")
        start_t = times_part[0].strip()
        end_t = times_part[1].strip()

        cursor.execute("""
            INSERT INTO OfficeHours (doctor_id, days, start_time, end_time, raw_schedule)
            VALUES (?, ?, ?, ?, ?);
        """, (doc_id, days_part, start_t, end_t, oh_str))

        # إنشاء حساب تسجيل دخول لكل دكتور باسم البريد قبل @
        uname = email.split("@")[0]
        cursor.execute("""
            INSERT OR IGNORE INTO Users (username, password_hash, role, doctor_id)
            VALUES (?, 'doctor123', 'Faculty', ?);
        """, (uname, doc_id))

    # إنشاء حساب مسؤول النظام الرئيسي (Admin)
    cursor.execute("""
        INSERT OR IGNORE INTO Users (username, password_hash, role, doctor_id)
        VALUES ('admin', 'admin123', 'Admin', NULL);
    """)

    conn.commit()
    conn.close()
    print(f"تم إنشاء قاعدة البيانات ({db_path}) بنجاح وتغذيتها بـ 20 دكتوراً و5 أقسام و3 مبانٍ من ملف doctors.xlsx!")


if __name__ == "__main__":
    create_and_seed_database()