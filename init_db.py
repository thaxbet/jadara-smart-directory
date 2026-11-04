# -*- coding: utf-8 -*-
"""
ملف إنشاء وتجهيز قاعدة البيانات (100 دكتور من 1 إلى 100 - المباني A, B, C, D - الأيام المرنة)
مشروع: دليل الساعات المكتبية ومواقع الدكاترة الذكي
إعداد المطور الرئيسي: ثابت قيس محمد قواسمة (202220020)
"""

import sqlite3

DB_FILENAME = "database.db"

RAW_DOCTORS = """1|د. أحمد إبراهيم خليل|أستاذ مشارك|1|1|الطابق الثاني|B-204|a.khalil@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
2|د. رانيا محمود القضاة|أستاذ مساعد|2|1|الطابق الأول|B-108|r.qudah@jadara.edu.jo|Mon,Wed|11:00 - 12:30
3|أ.د. طارق زياد العبدالله|أستاذ دكتور|3|3|الطابق الثالث|C-312|t.abdallah@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
4|د. هبة سامي الخطيب|أستاذ مساعد|4|2|الطابق الثاني|A-215|h.khatib@jadara.edu.jo|Mon,Wed|09:30 - 11:00
5|د. حسام عمر التميمي|أستاذ مشارك|5|4|الطابق الأرضي|D-005|h.tamimi@jadara.edu.jo|Sun,Tue,Thu|09:00 - 10:00
6|د. يزن مصطفى العزام|أستاذ مساعد|1|1|الطابق الثاني|B-206|y.azzam@jadara.edu.jo|Mon,Wed|12:30 - 14:00
7|د. منى فؤاد الروسان|أستاذ مشارك|2|1|الطابق الأول|B-112|m.rousan@jadara.edu.jo|Sun,Tue,Thu|11:00 - 12:00
8|د. حمزة علي الجراح|أستاذ مساعد|3|3|الطابق الثالث|C-305|h.jarrah@jadara.edu.jo|Sun,Tue,Thu|13:00 - 14:00
9|د. ليلى حسن بني هاني|أستاذ مساعد|4|2|الطابق الثاني|A-220|l.banihani@jadara.edu.jo|Mon,Wed|10:00 - 11:30
10|د. فراس ناصر الزعبي|أستاذ دكتور|2|1|الطابق الأول|B-101|f.zoubi@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
11|د. دانية عبد الله الشبول|أستاذ مساعد|5|4|الطابق الأول|D-104|d.shboul@jadara.edu.jo|Mon,Wed|08:30 - 10:00
12|د. خالد وليد الطعاني|أستاذ مشارك|1|1|الطابق الثاني|B-202|k.taani@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
13|د. سميرة عدنان العمري|أستاذ مساعد|2|1|الطابق الأول|B-115|s.omari@jadara.edu.jo|Mon,Wed|13:00 - 14:30
14|د. مجد توفيق مقابلة|أستاذ مشارك|3|3|الطابق الثالث|C-318|m.muqableh@jadara.edu.jo|Sun,Tue,Thu|11:00 - 12:00
15|د. عمر بشير غرايبة|أستاذ مساعد|4|2|الطابق الثاني|A-218|o.gharaibeh@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
16|د. ولاء محمود البطاينة|مدرس|5|4|الطابق الأرضي|D-009|w.bataineh@jadara.edu.jo|Mon,Wed|11:30 - 13:00
17|د. بشار كمال الهنداوي|أستاذ مشارك|1|1|الطابق الثاني|B-210|b.hindawi@jadara.edu.jo|Sun,Tue,Thu|09:00 - 10:00
18|د. نادين سمير عبيدات|أستاذ مساعد|2|1|الطابق الأول|B-105|n.obeidat@jadara.edu.jo|Mon,Wed|10:00 - 11:30
19|د. معتز نضال الخصاونة|أستاذ مساعد|3|3|الطابق الثالث|C-301|m.khasawneh@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
20|د. إيناس كمال مريان|أستاذ مساعد|1|1|الطابق الثاني|B-208|e.maryan@jadara.edu.jo|Mon,Wed|12:00 - 13:30
21|أ.د. بلال محمد احمد زقيبه|أستاذ دكتور|1|1|الطابق الثاني|B-201|zaqaibeh@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
22|د. نذير خليف مصطفى غرايبه|أستاذ مشارك|1|1|الطابق الثاني|B-203|doc22@jadara.edu.jo|Mon,Wed|13:00 - 14:30
23|د. زاهي عبدالله محمود ابو سرحان|أستاذ مساعد|1|1|الطابق الثاني|B-205|z.abusarhan@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
24|د. بشرى طلال علي غزاله|أستاذ مساعد|1|1|الطابق الثاني|B-207|bu.ghazala@jadara.edu.jo|Mon,Wed|10:30 - 12:00
25|د. احمد علي عبدالكريم المهيرات|أستاذ مساعد|1|1|الطابق الثاني|B-209|a.mherat@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
26|د. باسم يوسف مفضي الزغول|أستاذ مساعد|1|1|الطابق الثاني|B-211|b.zughoul@jadara.edu.jo|Mon,Wed|09:00 - 10:30
27|د. علي عدنان حسين المزاري|أستاذ مساعد|1|1|الطابق الثاني|B-212|a.almazari@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
28|د. مرح يحيى عبدالحافظ الصرايرة|محاضر|1|1|الطابق الثاني|B-213|m.sarireh@jadara.edu.jo|Mon,Wed|11:00 - 12:30
29|أ.د. رياض فرحان محمد الشلبي|أستاذ دكتور|2|1|الطابق الأول|B-102|doc29@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
30|أ.د. محمد صبحي محمد البطاح|أستاذ دكتور|2|1|الطابق الأول|B-103|albatah@jadara.edu.jo|Mon,Wed|13:00 - 14:30
31|د. صالح علي خطاب العمري|أستاذ مشارك|2|1|الطابق الأول|B-104|omari08@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
32|د. اروى حسن فؤاد ظبيان|أستاذ مشارك|2|1|الطابق الأول|B-106|arwa@jadara.edu.jo|Mon,Wed|10:30 - 12:00
33|د. أسعد محمود اسعد الناصر|أستاذ مشارك|2|1|الطابق الأول|B-107|doc33@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
34|د. محمد جازي عبدالله البواعنه|أستاذ مشارك|2|1|الطابق الأول|B-109|doc34@jadara.edu.jo|Mon,Wed|09:00 - 10:30
35|د. ايمن محمد مصطفى ابو الرب|أستاذ مساعد|2|1|الطابق الأول|B-110|A.Abu-Errub@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
36|د. أيات أمين احمد الجراح|أستاذ مساعد|2|1|الطابق الأول|B-111|ay.aljarrah@jadara.edu.jo|Mon,Wed|11:00 - 12:30
37|د. عمر يوسف فيصل رواشدة|أستاذ مساعد|2|1|الطابق الأول|B-113|doc37@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
38|د. باسم محمد ذيب الرفاعي|أستاذ مساعد|2|1|الطابق الأول|B-114|b.rifai@jadara.edu.jo|Mon,Wed|13:00 - 14:30
39|د. محمد هايل عبدالكريم الرفاعي|أستاذ مساعد|2|1|الطابق الأول|B-116|m.alrefai@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
40|د. سامي صالح حسن قواسمه|أستاذ مساعد|2|1|الطابق الأول|B-117|sqawasmeh@jadara.edu.jo|Mon,Wed|10:30 - 12:00
41|د. بلال محمد طلال البطاينة|أستاذ مساعد|2|1|الطابق الأول|B-118|b.bataineh@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
42|د. حمزه محمد حسين الصمادي|أستاذ مساعد|2|1|الطابق الأول|B-119|doc42@jadara.edu.jo|Mon,Wed|09:00 - 10:30
43|د. سفيان احمد علي قسايمه|أستاذ مساعد|2|1|الطابق الأول|B-120|doc43@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
44|د. عبدالله واصف محمد مراشدة|أستاذ مساعد|2|1|الطابق الأول|B-121|doc44@jadara.edu.jo|Mon,Wed|11:00 - 12:30
45|د. نشأت علي محمد الرفاعي|أستاذ مساعد|2|1|الطابق الأول|B-122|doc45@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
46|د. محمد تحسين عبدالله طلعت|أستاذ مساعد|2|1|الطابق الأول|B-123|doc46@jadara.edu.jo|Mon,Wed|13:00 - 14:30
47|د. عبير ضرار يوسف ملكاوي|أستاذ مساعد|2|1|الطابق الأول|B-124|doc47@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
48|د. احلام شبلي محمد جوارنه|أستاذ مساعد|2|1|الطابق الأول|B-125|doc48@jadara.edu.jo|Mon,Wed|10:30 - 12:00
49|د. احمد خليفه محمود العمري|أستاذ مساعد|2|1|الطابق الأول|B-126|doc49@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
50|د. اريج علي حمد الحمود|محاضر|2|1|الطابق الأول|B-127|a.hamad@jadara.edu.jo|Mon,Wed|09:00 - 10:30
51|د. حسام اياد احمد مصطفى|محاضر|2|1|الطابق الأول|B-128|doc51@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
52|د. احمد زياد علي عودات|محاضر|2|1|الطابق الأول|B-129|doc52@jadara.edu.jo|Mon,Wed|11:00 - 12:30
53|د. مشهور معن مشهور بني عايش|محاضر|2|1|الطابق الأول|B-130|doc53@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
54|د. سارة باسم سليمان القرعان|محاضر|2|1|الطابق الأول|B-131|s.alquran@jadara.edu.jo|Mon,Wed|13:00 - 14:30
55|د. معن تيسير اكريم الرشدان|أستاذ مشارك|4|2|الطابق الثاني|A-214|dr.maen@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
56|د. صالح ابراهيم أحمد العمر|أستاذ مشارك|4|2|الطابق الثاني|A-216|saleh.o@jadara.edu.jo|Mon,Wed|10:30 - 12:00
57|د. معتز خالد يوسف عبد الواحد|أستاذ مشارك|4|2|الطابق الثاني|A-217|mutaz@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
58|د. مروان ناصر يوسف عتوم|أستاذ مساعد|4|2|الطابق الثاني|A-219|m.atoom@jadara.edu.jo|Mon,Wed|09:00 - 10:30
59|د. لؤي ناصر محمود نمراوي|أستاذ مساعد|4|2|الطابق الثاني|A-221|l.alnamrawi@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
60|د. تامر عبدالمجيد صالح بني عامر|أستاذ مساعد|4|2|الطابق الثاني|A-222|t.baniamer@jadara.edu.jo|Mon,Wed|11:00 - 12:30
61|د. فراس حنا سليم زوايده|أستاذ مساعد|4|2|الطابق الثاني|A-223|f.zawaideh@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
62|د. حسن عوض حسن السخني|أستاذ مساعد|4|2|الطابق الثاني|A-224|h.alsukhni@jadara.edu.jo|Mon,Wed|13:00 - 14:30
63|د. ايناس حسن موسى كنعان|محاضر|4|2|الطابق الثاني|A-225|e.kanan@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
64|د. يزن يحيى محمود العجلوني|محاضر|4|2|الطابق الثاني|A-226|doc64@jadara.edu.jo|Mon,Wed|10:30 - 12:00
65|د. معاذ مصطفى احمد نجيب|أستاذ مشارك|5|4|الطابق الأول|D-101|m.najeeb@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
66|د. محمد منصور فواز الخصاونة|أستاذ مشارك|5|4|الطابق الأول|D-102|m.alkhasawneh@jadara.edu.jo|Mon,Wed|09:00 - 10:30
67|د. معتصم شبيب حسين الخصاونه|أستاذ مشارك|5|4|الطابق الأول|D-103|doc67@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
68|د. عمر احمد ناجي عبيدات|أستاذ مساعد|5|4|الطابق الأول|D-105|doc68@jadara.edu.jo|Mon,Wed|11:00 - 12:30
69|د. احمد محمد لطفي الزريقي|أستاذ مساعد|5|4|الطابق الأول|D-106|doc69@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
70|د. معن مروان علي الزعبي|أستاذ مساعد|5|4|الطابق الأول|D-107|m.alzubi@jadara.edu.jo|Mon,Wed|13:00 - 14:30
71|د. عمران محمود محمد الجراح|أستاذ مساعد|5|4|الطابق الأول|D-108|o.aljarrah@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
72|أ.د. صالح ارشيد الطه العقيلي|أستاذ دكتور|3|3|الطابق الثالث|C-302|doc72@jadara.edu.jo|Mon,Wed|10:30 - 12:00
73|أ.د. احمد موسى مطلق العودات|أستاذ دكتور|3|3|الطابق الثالث|C-303|a.odat@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
74|د. سليم عيسى سليم الزعبي|أستاذ مشارك|3|3|الطابق الثالث|C-304|sa.alzoubi@jadara.edu.jo|Mon,Wed|09:00 - 10:30
75|د. مراد محمود علي بشابشه|أستاذ مساعد|3|3|الطابق الثالث|C-306|m.bashabsheh@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
76|د. مصطفى عبدالكريم احمد عبابنه|أستاذ مساعد|3|3|الطابق الثالث|C-307|mu.ababneh@jadara.edu.jo|Mon,Wed|11:00 - 12:30
77|د. احمد هاني حسين سوالمه|أستاذ مساعد|3|3|الطابق الثالث|C-308|doc77@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
78|د. احمد قاسم احمد مومني|أستاذ مساعد|3|3|الطابق الثالث|C-309|doc78@jadara.edu.jo|Mon,Wed|13:00 - 14:30
79|د. ندى جودت عبدالله الجراح|محاضر|3|3|الطابق الثالث|C-310|n.aljarrah@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
80|أ.د. نوح طلال محمد الهنداوي|أستاذ|1|1|الطابق الثاني|B-227|doc80@jadara.edu.jo|Mon,Wed|10:30 - 12:00
81|د. ليلى احمد عبدالله هيلات|مدرس|2|1|الطابق الأول|B-132|doc81@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
82|د. مصعب تيسير اكريم الرشدان|مدرس|2|1|الطابق الأول|B-133|doc82@jadara.edu.jo|Mon,Wed|09:00 - 10:30
83|د. محمد عبدالكريم سليم الفهيد|مدرس|2|1|الطابق الأول|B-134|doc83@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
84|د. عيسى محمد ابراهيم الصمادي|أستاذ مساعد|2|1|الطابق الأول|B-135|doc84@jadara.edu.jo|Mon,Wed|11:00 - 12:30
85|أ.د. مفلح محمد مفلح الذيابات|أستاذ|2|1|الطابق الأول|B-136|doc85@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
86|د. ايهاب عبدالرحمن سعيد مشعل|مدرس|2|1|الطابق الأول|B-137|doc86@jadara.edu.jo|Mon,Wed|13:00 - 14:30
87|د. اياد ياسين مصطفى الزعبي|أستاذ مساعد|2|1|الطابق الأول|B-138|doc87@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
88|د. رند خالد عبدالقادر الحايك|مدرس|2|1|الطابق الأول|B-139|doc88@jadara.edu.jo|Mon,Wed|10:30 - 12:00
89|د. عرين عبدالمولى ابراهيم بني سليم|مدرس|2|1|الطابق الأول|B-140|doc89@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
90|د. هبه زياد قاسم بطاينه|مدرس|2|1|الطابق الأول|B-141|doc90@jadara.edu.jo|Mon,Wed|09:00 - 10:30
91|د. ايمان محمود عبدالكريم الشرع|مدرس|2|1|الطابق الأول|B-142|doc91@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
92|د. ميس عبدالحليم عوده الزبون|مدرس|2|1|الطابق الأول|B-143|doc92@jadara.edu.jo|Mon,Wed|11:00 - 12:30
93|د. محمد فيصل محمد ابوقطيش|مدرس|4|2|الطابق الثاني|A-228|doc93@jadara.edu.jo|Sun,Tue,Thu|12:00 - 13:00
94|د. محمد باسم محمد بني هاني|مدرس|4|2|الطابق الثاني|A-229|doc94@jadara.edu.jo|Mon,Wed|13:00 - 14:30
95|د. باسل محمد ناصر الزبون|مدرس|4|2|الطابق الثاني|A-230|doc95@jadara.edu.jo|Sun,Tue,Thu|14:00 - 15:00
96|د. عماد محمد سلامه العبيني|أستاذ مساعد|5|4|الطابق الأول|D-109|doc96@jadara.edu.jo|Mon,Wed|10:30 - 12:00
97|د. محمد تيسير محمد ابو الكرسنه|مدرس|5|4|الطابق الأول|D-110|doc97@jadara.edu.jo|Sun,Tue,Thu|08:30 - 09:30
98|د. هديل عمر حسن العمري|مدرس|3|3|الطابق الثالث|C-311|doc98@jadara.edu.jo|Mon,Wed|09:00 - 10:30
99|د. احلام حسين ابراهيم مقدادي|مدرس|3|3|الطابق الثالث|C-313|doc99@jadara.edu.jo|Sun,Tue,Thu|10:00 - 11:00
100|د. احمد يوسف احمد الشوبكي|مدرس|3|3|الطابق الثالث|C-314|doc100@jadara.edu.jo|Mon,Wed|11:00 - 12:30"""


def create_and_seed_database(db_path=DB_FILENAME):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode = MEMORY;")
    cur.execute("PRAGMA foreign_keys = OFF;")
    for t in ["Users", "OfficeHours", "FacultyMembers", "Buildings", "Departments"]:
        cur.execute(f"DROP TABLE IF EXISTS {t};")
    cur.execute("PRAGMA foreign_keys = ON;")

    cur.execute("""
    CREATE TABLE Departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_name TEXT NOT NULL UNIQUE
    );""")

    cur.execute("""
    CREATE TABLE Buildings (
        building_id INTEGER PRIMARY KEY AUTOINCREMENT,
        building_code TEXT NOT NULL UNIQUE,
        building_name TEXT NOT NULL UNIQUE
    );""")

    cur.execute("""
    CREATE TABLE FacultyMembers (
        doctor_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        rank TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        building_id INTEGER NOT NULL,
        floor TEXT NOT NULL,
        office_number TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        is_deleted INTEGER DEFAULT 0,
        FOREIGN KEY (department_id) REFERENCES Departments(department_id),
        FOREIGN KEY (building_id) REFERENCES Buildings(building_id)
    );""")

    cur.execute("""
    CREATE TABLE OfficeHours (
        schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        days TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        raw_schedule TEXT NOT NULL,
        FOREIGN KEY (doctor_id) REFERENCES FacultyMembers(doctor_id) ON DELETE CASCADE
    );""")

    cur.execute("""
    CREATE TABLE Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        doctor_id INTEGER,
        FOREIGN KEY (doctor_id) REFERENCES FacultyMembers(doctor_id) ON DELETE SET NULL
    );""")

    departments = [
        "هندسة البرمجيات",
        "علم الحاسوب",
        "الروبوتات والذكاء الاصطناعي",
        "شبكات الحاسوب والأمن السيبراني",
        "علوم إنترنت الأشياء",
    ]
    for d in departments:
        cur.execute("INSERT INTO Departments (department_name) VALUES (?);", (d,))

    buildings = [
        ("B", "مبنى B — تكنولوجيا المعلومات (IT)"),
        ("A", "مبنى A — الشبكات والأمن السيبراني"),
        ("C", "مبنى C — الروبوتات والذكاء الاصطناعي"),
        ("D", "مبنى D — علوم إنترنت الأشياء"),
    ]
    for c, n in buildings:
        cur.execute("INSERT INTO Buildings (building_code, building_name) VALUES (?, ?);", (c, n))

    for line in RAW_DOCTORS.strip().splitlines():
        doc_id, name, rank, d_id, b_id, fl, off, em, days_csv, times_p = line.split("|")
        doc_id, d_id, b_id = int(doc_id), int(d_id), int(b_id)
        cur.execute(
            "INSERT INTO FacultyMembers VALUES (?,?,?,?,?,?,?,?,0);",
            (doc_id, name, rank, d_id, b_id, fl, off, em),
        )
        st, et = [x.strip() for x in times_p.split("-")]
        raw_s = f"{days_csv} ({st} - {et})"
        cur.execute(
            "INSERT INTO OfficeHours (doctor_id, days, start_time, end_time, raw_schedule) VALUES (?,?,?,?,?);",
            (doc_id, days_csv, st, et, raw_s),
        )
        uname = em.split("@")[0]
        cur.execute(
            "INSERT OR IGNORE INTO Users (username, password_hash, role, doctor_id) VALUES (?, 'doctor123', 'Faculty', ?);",
            (uname, doc_id),
        )

    cur.execute("INSERT INTO Users (username, password_hash, role, doctor_id) VALUES ('admin', 'admin123', 'Admin', NULL);")
    conn.commit()
    conn.close()
    print("✅ تم بناء قاعدة البيانات (الدكاترة 1 إلى 100 | المباني A, B, C, D | الأيام الفردية) بنجاح!")


if __name__ == "__main__":
    create_and_seed_database()