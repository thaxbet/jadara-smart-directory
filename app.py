from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import re
import socket
from datetime import datetime
from markupsafe import Markup

app = Flask(__name__)
app.secret_key = "jadara_university_secret_key_2026_v7"
DB_NAME = "database.db"


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


LAN_IP = get_lan_ip()

ARABIC_DIGITS_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def norm_digits(text: str) -> str:
    return (text or "").translate(ARABIC_DIGITS_MAP)



def create_and_seed_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS Messages")
    cursor.execute("DROP TABLE IF EXISTS OfficeHours")
    cursor.execute("DROP TABLE IF EXISTS Users")
    cursor.execute("DROP TABLE IF EXISTS Doctors")
    cursor.execute("DROP TABLE IF EXISTS Departments")
    cursor.execute("DROP TABLE IF EXISTS Buildings")

    cursor.execute("""
    CREATE TABLE Buildings (
        code TEXT PRIMARY KEY,
        name_ar TEXT NOT NULL,
        name_en TEXT NOT NULL,
        description_ar TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE Departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        building_code TEXT NOT NULL,
        FOREIGN KEY (building_code) REFERENCES Buildings(code)
    )
    """)

    cursor.execute("""
    CREATE TABLE Doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        academic_rank TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        building_code TEXT NOT NULL,
        floor TEXT NOT NULL,
        office_number TEXT NOT NULL,
        email TEXT NOT NULL,
        live_status TEXT DEFAULT 'Available',
        is_deleted INTEGER DEFAULT 0,
        FOREIGN KEY (department_id) REFERENCES Departments(id),
        FOREIGN KEY (building_code) REFERENCES Buildings(code)
    )
    """)

    cursor.execute("""
    CREATE TABLE OfficeHours (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        days TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        FOREIGN KEY (doctor_id) REFERENCES Doctors(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        doctor_id INTEGER,
        full_name TEXT,
        student_number TEXT,
        department_id INTEGER,
        FOREIGN KEY (doctor_id) REFERENCES Doctors(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE Messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_user_id INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        student_number TEXT NOT NULL,
        doctor_id INTEGER NOT NULL,
        template_type TEXT NOT NULL,
        student_note TEXT,
        doctor_status TEXT DEFAULT 'Pending',
        suggested_time TEXT DEFAULT '',
        doctor_reply TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        replied_at TEXT DEFAULT '',
        FOREIGN KEY (student_user_id) REFERENCES Users(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES Doctors(id) ON DELETE CASCADE
    )
    """)

    buildings = [
        ("A", "مبنى A — الشبكات والأمن السيبراني", "Building A — Networks & Cyber Security", "يضم مكاتب وقاعات الشبكات والأمن السيبراني والهندسة"),
        ("B", "مبنى B — تكنولوجيا المعلومات (IT)", "Building B — Information Technology (IT)", "يضم أقسام هندسة البرمجيات وعلم الحاسوب وتكنولوجيا المعلومات"),
        ("C", "مبنى C — الروبوتات والذكاء الاصطناعي", "Building C — Robotics & Artificial Intelligence", "يضم أقسام الروبوتات والذكاء الاصطناعي والأعمال"),
        ("D", "مبنى D — علوم إنترنت الأشياء", "Building D — Internet of Things (IoT)", "يضم أقسام علوم إنترنت الأشياء والعلوم المساندة"),
    ]
    cursor.executemany(
        "INSERT INTO Buildings (code, name_ar, name_en, description_ar) VALUES (?, ?, ?, ?)",
        buildings,
    )

    departments = [
        ("هندسة البرمجيات", "B"),
        ("علم الحاسوب", "B"),
        ("الروبوتات والذكاء الاصطناعي", "C"),
        ("شبكات الحاسوب والأمن السيبراني", "A"),
        ("علوم إنترنت الأشياء", "D"),
        ("إدارة الأعمال", "C"),
        ("المحاسبة", "C"),
        ("القانون", "A"),
        ("الهندسة المدنية", "A"),
        ("اللغة الإنجليزية والترجمة", "D"),
    ]
    cursor.executemany(
        "INSERT INTO Departments (name, building_code) VALUES (?, ?)",
        departments,
    )

    first_names = [
        "أحمد", "محمد", "محمود", "علي", "عمر", "خالد", "طارق", "زيد", "فراس", "رامي",
        "سامر", "ياسر", "بلال", "عماد", "زياد", "وليد", "مهند", "أنس", "حسام", "نبيل",
        "سارة", "رنا", "مريم", "لينا", "نور", "هدى", "دانا", "ربى", "ميساء", "عبير",
    ]
    middle_names = [
        "إبراهيم", "عبدالله", "حسين", "حسن", "سليمان", "يوسف", "صالح", "جمال", "كمال", "فؤاد",
        "توفيق", "منصور", "ناصر", "سمير", "عادل", "ماهر", "قيس", "سفيان", "عدنان", "رضوان",
    ]
    last_names = [
        "خليل", "الزعبي", "العمري", "الخطيب", "المومني", "الرواشدة", "العبادي", "البطاينة", "الجبور", "القرعان",
        "الحراحشة", "الخوالدة", "الشرمان", "العزام", "عبيدات", "ملكاوي", "خصاونة", "طبيشات", "قواسمة", "شطناوي",
    ]
    en_first = [
        "a", "m", "ma", "al", "o", "k", "t", "z", "f", "r",
        "s", "y", "b", "e", "zi", "w", "mu", "an", "h", "n",
        "sa", "ra", "mr", "l", "no", "hu", "d", "ru", "my", "ab",
    ]
    en_last = [
        "khalil", "zoubi", "omari", "khatib", "momani", "rawashdeh", "abbadi", "bataineh", "jabour", "quraan",
        "harahsheh", "khawaldeh", "shorman", "azzam", "obeidat", "malkawi", "khasawneh", "tbeishat", "qawasmeh", "shatnawi",
    ]
    ranks = ["أستاذ دكتور", "أستاذ مشارك", "أستاذ مساعد", "مدرس"]
    floors = ["الطابق الأول", "الطابق الثاني", "الطابق الثالث"]
    day_patterns = [
        "الأحد , الثلاثاء , الخميس",
        "الإثنين , الأربعاء",
        "الأحد , الثلاثاء",
        "الإثنين , الأربعاء , الخميس",
        "الأحد , الإثنين , الثلاثاء , الأربعاء , الخميس",
        "السبت , الإثنين , الأربعاء",
        "الثلاثاء , الخميس",
    ]
    time_slots = [
        ("09:00", "10:30"),
        ("10:00", "11:00"),
        ("11:00", "12:30"),
        ("12:00", "13:30"),
        ("13:00", "14:30"),
        ("14:00", "15:30"),
    ]
    live_statuses = ["Available", "Available", "Available", "InLecture", "Busy", "OffDuty"]

    cursor.execute("INSERT INTO Users (username, password, role, doctor_id, full_name) VALUES ('admin', 'admin123', 'admin', NULL, 'مدير النظام')")

    used_usernames = {"admin"}

    for idx in range(1, 101):
        dept_id = ((idx - 1) % 10) + 1
        b_code = departments[dept_id - 1][1]

        if idx == 1:
            full_name = "د. أحمد إبراهيم خليل"
            rank = "أستاذ مشارك"
            dept_id = 1
            b_code = "B"
            floor = "الطابق الثاني"
            office = "B-204"
            email = "a.khalil@jadara.edu.jo"
            uname = "a.khalil"
            days = "الأحد , الثلاثاء , الخميس"
            st, et = "10:00", "11:00"
            l_stat = "Available"
        elif idx == 70:
            full_name = "د. معن مروان علي الزعبي"
            rank = "أستاذ مساعد"
            dept_id = 1
            b_code = "B"
            floor = "الطابق الثاني"
            office = "B-210"
            email = "m.alzoubi@jadara.edu.jo"
            uname = "m.alzoubi"
            days = "الأحد , الثلاثاء , الخميس"
            st, et = "11:00", "12:30"
            l_stat = "Available"
        else:
            fn = first_names[(idx * 3) % len(first_names)]
            mn = middle_names[(idx * 7) % len(middle_names)]
            ln = last_names[(idx * 5) % len(last_names)]
            prefix = "أ.د." if idx % 6 == 0 else "د."
            full_name = f"{prefix} {fn} {mn} {ln}"
            rank = ranks[idx % len(ranks)]
            floor_idx = (idx % 3)
            floor = floors[floor_idx]
            room_num = (floor_idx + 1) * 100 + ((idx % 25) + 1)
            office = f"{b_code}-{room_num}"
            ef = en_first[(idx * 3) % len(en_first)]
            el = en_last[(idx * 5) % len(en_last)]
            uname = f"{ef}.{el}{idx}"
            if uname in used_usernames:
                uname = f"doc{idx}"
            email = f"{uname}@jadara.edu.jo"
            days = day_patterns[idx % len(day_patterns)]
            st, et = time_slots[idx % len(time_slots)]
            l_stat = live_statuses[idx % len(live_statuses)]

        used_usernames.add(uname)

        cursor.execute(
            """
            INSERT INTO Doctors (full_name, academic_rank, department_id, building_code, floor, office_number, email, live_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (full_name, rank, dept_id, b_code, floor, office, email, l_stat),
        )
        doc_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO OfficeHours (doctor_id, days, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            (doc_id, days, st, et),
        )

        cursor.execute(
            """
            INSERT INTO Users (username, password, role, doctor_id, full_name)
            VALUES (?, 'doctor123', 'doctor', ?, ?)
            """,
            (uname, doc_id, full_name),
        )

    students = [
        ("thabet", "student123", "student", "ثابت قيس محمد قواسمة", "202220020", 1),
        ("aws", "student123", "student", "أوس ماهر عللوه", "202210304", 1),
        ("yazeed", "student123", "student", "يزيد معاوية سفيان شلول", "202211043", 1),
    ]
    for u, p, r, fn, sn, did in students:
        cursor.execute(
            """
            INSERT INTO Users (username, password, role, doctor_id, full_name, student_number, department_id)
            VALUES (?, ?, ?, NULL, ?, ?, ?)
            """,
            (u, p, r, fn, sn, did),
        )

    sample_messages = [
        (
            102,
            "ثابت قيس محمد قواسمة",
            "202220020",
            70,
            "مناقشة مشروع التخرج / تدريب ميداني",
            "دكتور معن يعطيك العافية، نود عرض التحديث الجديد لمشروع التخرج اليوم.",
            "Available",
            "11:30 صباحاً",
            "أهلاً بك يا ثابت، أنا متاح في مكتبي B-210 الساعة 11:30 صباحاً، تفضلوا بالحضور.",
            "2026-11-10 09:15",
            "2026-11-10 09:30",
        ),
        (
            102,
            "ثابت قيس محمد قواسمة",
            "202220020",
            1,
            "طلب موعد إرشاد أكاديمي / استفسار عن مادة",
            "دكتور أحمد، هل يمكنني المرور لمراجعة خطة الفصل القادم؟",
            "Postponed",
            "01:15 ظهراً",
            "لدي اجتماع قسم الساعة 10، يرجى التأجيل والحضور الساعة 01:15 ظهراً.",
            "2026-11-10 10:00",
            "2026-11-10 10:12",
        ),
        (
            103,
            "أوس ماهر عللوه",
            "202210304",
            1,
            "طلب تحديد موعد بديل للساعات المكتبية",
            "دكتور أحمد، لدي محاضرة وقت الساعات المكتبية، متى يناسبك أن أمر عليك؟",
            "Pending",
            "",
            "",
            "2026-11-10 10:25",
            "",
        ),
    ]
    cursor.executemany(
        """
        INSERT INTO Messages (student_user_id, student_name, student_number, doctor_id, template_type, student_note, doctor_status, suggested_time, doctor_reply, created_at, replied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sample_messages,
    )

    conn.commit()
    conn.close()
    print("✅ تم إنشاء قاعدة البيانات (100 دكتور + بوابة الطلبة + نظام المراسلة الذكي) بنجاح!")

def ensure_db_ready():
    need_rebuild = not os.path.exists(DB_NAME)
    if not need_rebuild:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA table_info(Departments)")
            dept_cols = [c[1] for c in cur.fetchall()]
            cur.execute("PRAGMA table_info(Doctors)")
            doc_cols = [c[1] for c in cur.fetchall()]
            cur.execute("PRAGMA table_info(Users)")
            user_cols = [c[1] for c in cur.fetchall()]
            cur.execute("PRAGMA table_info(Messages)")
            msg_cols = [c[1] for c in cur.fetchall()]
            if (
                "id" not in dept_cols
                or "name" not in dept_cols
                or "building_code" not in dept_cols
                or "live_status" not in doc_cols
                or "student_number" not in user_cols
                or "doctor_status" not in msg_cols
            ):
                need_rebuild = True
            elif "is_deleted" not in doc_cols:
                cur.execute("ALTER TABLE Doctors ADD COLUMN is_deleted INTEGER DEFAULT 0")
                conn.commit()
        except Exception:
            need_rebuild = True
        finally:
            conn.close()
    if need_rebuild:
        create_and_seed_database()


ensure_db_ready()


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


ALL_DAYS_AR = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس"]
ALL_FLOORS_AR = ["الطابق الأرضي", "الطابق الأول", "الطابق الثاني", "الطابق الثالث"]

LIVE_STATUS_META = [
    ("Available", "🟢 متواجد بالمكتب الآن", "🟢 Available in Office Now", "st-Available"),
    ("Busy", "🟡 في اجتماع قسم / مشغول", "🟡 In Dept Meeting / Busy", "st-InLecture"),
    ("InLecture", "🔴 في محاضرة حالياً", "🔴 In Lecture Now", "st-Busy"),
    ("OffDuty", "⚪ غير متواجد / خارج الدوام", "⚪ Off Duty / Unavailable", "st-OffDuty"),
]

DAY_EN = {
    "السبت": "Saturday",
    "الأحد": "Sunday",
    "الإثنين": "Monday",
    "الثلاثاء": "Tuesday",
    "الأربعاء": "Wednesday",
    "الخميس": "Thursday",
}

DAY_SHORT_EN = {
    "السبت": "Sat",
    "الأحد": "Sun",
    "الإثنين": "Mon",
    "الثلاثاء": "Tue",
    "الأربعاء": "Wed",
    "الخميس": "Thu",
}

DEPT_EN = {
    "هندسة البرمجيات": "Software Engineering",
    "علم الحاسوب": "Computer Science",
    "الأمن السيبراني": "Cyber Security",
    "الذكاء الاصطناعي": "Artificial Intelligence",
    "إدارة الأعمال": "Business Administration",
    "المحاسبة": "Accounting",
    "القانون": "Law",
    "الهندسة المدنية": "Civil Engineering",
    "الصيدلة": "Pharmacy",
    "اللغة الإنجليزية والترجمة": "English Language & Translation",
    "الروبوتات والذكاء الاصطناعي": "Robotics & Artificial Intelligence",
    "شبكات الحاسوب والأمن السيبراني": "Computer Networks & Cyber Security",
    "علوم إنترنت الأشياء": "Internet of Things (IoT)",
}

DEPT_WORD_EN = {
    "هندسة": "Engineering",
    "الهندسة": "Engineering",
    "علم": "Science",
    "علوم": "Sciences",
    "العلوم": "Sciences",
    "تكنولوجيا": "Technology",
    "المعلومات": "Information",
    "الحاسوب": "Computer",
    "البرمجيات": "Software",
    "الأمن": "Security",
    "السيبراني": "Cyber",
    "الذكاء": "Artificial",
    "الاصطناعي": "Intelligence",
    "إدارة": "Management",
    "الإدارة": "Administration",
    "الأعمال": "Business",
    "المحاسبة": "Accounting",
    "القانون": "Law",
    "المدنية": "Civil",
    "المعمارية": "Architecture",
    "الكهربائية": "Electrical",
    "الميكانيكية": "Mechanical",
    "الصناعية": "Industrial",
    "الطبية": "Biomedical",
    "الصيدلة": "Pharmacy",
    "التمريض": "Nursing",
    "الطب": "Medicine",
    "الأسنان": "Dentistry",
    "البيانات": "Data",
    "الشبكات": "Networks",
    "شبكات": "Networks",
    "الاتصالات": "Telecommunications",
    "نظم": "Systems",
    "المالية": "Finance",
    "والمصرفية": "& Banking",
    "التسويق": "Marketing",
    "الرقمي": "Digital",
    "اللغة": "Language",
    "العربية": "Arabic",
    "الإنجليزية": "English",
    "والترجمة": "& Translation",
    "الترجمة": "Translation",
    "التربية": "Education",
    "الخاصة": "Special",
    "الرياضية": "Physical Education",
    "الرياضيات": "Mathematics",
    "الفيزياء": "Physics",
    "الكيمياء": "Chemistry",
    "الأحياء": "Biology",
    "الإعلام": "Media",
    "الصحافة": "Journalism",
    "التصميم": "Design",
    "الجرافيكي": "Graphic",
    "الداخلي": "Interior",
    "الروبوتات": "Robotics",
    "إنترنت": "Internet of",
    "الأشياء": "Things (IoT)",
}

RANK_EN = {
    "أستاذ دكتور": "Full Professor",
    "أستاذ مشارك": "Associate Professor",
    "أستاذ مساعد": "Assistant Professor",
    "مدرس": "Lecturer",
}

FLOOR_EN = {
    "الطابق الأرضي": "Ground Floor",
    "الطابق الأول": "First Floor",
    "الطابق الثاني": "Second Floor",
    "الطابق الثالث": "Third Floor",
    "الطابق الرابع": "Fourth Floor",
}

NAME_EN = {
    "أ.د.": "Prof. Dr.",
    "د.": "Dr.",
    "ثابت": "Thabet",
    "قيس": "Qais",
    "محمد": "Mohammad",
    "قواسمة": "Qawasmeh",
    "القواسمة": "Al-Qawasmeh",
    "أوس": "Aws",
    "ماهر": "Maher",
    "عللوه": "Alalweh",
    "يزيد": "Yazeed",
    "معاوية": "Muawiyah",
    "سفيان": "Sufyan",
    "شلول": "Shaloul",
    "الشلول": "Al-Shaloul",
    "معن": "Maan",
    "مروان": "Marwan",
    "علي": "Ali",
    "الزعبي": "Al-Zoubi",
    "أحمد": "Ahmad",
    "احمد": "Ahmad",
    "إبراهيم": "Ibrahim",
    "ابراهيم": "Ibrahim",
    "خليل": "Khalil",
    "محمود": "Mahmoud",
    "عمر": "Omar",
    "خالد": "Khaled",
    "طارق": "Tareq",
    "زيد": "Zaid",
    "فراس": "Firas",
    "رامي": "Rami",
    "سامر": "Samer",
    "ياسر": "Yasser",
    "بلال": "Bilal",
    "عماد": "Imad",
    "زياد": "Ziad",
    "وليد": "Waleed",
    "مهند": "Mohannad",
    "أنس": "Anas",
    "حسام": "Hussam",
    "نبيل": "Nabil",
    "سارة": "Sara",
    "رنا": "Rana",
    "مريم": "Maryam",
    "لينا": "Lina",
    "نور": "Noor",
    "هدى": "Huda",
    "دانا": "Dana",
    "ربى": "Ruba",
    "ميساء": "Maysaa",
    "عبير": "Abeer",
    "عبدالله": "Abdullah",
    "حسين": "Hussein",
    "حسن": "Hassan",
    "سليمان": "Suleiman",
    "يوسف": "Yousef",
    "صالح": "Saleh",
    "جمال": "Jamal",
    "كمال": "Kamal",
    "فؤاد": "Fouad",
    "توفيق": "Tawfiq",
    "منصور": "Mansour",
    "ناصر": "Nasser",
    "سمير": "Samir",
    "عادل": "Adel",
    "عدنان": "Adnan",
    "رضوان": "Radwan",
    "العمري": "Al-Omari",
    "الخطيب": "Al-Khatib",
    "المومني": "Al-Momani",
    "الرواشدة": "Al-Rawashdeh",
    "العبادي": "Al-Abbadi",
    "البطاينة": "Al-Bataineh",
    "الجبور": "Al-Jabour",
    "القرعان": "Al-Quraan",
    "الحراحشة": "Al-Harahsheh",
    "الخوالدة": "Al-Khawaldeh",
    "الشرمان": "Al-Shorman",
    "العزام": "Al-Azzam",
    "عبيدات": "Obeidat",
    "ملكاوي": "Malkawi",
    "خصاونة": "Khasawneh",
    "الخصاونة": "Al-Khasawneh",
    "طبيشات": "Tbeishat",
    "شطناوي": "Shatnawi",
    "التميمي": "Al-Tamimi",
    "الشبول": "Al-Shboul",
    "الجراح": "Al-Jarrah",
    "الزريقي": "Al-Zureiqi",
    "العتيبي": "Al-Otaibi",
    "مدير": "System",
    "النظام": "Admin",
}

AR_CHAR_MAP = {
    "ا": "a", "أ": "a", "إ": "i", "آ": "a", "ب": "b", "ت": "t", "ث": "th",
    "ج": "j", "ح": "h", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "ع": "a",
    "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "ة": "h", "و": "w", "ي": "y", "ى": "a", "ئ": "e", "ؤ": "o", "ء": "",
}

STUDENT_TEMPLATES = [
    ("طلب موعد إرشاد أكاديمي / استفسار عن مادة", "Academic Advising / Course Inquiry Appointment"),
    ("مناقشة مشروع التخرج / تدريب ميداني", "Graduation Project / Field Training Discussion"),
    ("طلب تحديد موعد بديل للساعات المكتبية", "Request Alternative Office Hours Slot"),
    ("رسالة مباشرة من الدكتور إلى الطالب", "Direct Message / Appointment from Doctor to Student"),
]

TPL_EN_MAP = {ar: en for ar, en in STUDENT_TEMPLATES}

MSG_PHRASES_EN = {
    "دكتور معن يعطيك العافية، نود عرض التحديث الجديد لمشروع التخرج اليوم.": "Dr. Maan, we would like to present our new graduation project update today.",
    "أهلاً بك يا ثابت، أنا متاح في مكتبي B-210 الساعة 11:30 صباحاً، تفضلوا بالحضور.": "Welcome Thabet, I am available in my office B-210 at 11:30 AM, please come by.",
    "دكتور أحمد، هل يمكنني المرور لمراجعة خطة الفصل القادم؟": "Dr. Ahmad, may I pass by to review next semester's study plan?",
    "لدي اجتماع قسم الساعة 10، يرجى التأجيل والحضور الساعة 01:15 ظهراً.": "I have a department meeting at 10:00, please postpone and come at 01:15 PM.",
    "دكتور أحمد، لدي محاضرة وقت الساعات المكتبية، متى يناسبك أن أمر عليك؟": "Dr. Ahmad, I have a lecture during office hours, when can I pass by?",
    "يرجى الحضور في الموعد المحدد": "Please attend at the specified hour",
    "صباحاً": "AM",
    "ظهراً": "PM",
    "مساءً": "PM",
}


def transliterate_ar_word(word: str) -> str:
    if not any("\u0600" <= ch <= "\u06FF" for ch in word):
        return word
    if word.startswith("ال") and len(word) > 2:
        rest = "".join(AR_CHAR_MAP.get(ch, ch) for ch in word[2:])
        return "Al-" + rest.capitalize()
    out = "".join(AR_CHAR_MAP.get(ch, ch) for ch in word)
    return out.capitalize()


def tr_name(ar_name: str, lang: str) -> str:
    if not ar_name or lang != "en":
        return ar_name or ""
    parts = ar_name.split()
    return " ".join(NAME_EN.get(p, transliterate_ar_word(p)) for p in parts)


def tr_dept(ar_dept: str, lang: str) -> str:
    if not ar_dept or lang != "en":
        return ar_dept or ""
    if ar_dept in DEPT_EN:
        return DEPT_EN[ar_dept]
    parts = ar_dept.split()
    return " ".join(DEPT_WORD_EN.get(p, transliterate_ar_word(p)) for p in parts)


def tr_rank(ar_rank: str, lang: str) -> str:
    if lang != "en":
        return ar_rank
    return RANK_EN.get(ar_rank, ar_rank)


def tr_floor(ar_floor: str, lang: str) -> str:
    if not ar_floor or lang != "en":
        return ar_floor or ""
    return FLOOR_EN.get(ar_floor, transliterate_ar_word(ar_floor))


def tr_days(ar_days: str, lang: str) -> str:
    if not ar_days or lang != "en":
        return ar_days or ""
    out = ar_days
    for k, v in DAY_EN.items():
        out = out.replace(k, v)
    return out.replace("،", ",")


def tr_days_short(ar_days: str) -> str:
    if not ar_days:
        return ""
    out = ar_days
    for k, v in DAY_SHORT_EN.items():
        out = out.replace(k, v)
    return out.replace("،", ",").replace(" ", "")


def tr_tpl(tpl_text: str, lang: str) -> str:
    if not tpl_text or lang != "en":
        return tpl_text or ""
    return TPL_EN_MAP.get(tpl_text, tr_msg(tpl_text, lang))


def tr_msg(msg_text: str, lang: str) -> str:
    if not msg_text or lang != "en":
        return msg_text or ""
    if msg_text in MSG_PHRASES_EN:
        return MSG_PHRASES_EN[msg_text]
    out = msg_text
    for k, v in MSG_PHRASES_EN.items():
        out = out.replace(k, v)
    return out


def generate_qr_svg(text_to_encode: str, size: int = 148) -> Markup:
    """Pure-Python ISO/IEC 18004 QR Code Generator (Versions 2-8, Level L)."""
    data = text_to_encode.encode("utf-8")
    SPECS = [
        (2, 25, 34, 10, 1, [6, 18], None),
        (3, 29, 55, 15, 1, [6, 22], None),
        (4, 33, 80, 20, 1, [6, 26], None),
        (5, 37, 108, 26, 1, [6, 30], None),
        (6, 41, 136, 18, 2, [6, 34], None),
        (7, 45, 156, 20, 2, [6, 22, 38], 0x07C94),
        (8, 49, 194, 24, 2, [6, 24, 42], 0x085BC),
    ]
    for ver, N, data_cw, ecc_per_blk, num_blk, align_pos, ver_info in SPECS:
        if len(data) <= data_cw - 2:
            break
    else:
        ver, N, data_cw, ecc_per_blk, num_blk, align_pos, ver_info = SPECS[-1]
        data = data[: data_cw - 2]

    exp = [0] * 512
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        exp[i] = exp[i - 255]

    g = [1]
    for i in range(ecc_per_blk):
        ng = [0] * (len(g) + 1)
        for j, v in enumerate(g):
            ng[j] ^= v
            ng[j + 1] ^= exp[log[v] + i] if v else 0
        g = ng

    bits = [0, 1, 0, 0]
    n = len(data)
    for i in range(7, -1, -1):
        bits.append((n >> i) & 1)
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    bits.extend([0] * min(4, data_cw * 8 - len(bits)))
    while len(bits) % 8 != 0:
        bits.append(0)
    codewords = [int("".join(str(b) for b in bits[i : i + 8]), 2) for i in range(0, len(bits), 8)]
    pad_bytes = [0xEC, 0x11]
    idx = 0
    while len(codewords) < data_cw:
        codewords.append(pad_bytes[idx % 2])
        idx += 1

    def rs_encode(blk):
        rem = blk[:] + [0] * ecc_per_blk
        for i in range(len(blk)):
            coef = rem[i]
            if coef != 0:
                l_c = log[coef]
                for j in range(1, ecc_per_blk + 1):
                    if g[j] != 0:
                        rem[i + j] ^= exp[l_c + log[g[j]]]
        return rem[len(blk) :]

    if num_blk == 1:
        all_cw = codewords + rs_encode(codewords)
    else:
        k = data_cw // num_blk
        b1, b2 = codewords[:k], codewords[k:]
        e1, e2 = rs_encode(b1), rs_encode(b2)
        all_cw = []
        for i in range(k):
            all_cw.extend([b1[i], b2[i]])
        for i in range(ecc_per_blk):
            all_cw.extend([e1[i], e2[i]])

    stream = []
    for cw in all_cw:
        for i in range(7, -1, -1):
            stream.append((cw >> i) & 1)
    stream.extend([0] * 7)

    mat = [[0] * N for _ in range(N)]
    is_func = [[False] * N for _ in range(N)]

    def set_finder(r0, c0):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                r, c = r0 + dr, c0 + dc
                if 0 <= r < N and 0 <= c < N:
                    on = (0 <= dr <= 6 and 0 <= dc <= 6) and (
                        dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4)
                    )
                    mat[r][c] = 1 if on else 0
                    is_func[r][c] = True

    set_finder(0, 0)
    set_finder(0, N - 7)
    set_finder(N - 7, 0)

    for ar in align_pos:
        for ac in align_pos:
            if (ar == 6 and ac == 6) or (ar == 6 and ac == N - 7) or (ar == N - 7 and ac == 6):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    r, c = ar + dr, ac + dc
                    on = abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0)
                    mat[r][c] = 1 if on else 0
                    is_func[r][c] = True

    for i in range(8, N - 8):
        if not is_func[6][i]:
            mat[6][i] = (i + 1) % 2
            is_func[6][i] = True
        if not is_func[i][6]:
            mat[i][6] = (i + 1) % 2
            is_func[i][6] = True

    mat[N - 8][8] = 1
    is_func[N - 8][8] = True
    for i in range(9):
        if i != 6:
            is_func[8][i] = is_func[i][8] = True
    for i in range(8):
        is_func[8][N - 1 - i] = is_func[N - 1 - i][8] = True

    if ver_info is not None:
        for i in range(18):
            bit = (ver_info >> i) & 1
            r, c = i // 3, N - 11 + (i % 3)
            mat[r][c] = mat[c][r] = bit
            is_func[r][c] = is_func[c][r] = True

    bit_idx = 0
    up = True
    col = N - 1
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(N - 1, -1, -1) if up else range(N)
        for r in rows:
            for c in (col, col - 1):
                if not is_func[r][c]:
                    b = stream[bit_idx] if bit_idx < len(stream) else 0
                    bit_idx += 1
                    if (r + c) % 2 == 0:
                        b ^= 1
                    mat[r][c] = b
        up = not up
        col -= 2

    fmt = [int(x) for x in "111011111000100"]
    f_pos1 = [
        (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
        (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8),
    ]
    f_pos2 = [
        (N - 1, 8), (N - 2, 8), (N - 3, 8), (N - 4, 8), (N - 5, 8), (N - 6, 8), (N - 7, 8),
        (8, N - 8), (8, N - 7), (8, N - 6), (8, N - 5), (8, N - 4), (8, N - 3), (8, N - 2), (8, N - 1),
    ]
    for i, b in enumerate(fmt):
        r1, c1 = f_pos1[i]
        r2, c2 = f_pos2[i]
        mat[r1][c1] = b
        mat[r2][c2] = b

    quiet = 4
    tot = N + 2 * quiet
    rects = [f'<rect x="0" y="0" width="{tot}" height="{tot}" fill="#ffffff"/>']
    for r in range(N):
        for c in range(N):
            if mat[r][c]:
                rects.append(f'<rect x="{c+quiet}" y="{r+quiet}" width="1" height="1" fill="#0f2942"/>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {tot} {tot}" shape-rendering="crispEdges" style="background:#fff; border-radius:8px; border:1px solid #cbd5e1; display:block; margin:0 auto;">{"".join(rects)}</svg>'
    return Markup(svg)


def build_doctor_qr_payload(doc, mode: str = "vcard") -> str:
    en_name = tr_name(doc["full_name"], "en")
    office = doc["office_number"]
    days_short = tr_days_short(doc["days"] or "")
    hours = f"{doc['start_time'] or ''}-{doc['end_time'] or ''}"
    if mode == "url":
        return f"http://{LAN_IP}:5000/doctor/{doc['id']}"
    return (
        f"BEGIN:VCARD\n"
        f"VERSION:3.0\n"
        f"FN:{en_name}\n"
        f"ORG:Jadara Univ ({office})\n"
        f"EMAIL:{doc['email']}\n"
        f"NOTE:Hours:{days_short} {hours}\n"
        f"END:VCARD"
    )


@app.context_processor
def inject_helpers():
    lang = session.get("lang", "ar")
    unread_student_replies = 0
    pending_doc_msgs = 0
    try:
        conn = get_db_connection()
        if session.get("role") == "student":
            uid = session.get("user_id", 0)
            snum = session.get("student_number", "")
            sname = session.get("full_name", "")
            row = conn.execute(
                """
                SELECT COUNT(*) AS c FROM Messages
                WHERE (student_user_id = ? OR (student_number != '' AND student_number = ?) OR LOWER(student_name) = LOWER(?))
                  AND doctor_status != 'Pending'
                """,
                (uid, snum, sname),
            ).fetchone()
            unread_student_replies = row["c"] if row else 0
        elif session.get("role") == "doctor" and session.get("doctor_id"):
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM Messages WHERE doctor_id = ? AND doctor_status = 'Pending'",
                (session["doctor_id"],),
            ).fetchone()
            pending_doc_msgs = row["c"] if row else 0
        conn.close()
    except Exception:
        pass

    return dict(
        lang=lang,
        tr_name=tr_name,
        tr_dept=tr_dept,
        tr_rank=tr_rank,
        tr_floor=tr_floor,
        tr_days=tr_days,
        tr_tpl=tr_tpl,
        tr_msg=tr_msg,
        ALL_DAYS_AR=ALL_DAYS_AR,
        ALL_FLOORS_AR=ALL_FLOORS_AR,
        LIVE_STATUS_META=LIVE_STATUS_META,
        DAY_EN=DAY_EN,
        FLOOR_EN=FLOOR_EN,
        STUDENT_TEMPLATES=STUDENT_TEMPLATES,
        generate_qr_svg=generate_qr_svg,
        build_doctor_qr_payload=build_doctor_qr_payload,
        LAN_IP=LAN_IP,
        unread_student_replies=unread_student_replies,
        pending_doc_msgs=pending_doc_msgs,
    )


@app.route("/set_lang/<lang_code>")
def set_lang(lang_code):
    session["lang"] = "en" if lang_code == "en" else "ar"
    return redirect(request.referrer or url_for("home"))


BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="{{ 'en' if lang == 'en' else 'ar' }}" dir="{{ 'ltr' if lang == 'en' else 'rtl' }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ 'Jadara University | Smart Faculty Office Hours & AI Assistant' if lang == 'en' else 'جامعة جدارا | دليل الساعات المكتبية ومواقع الدكاترة الذكي' }}</title>
    <style>
        :root {
            --primary: #0f2942;
            --secondary: #0284c7;
            --accent: #d97706;
            --bg: #f1f5f9;
            --card: #ffffff;
            --text: #1e293b;
            --muted: #64748b;
            --border: #e2e8f0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: var(--bg); color: var(--text); line-height: 1.6; padding-bottom: 80px; }
        .navbar {
            background: linear-gradient(135deg, #0f2942 0%, #1e3a8a 100%);
            color: white;
            padding: 0.85rem 1.8rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            flex-wrap: wrap;
            gap: 10px;
        }
        .navbar h1 { font-size: 1.22rem; font-weight: 700; }
        .navbar a { color: white; text-decoration: none; margin: 0 4px; font-weight: 600; padding: 6px 12px; border-radius: 6px; transition: 0.2s; font-size: 0.88rem; display: inline-flex; align-items: center; gap: 5px; }
        .navbar a:hover { background: rgba(255,255,255,0.15); }
        .navbar .btn-lang { background: #f59e0b; color: #0f2942; font-weight: 800; }
        .navbar .btn-student { background: #10b981; color: #ffffff; }
        .navbar .btn-nav { background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); }
        .notif-pill { background: #ef4444; color: #fff; border-radius: 999px; padding: 1px 7px; font-size: 0.74rem; font-weight: 800; }
        .container { max-width: 1280px; margin: 1.4rem auto; padding: 0 1.2rem; }

        /* Top Building Cards */
        .bldg-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(265px, 1fr));
            gap: 12px;
            margin-bottom: 1.1rem;
        }
        .bldg-card {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
            transition: 0.15s;
        }
        .bldg-card:hover { border-color: var(--secondary); transform: translateY(-1px); }
        .bldg-code-box {
            background: var(--primary);
            color: #ffffff;
            font-weight: 800;
            font-size: 1.15rem;
            width: 38px;
            height: 38px;
            border-radius: 9px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        /* 4-Column Filter Panel */
        .filter-panel {
            background: #ffffff;
            padding: 1.2rem;
            border-radius: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            margin-bottom: 1.2rem;
            border: 1px solid var(--border);
        }
        .search-bar-full {
            width: 100%;
            padding: 11px 16px;
            border: 1px solid #cbd5e1;
            border-radius: 9px;
            font-size: 0.94rem;
            margin-bottom: 12px;
            outline: none;
        }
        .search-bar-full:focus { border-color: var(--secondary); box-shadow: 0 0 0 3px rgba(2,132,199,0.12); }
        .four-cols {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(245px, 1fr));
            gap: 12px;
            margin-bottom: 12px;
        }
        .col-box {
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 11px 12px;
            max-height: 210px;
            overflow-y: auto;
        }
        .col-title { font-weight: 700; font-size: 0.85rem; color: var(--primary); margin-bottom: 8px; display: block; }
        .chip-list { display: flex; flex-wrap: wrap; gap: 6px; }
        .chip-label {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: white;
            border: 1px solid #cbd5e1;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.81rem;
            cursor: pointer;
            user-select: none;
            transition: 0.15s;
        }
        .chip-label:hover { border-color: var(--secondary); }
        .chip-label input { accent-color: var(--secondary); }

        .btn {
            background: var(--secondary);
            color: white;
            border: none;
            padding: 9px 18px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 700;
            font-size: 0.9rem;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn:hover { opacity: 0.93; }
        .btn-dark { background: #0f2942; color: white; }
        .btn-light { background: #e2e8f0; color: #1e293b; }
        .btn-danger { background: #dc2626; color: white; }
        .btn-success { background: #059669; color: white; }

        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(295px, 1fr)); gap: 1.1rem; }
        .card {
            background: var(--card);
            border-radius: 12px;
            padding: 1.2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .card-header { display: flex; justify-content: space-between; align-items: center; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
        .card h3 { color: var(--primary); font-size: 1.08rem; margin-top: 4px; }
        .badge {
            display: inline-block;
            background: #e0f2fe;
            color: #0369a1;
            padding: 3px 9px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
        }
        .badge-bldg { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .status-dot {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
        }
        .st-Available { background: #dcfce7; color: #166534; }
        .st-InLecture { background: #fef3c7; color: #92400e; }
        .st-Busy { background: #fee2e2; color: #991b1b; }
        .st-OffDuty { background: #e2e8f0; color: #475569; }
        .st-Postponed { background: #fef3c7; color: #92400e; }
        .st-Pending { background: #e0f2fe; color: #0369a1; }
        .info-row { margin: 4px 0; font-size: 0.85rem; color: #334155; }
        .hours-box {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            padding: 8px 10px;
            margin-top: 8px;
            border-radius: 8px;
            font-size: 0.83rem;
            text-align: center;
            color: #065f46;
            font-weight: 700;
        }
        .alert { padding: 12px 16px; border-radius: 8px; margin-bottom: 1rem; background: #dcfce7; color: #166534; font-weight: 600; border: 1px solid #86efac; }
        .alert-error { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; margin-top: 0.8rem; }
        th, td { padding: 10px 12px; border-bottom: 1px solid var(--border); text-align: start; font-size: 0.88rem; }
        th { background: var(--primary); color: white; }
        .form-box { background: white; padding: 1.5rem; border-radius: 12px; max-width: 680px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .form-group { margin-bottom: 0.9rem; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 9px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.92rem; }
        .template-radio {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #f8fafc;
            border: 2px solid #cbd5e1;
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .template-radio:hover { border-color: var(--secondary); background: #eff6ff; }
        .template-radio input { width: auto; accent-color: var(--secondary); transform: scale(1.2); }

        /* AI Chatbot Styles */
        .chat-fab {
            position: fixed;
            bottom: 20px;
            inset-inline-start: 22px;
            background: linear-gradient(135deg, #0284c7, #0f2942);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 12px 22px;
            font-size: 0.94rem;
            font-weight: 800;
            box-shadow: 0 6px 22px rgba(2,132,199,0.4);
            cursor: pointer;
            z-index: 999;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .chat-window {
            position: fixed;
            bottom: 76px;
            inset-inline-start: 22px;
            width: 390px;
            max-width: calc(100vw - 32px);
            background: white;
            border-radius: 16px;
            box-shadow: 0 12px 35px rgba(0,0,0,0.22);
            border: 1px solid var(--border);
            display: none;
            flex-direction: column;
            overflow: hidden;
            z-index: 1000;
        }
        .chat-header {
            background: linear-gradient(135deg, #0f2942, #1e3a8a);
            color: white;
            padding: 12px 15px;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-body {
            padding: 12px;
            height: 320px;
            overflow-y: auto;
            background: #f8fafc;
            display: flex;
            flex-direction: column;
            gap: 9px;
            font-size: 0.86rem;
        }
        .chat-chips {
            display: flex;
            gap: 6px;
            padding: 8px 10px;
            background: #f1f5f9;
            border-top: 1px solid #e2e8f0;
            overflow-x: auto;
            white-space: nowrap;
        }
        .chat-chip {
            background: #ffffff;
            color: #0f2942;
            border: 1px solid #cbd5e1;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.76rem;
            font-weight: 700;
            cursor: pointer;
            flex-shrink: 0;
        }
        .chat-chip:hover { background: #e0f2fe; border-color: #0284c7; }
        .msg-bot { background: white; border: 1px solid var(--border); padding: 10px 12px; border-radius: 12px; align-self: flex-start; max-width: 94%; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
        .msg-user { background: var(--secondary); color: white; padding: 8px 12px; border-radius: 12px; align-self: flex-end; max-width: 85%; font-weight: 600; }
        .chat-input { display: flex; border-top: 1px solid var(--border); background: white; }
        .chat-input input { flex: 1; border: none; padding: 12px; outline: none; font-size: 0.88rem; }
        .chat-input button { background: var(--secondary); color: white; border: none; padding: 0 16px; font-weight: 700; cursor: pointer; }
        @media print {
            .navbar, .chat-fab, .chat-window, .no-print { display: none !important; }
            body { background: white; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>🎓 <a href="/" style="padding:0; background:none;">{{ 'Smart Faculty Office Hours Directory' if lang == 'en' else 'دليل الساعات المكتبية ومواقع الدكاترة الذكي' }}</a></h1>
        <div>
            <a href="/">{{ '🏠 Home' if lang == 'en' else '🏠 الرئيسية' }}</a>
            {% if lang == 'en' %}
                <a href="/set_lang/ar" class="btn-lang">🌐 العربية</a>
            {% else %}
                <a href="/set_lang/en" class="btn-lang">🌐 English</a>
            {% endif %}
            {% if session.get('user_id') %}
                {% if session.get('role') == 'admin' %}
                    <a href="/admin" class="btn-nav">{{ '⚙️ Admin Panel' if lang == 'en' else '⚙️ لوحة المدير' }}</a>
                {% elif session.get('role') == 'doctor' %}
                    <a href="/dashboard" class="btn-nav">
                        {{ '👨‍🏫 Doctor Dashboard' if lang == 'en' else '👨‍🏫 لوحة الدكتور' }} ({{ session.get('username') }})
                        {% if pending_doc_msgs > 0 %}<span class="notif-pill">{{ pending_doc_msgs }}</span>{% endif %}
                    </a>
                {% elif session.get('role') == 'student' %}
                    <a href="/student" class="btn-student">
                        {{ '🎓 Student Portal & Replies' if lang == 'en' else '🎓 حساب الطالب وردود الدكاترة' }} ({{ tr_name(session.get('full_name') or session.get('username'), lang) }})
                        {% if unread_student_replies > 0 %}<span class="notif-pill">{{ unread_student_replies }}</span>{% endif %}
                    </a>
                {% endif %}
                <a href="/logout" class="btn-nav" style="background:#dc2626;">{{ '🚪 Logout' if lang == 'en' else '🚪 خروج' }}</a>
            {% else %}
                <a href="/register" class="btn-student">{{ '🎓 Student Sign Up' if lang == 'en' else '🎓 تسجيل حساب طالب جديد' }}</a>
                <a href="/login" class="btn-nav">{{ '🔐 Login (Student / Doctor / Admin)' if lang == 'en' else '🔐 دخول (طالب / دكتور / إدارة)' }}</a>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for cat, msg in messages %}
                    <div class="alert {{ 'alert-error' if cat == 'error' else '' }}">{{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>

    <!-- Conversational AI Chatbot -->
    <button class="chat-fab" onclick="toggleChat()">
        🤖 {{ 'AI Smart Assistant' if lang == 'en' else 'المساعد الذكي AI' }}
    </button>
    <div class="chat-window" id="chatWindow">
        <div class="chat-header">
            <div>
                <div style="font-size:0.95rem;">🤖 {{ 'Jadara AI Academic Assistant' if lang == 'en' else 'المساعد الذكي التفاعلي (Jadara AI)' }}</div>
                <div style="font-size:0.72rem; color:#93c5fd; font-weight:400;">{{ 'Interactive Faculty & Office Hours AI' if lang == 'en' else 'مدعوم بالذكاء التفاعلي لخدمة طلبة جدارا' }}</div>
            </div>
            <button onclick="toggleChat()" style="background:none;border:none;color:white;font-size:1.1rem;cursor:pointer;">✕</button>
        </div>
        <div class="chat-body" id="chatBody">
            <div class="msg-bot">
                {% if lang == 'en' %}
                    👋 <b>Hello my friend! How are you doing today? 😊</b>
                {% else %}
                    👋 <b>مرحباً بك يا صديقي! كيف حالك اليوم؟ 😊</b>
                {% endif %}
            </div>
        </div>
        <div class="chat-input">
            <input type="text" id="chatInput" placeholder="{{ 'Chat with Jadara AI...' if lang == 'en' else 'دردش مع المساعد الذكي أو اسأل عن دكتور...' }}" onkeydown="if(event.key==='Enter') sendChat()">
            <button onclick="sendChat()">{{ 'Send' if lang == 'en' else 'إرسال' }}</button>
        </div>
    </div>

    <script>
        function toggleChat() {
            const w = document.getElementById('chatWindow');
            w.style.display = (w.style.display === 'flex') ? 'none' : 'flex';
        }
        function quickAsk(text) {
            const inp = document.getElementById('chatInput');
            inp.value = text;
            sendChat();
        }
        async function sendChat() {
            const inp = document.getElementById('chatInput');
            const q = inp.value.trim();
            if (!q) return;
            const body = document.getElementById('chatBody');
            const uDiv = document.createElement('div');
            uDiv.className = 'msg-user';
            uDiv.textContent = q;
            body.appendChild(uDiv);
            inp.value = '';

            const typingDiv = document.createElement('div');
            typingDiv.className = 'msg-bot';
            typingDiv.style.color = '#64748b';
            typingDiv.innerHTML = '🤖 <i>{{ "Thinking..." if lang == "en" else "جاري التفكير والبحث..." }}</i>';
            body.appendChild(typingDiv);
            body.scrollTop = body.scrollHeight;

            try {
                const res = await fetch('/api/chatbot?q=' + encodeURIComponent(q));
                const data = await res.json();
                body.removeChild(typingDiv);
                const bDiv = document.createElement('div');
                bDiv.className = 'msg-bot';
                bDiv.innerHTML = data.reply;
                body.appendChild(bDiv);
                body.scrollTop = body.scrollHeight;
            } catch (e) {
                body.removeChild(typingDiv);
            }
        }
    </script>
</body>
</html>
"""


OFF_TOPIC_KEYWORDS = [
    "طبخ", "طبخه", "أكل", "اكلة", "منسف", "شاورما", "برغر", "بيتزا", "مطعم", "وصفة",
    "مباراة", "مباراه", "كرة قدم", "كورة", "ريال مدريد", "برشلونة", "ميسي", "رونالدو", "دوري",
    "فيلم", "افلام", "أفلام", "مسلسل", "نتفلكس", "أغنية", "اغنية", "موسيقى",
    "ببجي", "فورتنايت", "لعبة", "العاب", "ألعاب", "بلايستيشن",
    "سياسة", "انتخابات", "حرب", "بورصة", "بيتكوين", "عملات رقمية",
    "طقس", "درجة الحرارة", "امطار", "ثلج", "نكتة", "نكته", "اضحك", "شعر", "غزل", "حب", "زواج",
    "اكتب كود", "حل واجب", "برمج لي", "بايثون", "جافا",
    "football", "soccer", "messi", "ronaldo", "madrid", "barcelona", "recipe", "cooking", "pizza",
    "burger", "movie", "netflix", "pubg", "fortnite", "politics", "weather", "bitcoin", "crypto", "joke",
]

GREETING_KEYWORDS = [
    "مرحبا", "مرحباً", "اهلا", "أهلا", "أهلاً", "هلا", "السلام عليكم", "سلام", "صباح الخير",
    "مساء الخير", "يعطيك العافية", "يعطيكم العافية", "كيفك", "كيف حالك", "شو اخبارك", "شو أخبارك",
    "شخبارك", "من انت", "مين انت", "شو بتعمل", "عرفني بنفسك",
    "hello", "hi", "hey", "good morning", "good evening", "how are you", "who are you",
]

THANKS_KEYWORDS = [
    "شكرا", "شكراً", "يسلمو", "مشكور", "الله يعطيك العافية", "ممتاز", "رائع", "تمام",
    "thanks", "thank you", "awesome", "great", "perfect",
]


HOW_ARE_YOU_REPLIES = [
    "الحمدلله", "الحمد لله", "بخير", "تمام", "منيح", "ممتاز", "كويس", "عالي العال", "روعة", "روعه",
    "حياك", "الله يسعدك", "يسعدك", "طيب", "ماشي الحال", "نحمد الله", "اشكر الله", "مبسوط",
    "fine", "good", "great", "im good", "i am good", "i am fine", "doing well", "alhamdulillah", "all good",
]


@app.route("/api/chatbot")
def api_chatbot():
    raw_q = request.args.get("q", "").strip()
    q = norm_digits(raw_q)
    lang = session.get("lang", "ar")
    q_low = q.lower().strip()

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT d.id, d.full_name, d.academic_rank, d.building_code, d.floor, d.office_number, d.email, d.live_status,
               dept.name AS dept_name, oh.days, oh.start_time, oh.end_time
        FROM Doctors d
        JOIN Departments dept ON d.department_id = dept.id
        LEFT JOIN OfficeHours oh ON d.id = oh.doctor_id
        WHERE COALESCE(d.is_deleted, 0) = 0
        ORDER BY d.id ASC
        """
    ).fetchall()
    conn.close()

    def status_badge(st):
        if lang == "en":
            return {
                "Available": "🟢 Available in Office Now",
                "Busy": "🟡 In Dept Meeting / Busy",
                "InLecture": "🔴 In Lecture Now",
                "OffDuty": "⚪ Off Duty / Unavailable",
            }.get(st, "🟢 Available")
        return {
            "Available": "🟢 متواجد بالمكتب الآن",
            "Busy": "🟡 في اجتماع قسم / مشغول",
            "InLecture": "🔴 في محاضرة حالياً",
            "OffDuty": "⚪ غير متواجد / خارج الدوام",
        }.get(st, "🟢 متواجد بالمكتب الآن")

    def format_doc_card(m):
        st_lbl = status_badge(m["live_status"])
        if lang == "en":
            return (
                f"<div style='margin-top:6px;padding:8px;background:#f8fafc;border-radius:8px;border:1px solid #cbd5e1;'>"
                f"👨‍🏫 <b><a href='/doctor/{m['id']}' style='color:#0284c7;'>#{m['id']} - {tr_name(m['full_name'], 'en')}</a></b> ({tr_dept(m['dept_name'], 'en')})<br>"
                f"📡 Status: <b>{st_lbl}</b><br>"
                f"🏛️ Bldg <b>{m['building_code']}</b> ({tr_floor(m['floor'], 'en')}) — Office: <b>{m['office_number']}</b><br>"
                f"⏰ Hours: <b>{tr_days(m['days'] or '', 'en')} ({m['start_time']} - {m['end_time']})</b><br>"
                f"✉️ {m['email']} | <a href='/doctor/{m['id']}#msg-box' style='color:#059669;font-weight:700;'>Message Doctor</a></div>"
            )
        return (
            f"<div style='margin-top:6px;padding:8px;background:#f8fafc;border-radius:8px;border:1px solid #cbd5e1;'>"
            f"👨‍🏫 <b><a href='/doctor/{m['id']}' style='color:#0284c7;'>#{m['id']} - {m['full_name']}</a></b> ({m['dept_name']})<br>"
            f"📡 الحالة الآن: <b>{st_lbl}</b><br>"
            f"🏛️ مبنى <b>{m['building_code']}</b> ({m['floor']}) — مكتب: <b>{m['office_number']}</b><br>"
            f"⏰ الساعات المكتبية: <b>{m['days']} ({m['start_time']} - {m['end_time']})</b><br>"
            f"✉️ {m['email']} | <a href='/doctor/{m['id']}#msg-box' style='color:#059669;font-weight:700;'>مراسلة الدكتور</a></div>"
        )

    # 1. Check Out-of-Scope / Off-Topic keywords FIRST
    if any(k in q_low for k in OFF_TOPIC_KEYWORDS):
        if lang == "en":
            return jsonify({
                "reply": (
                    "<div style='background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;padding:10px;border-radius:8px;'>"
                    "⚠️ <b>AI Scope Warning (Out of Academic Scope):</b><br>"
                    "Sorry! I am an Academic AI Assistant dedicated exclusively to <b>Jadara University</b> "
                    "(finding faculty offices, live availability status, office hours, and booking appointments). "
                    "I cannot engage in topics outside the university platform scope.<br>"
                    "💡 <i>Try asking me about a doctor's name, ID number (e.g., 66), or office hours!</i>"
                    "</div>"
                )
            })
        return jsonify({
            "reply": (
                "<div style='background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;padding:10px;border-radius:8px;'>"
                "⚠️ <b>تنبيه من المساعد الذكي (خارج نطاق المنصة الأكاديمية):</b><br>"
                "عذراً عزيزي الطالب! أنا مساعد ذكاء اصطناعي مخصص حصرياً لخدمة طلبة وأعضاء هيئة التدريس في <b>جامعة جدارا</b> "
                "(البحث عن مكاتب الدكاترة، الرقم التعريفي للدكتور، حالتهم الفورية، أوقات الساعات المكتبية، وحجز المواعيد). "
                "يرجى عدم الخروج عن نطاق الموقع الأكاديمي.<br>"
                "💡 <i>جرب أن تكتب لي اسم الدكتور أو رقمه التعريفي (مثل: <b>66</b> أو <b>70</b>)!</i>"
                "</div>"
            )
        })

    # 2. Check Doctor ID lookup (e.g. "66", "٦٦", "#66", "دكتور 66", "رقم 66", "doctor 66")
    id_match = re.match(r"^(?:#|رقم|دكتور|الدكتور| د\.|dr\.?|doctor|id)?\s*(\d{1,3})$", q_low)
    if id_match:
        target_id = int(id_match.group(1))
        doc_by_id = next((r for r in rows if r["id"] == target_id), None)
        if doc_by_id:
            session["last_chat_doc_id"] = doc_by_id["id"]
            if lang == "en":
                return jsonify({"reply": f"🤖 Here are the full details for Doctor <b>#{target_id}</b>:{format_doc_card(doc_by_id)}"})
            return jsonify({"reply": f"🤖 تفضل؛ هذه كامل تفاصيل الدكتور صاحب الرقم التعريفي <b>#{target_id}</b>:{format_doc_card(doc_by_id)}"})
        else:
            if lang == "en":
                return jsonify({"reply": f"⚠️ No active doctor found with ID <b>#{target_id}</b> (IDs range from 1 to 100)."})
            return jsonify({"reply": f"⚠️ لا يوجد دكتور فعال يحمل الرقم التعريفي <b>#{target_id}</b> حالياً (الأرقام من 1 إلى 100)."})

    # 3. Check Student response to "كيف حالك اليوم؟" (2-step interactive opener) or Greetings
    if any(hr in q_low for hr in HOW_ARE_YOU_REPLIES) or any(g in q_low for g in GREETING_KEYWORDS):
        if lang == "en":
            return jsonify({
                "reply": (
                    "🌟 <b>Glad to hear you are doing well! How can I help you today at Jadara University?</b><br>"
                    "Here are examples of what you can ask me:<br>"
                    "• 🔢 <b>Doctor ID Number:</b> Type any number from <code>1</code> to <code>100</code> (e.g., <b>66</b> or <b>70</b>) to get full details.<br>"
                    "• 👨‍🏫 <b>Doctor Name or Office:</b> e.g., <i>&quot;Dr. Maan Al-Zoubi&quot;</i> or <i>&quot;B-204&quot;</i>.<br>"
                    "• 📡 <b>Live Status:</b> <i>&quot;Who is available now?&quot;</i> or <i>&quot;Who is in a lecture?&quot;</i><br>"
                    "• ✉️ <b>Appointments:</b> <i>&quot;How do I message a doctor?&quot;</i>"
                )
            })
        return jsonify({
            "reply": (
                "🌟 <b>دوم يا رب تكون بخير وبأحسن حال! شو بقدر أساعدك اليوم في جامعة جدارا؟</b> 😊<br>"
                "إليك أمثلة على الأشياء التي أقدر أساعدك فيها فوراً:<br>"
                "• 🔢 <b>الرقم التعريفي للدكتور:</b> اكتب رقم أي دكتور من <code>1</code> إلى <code>100</code> (مثلاً اكتب: <b>66</b> أو <b>70</b>) وسأعطيك كامل تفاصيله.<br>"
                "• 👨‍🏫 <b>اسم الدكتور أو مكتبه:</b> مثل <i>«د. معن الزعبي»</i> أو <i>«د. أحمد خليل»</i> أو <i>«B-204»</i>.<br>"
                "• 📡 <b>حالة التواجد الفورية:</b> اسألني <i>«مين متواجد الآن؟»</i> أو <i>«مين في محاضرة أو مشغول؟»</i>.<br>"
                "• ✉️ <b>المواعيد والمراسلة:</b> اسألني <i>«كيف أراسل دكتور وأحجز موعد؟»</i>."
            )
        })

    # 4. Check contextual follow-up about the last discussed doctor
    last_doc_id = session.get("last_chat_doc_id")
    followup_words = ["ساعاته", "مكتبه", "وينه", "أيامه", "ايامه", "ايميله", "إيميله", "حالته", "هو فاضي", "هو متاح", "أراسله", "اراسله", "his hours", "his office", "his email", "is he available"]
    if last_doc_id and any(fw in q_low for fw in followup_words):
        doc_match = next((r for r in rows if r["id"] == last_doc_id), None)
        if doc_match:
            if lang == "en":
                return jsonify({"reply": f"🤖 Regarding <b>{tr_name(doc_match['full_name'], 'en')}</b>:{format_doc_card(doc_match)}"})
            return jsonify({"reply": f"🤖 بخصوص <b>{doc_match['full_name']}</b> الذي سألت عنه للتو:{format_doc_card(doc_match)}"})

    # 5. Check Live Status queries (Available / Busy / InLecture / OffDuty) -> show ALL matching doctors in scrollable list
    if any(w in q_low for w in ["متواجدين", "متواجدون", "متاحين", "مين متاح", "من متواجد", "مين فاضي", "available now", "who is available"]):
        avail = [r for r in rows if r["live_status"] == "Available"]
        cards = "<div style='max-height:210px;overflow-y:auto;padding-inline-end:4px;'>" + "".join(format_doc_card(m) for m in avail) + "</div>"
        if lang == "en":
            return jsonify({
                "reply": f"🟢 <b>All {len(avail)} Doctors Available in Office Right Now</b> (scroll to browse all):{cards}"
            })
        return jsonify({
            "reply": f"🟢 <b>قائمة جميع الدكاترة المتواجدين في مكاتبهم الآن ({len(avail)} دكتور)</b> — مرر للأسفل لاستعراضهم بالكامل:{cards}"
        })

    if any(w in q_low for w in ["محاضره", "محاضرة", "مشغول", "اجتماع", "غير متواجد", "خارج الدوام", "in lecture", "busy", "meeting"]):
        busy_docs = [r for r in rows if r["live_status"] in ("Busy", "InLecture", "OffDuty")]
        in_lec = sum(1 for r in rows if r["live_status"] == "InLecture")
        in_meet = sum(1 for r in rows if r["live_status"] == "Busy")
        off_d = sum(1 for r in rows if r["live_status"] == "OffDuty")
        cards = "<div style='max-height:200px;overflow-y:auto;padding-inline-end:4px;'>" + "".join(format_doc_card(m) for m in busy_docs) + "</div>"
        if lang == "en":
            return jsonify({
                "reply": (
                    f"📊 <b>Busy / Unavailable Doctors Now ({len(busy_docs)} total):</b><br>"
                    f"🔴 In Lecture: <b>{in_lec}</b> | 🟡 Meeting/Busy: <b>{in_meet}</b> | ⚪ Off Duty: <b>{off_d}</b>{cards}"
                )
            })
        return jsonify({
            "reply": (
                f"📊 <b>جميع الدكاترة غير المتاحين حالياً ({len(busy_docs)} دكتور):</b><br>"
                f"🔴 في محاضرة: <b>{in_lec}</b> | 🟡 اجتماع/مشغول: <b>{in_meet}</b> | ⚪ خارج الدوام: <b>{off_d}</b>{cards}"
            )
        })

    # 6. Check How to use site / How to book or message
    if any(w in q_low for w in ["كيف اراسل", "كيف أراسل", "كيف احجز", "كيف أحجز", "موعد", "رسالة", "رساله", "حساب طالب", "شو بقدر", "مساعدة", "how to message", "how do i", "book", "appointment"]):
        if lang == "en":
            return jsonify({
                "reply": (
                    "🎓 <b>How to Message a Doctor & Book an Office Hour:</b><br>"
                    "1️⃣ Click <a href='/register'><b>Student Sign Up</b></a> (or <a href='/login'><b>Login</b></a> with demo account <code>thabet</code> / <code>student123</code>).<br>"
                    "2️⃣ Open any doctor's card and pick one of the <b>3 Ready Message Templates</b>.<br>"
                    "3️⃣ The doctor will reply with their status (🟢 Available / 🔴 Busy / 🟡 Postponed) and specify the exact hour for you in your <a href='/student'><b>Student Portal</b></a>!"
                )
            })
        return jsonify({
            "reply": (
                "🎓 <b>طريقة مراسلة الدكتور وحجز موعد خطوة بخطوة:</b><br>"
                "1️⃣ سجل دخولك كطالب من <a href='/login'><b>صفحة الدخول</b></a> (أو أنشئ حسابك الفوري من <a href='/register'><b>تسجيل طالب جديد</b></a>).<br>"
                "2️⃣ اضغط على زر <b>«✉️ مراسلة الدكتور»</b> بجانب أي دكتور واختر إحدى <b>الرسائل الـ 3 الجاهزة</b>.<br>"
                "3️⃣ سيرد عليك الدكتور بـ (🟢 متاح / 🔴 مشغول / 🟡 تأجيل) مع تحديد الساعة المناسبة، ويصلك إشعار فوري في <a href='/student'><b>حساب الطالب</b></a>!"
            )
        })

    if any(t in q_low for t in THANKS_KEYWORDS):
        if lang == "en":
            return jsonify({"reply": "🌟 You're very welcome! Best of luck with your studies at Jadara University. Let me know if you need any other doctor's office or ID!"})
        return jsonify({"reply": "🌟 يا هلا فيك على الرحب والسعة! بالتوفيق في دراستك ومشروعك في جامعة جدارا. أنا موجود دائماً إذا احتجت تسأل عن أي دكتور أو رقم تعريفي!"})

    # 7. Check specific doctor name or office match (or embedded number)
    clean_q = (
        q_low.replace("دكتور", "")
        .replace("الدكتور", "")
        .replace("د.", "")
        .replace("أ.د.", "")
        .replace("وين", "")
        .replace("مكتب", "")
        .replace("ساعات", "")
        .replace("دوام", "")
        .replace("متى", "")
        .replace("بدي", "")
        .replace("اعرف", "")
        .replace("عن", "")
        .replace("رقم", "")
        .replace("dr.", "")
        .replace("dr", "")
        .replace("office", "")
        .replace("hours", "")
        .replace("where", "")
        .strip()
    )
    tokens = [t for t in clean_q.split() if len(t) >= 1]
    doc_matches = []
    if tokens:
        for r in rows:
            if any(tok.isdigit() and int(tok) == r["id"] for tok in tokens):
                doc_matches.append(r)
                continue
            ar_hay = f"{r['full_name']} {r['office_number']}".lower()
            en_hay = f"{tr_name(r['full_name'], 'en')} {r['office_number']}".lower()
            if any(len(tok) >= 2 and (tok in ar_hay or tok in en_hay) for tok in tokens):
                doc_matches.append(r)

    if doc_matches:
        session["last_chat_doc_id"] = doc_matches[0]["id"]
        cards = "<div style='max-height:210px;overflow-y:auto;'>" + "".join(format_doc_card(m) for m in doc_matches) + "</div>"
        if lang == "en":
            intro = f"🤖 Found <b>{len(doc_matches)}</b> matching faculty member(s):"
        else:
            intro = f"🤖 وجدت لك <b>{len(doc_matches)}</b> نتيجة مطابقة في دليل جامعة جدارا:"
        return jsonify({"reply": intro + cards})

    # 8. Check Department or Day queries
    dept_matches = []
    for r in rows:
        if r["dept_name"].lower() in q_low or tr_dept(r["dept_name"], "en").lower() in q_low or (r["days"] and any(d in q_low for d in ALL_DAYS_AR)):
            dept_matches.append(r)
    if dept_matches:
        cards = "<div style='max-height:210px;overflow-y:auto;'>" + "".join(format_doc_card(m) for m in dept_matches) + "</div>"
        return jsonify({"reply": (f"🤖 Found <b>{len(dept_matches)}</b> doctors:" if lang == "en" else f"🤖 وجدت <b>{len(dept_matches)}</b> دكتور مطابق لسؤالك:") + cards})

    # 9. Default Guardrail for unrecognized / general off-topic queries
    if lang == "en":
        return jsonify({
            "reply": (
                "<div style='background:#fffbeb;border:1px solid #fde68a;color:#92400e;padding:10px;border-radius:8px;'>"
                "🤖 <b>Jadara AI Scope Notice:</b><br>"
                "I couldn't match that to a Jadara University faculty member or academic service. Please note that I am restricted to <b>Jadara University's Faculty & Office Hours Directory</b> and cannot discuss external topics.<br>"
                "💡 <i>Try typing a doctor's ID number (e.g., <b>66</b>), name (<b>Maan</b>, <b>Ahmad</b>), or office number (<b>B-204</b>)!</i>"
                "</div>"
            )
        })
    return jsonify({
        "reply": (
            "<div style='background:#fffbeb;border:1px solid #fde68a;color:#92400e;padding:10px;border-radius:8px;'>"
            "🤖 <b>تنبيه نطاق المساعد الذكي لجامعة جدارا:</b><br>"
            "لم أتمكن من ربط رسالتك بدكتور أو خدمة أكاديمية داخل الموقع. يرجى العلم أنني مبرمج حصرياً لخدمة <b>دليل الساعات المكتبية ومواقع الدكاترة في جامعة جدارا</b> ولا يمكنني النقاش في مواضيع خارج نطاق الموقع.<br>"
            "💡 <i>جرب كتابة الرقم التعريفي للدكتور (مثل: <b>66</b>)، أو اسم الدكتور (<b>معن</b>، <b>أحمد</b>)، أو رقم المكتب (<b>B-204</b>)!</i>"
            "</div>"
        )
    })


@app.route("/")
def home():
    search_q = norm_digits(request.args.get("q", "").strip())
    selected_depts = request.args.getlist("depts")
    selected_buildings = request.args.getlist("buildings")
    bldg_single = request.args.get("bldg", "").strip()
    if bldg_single and bldg_single not in selected_buildings:
        selected_buildings.append(bldg_single)

    selected_days = request.args.getlist("days")
    selected_floors = request.args.getlist("floors")
    selected_statuses = request.args.getlist("statuses")
    status_single = request.args.get("status", "").strip()
    if status_single and status_single not in selected_statuses:
        selected_statuses.append(status_single)

    conn = get_db_connection()
    departments = conn.execute("SELECT rowid AS id, * FROM Departments").fetchall()
    buildings_raw = conn.execute("SELECT * FROM Buildings ORDER BY code ASC").fetchall()
    all_docs_raw = conn.execute("SELECT building_code, live_status FROM Doctors WHERE COALESCE(is_deleted, 0) = 0").fetchall()

    bldg_stats = {}
    for b in buildings_raw:
        c_code = b["code"]
        b_docs = [d for d in all_docs_raw if d["building_code"] == c_code]
        bldg_stats[c_code] = {
            "total": len(b_docs),
            "avail": sum(1 for d in b_docs if d["live_status"] == "Available"),
            "busy": sum(1 for d in b_docs if d["live_status"] in ("Busy", "InLecture")),
        }

    status_counts = {
        "Available": sum(1 for d in all_docs_raw if d["live_status"] == "Available"),
        "Busy": sum(1 for d in all_docs_raw if d["live_status"] == "Busy"),
        "InLecture": sum(1 for d in all_docs_raw if d["live_status"] == "InLecture"),
        "OffDuty": sum(1 for d in all_docs_raw if d["live_status"] == "OffDuty"),
    }

    query = """
        SELECT d.id, d.full_name, d.academic_rank, d.department_id, d.building_code, d.floor, d.office_number, d.email, d.live_status,
               dept.name AS department_name,
               b.name_ar AS building_name_ar, b.name_en AS building_name_en,
               oh.days, oh.start_time, oh.end_time
        FROM Doctors d
        JOIN Departments dept ON d.department_id = dept.id
        JOIN Buildings b ON d.building_code = b.code
        LEFT JOIN OfficeHours oh ON d.id = oh.doctor_id
        WHERE COALESCE(d.is_deleted, 0) = 0
    """
    params = []

    if selected_depts:
        placeholders = ",".join(["?"] * len(selected_depts))
        query += f" AND d.department_id IN ({placeholders})"
        params.extend(selected_depts)

    if selected_buildings:
        placeholders = ",".join(["?"] * len(selected_buildings))
        query += f" AND d.building_code IN ({placeholders})"
        params.extend(selected_buildings)

    if selected_floors:
        placeholders = ",".join(["?"] * len(selected_floors))
        query += f" AND d.floor IN ({placeholders})"
        params.extend(selected_floors)

    if selected_statuses:
        placeholders = ",".join(["?"] * len(selected_statuses))
        query += f" AND d.live_status IN ({placeholders})"
        params.extend(selected_statuses)

    query += " ORDER BY d.id ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    doctors = []
    for r in rows:
        if search_q:
            q_low = search_q.lower()
            en_name = tr_name(r["full_name"], "en").lower()
            if (
                q_low != str(r["id"])
                and f"#{r['id']}" != q_low
                and q_low not in r["full_name"].lower()
                and q_low not in en_name
                and q_low not in r["office_number"].lower()
                and q_low not in r["email"].lower()
            ):
                continue
        if selected_days:
            doc_days = r["days"] or ""
            if not any(day in doc_days for day in selected_days):
                continue
        doctors.append(r)

    content = """
    {% extends "base" %}
    {% block content %}
    <!-- Top Interactive Building Cards (Clean & Simple) -->
    <div class="bldg-grid no-print">
        {% for b in buildings %}
        {% set st = bldg_stats[b.code] %}
        <div class="bldg-card" style="{% if b.code in selected_buildings %}border:2px solid var(--secondary); background:#f0f9ff;{% endif %}">
            <div>
                <a href="/?bldg={{ b.code }}" style="color:var(--secondary); font-weight:800; font-size:0.84rem; text-decoration:none;">
                    {{ 'Browse ←' if lang == 'en' else 'استعراض ←' }}
                </a>
            </div>
            <div style="text-align:end; flex:1;">
                <div style="font-weight:800; font-size:0.92rem; color:var(--primary);">
                    {{ b.name_en if lang == 'en' else b.name_ar }}
                </div>
                <div style="font-size:0.78rem; color:var(--muted); margin-top:2px;">
                    {{ st.total }} {{ 'Doctors' if lang == 'en' else 'دكتور' }}
                </div>
            </div>
            <div class="bldg-code-box">{{ b.code }}</div>
        </div>
        {% endfor %}
    </div>

    <!-- 4-Column Multi-Filter Box -->
    <div class="filter-panel no-print">
        <form method="GET" action="/">
            <input type="text" class="search-bar-full" name="q" placeholder="{{ '🔍 Search by any part of doctor name, office number (e.g. B-204), or email...' if lang == 'en' else '🔍 ابحث بأي جزء من اسم الدكتور، رقم المكتب (مثل B-204)، أو البريد...' }}" value="{{ search_q }}">

            <div class="four-cols">
                <!-- Col 1: Academic Departments -->
                <div class="col-box">
                    <span class="col-title">🧩 {{ 'Academic Departments (Multi):' if lang == 'en' else 'الأقسام الأكاديمية (متعدد):' }}</span>
                    <div class="chip-list">
                        {% for dept in departments %}
                        <label class="chip-label">
                            <input type="checkbox" name="depts" value="{{ dept.id|string }}" {% if (dept.id|string) in selected_depts %}checked{% endif %}>
                            <span>{{ tr_dept(dept.name, lang) }}</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>

                <!-- Col 2: University Buildings -->
                <div class="col-box">
                    <span class="col-title">🏢 {{ 'University Buildings (A, B, C, D):' if lang == 'en' else 'المباني الجامعية (A, B, C, D):' }}</span>
                    <div class="chip-list">
                        {% for b in buildings %}
                        <label class="chip-label" style="width:100%;">
                            <input type="checkbox" name="buildings" value="{{ b.code }}" {% if b.code in selected_buildings %}checked{% endif %}>
                            <span>{{ b.name_en if lang == 'en' else b.name_ar }}</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>

                <!-- Col 3: All 4 Live Statuses + Floors -->
                <div class="col-box">
                    <span class="col-title">📡 {{ 'Live Status & Floors (All States):' if lang == 'en' else 'الحالة الفورية للدكتور والطوابق:' }}</span>
                    <div class="chip-list" style="margin-bottom:8px; padding-bottom:8px; border-bottom:1px dashed #cbd5e1;">
                        {% for st_code, st_ar, st_en, st_cls in LIVE_STATUS_META %}
                        <label class="chip-label" style="width:100%; font-weight:700; {% if st_code == 'Available' %}background:#f0fdf4;border-color:#86efac;{% elif st_code == 'Busy' %}background:#fffbeb;border-color:#fde68a;{% elif st_code == 'InLecture' %}background:#fef2f2;border-color:#fca5a5;{% endif %}">
                            <input type="checkbox" name="statuses" value="{{ st_code }}" {% if st_code in selected_statuses %}checked{% endif %}>
                            <span>{{ st_en if lang == 'en' else st_ar }} ({{ status_counts[st_code] }})</span>
                        </label>
                        {% endfor %}
                    </div>
                    <div class="chip-list">
                        {% for fl in ALL_FLOORS_AR %}
                        <label class="chip-label">
                            <input type="checkbox" name="floors" value="{{ fl }}" {% if fl in selected_floors %}checked{% endif %}>
                            <span>{{ tr_floor(fl, lang) }}</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>

                <!-- Col 4: Office Hours Days -->
                <div class="col-box">
                    <span class="col-title">📅 {{ 'Office Hours Days (Flexible):' if lang == 'en' else 'أيام الساعات المكتبية (مرن):' }}</span>
                    <div class="chip-list">
                        {% for day in ALL_DAYS_AR %}
                        <label class="chip-label">
                            <input type="checkbox" name="days" value="{{ day }}" {% if day in selected_days %}checked{% endif %}>
                            <span>{{ DAY_EN[day] if lang == 'en' else day }}</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <div style="display:flex; justify-content:center; gap:10px; flex-wrap:wrap;">
                <button type="submit" class="btn">🔍 {{ 'Apply Filters & Search' if lang == 'en' else 'تطبيق الفلترة والبحث' }}</button>
                <a href="/" class="btn btn-dark">{{ 'Reset All' if lang == 'en' else 'إعادة ضبط الكل' }}</a>
                <button type="button" onclick="window.print()" class="btn btn-light">🖨️ {{ 'Print Displayed Schedule' if lang == 'en' else 'طباعة الجدول المعروض' }}</button>
            </div>
        </form>
    </div>

    <div style="margin-bottom: 12px; font-weight: 800; color: var(--primary); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <span>{{ 'Displayed Results:' if lang == 'en' else 'عدد النتائج المعروضة:' }} {{ doctors|length }} {{ 'out of 100 Doctors (Numbered 1 to 100)' if lang == 'en' else 'من أصل 100 دكتور (مرقمين من 1 إلى 100)' }}</span>
        {% if selected_statuses %}
            <span style="background:#e0f2fe; color:#0369a1; padding:4px 12px; border-radius:20px; font-size:0.84rem;">
                ⚡ {{ 'Active Status Filter:' if lang == 'en' else 'فلتر الحالة الفورية مفعل:' }} {{ selected_statuses|join(', ') }}
            </span>
        {% endif %}
    </div>

    <div class="grid">
        {% for doc in doctors %}
        <div class="card">
            <div>
                <div class="card-header">
                    <span class="badge">{{ tr_dept(doc.department_name, lang) }}</span>
                    <span class="badge badge-bldg">#{{ doc.id }} | {{ doc.building_code }}</span>
                </div>
                <div style="margin-bottom:6px;">
                    {% if doc.live_status == 'Available' %}
                        <span class="status-dot st-Available">🟢 {{ 'Available in Office Now' if lang == 'en' else 'متواجد بالمكتب الآن' }}</span>
                    {% elif doc.live_status == 'Busy' %}
                        <span class="status-dot st-InLecture">🟡 {{ 'In Dept Meeting / Busy' if lang == 'en' else 'في اجتماع قسم / مشغول' }}</span>
                    {% elif doc.live_status == 'InLecture' %}
                        <span class="status-dot st-Busy">🔴 {{ 'In Lecture Now' if lang == 'en' else 'في محاضرة حالياً' }}</span>
                    {% else %}
                        <span class="status-dot st-OffDuty">⚪ {{ 'Off Duty / Unavailable' if lang == 'en' else 'غير متواجد / خارج الدوام' }}</span>
                    {% endif %}
                </div>
                <h3>{{ tr_name(doc.full_name, lang) }}</h3>
                <p style="color: var(--muted); font-size: 0.82rem; margin-bottom: 8px;">{{ tr_rank(doc.academic_rank, lang) }}</p>
                <div class="info-row">📍 <strong>{{ 'Building:' if lang == 'en' else 'المبنى:' }}</strong> {{ doc.building_name_en if lang == 'en' else doc.building_name_ar }}</div>
                <div class="info-row">🚪 <strong>{{ 'Floor & Office:' if lang == 'en' else 'الطابق والمكتب:' }}</strong> {{ tr_floor(doc.floor, lang) }} — <strong style="color:var(--primary);">{{ doc.office_number }}</strong></div>
                <div class="info-row">✉️ {{ doc.email }}</div>
                <div class="hours-box">
                    🕒 {{ tr_days(doc.days, lang) if doc.days else ('Not set' if lang == 'en' else 'غير محدد') }}<br>
                    ⏰ {{ doc.start_time }} - {{ doc.end_time }}
                </div>
            </div>
            <div style="margin-top: 12px; display:flex; gap:8px;">
                <a href="/doctor/{{ doc.id }}" class="btn btn-dark" style="flex:1; padding:8px 10px; font-size:0.84rem;">{{ 'Details & QR' if lang == 'en' else 'التفاصيل و QR' }}</a>
                <a href="/doctor/{{ doc.id }}#msg-box" class="btn" style="flex:1; padding:8px 10px; font-size:0.84rem;">✉️ {{ 'Message Doctor' if lang == 'en' else 'مراسلة الدكتور' }}</a>
            </div>
        </div>
        {% else %}
        <p style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--muted);">{{ 'No matching results found.' if lang == 'en' else 'لا توجد نتائج مطابقة لبحثك.' }}</p>
        {% endfor %}
    </div>
    {% endblock %}
    """
    full_tpl = BASE_LAYOUT.replace("{% block content %}{% endblock %}", content.split("{% block content %}")[1].split("{% endblock %}")[0])
    return render_template_string(
        full_tpl,
        doctors=doctors,
        departments=departments,
        buildings=buildings_raw,
        bldg_stats=bldg_stats,
        status_counts=status_counts,
        search_q=search_q,
        selected_depts=selected_depts,
        selected_buildings=selected_buildings,
        selected_days=selected_days,
        selected_floors=selected_floors,
        selected_statuses=selected_statuses,
    )


@app.route("/doctor/<int:doc_id>")
def doctor_details(doc_id):
    qr_mode = request.args.get("qr", "vcard")
    conn = get_db_connection()
    doc = conn.execute(
        """
        SELECT d.*, dept.name AS department_name, b.name_ar AS building_name_ar, b.name_en AS building_name_en,
               oh.days, oh.start_time, oh.end_time
        FROM Doctors d
        JOIN Departments dept ON d.department_id = dept.id
        JOIN Buildings b ON d.building_code = b.code
        LEFT JOIN OfficeHours oh ON d.id = oh.doctor_id
        WHERE d.id = ?
        """,
        (doc_id,),
    ).fetchone()
    conn.close()
    if not doc:
        return redirect(url_for("home"))

    qr_payload = build_doctor_qr_payload(doc, qr_mode)

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="form-box" style="max-width:780px; margin-bottom: 1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:15px;">
            <div>
                <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                    <span class="badge">{{ tr_dept(doc.department_name, lang) }}</span>
                    <span class="badge badge-bldg">#{{ doc.id }} | {{ doc.building_code }}</span>
                    {% if doc.live_status == 'Available' %}
                        <span class="status-dot st-Available">🟢 {{ 'Available in Office Now' if lang == 'en' else 'متواجد بالمكتب الآن' }}</span>
                    {% elif doc.live_status == 'Busy' %}
                        <span class="status-dot st-InLecture">🟡 {{ 'In Dept Meeting / Busy' if lang == 'en' else 'في اجتماع قسم / مشغول' }}</span>
                    {% elif doc.live_status == 'InLecture' %}
                        <span class="status-dot st-Busy">🔴 {{ 'In Lecture Now' if lang == 'en' else 'في محاضرة حالياً' }}</span>
                    {% else %}
                        <span class="status-dot st-OffDuty">⚪ {{ 'Off Duty / Unavailable' if lang == 'en' else 'غير متواجد / خارج الدوام' }}</span>
                    {% endif %}
                </div>
                <h2 style="margin-top:10px; color:var(--primary);">{{ tr_name(doc.full_name, lang) }}</h2>
                <p style="color:var(--muted); margin-bottom:15px;">{{ tr_rank(doc.academic_rank, lang) }}</p>
            </div>
            <div style="text-align:center; background:#f8fafc; padding:12px; border-radius:12px; border:1px solid #cbd5e1; min-width:190px;">
                {{ generate_qr_svg(qr_payload, 148) }}
                <div style="font-size:0.76rem; color:var(--primary); font-weight:700; margin-top:6px;">
                    📱 {{ 'Scan with Phone Camera' if lang == 'en' else 'امسح بكاميرا الهاتف فوراً' }} ({{ doc.office_number }})
                </div>
                <div class="no-print" style="margin-top:6px; display:flex; gap:4px; justify-content:center;">
                    <a href="/doctor/{{ doc.id }}?qr=vcard" style="font-size:0.7rem; padding:3px 7px; border-radius:5px; text-decoration:none; font-weight:700; background:{{ '#0284c7' if qr_mode != 'url' else '#e2e8f0' }}; color:{{ '#fff' if qr_mode != 'url' else '#1e293b' }};">
                        {{ '📇 Smart Card QR' if lang == 'en' else '📇 بطاقة هاتف ذكية' }}
                    </a>
                    <a href="/doctor/{{ doc.id }}?qr=url" style="font-size:0.7rem; padding:3px 7px; border-radius:5px; text-decoration:none; font-weight:700; background:{{ '#0284c7' if qr_mode == 'url' else '#e2e8f0' }}; color:{{ '#fff' if qr_mode == 'url' else '#1e293b' }};">
                        {{ '🔗 Direct Link QR' if lang == 'en' else '🔗 رابط مباشر' }}
                    </a>
                </div>
            </div>
        </div>

        <table>
            <tr><th>{{ 'Building' if lang == 'en' else 'المبنى الجامعي' }}</th><td>{{ doc.building_name_en if lang == 'en' else doc.building_name_ar }}</td></tr>
            <tr><th>{{ 'Floor' if lang == 'en' else 'الطابق' }}</th><td>{{ tr_floor(doc.floor, lang) }}</td></tr>
            <tr><th>{{ 'Office Number' if lang == 'en' else 'رقم المكتب' }}</th><td><strong>{{ doc.office_number }}</strong></td></tr>
            <tr><th>{{ 'Official Email' if lang == 'en' else 'البريد الإلكتروني' }}</th><td>{{ doc.email }}</td></tr>
            <tr><th>{{ 'Office Hours Days' if lang == 'en' else 'أيام الساعات المكتبية' }}</th><td><strong>{{ tr_days(doc.days, lang) }}</strong></td></tr>
            <tr><th>{{ 'Time Slot' if lang == 'en' else 'التوقيت' }}</th><td><strong>{{ doc.start_time }} - {{ doc.end_time }}</strong></td></tr>
        </table>
        <div class="no-print" style="margin-top: 16px; display:flex; gap:10px; flex-wrap:wrap;">
            <a href="/" class="btn btn-light">{{ '⬅️ Back to Directory' if lang == 'en' else '⬅️ العودة للدليل' }}</a>
            <button onclick="window.print()" class="btn btn-dark">🖨️ {{ 'Print Office Door QR Card' if lang == 'en' else 'طباعة بطاقة باب المكتب مع QR' }}</button>
        </div>
    </div>

    <div class="form-box no-print" id="msg-box" style="max-width:780px; border-top: 4px solid #10b981;">
        <h3 style="color:var(--primary); margin-bottom:6px;">
            ✉️ {{ 'Message Doctor & Request Appointment (Choose 1 of 3 Ready Messages)' if lang == 'en' else 'مراسلة الدكتور وتحديد موعد (اختر من الرسائل الثلاث الجاهزة)' }}
        </h3>
        {% if session.get('role') == 'student' %}
            <p style="color:var(--muted); font-size:0.88rem; margin-bottom:14px;">
                {{ 'Logged in as Student:' if lang == 'en' else 'أنت مسجل الدخول كطالب:' }}
                <strong>{{ tr_name(session.get('full_name'), lang) }} ({{ session.get('student_number') }})</strong>
            </p>
            <form method="POST" action="/student/send_message/{{ doc.id }}">
                <div class="form-group">
                    <label>{{ '1. Select Ready Message Template (3 Options):' if lang == 'en' else '1. اختر إحدى الرسائل الجاهزة الثلاث لإرسالها للدكتور:' }}</label>
                    {% for ar_t, en_t in STUDENT_TEMPLATES[:3] %}
                    <label class="template-radio">
                        <input type="radio" name="template_type" value="{{ ar_t }}" {% if loop.first %}checked{% endif %}>
                        <span>📌 {{ en_t if lang == 'en' else ar_t }}</span>
                    </label>
                    {% endfor %}
                </div>
                <div class="form-group">
                    <label>{{ '2. Additional Note / Course Name (Optional):' if lang == 'en' else '2. ملاحظة إضافية أو اسم المادة (اختياري):' }}</label>
                    <textarea name="student_note" rows="2" placeholder="{{ 'Example: Dr., can I pass by today regarding Software Engineering project?' if lang == 'en' else 'مثال: دكتور يعطيك العافية، أود المرور بخصوص مشروع التخرج أو مادة هندسة البرمجيات...' }}"></textarea>
                </div>
                <button type="submit" class="btn btn-success" style="width:100%; font-size:1rem;">
                    🚀 {{ 'Send Message to Doctor Now' if lang == 'en' else 'إرسال الرسالة للدكتور الآن' }}
                </button>
            </form>
        {% else %}
            <div style="background:#f0fdf4; border:1px solid #86efac; padding:16px; border-radius:10px; text-align:center;">
                <p style="margin-bottom:12px; font-weight:600; color:#166534;">
                    {{ 'Please log in with your Student Account (or create a new Student Account in seconds) to message the doctor and receive their reply & appointment time:' if lang == 'en' else 'يرجى تسجيل الدخول بحساب طالب (أو إنشاء حساب طالب جديد في ثوانٍ) لإرسال رسالة للدكتور واستقبال رده وموعده:' }}
                </p>
                <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
                    <a href="/login" class="btn">{{ '🔐 Student Login' if lang == 'en' else '🔐 دخول الطلبة' }}</a>
                    <a href="/register" class="btn btn-success">{{ '🎓 Create New Student Account' if lang == 'en' else '🎓 إنشاء حساب طالب جديد' }}</a>
                </div>
            </div>
        {% endif %}
    </div>
    {% endblock %}
    """
    full_tpl = BASE_LAYOUT.replace("{% block content %}{% endblock %}", content.split("{% block content %}")[1].split("{% endblock %}")[0])
    return render_template_string(full_tpl, doc=doc, qr_payload=qr_payload, qr_mode=qr_mode)


@app.route("/register", methods=["GET", "POST"])
def register():
    conn = get_db_connection()
    departments = conn.execute("SELECT rowid AS id, * FROM Departments").fetchall()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        student_number = request.form.get("student_number", "").strip()
        department_id = request.form.get("department_id", "1")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not (full_name and student_number and username and password):
            flash("يرجى تعبئة جميع الحقول المطلوبة.", "error")
        else:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO Users (username, password, role, doctor_id, full_name, student_number, department_id)
                    VALUES (?, ?, 'student', NULL, ?, ?, ?)
                    """,
                    (username, password, full_name, student_number, department_id),
                )
                conn.commit()
                new_id = cur.lastrowid
                conn.close()
                session["user_id"] = new_id
                session["username"] = username
                session["role"] = "student"
                session["full_name"] = full_name
                session["student_number"] = student_number
                flash("🎉 تم إنشاء حساب الطالب بنجاح! يمكنك الآن مراسلة أي دكتور واستقبال ردوده ومواعيده.")
                return redirect(url_for("student_portal"))
            except sqlite3.IntegrityError:
                flash("⚠️ اسم المستخدم مسجل مسبقاً، يرجى اختيار اسم مستخدم آخر.", "error")

    conn.close()
    content = """
    {% extends "base" %}
    {% block content %}
    <div class="form-box" style="max-width:480px;">
        <h2 style="margin-bottom: 0.4rem; text-align:center; color:var(--primary);">
            {{ '🎓 Create New Student Account' if lang == 'en' else '🎓 إنشاء حساب طالب جديد' }}
        </h2>
        <p style="text-align:center; color:var(--muted); font-size:0.88rem; margin-bottom:1.2rem;">
            {{ 'Register to message doctors and receive office hour appointments (All departments added by Admin appear automatically)' if lang == 'en' else 'سجل حسابك لتتمكن من مراسلة الدكاترة واستلام مواعيد الساعات المكتبية (تظهر هنا جميع التخصصات المضافة من الإدارة تلقائياً)' }}
        </p>
        <form method="POST">
            <div class="form-group">
                <label>{{ 'Student Full Name' if lang == 'en' else 'الاسم الرباعي للطالب' }}</label>
                <input type="text" name="full_name" placeholder="{{ 'Example: Thabet Qais Mohammad Qawasmeh' if lang == 'en' else 'مثال: ثابت قيس محمد قواسمة' }}" required>
            </div>
            <div class="form-group">
                <label>{{ 'University ID' if lang == 'en' else 'الرقم الجامعي (Student ID)' }}</label>
                <input type="text" name="student_number" placeholder="{{ 'Example: 202220020' if lang == 'en' else 'مثال: 202220020' }}" required>
            </div>
            <div class="form-group">
                <label>{{ 'Department / Major' if lang == 'en' else 'التخصص / القسم' }}</label>
                <select name="department_id" required>
                    {% for dept in departments %}
                    <option value="{{ dept.id }}">{{ tr_dept(dept.name, lang) }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="form-group">
                <label>{{ 'Username' if lang == 'en' else 'اسم المستخدم للدخول (Username)' }}</label>
                <input type="text" name="username" placeholder="{{ 'Example: thabet2026' if lang == 'en' else 'مثال: thabet2026' }}" required>
            </div>
            <div class="form-group">
                <label>{{ 'Password' if lang == 'en' else 'كلمة المرور (Password)' }}</label>
                <input type="password" name="password" placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn btn-success" style="width:100%;">
                {{ '🎓 Register & Sign In' if lang == 'en' else '🎓 إنشاء حساب الطالب والدخول فوراً' }}
            </button>
        </form>
    </div>
    {% endblock %}
    """
    full_tpl = BASE_LAYOUT.replace("{% block content %}{% endblock %}", content.split("{% block content %}")[1].split("{% endblock %}")[0])
    return render_template_string(full_tpl, departments=departments)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM Users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["doctor_id"] = user["doctor_id"]
            session["full_name"] = user["full_name"] or user["username"]
            session["student_number"] = user["student_number"] or ""
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user["role"] == "student":
                return redirect(url_for("student_portal"))
            return redirect(url_for("doctor_dashboard"))
        else:
            flash("اسم المستخدم أو كلمة المرور غير صحيحة!", "error")

    content = """
    {% extends "base" %}
    {% block content %}
    <div class="form-box" style="max-width:460px;">
        <h2 style="margin-bottom: 1rem; text-align:center; color:var(--primary);">
            {{ '🔐 Unified Portal Login' if lang == 'en' else '🔐 تسجيل الدخول الموحد (طالب / دكتور / إدارة)' }}
        </h2>
        <form method="POST">
            <div class="form-group">
                <label>{{ 'Username' if lang == 'en' else 'اسم المستخدم (Username)' }}</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>{{ 'Password' if lang == 'en' else 'كلمة المرور (Password)' }}</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn" style="width:100%;">{{ 'Sign In' if lang == 'en' else 'دخول' }}</button>
        </form>
        <div style="margin-top:14px; text-align:center;">
            <a href="/register" style="color:#059669; font-weight:700; text-decoration:none;">
                {{ '🎓 New Student? Create your Student Account here' if lang == 'en' else '🎓 طالب جديد؟ اضغط هنا لإنشاء حساب طالب جديد' }}
            </a>
        </div>
        <div style="margin-top:14px; font-size:0.82rem; color:var(--muted); background:#f8fafc; padding:12px; border-radius:8px; border:1px solid var(--border);">
            <strong>{{ 'Ready Demo Accounts:' if lang == 'en' else 'حسابات جاهزة للتجربة السريعة:' }}</strong><br>
            • {{ 'Student (Thabet):' if lang == 'en' else 'حساب طالب (ثابت):' }} <code>thabet</code> / <code>student123</code><br>
            • {{ 'Student (Aws):' if lang == 'en' else 'حساب طالب (أوس):' }} <code>aws</code> / <code>student123</code><br>
            • {{ 'Student (Yazeed):' if lang == 'en' else 'حساب طالب (يزيد):' }} <code>yazeed</code> / <code>student123</code><br>
            • {{ 'Supervisor (Dr. Maan):' if lang == 'en' else 'مشرف المشروع (د. معن الزعبي):' }} <code>m.alzoubi</code> / <code>doctor123</code><br>
            • {{ 'Doctor #1 (Dr. Ahmad):' if lang == 'en' else 'حساب دكتور (د. أحمد خليل):' }} <code>a.khalil</code> / <code>doctor123</code><br>
            • {{ 'System Admin:' if lang == 'en' else 'مدير النظام (Admin):' }} <code>admin</code> / <code>admin123</code>
        </div>
    </div>
    {% endblock %}
    """
    full_tpl = BASE_LAYOUT.replace("{% block content %}{% endblock %}", content.split("{% block content %}")[1].split("{% endblock %}")[0])
    return render_template_string(full_tpl)


@app.route("/logout")
def logout():
    lang = session.get("lang", "ar")
    session.clear()
    session["lang"] = lang
    return redirect(url_for("home"))


@app.route("/student")
def student_portal():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    conn = get_db_connection()
    doctors = conn.execute(
        """
        SELECT d.id, d.full_name, d.office_number, d.building_code, d.live_status, dept.name AS dept_name
        FROM Doctors d
        JOIN Departments dept ON d.department_id = dept.id
        ORDER BY d.id ASC
        """
    ).fetchall()

    uid = session.get("user_id", 0)
    snum = (session.get("student_number") or "").strip()
    sname = (session.get("full_name") or "").strip()

    my_messages = conn.execute(
        """
        SELECT m.*, d.full_name AS doc_name, d.office_number, d.building_code, d.email AS doc_email
        FROM Messages m
        JOIN Doctors d ON m.doctor_id = d.id
        WHERE m.student_user_id = ?
           OR (? != '' AND m.student_number = ?)
           OR (? != '' AND LOWER(m.student_name) = LOWER(?))
        ORDER BY m.id DESC
        """,
        (uid, snum, snum, sname, sname),
    ).fetchall()
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div style="display:grid; grid-template-columns: 1fr 1.35fr; gap: 1.4rem; align-items:start;">
        <div class="form-box" style="margin:0; max-width:100%; border-top:4px solid #10b981;">
            <h3 style="color:var(--primary); margin-bottom:6px;">
                ✉️ {{ 'Send Quick Message to a Doctor' if lang == 'en' else 'إرسال رسالة سريعة لدكتور' }}
            </h3>
            <p style="color:var(--muted); font-size:0.86rem; margin-bottom:12px;">
                {{ 'Student:' if lang == 'en' else 'الطالب:' }} <strong>{{ tr_name(session.get('full_name'), lang) }}</strong> ({{ session.get('student_number') }})
            </p>
            <form method="POST" action="/student/send_message_portal">
                <div class="form-group">
                    <label>{{ 'Select Doctor:' if lang == 'en' else 'اختر الدكتور:' }}</label>
                    <select name="doctor_id" required>
                        {% for d in doctors %}
                        <option value="{{ d.id }}">#{{ d.id }} - {{ tr_name(d.full_name, lang) }} ({{ d.office_number }} | {{ tr_dept(d.dept_name, lang) }})</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>{{ 'Choose 1 of the 3 Ready Messages:' if lang == 'en' else 'اختر إحدى الرسائل الجاهزة الثلاث:' }}</label>
                    {% for ar_t, en_t in STUDENT_TEMPLATES[:3] %}
                    <label class="template-radio">
                        <input type="radio" name="template_type" value="{{ ar_t }}" {% if loop.first %}checked{% endif %}>
                        <span style="font-size:0.86rem;">📌 {{ en_t if lang == 'en' else ar_t }}</span>
                    </label>
                    {% endfor %}
                </div>
                <div class="form-group">
                    <label>{{ 'Your Note / Question (Optional):' if lang == 'en' else 'ملاحظتك أو سؤالك للدكتور (اختياري):' }}</label>
                    <textarea name="student_note" rows="2" placeholder="{{ 'Write a short note...' if lang == 'en' else 'اكتب سؤالك أو الوقت المقترح...' }}"></textarea>
                </div>
                <button type="submit" class="btn btn-success" style="width:100%;">
                    🚀 {{ 'Send Message Now' if lang == 'en' else 'إرسال الرسالة للدكتور الآن' }}
                </button>
            </form>
        </div>

        <div class="form-box" style="margin:0; max-width:100%; border-top:4px solid var(--secondary);">
            <h3 style="color:var(--primary); margin-bottom:12px;">
                📬 {{ 'Doctor Replies, Direct Messages & Appointments' if lang == 'en' else 'ردود الدكاترة والرسائل والمواعيد المحددة لك' }} ({{ my_messages|length }})
            </h3>
            {% for m in my_messages %}
            <div style="border:1px solid var(--border); border-radius:10px; padding:14px; margin-bottom:12px; background:#f8fafc;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
                    <strong style="color:var(--primary); font-size:0.98rem;">
                        👨‍🏫 <a href="/doctor/{{ m.doctor_id }}" style="color:var(--secondary); text-decoration:none;">{{ tr_name(m.doc_name, lang) }}</a>
                        <span class="badge badge-bldg">{{ m.office_number }}</span>
                    </strong>
                    {% if m.doctor_status == 'Available' %}
                        <span class="status-dot st-Available">🟢 {{ 'Doctor Reply: Available' if lang == 'en' else 'رد الدكتور: متاح (موافق على الموعد)' }}</span>
                    {% elif m.doctor_status == 'Busy' %}
                        <span class="status-dot st-Busy">🔴 {{ 'Doctor Reply: Busy' if lang == 'en' else 'رد الدكتور: مشغول حالياً' }}</span>
                    {% elif m.doctor_status == 'Postponed' %}
                        <span class="status-dot st-Postponed">🟡 {{ 'Doctor Reply: Postponed to New Time' if lang == 'en' else 'رد الدكتور: تأجيل إلى موعد جديد' }}</span>
                    {% else %}
                        <span class="status-dot st-Pending">⏳ {{ 'Waiting for Doctor Reply' if lang == 'en' else 'بانتظار رد الدكتور' }}</span>
                    {% endif %}
                </div>
                <div style="font-size:0.86rem; color:#0369a1; font-weight:700; margin-bottom:4px;">
                    📌 {{ tr_tpl(m.template_type, lang) }}
                </div>
                {% if m.student_note %}
                <div style="font-size:0.86rem; color:#334155; margin-bottom:6px;">
                    💬 <strong>{{ 'Your Message:' if lang == 'en' else 'رسالتك:' }}</strong> "{{ tr_msg(m.student_note, lang) }}"
                </div>
                {% endif %}
                <div style="font-size:0.76rem; color:var(--muted);">🕒 {{ m.created_at }}</div>

                {% if m.doctor_status != 'Pending' %}
                <div style="margin-top:10px; background:#ffffff; border-inline-start:4px solid #10b981; padding:10px 12px; border-radius:6px; border:1px solid #cbd5e1;">
                    <div style="font-weight:700; color:#0f2942; font-size:0.9rem;">
                        ⏰ {{ 'Specified Available Hour from Doctor:' if lang == 'en' else 'الساعة المتاحة التي حددها الدكتور:' }}
                        <span style="color:#059669; background:#dcfce7; padding:2px 8px; border-radius:6px;">{{ tr_msg(m.suggested_time, lang) if m.suggested_time else ('During Office Hours' if lang == 'en' else 'خلال الساعات المكتبية') }}</span>
                    </div>
                    {% if m.doctor_reply %}
                    <div style="font-size:0.88rem; color:#1e293b; margin-top:5px;">
                        📝 <strong>{{ 'Doctor Note:' if lang == 'en' else 'رسالة الدكتور لك:' }}</strong> {{ tr_msg(m.doctor_reply, lang) }}
                    </div>
                    {% endif %}
                    <div style="font-size:0.74rem; color:var(--muted); margin-top:4px;">✓ {{ 'Replied at:' if lang == 'en' else 'تاريخ رد الدكتور:' }} {{ m.replied_at }}</div>
                </div>
                {% endif %}
            </div>
            {% else %}
            <p style="color:var(--muted); text-align:center; padding:1.5rem;">
                {{ 'You have not sent or received any messages yet.' if lang == 'en' else 'لا توجد رسائل بعد. اختر دكتوراً من القائمة على اليمين وأرسل له رسالة جاهزة الآن!' }}
            </p>
            {% endfor %}
        </div>
    </div>
    {% endblock %}
    """
    full_tpl = BASE_LAYOUT.replace("{% block content %}{% endblock %}", content.split("{% block content %}")[1].split("{% endblock %}")[0])
    return render_template_string(full_tpl, doctors=doctors, my_messages=my_messages)


@app.route("/student/send_message/<int:doc_id>", methods=["POST"])
def student_send_message(doc_id):
    if session.get("role") != "student":
        return redirect(url_for("login"))

    template_type = request.form.get("template_type", STUDENT_TEMPLATES[0][0])
    student_note = request.form.get("student_note", "").strip()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO Messages (student_user_id, student_name, student_number, doctor_id, template_type, student_note, doctor_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)
        """,
        (
            session["user_id"],
            session.get("full_name", session["username"]),
            session.get("student_number", "202220020"),
            doc_id,
            template_type,
            student_note,
            now_str,
        ),
    )
    conn.commit()
    conn.close()
    flash("✅ تم إرسال رسالتك للدكتور بنجاح! ستظهر لك إجابة الدكتور والساعة المحددة هنا في حسابك فور رده.")
    return redirect(url_for("student_portal"))


@app.route("/student/send_message_portal", methods=["POST"])
def student_send_message_portal():
    doc_id = int(request.form.get("doctor_id", 1))
    return student_send_message(doc_id)


@app.route("/dashboard", methods=["GET", "POST"])
def doctor_dashboard():
    if session.get("role") != "doctor":
        return redirect(url_for("login"))

    doc_id = session["doctor_id"]
    conn = get_db_connection()

    if request.method == "POST":
        building_code = request.form["building_code"]
        floor = request.form["floor"]
        office = request.form["office_number"]
        live_status = request.form.get("live_status", "Available")
        picked_days = request.form.getlist("days_list")
        days_str = " , ".join(picked_days) if picked_days else "الأحد , الثلاثاء"
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]

        conn.execute(
            "UPDATE Doctors SET building_code = ?, floor = ?, office_number = ?, live_status = ? WHERE id = ?",
            (building_code, floor, office, live_status, doc_id),
        )
        conn.execute(
            "UPDATE OfficeHours SET days = ?, start_time = ?, end_time = ? WHERE doctor_id = ?",
            (days_str, start_time, end_time, doc_id),
        )
        conn.commit()
        flash("✅ تم تحديث حالة تواجدك ومكتبك وساعاتك المكتبية بنجاح!")

    doc = conn.execute(
        """
        SELECT d.*, dept.name AS dept_name, oh.days, oh.start_time, oh.end_time
        FROM Doctors d
        JOIN Departments dept ON d.department_id = dept.id
        LEFT JOIN OfficeHours oh ON d.id = oh.doctor_id
        WHERE d.id = ?
        """,
        (doc_id,),
    ).fetchone()
    buildings = conn.execute("SELECT * FROM Buildings ORDER BY code ASC").fetchall()
    students_list = conn.execute(
        "SELECT id, full_name, student_number, username FROM Users WHERE role = 'student' ORDER BY id DESC"
    ).fetchall()
    inbox_messages = conn.execute(
        "SELECT * FROM Messages WHERE doctor_id = ? ORDER BY id DESC",
        (doc_id,),
    ).fetchall()
    conn.close()

    current_days = [d.strip() for d in (doc["days"] or "").split(",") if d.strip()]
    floors_list = ["الطابق الأرضي", "الطابق الأول", "الطابق الثاني", "الطابق الثالث"]

    content = """
    {% extends "base" %}
    {% block content %}
    <div style="display:grid; grid-template-columns: 1fr 1.35fr; gap: 1.4rem; align-items:start;">
        <div class="form-box" style="margin:0; max-width:100%;">
            <h2 style="color:var(--primary);">{{ tr_name(doc.full_name, lang) }} (#{{ doc.id }})</h2>
            <p style="color: var(--muted); margin-bottom: 1rem;">{{ tr_rank(doc.academic_rank, lang) }} — {{ tr_dept(doc.dept_name, lang) }}</p>
            <form method="POST">
                <div class="form-group">
                    <label style="color:#0369a1;">📡 {{ 'My Live Office Status Now:' if lang == 'en' else 'حالة تواجدي المباشرة الآن (تظهر للطلبة فوراً):' }}</label>
                    <select name="live_status" style="font-weight:700; border:2px solid #0284c7;">
                        <option value="Available" {% if doc.live_status == 'Available' %}selected{% endif %}>🟢 {{ 'Available in Office Now' if lang == 'en' else 'متواجد بالمكتب الآن' }}</option>
                        <option value="Busy" {% if doc.live_status == 'Busy' %}selected{% endif %}>🟡 {{ 'In Dept Meeting / Busy' if lang == 'en' else 'في اجتماع قسم / مشغول' }}</option>
                        <option value="InLecture" {% if doc.live_status == 'InLecture' %}selected{% endif %}>🔴 {{ 'In Lecture Now' if lang == 'en' else 'في محاضرة حالياً' }}</option>
                        <option value="OffDuty" {% if doc.live_status == 'OffDuty' %}selected{% endif %}>⚪ {{ 'Off Duty / Unavailable' if lang == 'en' else 'غير متواجد / خارج الدوام' }}</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>{{ 'Building' if lang == 'en' else 'المبنى' }}</label>
                    <select name="building_code">
                        {% for b in buildings %}
                        <option value="{{ b.code }}" {% if b.code == doc.building_code %}selected{% endif %}>{{ b.name_en if lang == 'en' else b.name_ar }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>{{ 'Floor' if lang == 'en' else 'الطابق' }}</label>
                    <select name="floor" required>
                        {% for fl in floors_list %}
                        <option value="{{ fl }}" {% if fl == doc.floor %}selected{% endif %}>{{ tr_floor(fl, lang) }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>{{ 'Office Number' if lang == 'en' else 'رقم المكتب' }}</label>
                    <input type="text" name="office_number" value="{{ doc.office_number }}" required>
                </div>
                <div class="form-group">
                    <label>{{ 'Select Office Hours Days' if lang == 'en' else 'اختر أيام الساعات المكتبية' }}</label>
                    <div class="chip-list" style="padding: 8px; background: #f8fafc; border: 1px solid var(--border); border-radius: 8px;">
                        {% for day in ALL_DAYS_AR %}
                        <label class="chip-label">
                            <input type="checkbox" name="days_list" value="{{ day }}" {% if day in current_days %}checked{% endif %}>
                            <span>{{ DAY_EN[day] if lang == 'en' else day }}</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>
                <div style="display:flex; gap:10px;">
                    <div class="form-group" style="flex:1;">
                        <label>{{ 'Start Time' if lang == 'en' else 'من الساعة' }}</label>
                        <input type="text" name="start_time" value="{{ doc.start_time }}" required>
                    </div>
                    <div class="form-group" style="flex:1;">
                        <label>{{ 'End Time' if lang == 'en' else 'إلى الساعة' }}</label>
                        <input type="text" name="end_time" value="{{ doc.end_time }}" required>
                    </div>
                </div>
                <button type="submit" class="btn" style="width:100%;">💾 {{ 'Save Office & Schedule Changes' if lang == 'en' else 'حفظ تعديلات المكتب والجدول' }}</button>
            </form>
        </div>

        <div style="display:flex; flex-direction:column; gap:1.2rem;">
            <!-- Direct Message from Doctor to Student -->
            <div class="form-box" style="margin:0; max-width:100%; border-top:4px solid #10b981; background:#f0fdf4;">
                <h3 style="color:#065f46; margin-bottom:8px;">
                    📨 {{ 'Send Direct Message / Appointment to a Student' if lang == 'en' else 'إرسال رسالة أو موعد مباشر من الدكتور إلى طالب' }}
                </h3>
                <form method="POST" action="/doctor/send_to_student">
                    <div style="display:grid; grid-template-columns: 1.3fr 1fr; gap:8px; margin-bottom:8px;">
                        <div>
                            <label style="font-size:0.82rem; font-weight:700;">{{ 'Select Student:' if lang == 'en' else 'اختر الطالب المستلم:' }}</label>
                            <select name="student_user_id" required style="width:100%; padding:7px; border-radius:6px; border:1px solid #cbd5e1;">
                                {% for st in students_list %}
                                <option value="{{ st.id }}">{{ tr_name(st.full_name, lang) }} ({{ st.student_number }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div>
                            <label style="font-size:0.82rem; font-weight:700;">⏰ {{ 'Available Hour:' if lang == 'en' else 'الساعة المحددة للطالب:' }}</label>
                            <input type="text" name="suggested_time" placeholder="{{ 'e.g. 12:30 PM' if lang == 'en' else 'مثال: 12:30 ظهراً' }}" value="12:30" required style="width:100%; padding:7px; border-radius:6px; border:1px solid #cbd5e1;">
                        </div>
                    </div>
                    <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px;">
                        <label style="background:#dcfce7; color:#166534; padding:4px 10px; border-radius:8px; font-size:0.82rem; font-weight:700; cursor:pointer;">
                            <input type="radio" name="doctor_status" value="Available" checked> 🟢 {{ 'Available' if lang == 'en' else 'متاح' }}
                        </label>
                        <label style="background:#fee2e2; color:#991b1b; padding:4px 10px; border-radius:8px; font-size:0.82rem; font-weight:700; cursor:pointer;">
                            <input type="radio" name="doctor_status" value="Busy"> 🔴 {{ 'Busy' if lang == 'en' else 'مشغول' }}
                        </label>
                        <label style="background:#fef3c7; color:#92400e; padding:4px 10px; border-radius:8px; font-size:0.82rem; font-weight:700; cursor:pointer;">
                            <input type="radio" name="doctor_status" value="Postponed"> 🟡 {{ 'Postponed' if lang == 'en' else 'تأجيل' }}
                        </label>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <input type="text" name="doctor_reply" placeholder="{{ 'Write message to student (e.g. Please pass by my office at 12:30)...' if lang == 'en' else 'اكتب رسالتك للطالب (مثال: يرجى مراجعتي في المكتب بالساعة المحددة)...' }}" required style="flex:1; padding:8px; border-radius:6px; border:1px solid #cbd5e1;">
                        <button type="submit" class="btn btn-success" style="padding:8px 16px;">📤 {{ 'Send to Student' if lang == 'en' else 'إرسال للطالب' }}</button>
                    </div>
                </form>
            </div>

            <!-- Incoming Student Messages -->
            <div class="form-box" style="margin:0; max-width:100%; border-top:4px solid var(--accent);">
                <h3 style="color:var(--primary); margin-bottom:10px;">
                    📩 {{ 'Incoming Student Messages (Reply with Status & Time)' if lang == 'en' else 'رسائل الطلبة الواردة (رد على الطالب وحدد الساعة المتاحة)' }} ({{ inbox_messages|length }})
                </h3>
                {% for m in inbox_messages %}
                <div style="border:1px solid var(--border); border-radius:10px; padding:14px; margin-bottom:12px; background:#f8fafc;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                        <strong style="color:var(--primary);">🎓 {{ tr_name(m.student_name, lang) }} ({{ m.student_number }})</strong>
                        <span class="status-dot st-{{ m.doctor_status }}">
                            {% if m.doctor_status == 'Available' %}🟢 {{ 'Replied: Available' if lang == 'en' else 'تم الرد: متاح' }}
                            {% elif m.doctor_status == 'Busy' %}🔴 {{ 'Replied: Busy' if lang == 'en' else 'تم الرد: مشغول' }}
                            {% elif m.doctor_status == 'Postponed' %}🟡 {{ 'Replied: Postponed' if lang == 'en' else 'تم الرد: تأجيل' }}
                            {% else %}⏳ {{ 'Pending Doctor Reply' if lang == 'en' else 'بانتظار ردك' }}{% endif %}
                        </span>
                    </div>
                    <div style="font-size:0.86rem; color:#0369a1; font-weight:700; margin:5px 0;">📌 {{ tr_tpl(m.template_type, lang) }}</div>
                    {% if m.student_note %}
                    <div style="font-size:0.86rem; background:white; padding:7px 10px; border-radius:6px; border:1px solid #e2e8f0; margin-bottom:8px;">
                        💬 "{{ tr_msg(m.student_note, lang) }}"
                    </div>
                    {% endif %}
                    <div style="font-size:0.75rem; color:var(--muted); margin-bottom:8px;">🕒 {{ m.created_at }}</div>

                    <form method="POST" action="/doctor/reply_message/{{ m.id }}" style="background:white; padding:10px; border-radius:8px; border:1px solid #cbd5e1;">
                        <div style="font-weight:700; font-size:0.84rem; margin-bottom:6px; color:var(--primary);">
                            ⚡ {{ 'Select Reply Status (3 Options):' if lang == 'en' else 'اختر حالة الرد على الطالب (3 خيارات جاهزة):' }}
                        </div>
                        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px;">
                            <label style="background:#dcfce7; color:#166534; padding:5px 10px; border-radius:8px; font-size:0.82rem; font-weight:700; cursor:pointer;">
                                <input type="radio" name="doctor_status" value="Available" {% if m.doctor_status in ('Available', 'Pending') %}checked{% endif %}>
                                🟢 {{ 'Available' if lang == 'en' else 'متاح' }}
                            </label>
                            <label style="background:#fee2e2; color:#991b1b; padding:5px 10px; border-radius:8px; font-size:0.82rem; font-weight:700; cursor:pointer;">
                                <input type="radio" name="doctor_status" value="Busy" {% if m.doctor_status == 'Busy' %}checked{% endif %}>
                                🔴 {{ 'Busy' if lang == 'en' else 'مشغول' }}
                            </label>
                            <label style="background:#fef3c7; color:#92400e; padding:5px 10px; border-radius:8px; font-size:0.82rem; font-weight:700; cursor:pointer;">
                                <input type="radio" name="doctor_status" value="Postponed" {% if m.doctor_status == 'Postponed' %}checked{% endif %}>
                                🟡 {{ 'Postpone' if lang == 'en' else 'تأجيل' }}
                            </label>
                        </div>
                        <div style="display:grid; grid-template-columns: 1fr 1.5fr; gap:8px; margin-bottom:8px;">
                            <div>
                                <label style="font-size:0.78rem; font-weight:700;">⏰ {{ 'Available Hour:' if lang == 'en' else 'الساعة المتاحة للطالب:' }}</label>
                                <input type="text" name="suggested_time" value="{{ tr_msg(m.suggested_time, lang) if m.suggested_time else '12:30' }}" placeholder="{{ 'e.g. 12:30 PM' if lang == 'en' else 'مثال: 12:30 ظهراً' }}" style="width:100%; padding:6px 8px; border:1px solid #cbd5e1; border-radius:6px; font-size:0.85rem;">
                            </div>
                            <div>
                                <label style="font-size:0.78rem; font-weight:700;">💬 {{ 'Reply Message:' if lang == 'en' else 'رسالة الرد للطالب:' }}</label>
                                <input type="text" name="doctor_reply" value="{{ tr_msg(m.doctor_reply, lang) }}" placeholder="{{ 'Come by at the specified hour...' if lang == 'en' else 'تفضل بالحضور للمكتب في الساعة المحددة...' }}" style="width:100%; padding:6px 8px; border:1px solid #cbd5e1; border-radius:6px; font-size:0.85rem;">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-success" style="width:100%; padding:8px; font-size:0.88rem;">
                            📤 {{ 'Send Reply & Time to Student Now' if lang == 'en' else 'إرسال الرد والساعة للطالب الآن' }}
                        </button>
                    </form>
                </div>
                {% else %}
                <p style="color:var(--muted); text-align:center; padding:1.5rem;">{{ 'No student messages yet.' if lang == 'en' else 'لا توجد رسائل واردة من الطلبة حالياً.' }}</p>
                {% endfor %}
            </div>
        </div>
    </div>
    {% endblock %}
    """
    full_tpl = BASE_LAYOUT.replace("{% block content %}{% endblock %}", content.split("{% block content %}")[1].split("{% endblock %}")[0])
    return render_template_string(
        full_tpl,
        doc=doc,
        buildings=buildings,
        students_list=students_list,
        current_days=current_days,
        inbox_messages=inbox_messages,
        floors_list=floors_list,
    )


@app.route("/doctor/reply_message/<int:msg_id>", methods=["POST"])
def doctor_reply_message(msg_id):
    if session.get("role") != "doctor":
        return redirect(url_for("login"))

    doctor_status = request.form.get("doctor_status", "Available")
    suggested_time = request.form.get("suggested_time", "").strip()
    doctor_reply = request.form.get("doctor_reply", "").strip()
    if not doctor_reply:
        doctor_reply = "Please attend at the specified hour" if session.get("lang") == "en" else "يرجى الحضور في الموعد المحدد"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_db_connection()
    conn.execute(
        """
        UPDATE Messages
        SET doctor_status = ?, suggested_time = ?, doctor_reply = ?, replied_at = ?
        WHERE id = ? AND doctor_id = ?
        """,
        (doctor_status, suggested_time, doctor_reply, now_str, msg_id, session["doctor_id"]),
    )
    conn.commit()
    conn.close()
    flash("✅ تم إرسال ردك وتحديد الساعة للطالب بنجاح! سيظهر الرد الآن في حساب الطالب مباشرة.")
    return redirect(url_for("doctor_dashboard"))


@app.route("/doctor/send_to_student", methods=["POST"])
def doctor_send_to_student():
    if session.get("role") != "doctor":
        return redirect(url_for("login"))

    student_user_id = int(request.form.get("student_user_id", 0))
    doctor_status = request.form.get("doctor_status", "Available")
    suggested_time = request.form.get("suggested_time", "12:30").strip()
    doctor_reply = request.form.get("doctor_reply", "").strip()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_db_connection()
    st = conn.execute("SELECT * FROM Users WHERE id = ?", (student_user_id,)).fetchone()
    if st:
        conn.execute(
            """
            INSERT INTO Messages (student_user_id, student_name, student_number, doctor_id, template_type, student_note, doctor_status, suggested_time, doctor_reply, created_at, replied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                st["id"],
                st["full_name"] or st["username"],
                st["student_number"] or "",
                session["doctor_id"],
                "رسالة مباشرة من الدكتور إلى الطالب",
                "",
                doctor_status,
                suggested_time,
                doctor_reply,
                now_str,
                now_str,
            ),
        )
        conn.commit()
        flash(f"✅ تم إرسال رسالتك والموعد ({suggested_time}) مباشرة إلى الطالب ({st['full_name']}) بنجاح!")
    conn.close()
    return redirect(url_for("doctor_dashboard"))


@app.route("/admin", methods=["GET"])
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    doctors = conn.execute(
        """
        SELECT d.*, dept.name AS dept_name, oh.days, oh.start_time, oh.end_time
        FROM Doctors d
        JOIN Departments dept ON d.department_id = dept.id
        LEFT JOIN OfficeHours oh ON d.id = oh.doctor_id
        WHERE COALESCE(d.is_deleted, 0) = 0
        ORDER BY d.id ASC
        """
    ).fetchall()
    deleted_doctors = conn.execute(
        """
        SELECT d.*, dept.name AS dept_name, oh.days, oh.start_time, oh.end_time
        FROM Doctors d
        JOIN Departments dept ON d.department_id = dept.id
        LEFT JOIN OfficeHours oh ON d.id = oh.doctor_id
        WHERE COALESCE(d.is_deleted, 0) = 1
        ORDER BY d.id ASC
        """
    ).fetchall()
    departments = conn.execute("SELECT rowid AS id, * FROM Departments").fetchall()
    buildings = conn.execute("SELECT * FROM Buildings ORDER BY code ASC").fetchall()
    stats_msg = conn.execute("SELECT COUNT(*) AS c FROM Messages").fetchone()["c"]
    stats_stu = conn.execute("SELECT COUNT(*) AS c FROM Users WHERE role='student'").fetchone()["c"]
    conn.close()

    content = """
    {% extends "base" %}
    {% block content %}
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-bottom:1.2rem;">
        <div class="card" style="background:#0f2942; color:white;">
            <div style="font-size:0.85rem; opacity:0.85;">{{ 'Total Faculty Members' if lang == 'en' else 'إجمالي الدكاترة' }}</div>
            <div style="font-size:1.8rem; font-weight:800; color:#f59e0b;">{{ doctors|length }}</div>
        </div>
        <div class="card" style="background:#1e3a8a; color:white;">
            <div style="font-size:0.85rem; opacity:0.85;">{{ 'Academic Departments' if lang == 'en' else 'الأقسام الأكاديمية' }}</div>
            <div style="font-size:1.8rem; font-weight:800; color:#38bdf8;">{{ departments|length }}</div>
        </div>
        <div class="card" style="background:#065f46; color:white;">
            <div style="font-size:0.85rem; opacity:0.85;">{{ 'Registered Students' if lang == 'en' else 'الطلبة المسجلون' }}</div>
            <div style="font-size:1.8rem; font-weight:800; color:#6ee7b7;">{{ stats_stu }}</div>
        </div>
        <div class="card" style="background:#7c2d12; color:white;">
            <div style="font-size:0.85rem; opacity:0.85;">{{ 'Student-Doctor Messages' if lang == 'en' else 'الرسائل والمواعيد المتبادلة' }}</div>
            <div style="font-size:1.8rem; font-weight:800; color:#fde047;">{{ stats_msg }}</div>
        </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; margin-bottom: 1.5rem;">
        <div class="form-box" style="margin:0; max-width:100%;">
            <h3 style="color:var(--primary); margin-bottom:10px;">➕ {{ 'Add New Academic Department (Appears to Students Immediately)' if lang == 'en' else 'إضافة قسم أكاديمي جديد (يظهر للطلبة في التسجيل فوراً)' }}</h3>
            <form method="POST" action="/admin/add_department">
                <div class="form-group">
                    <label>{{ 'Department Name' if lang == 'en' else 'اسم القسم الجديد' }}</label>
                    <input type="text" name="dept_name" placeholder="{{ 'e.g. Data Science & AI' if lang == 'en' else 'مثال: علم البيانات' }}" required>
                </div>
                <div class="form-group">
                    <label>{{ 'Building' if lang == 'en' else 'المبنى التابع له' }}</label>
                    <select name="building_code">
                        {% for b in buildings %}
                        <option value="{{ b.code }}">{{ b.name_en if lang == 'en' else b.name_ar }}</option>
                        {% endfor %}
                    </select>
                </div>
                <button type="submit" class="btn">{{ 'Add Department' if lang == 'en' else 'إضافة القسم' }}</button>
            </form>
        </div>

        <div class="form-box" style="margin:0; max-width:100%;">
            <h3 style="color:var(--primary); margin-bottom:10px;">➕ {{ 'Add New Building' if lang == 'en' else 'إضافة مبنى جامعي جديد' }}</h3>
            <form method="POST" action="/admin/add_building">
                <div style="display:flex; gap:8px;">
                    <div class="form-group" style="flex:1;">
                        <label>{{ 'Building Code' if lang == 'en' else 'رمز المبنى' }}</label>
                        <input type="text" name="code" placeholder="E" required>
                    </div>
                    <div class="form-group" style="flex:2;">
                        <label>{{ 'Arabic Name' if lang == 'en' else 'اسم المبنى بالعربي' }}</label>
                        <input type="text" name="name_ar" placeholder="مبنى E — المختبرات" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>{{ 'English Name' if lang == 'en' else 'اسم المبنى بالإنجليزي' }}</label>
                    <input type="text" name="name_en" placeholder="Building E — Labs" required>
                </div>
                <button type="submit" class="btn">{{ 'Add Building' if lang == 'en' else 'إضافة المبنى' }}</button>
            </form>
        </div>
    </div>

    <div class="form-box" style="max-width: 100%; margin-bottom: 1.8rem;">
        <h3 style="margin-bottom: 1rem; color:var(--primary);">👨‍🏫 {{ 'Add New Faculty Member' if lang == 'en' else 'إضافة عضو هيئة تدريس جديد' }}</h3>
        <form method="POST" action="/admin/add_doctor" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px;">
            <input type="text" name="full_name" placeholder="{{ 'Full Name (Dr. ...)' if lang == 'en' else 'الاسم الكامل (د. ...)' }}" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
            <select name="academic_rank" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
                <option value="أستاذ دكتور">{{ tr_rank('أستاذ دكتور', lang) }}</option>
                <option value="أستاذ مشارك">{{ tr_rank('أستاذ مشارك', lang) }}</option>
                <option value="أستاذ مساعد">{{ tr_rank('أستاذ مساعد', lang) }}</option>
                <option value="مدرس">{{ tr_rank('مدرس', lang) }}</option>
            </select>
            <select name="department_id" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
                {% for dept in departments %}
                <option value="{{ dept.id }}">{{ tr_dept(dept.name, lang) }}</option>
                {% endfor %}
            </select>
            <select name="building_code" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
                {% for b in buildings %}
                <option value="{{ b.code }}">{{ b.name_en if lang == 'en' else b.name_ar }}</option>
                {% endfor %}
            </select>
            <select name="floor" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
                <option value="الطابق الأرضي">{{ tr_floor('الطابق الأرضي', lang) }}</option>
                <option value="الطابق الأول">{{ tr_floor('الطابق الأول', lang) }}</option>
                <option value="الطابق الثاني">{{ tr_floor('الطابق الثاني', lang) }}</option>
                <option value="الطابق الثالث">{{ tr_floor('الطابق الثالث', lang) }}</option>
            </select>
            <input type="text" name="office_number" placeholder="{{ 'Office (B-205)' if lang == 'en' else 'رقم المكتب (B-205)' }}" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
            <input type="email" name="email" placeholder="email@jadara.edu.jo" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
            <input type="text" name="days" placeholder="الأحد , الثلاثاء , الخميس" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
            <input type="text" name="start_time" placeholder="10:00" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
            <input type="text" name="end_time" placeholder="11:30" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
            <input type="text" name="username" placeholder="{{ 'Doctor Username' if lang == 'en' else 'اسم مستخدم للدكتور' }}" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
            <input type="text" name="password" placeholder="{{ 'Password' if lang == 'en' else 'كلمة المرور' }}" value="doctor123" required style="padding:9px;border:1px solid #cbd5e1;border-radius:8px;">
            <button type="submit" class="btn" style="grid-column: 1/-1;">➕ {{ 'Add Doctor to Database' if lang == 'en' else 'إضافة الدكتور إلى قاعدة البيانات' }}</button>
        </form>
    </div>

    {% if deleted_doctors %}
    <div class="form-box" style="max-width:100%; margin-bottom:1.8rem; border:2px solid #f59e0b; background:#fffbeb;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
            <h3 style="color:#92400e;">♻️ {{ 'Deleted Doctors — Click Restore to Recover Immediately' if lang == 'en' else 'سلة المحذوفات — الدكاترة المحذوفون (يمكنك استرداد أي دكتور فوراً)' }} ({{ deleted_doctors|length }})</h3>
            <a href="/admin/restore_all" class="btn btn-success" style="padding:7px 14px; font-size:0.84rem;">🔄 {{ 'Restore All Deleted Doctors' if lang == 'en' else 'استرداد جميع الدكاترة المحذوفين' }}</a>
        </div>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>{{ 'Doctor Name' if lang == 'en' else 'اسم الدكتور' }}</th>
                    <th>{{ 'Department' if lang == 'en' else 'القسم' }}</th>
                    <th>{{ 'Building & Office' if lang == 'en' else 'المبنى والمكتب' }}</th>
                    <th>{{ 'Restore' if lang == 'en' else 'استرداد' }}</th>
                </tr>
            </thead>
            <tbody>
                {% for ddoc in deleted_doctors %}
                <tr>
                    <td><strong>#{{ ddoc.id }}</strong></td>
                    <td>{{ tr_name(ddoc.full_name, lang) }}</td>
                    <td>{{ tr_dept(ddoc.dept_name, lang) }}</td>
                    <td>{{ ddoc.building_code }} | <strong>{{ ddoc.office_number }}</strong></td>
                    <td>
                        <a href="/admin/restore/{{ ddoc.id }}" class="btn btn-success" style="padding:5px 12px; font-size:0.8rem;">♻️ {{ 'Restore Doctor' if lang == 'en' else 'استرداد الدكتور' }}</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}

    <h3>📋 {{ 'Active Faculty Directory Management' if lang == 'en' else 'قائمة الدكاترة الفعالين حالياً' }} ({{ doctors|length }})</h3>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>{{ 'Doctor Name' if lang == 'en' else 'اسم الدكتور' }}</th>
                <th>{{ 'Department' if lang == 'en' else 'القسم' }}</th>
                <th>{{ 'Building & Office' if lang == 'en' else 'المبنى والمكتب' }}</th>
                <th>{{ 'Days & Hours' if lang == 'en' else 'الأيام والساعات' }}</th>
                <th>{{ 'Action' if lang == 'en' else 'إجراء' }}</th>
            </tr>
        </thead>
        <tbody>
            {% for doc in doctors %}
            <tr>
                <td><strong>{{ doc.id }}</strong></td>
                <td>{{ tr_name(doc.full_name, lang) }}</td>
                <td>{{ tr_dept(doc.dept_name, lang) }}</td>
                <td>{{ doc.building_code }} | <strong>{{ doc.office_number }}</strong> ({{ tr_floor(doc.floor, lang) }})</td>
                <td>{{ tr_days(doc.days, lang) }} ({{ doc.start_time }} - {{ doc.end_time }})</td>
                <td>
                    <a href="/admin/delete/{{ doc.id }}" class="btn btn-danger" style="padding: 4px 10px; font-size: 0.78rem;">{{ 'Delete' if lang == 'en' else 'حذف' }}</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endblock %}
    """
    full_tpl = BASE_LAYOUT.replace("{% block content %}{% endblock %}", content.split("{% block content %}")[1].split("{% endblock %}")[0])
    return render_template_string(full_tpl, doctors=doctors, deleted_doctors=deleted_doctors, departments=departments, buildings=buildings, stats_msg=stats_msg, stats_stu=stats_stu)


@app.route("/admin/add_department", methods=["POST"])
def admin_add_department():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    dept_name = request.form["dept_name"].strip()
    b_code = request.form["building_code"].strip()
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO Departments (name, building_code) VALUES (?, ?)", (dept_name, b_code))
        conn.commit()
        flash("✅ تم إضافة القسم الجديد بنجاح! سيظهر الآن للطلبة في صفحة التسجيل والفلترة.")
    except Exception:
        flash("⚠️ هذا القسم موجود مسبقاً.", "error")
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add_building", methods=["POST"])
def admin_add_building():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    code = request.form["code"].strip().upper()
    name_ar = request.form["name_ar"].strip()
    name_en = request.form["name_en"].strip()
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO Buildings (code, name_ar, name_en, description_ar) VALUES (?, ?, ?, ?)",
            (code, name_ar, name_en, name_ar),
        )
        conn.commit()
        flash("✅ تم إضافة المبنى الجديد بنجاح!")
    except Exception:
        flash("⚠️ رمز المبنى موجود مسبقاً.", "error")
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/add_doctor", methods=["POST"])
def add_doctor():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Doctors (full_name, academic_rank, department_id, building_code, floor, office_number, email, live_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Available')
        """,
        (
            request.form["full_name"],
            request.form["academic_rank"],
            request.form["department_id"],
            request.form["building_code"],
            request.form["floor"],
            request.form["office_number"],
            request.form["email"],
        ),
    )
    new_doc_id = cur.lastrowid

    cur.execute(
        "INSERT INTO OfficeHours (doctor_id, days, start_time, end_time) VALUES (?, ?, ?, ?)",
        (new_doc_id, request.form["days"], request.form["start_time"], request.form["end_time"]),
    )
    cur.execute(
        "INSERT INTO Users (username, password, role, doctor_id, full_name) VALUES (?, ?, 'doctor', ?, ?)",
        (request.form["username"], request.form["password"], new_doc_id, request.form["full_name"]),
    )
    conn.commit()
    conn.close()
    flash("✅ تم إضافة الدكتور الجديد بنجاح!")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete/<int:doc_id>")
def delete_doctor(doc_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("UPDATE Doctors SET is_deleted = 1 WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    flash(f"🗑️ تم نقل الدكتور (#{doc_id}) إلى سلة المحذوفات؛ يمكنك استرداده في أي وقت من قسم (سلة المحذوفات) بالأسفل.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/restore/<int:doc_id>")
def restore_doctor(doc_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("UPDATE Doctors SET is_deleted = 0 WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    flash(f"♻️ تم استرداد الدكتور (#{doc_id}) وإعادته إلى الدليل الفعال بنجاح!")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/restore_all")
def restore_all_doctors():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("UPDATE Doctors SET is_deleted = 0")
    conn.commit()
    conn.close()
    flash("♻️ تم استرداد جميع الدكاترة المحذوفين وإعادتهم للدليل بنجاح!")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)