# -*- coding: utf-8 -*-
"""
السيرفر الرئيسي لتطبيق الويب (Flask) - النسخة المحدثة الشاملة (AR / EN + ترجمة أسماء الدكاترة)
مشروع: دليل الساعات المكتبية ومواقع الدكاترة الذكي
إعداد المطور الرئيسي: ثابت قيس محمد قواسمة (202220020)
"""

import os
import re
import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template_string, jsonify
import init_db

app = Flask(__name__)
app.secret_key = "jadara_smart_directory_secret_key_2026"
DB_PATH = "database.db"

ALL_DAYS = [
    ("Sat", "السبت", "Saturday"),
    ("Sun", "الأحد", "Sunday"),
    ("Mon", "الإثنين", "Monday"),
    ("Tue", "الثلاثاء", "Tuesday"),
    ("Wed", "الأربعاء", "Wednesday"),
    ("Thu", "الخميس", "Thursday"),
]

DEPT_EN = {
    "هندسة البرمجيات": "Software Engineering",
    "علم الحاسوب": "Computer Science",
    "الروبوتات والذكاء الاصطناعي": "Robotics & Artificial Intelligence",
    "شبكات الحاسوب والأمن السيبراني": "Computer Networks & Cybersecurity",
    "علوم إنترنت الأشياء": "Internet of Things (IoT)",
}

BLDG_EN = {
    "مبنى B — تكنولوجيا المعلومات (IT)": "Building B — Information Technology (IT)",
    "مبنى A — الشبكات والأمن السيبراني": "Building A — Networks & Cybersecurity",
    "مبنى C — الروبوتات والذكاء الاصطناعي": "Building C — Robotics & AI",
    "مبنى D — علوم إنترنت الأشياء": "Building D — Internet of Things (IoT)",
}

RANK_EN = {
    "أستاذ دكتور": "Full Professor",
    "أستاذ": "Professor",
    "أستاذ مشارك": "Associate Professor",
    "أستاذ مساعد": "Assistant Professor",
    "مدرس": "Instructor",
    "محاضر": "Lecturer",
}

FLOOR_EN = {
    "الطابق الأرضي": "Ground Floor",
    "الطابق الأول": "First Floor",
    "الطابق الثاني": "Second Floor",
    "الطابق الثالث": "Third Floor",
}

WORD_EN = {
    "أ.د.": "Prof. Dr.", "د.": "Dr.",
    "أحمد": "Ahmad", "احمد": "Ahmad", "إبراهيم": "Ibrahim", "ابراهيم": "Ibrahim", "خليل": "Khalil",
    "رانيا": "Rania", "محمود": "Mahmoud", "القضاة": "Al-Qudah",
    "طارق": "Tariq", "زياد": "Ziad", "العبدالله": "Al-Abdallah",
    "هبة": "Hiba", "هبه": "Hiba", "سامي": "Sami", "الخطيب": "Al-Khatib",
    "حسام": "Hussam", "عمر": "Omar", "التميمي": "Al-Tamimi",
    "يزن": "Yazan", "مصطفى": "Mustafa", "العزام": "Al-Azzam",
    "منى": "Muna", "فؤاد": "Fouad", "الروسان": "Al-Rousan",
    "حمزة": "Hamza", "حمزه": "Hamza", "علي": "Ali", "الجراح": "Al-Jarrah",
    "ليلى": "Laila", "حسن": "Hassan", "بني": "Bani", "هاني": "Hani",
    "فراس": "Firas", "ناصر": "Nasser", "الزعبي": "Al-Zoubi",
    "دانية": "Dania", "عبد": "Abd", "الله": "Allah", "عبدالله": "Abdullah", "الشبول": "Al-Shboul",
    "خالد": "Khaled", "وليد": "Walid", "الطعاني": "Al-Taani",
    "سميرة": "Samira", "عدنان": "Adnan", "العمري": "Al-Omari",
    "مجد": "Majd", "توفيق": "Tawfiq", "مقابلة": "Muqableh",
    "بشير": "Bashir", "غرايبة": "Gharaibeh", "غرايبه": "Gharaibeh",
    "ولاء": "Walaa", "البطاينة": "Al-Bataineh", "بطاينه": "Bataineh",
    "بشار": "Bashar", "كمال": "Kamal", "الهنداوي": "Al-Hindawi",
    "نادين": "Nadine", "سمير": "Samir", "عبيدات": "Obeidat",
    "معتز": "Mutaz", "نضال": "Nidal", "الخصاونة": "Al-Khasawneh", "الخصاونه": "Al-Khasawneh",
    "إيناس": "Enas", "ايناس": "Enas", "مريان": "Maryan",
    "بلال": "Bilal", "محمد": "Mohammad", "زقيبه": "Zaqaibeh",
    "نذير": "Nathir", "خليف": "Khlaif",
    "زاهي": "Zahi", "ابو": "Abu", "سرحان": "Sarhan",
    "بشرى": "Bushra", "طلال": "Talal", "غزاله": "Ghazaleh",
    "عبدالكريم": "Abdelkarim", "المهيرات": "Al-Mheirat",
    "باسم": "Basem", "يوسف": "Yousef", "مفضي": "Mufdi", "الزغول": "Al-Zughoul",
    "حسين": "Hussein", "المزاري": "Al-Mazari",
    "مرح": "Marah", "يحيى": "Yahya", "عبدالحافظ": "Abdelhafiz", "الصرايرة": "Al-Sarayreh",
    "رياض": "Riyad", "فرحان": "Farhan", "الشلبي": "Al-Shalabi",
    "صبحي": "Subhi", "البطاح": "Al-Batah",
    "صالح": "Saleh", "خطاب": "Khattab",
    "اروى": "Arwa", "ظبيان": "Dabyan",
    "أسعد": "Asaad", "اسعد": "Asaad", "الناصر": "Al-Nasser",
    "جازي": "Jazi", "البواعنه": "Al-Bawaneh",
    "ايمن": "Ayman", "الرب": "Al-Rub",
    "أيات": "Ayat", "أمين": "Amin",
    "فيصل": "Faisal", "رواشدة": "Rawashdeh",
    "ذيب": "Theeb", "الرفاعي": "Al-Rifai",
    "هايل": "Hayel", "قواسمه": "Qawasmeh",
    "الصمادي": "Al-Smadi", "سفيان": "Sufyan", "قسايمه": "Qasaimeh",
    "واصف": "Wasef", "مراشدة": "Marashdeh",
    "نشأت": "Nashaat", "تحسين": "Tahseen", "طلعت": "Talaat",
    "عبير": "Abeer", "ضرار": "Dirar", "ملكاوي": "Malkawi",
    "احلام": "Ahlam", "شبلي": "Shibli", "جوارنه": "Jawarneh",
    "خليفه": "Khalifeh", "اريج": "Areej", "حمد": "Hamad", "الحمود": "Al-Hmoud",
    "اياد": "Eyad", "عودات": "Odat", "العودات": "Al-Odat",
    "مشهور": "Mashhour", "معن": "Maan", "عايش": "Ayesh",
    "سارة": "Sara", "سليمان": "Suleiman", "القرعان": "Al-Quran",
    "تيسير": "Tayseer", "اكريم": "Kareem", "الرشدان": "Al-Rashdan",
    "العمر": "Al-Omar", "الواحد": "Al-Wahed",
    "مروان": "Marwan", "عتوم": "Atoom",
    "لؤي": "Louay", "نمراوي": "Namrawi",
    "تامر": "Tamer", "عبدالمجيد": "Abdelmajeed", "عامر": "Amer",
    "حنا": "Hanna", "سليم": "Salim", "زوايده": "Zawaideh",
    "عوض": "Awad", "السخني": "Al-Sukhni",
    "موسى": "Mousa", "كنعان": "Kanaan", "العجلوني": "Al-Ajlouni",
    "معاذ": "Moath", "نجيب": "Najeeb",
    "منصور": "Mansour", "فواز": "Fawaz",
    "معتصم": "Motasem", "شبيب": "Shabeeb",
    "ناجي": "Naji", "لطفي": "Lutfi", "الزريقي": "Al-Zureiqi",
    "عمران": "Omran", "ارشيد": "Arsheed", "الطه": "Al-Taha", "العقيلي": "Al-Aqeeli",
    "مطلق": "Mutlaq", "عيسى": "Issa",
    "مراد": "Murad", "بشابشه": "Bashabsheh",
    "عبابنه": "Ababneh", "سوالمه": "Sawalmeh",
    "قاسم": "Qasem", "مومني": "Momani",
    "ندى": "Nada", "جودت": "Jawdat",
    "نوح": "Nouh", "هيلات": "Hailat",
    "مصعب": "Musab", "الفهيد": "Al-Fuhaid",
    "مفلح": "Mufleh", "الذيابات": "Al-Thiyabat",
    "ايهاب": "Ehab", "عبدالرحمن": "Abdelrahman", "سعيد": "Saeed", "مشعل": "Mashal",
    "ياسين": "Yassin", "رند": "Rand", "عبدالقادر": "Abdelqader", "الحايك": "Al-Hayek",
    "عرين": "Areen", "عبدالمولى": "Abdelmawla", "ايمان": "Eman", "الشرع": "Al-Shara",
    "ميس": "Mays", "عبدالحليم": "Abdelhalim", "عوده": "Odeh", "الزبون": "Al-Zboun",
    "ابوقطيش": "Abu-Qtaish", "باسل": "Basel",
    "عماد": "Emad", "سلامه": "Salameh", "العبيني": "Al-Obeini",
    "الكرسنه": "Al-Karsaneh", "هديل": "Hadeel",
    "مقدادي": "Miqdadi", "الشوبكي": "Al-Shobaki",
    "ثابت": "Thabet", "قيس": "Qais", "قواسمة": "Qawasmeh",
    "أوس": "Aws", "ماهر": "Maher", "عللوه": "Alalweh",
    "يزيد": "Yazeed", "معاوية": "Muawiyah", "شلول": "Shaloul",
}

CHAR_MAP = {
    "ا": "a", "أ": "a", "إ": "i", "آ": "a", "ب": "b", "ت": "t", "ث": "th",
    "ج": "j", "ح": "h", "خ": "kh", "د": "d", "ذ": "th", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "ع": "a",
    "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "ة": "eh", "و": "w", "ؤ": "o", "ي": "y", "ى": "a", "ئ": "e", "ء": "",
}


def to_english_name(ar_name):
    if not ar_name:
        return ""
    out = []
    for w in ar_name.strip().split():
        if w in WORD_EN:
            out.append(WORD_EN[w])
        else:
            if w.startswith("ال") and len(w) > 2:
                rest = "".join(CHAR_MAP.get(c, c) for c in w[2:]).capitalize()
                out.append(f"Al-{rest}")
            else:
                out.append("".join(CHAR_MAP.get(c, c) for c in w).capitalize())
    return " ".join(out)


def tr_name(ar_name):
    if get_lang() == "en":
        return to_english_name(ar_name)
    return ar_name


def get_lang():
    return session.get("lang", "ar")


def tr_val(val, mapping):
    if get_lang() == "en":
        return mapping.get(val, val)
    return val


def format_days_badge(days_csv):
    if not days_csv:
        return "—"
    lang = get_lang()
    day_map = {code: (ar if lang == "ar" else en) for code, ar, en in ALL_DAYS}
    parts = [d.strip() for d in days_csv.split(",") if d.strip()]
    return " ، ".join(day_map.get(p, p) for p in parts) if lang == "ar" else ", ".join(day_map.get(p, p) for p in parts)


def normalize_ar(text):
    if not text:
        return ""
    t = text.strip().lower()
    t = re.sub(r"[أإآ]", "ا", t)
    t = re.sub(r"ة", "ه", t)
    t = re.sub(r"ى", "ي", t)
    t = re.sub(r"^(ال|د\.|أ\.د\.|دكتور|الدكتور|dr\.|prof\.)\s*", "", t)
    return t


def ensure_db_ready():
    needs_seed = not os.path.exists(DB_PATH)
    if not needs_seed:
        try:
            conn = sqlite3.connect(DB_PATH)
            cnt = conn.execute("SELECT COUNT(*) FROM FacultyMembers").fetchone()[0]
            min_id = conn.execute("SELECT MIN(doctor_id) FROM FacultyMembers").fetchone()[0]
            cols = [r[1] for r in conn.execute("PRAGMA table_info(FacultyMembers)").fetchall()]
            conn.close()
            if cnt < 100 or min_id != 1 or "is_deleted" not in cols:
                needs_seed = True
        except Exception:
            needs_seed = True
    if needs_seed:
        init_db.create_and_seed_database(DB_PATH)


def get_db():
    ensure_db_ready()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = MEMORY;")
    return conn


BASE_STYLE = """
<style>
  :root { --primary:#0f2942; --accent:#0284c7; --bg:#f1f5f9; --card:#ffffff; --text:#1e293b; --muted:#64748b; --border:#cbd5e1; }
  * { box-sizing:border-box; margin:0; padding:0; font-family:'Segoe UI',Tahoma,system-ui,sans-serif; }
  body { background:var(--bg); color:var(--text); direction:{{ 'rtl' if lang=='ar' else 'ltr' }}; text-align:{{ 'right' if lang=='ar' else 'left' }}; padding-bottom:80px; }
  header { background:linear-gradient(135deg,#0f2942,#1e3a8a); color:#fff; padding:1rem 2rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; box-shadow:0 4px 12px rgba(0,0,0,0.12); }
  header a.brand { color:#fff; text-decoration:none; font-size:1.25rem; font-weight:800; }
  .nav-links { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
  .nav-links a { color:#fff; text-decoration:none; padding:7px 13px; border-radius:8px; background:rgba(255,255,255,0.14); font-size:0.86rem; font-weight:600; }
  .nav-links a:hover { background:rgba(255,255,255,0.26); }
  .lang-btn { background:#f59e0b !important; color:#0f172a !important; font-weight:800 !important; }
  .container { max-width:1340px; margin:1.3rem auto; padding:0 1rem; }
  .filter-box { background:#fff; padding:1.1rem; border-radius:12px; border:1px solid var(--border); margin-bottom:1.2rem; }
  .search-input { width:100%; padding:11px 14px; border:1.5px solid var(--border); border-radius:8px; font-size:0.95rem; margin-bottom:12px; }
  .multi-filters { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; }
  .filter-group { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; }
  .filter-group h4 { font-size:0.84rem; color:var(--primary); margin-bottom:7px; border-bottom:1px solid #e2e8f0; padding-bottom:4px; }
  .chk-list { display:flex; flex-wrap:wrap; gap:6px; max-height:115px; overflow-y:auto; }
  .chk-pill { display:inline-flex; align-items:center; gap:5px; background:#fff; border:1px solid #cbd5e1; padding:4px 9px; border-radius:999px; font-size:0.78rem; cursor:pointer; user-select:none; }
  .chk-pill input { accent-color:var(--accent); cursor:pointer; }
  .btn { padding:9px 16px; border:none; border-radius:8px; cursor:pointer; font-weight:700; font-size:0.86rem; text-decoration:none; display:inline-block; text-align:center; }
  .btn-primary { background:var(--accent); color:#fff; }
  .btn-dark { background:var(--primary); color:#fff; }
  .btn-danger { background:#dc2626; color:#fff; }
  .btn-success { background:#16a34a; color:#fff; }
  .stats-bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; font-weight:700; color:var(--primary); flex-wrap:wrap; gap:8px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(310px,1fr)); gap:1rem; }
  .card { background:#fff; border-radius:12px; padding:1.1rem; border:1px solid var(--border); display:flex; flex-direction:column; justify-content:space-between; transition:transform 0.15s; }
  .card:hover { transform:translateY(-2px); box-shadow:0 8px 18px rgba(0,0,0,0.07); }
  .badge { display:inline-block; padding:3px 9px; border-radius:999px; font-size:0.75rem; font-weight:700; background:#e0f2fe; color:#0369a1; }
  .badge-bldg { background:#fef3c7; color:#92400e; }
  .meta { font-size:0.84rem; color:#334155; margin:4px 0; }
  .hours-pill { margin-top:8px; background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; padding:7px 10px; border-radius:8px; font-size:0.81rem; font-weight:600; }
  .alert { padding:11px 15px; border-radius:8px; margin-bottom:1rem; font-weight:700; background:#dcfce7; color:#166534; border:1px solid #86efac; }
  table { width:100%; border-collapse:collapse; background:#fff; border-radius:10px; overflow:hidden; font-size:0.82rem; }
  th, td { padding:8px 9px; border-bottom:1px solid var(--border); text-align:{{ 'right' if lang=='ar' else 'left' }}; }
  th { background:var(--primary); color:#fff; font-weight:700; white-space:nowrap; }
  tr.deleted-row { background:#fee2e2 !important; opacity:0.92; }
  .del-badge { background:#dc2626; color:#fff; padding:3px 8px; border-radius:6px; font-size:0.74rem; font-weight:800; display:inline-block; }
  input[type=text], input[type=email], input[type=password], select { padding:6px 8px; border:1px solid var(--border); border-radius:6px; font-size:0.81rem; }
  .chat-fab { position:fixed; bottom:20px; {{ 'left:20px;' if lang=='ar' else 'right:20px;' }} background:linear-gradient(135deg,#0284c7,#1e3a8a); color:#fff; border:none; border-radius:999px; padding:12px 20px; font-size:0.92rem; font-weight:800; cursor:pointer; box-shadow:0 8px 22px rgba(2,132,199,0.4); z-index:999; }
  .chat-win { display:none; position:fixed; bottom:76px; {{ 'left:20px;' if lang=='ar' else 'right:20px;' }} width:360px; max-width:92vw; background:#fff; border-radius:14px; border:1px solid var(--border); box-shadow:0 14px 34px rgba(0,0,0,0.22); z-index:1000; overflow:hidden; }
  .chat-head { background:var(--primary); color:#fff; padding:11px 14px; font-weight:800; display:flex; justify-content:space-between; align-items:center; }
  .chat-body { height:270px; overflow-y:auto; padding:11px; background:#f8fafc; display:flex; flex-direction:column; gap:8px; font-size:0.84rem; }
  .msg-bot { background:#e0f2fe; color:#0f172a; padding:8px 11px; border-radius:10px; align-self:flex-start; max-width:90%; line-height:1.45; }
  .msg-user { background:var(--accent); color:#fff; padding:8px 11px; border-radius:10px; align-self:flex-end; max-width:85%; }
  .chat-foot { display:flex; border-top:1px solid var(--border); background:#fff; }
  .chat-foot input { flex:1; border:none; padding:10px; outline:none; font-size:0.85rem; }
  .chat-foot button { background:var(--accent); color:#fff; border:none; padding:0 15px; font-weight:800; cursor:pointer; }
</style>
"""

CHATBOT_WIDGET = """
<button class="chat-fab" onclick="toggleChat()">🤖 {{ 'المساعد الذكي' if lang=='ar' else 'Smart Assistant' }}</button>
<div class="chat-win" id="chatWin">
  <div class="chat-head">
    <span>🤖 {{ 'مساعد الساعات المكتبية الذكي' if lang=='ar' else 'Smart Office Hours Bot' }}</span>
    <span style="cursor:pointer;" onclick="toggleChat()">✕</span>
  </div>
  <div class="chat-body" id="chatBody">
    <div class="msg-bot">
      {{ 'مرحباً! اكتب أي اسم من اسم الدكتور (الأول أو الثاني أو الثالث أو العائلة مثل: أحمد، معن، مروان، الزعبي، بلال) أو رقم المكتب أو المبنى (A, B, C, D) وسأعطيك التفاصيل فوراً.' if lang=='ar' else 'Hello! Type any part of a doctor name (e.g., Ahmad, Maan, Marwan, Zoubi, Bilal), office number, or building (A, B, C, D) to get instant details.' }}
    </div>
  </div>
  <div class="chat-foot">
    <input type="text" id="chatInput" placeholder="{{ 'اكتب اسم الدكتور أو المكتب...' if lang=='ar' else 'Type doctor name or office...' }}" onkeydown="if(event.key==='Enter')sendChat()">
    <button onclick="sendChat()">{{ 'إرسال' if lang=='ar' else 'Send' }}</button>
  </div>
</div>
<script>
function toggleChat(){
  const w = document.getElementById('chatWin');
  w.style.display = (w.style.display === 'block') ? 'none' : 'block';
}
async function sendChat(){
  const inp = document.getElementById('chatInput');
  const q = inp.value.trim();
  if(!q) return;
  const body = document.getElementById('chatBody');
  body.innerHTML += `<div class="msg-user">${q}</div>`;
  inp.value = '';
  body.scrollTop = body.scrollHeight;
  const res = await fetch('/api/chat', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({q})
  });
  const data = await res.json();
  body.innerHTML += `<div class="msg-bot">${data.reply}</div>`;
  body.scrollTop = body.scrollHeight;
}
</script>
"""


@app.route("/lang/<code>")
def switch_lang(code):
    session["lang"] = "en" if code == "en" else "ar"
    return redirect(request.referrer or url_for("home"))


@app.route("/api/chat", methods=["POST"])
def api_chat():
    lang = get_lang()
    data = request.get_json(silent=True) or {}
    q_raw = (data.get("q") or "").strip()
    if not q_raw:
        return jsonify({"reply": "يرجى كتابة سؤالك." if lang == "ar" else "Please enter a query."})

    conn = get_db()
    docs = conn.execute("""
        SELECT f.*, d.department_name, b.building_code, b.building_name,
               o.days, o.start_time, o.end_time
        FROM FacultyMembers f
        JOIN Departments d ON f.department_id = d.department_id
        JOIN Buildings b ON f.building_id = b.building_id
        LEFT JOIN OfficeHours o ON f.doctor_id = o.doctor_id
        WHERE f.is_deleted = 0
        ORDER BY f.doctor_id
    """).fetchall()
    conn.close()

    stop_words = {"وين", "مكتب", "ساعات", "دكتور", "الدكتور", "متى", "قسم", "مبنى", "في", "من", "عن", "اعطني", "بدي", "اسم", "where", "is", "office", "dr", "doctor", "prof", "hours"}
    raw_tokens = [t for t in re.split(r"\s+", q_raw) if t and t.lower().strip(".") not in stop_words]
    if not raw_tokens:
        raw_tokens = [q_raw]
    norm_tokens = [normalize_ar(t) for t in raw_tokens if normalize_ar(t)]

    matches = []
    for d in docs:
        name_norm = normalize_ar(d["name"])
        name_en_low = to_english_name(d["name"]).lower()
        name_parts = name_norm.split() + [p.strip(".-") for p in re.split(r"[\s\-]+", name_en_low) if p]
        dept_norm = normalize_ar(d["department_name"]) + " " + DEPT_EN.get(d["department_name"], "").lower()
        off_low = (d["office_number"] or "").lower()
        bldg_low = (d["building_code"] or "").lower()

        matched_all = True
        for nt in norm_tokens:
            part_hit = (
                any(nt in p or p in nt for p in name_parts if len(p) >= 2)
                or (nt in name_norm)
                or (nt in name_en_low)
                or (nt in dept_norm)
                or (nt == bldg_low)
                or (nt in off_low)
            )
            if not part_hit:
                matched_all = False
                break
        if matched_all:
            matches.append(d)

    if not matches:
        return jsonify({
            "reply": ("لم أجد دكتوراً مطابقاً. جرب كتابة الاسم الأول أو الثاني أو اسم العائلة فقط (مثل: أحمد، معن، الزعبي، بلال)."
                      if lang == "ar" else
                      "No matching doctor found. Try typing just the first, second, or last name (e.g., Ahmad, Maan, Zoubi, Bilal).")
        })

    lines = []
    for m in matches[:6]:
        days_txt = format_days_badge(m["days"])
        disp_name = tr_name(m["name"])
        lines.append(
            f"• <b>#{m['doctor_id']} {disp_name}</b> ({tr_val(m['department_name'], DEPT_EN)})<br>"
            f"📍 {tr_val(m['building_name'], BLDG_EN)} | {tr_val(m['floor'], FLOOR_EN)} | <b>{m['office_number']}</b><br>"
            f"🕒 {days_txt} ({m['start_time']} - {m['end_time']}) — <a href='/doctor/{m['doctor_id']}'>{'التفاصيل' if lang=='ar' else 'Details'}</a>"
        )
    more = ""
    if len(matches) > 6:
        more = f"<br><small>+ {len(matches)-6} {'نتائج أخرى' if lang=='ar' else 'more results'}</small>"
    return jsonify({"reply": "<br><br>".join(lines) + more})


@app.route("/")
def home():
    lang = get_lang()
    conn = get_db()
    q = request.args.get("q", "").strip()
    sel_depts = [x for x in request.args.getlist("dept") if x]
    sel_bldgs = [x for x in request.args.getlist("bldg") if x]
    sel_floors = [x for x in request.args.getlist("floor") if x]
    sel_days = [x for x in request.args.getlist("day") if x]

    sql = """
        SELECT f.doctor_id, f.name, f.rank, f.floor, f.office_number, f.email,
               d.department_id, d.department_name,
               b.building_id, b.building_code, b.building_name,
               o.days, o.start_time, o.end_time
        FROM FacultyMembers f
        JOIN Departments d ON f.department_id = d.department_id
        JOIN Buildings b ON f.building_id = b.building_id
        LEFT JOIN OfficeHours o ON f.doctor_id = o.doctor_id
        WHERE f.is_deleted = 0
    """
    params = []
    if sel_depts:
        placeholders = ",".join("?" for _ in sel_depts)
        sql += f" AND f.department_id IN ({placeholders})"
        params.extend(sel_depts)
    if sel_bldgs:
        placeholders = ",".join("?" for _ in sel_bldgs)
        sql += f" AND b.building_code IN ({placeholders})"
        params.extend(sel_bldgs)
    if sel_floors:
        placeholders = ",".join("?" for _ in sel_floors)
        sql += f" AND f.floor IN ({placeholders})"
        params.extend(sel_floors)
    if sel_days:
        day_conds = " OR ".join("o.days LIKE ?" for _ in sel_days)
        sql += f" AND ({day_conds})"
        params.extend([f"%{dy}%" for dy in sel_days])

    sql += " ORDER BY f.doctor_id ASC"
    all_rows = conn.execute(sql, params).fetchall()

    # Bilingual search filtering (matches Arabic name, English name, office, email, or department)
    if q:
        q_low = q.lower()
        q_norm = normalize_ar(q)
        doctors = []
        for r in all_rows:
            en_name = to_english_name(r["name"]).lower()
            ar_norm = normalize_ar(r["name"])
            if (
                q_low in r["name"].lower()
                or q_norm in ar_norm
                or q_low in en_name
                or q_low in (r["office_number"] or "").lower()
                or q_low in (r["email"] or "").lower()
                or q_low in (r["department_name"] or "").lower()
                or q_low in DEPT_EN.get(r["department_name"], "").lower()
                or q_low == (r["building_code"] or "").lower()
            ):
                doctors.append(r)
    else:
        doctors = all_rows

    departments = conn.execute("SELECT * FROM Departments ORDER BY department_id").fetchall()
    buildings = conn.execute("SELECT * FROM Buildings ORDER BY building_code").fetchall()
    total_active = conn.execute("SELECT COUNT(*) FROM FacultyMembers WHERE is_deleted = 0").fetchone()[0]
    conn.close()

    floors_list = ["الطابق الأرضي", "الطابق الأول", "الطابق الثاني", "الطابق الثالث"]

    html = """
    <!DOCTYPE html>
    <html lang="{{ lang }}">
    <head><meta charset="UTF-8"><title>{{ 'دليل الساعات المكتبية ومواقع الدكاترة الذكي' if lang=='ar' else 'Smart Faculty Office Hours Directory' }}</title>""" + BASE_STYLE + """</head>
    <body>
      <header>
        <a class="brand" href="/">🎓 {{ 'دليل الساعات المكتبية ومواقع الدكاترة الذكي' if lang=='ar' else 'Smart Faculty Office Hours Directory' }}</a>
        <div class="nav-links">
          <a class="lang-btn" href="/lang/{{ 'en' if lang=='ar' else 'ar' }}">🌐 {{ 'English' if lang=='ar' else 'العربية' }}</a>
          {% if session.get('user_id') %}
            <a href="/dashboard">⚙️ {{ 'لوحة التحكم' if lang=='ar' else 'Dashboard' }} ({{ session.get('username') }})</a>
            <a href="/logout">🚪 {{ 'خروج' if lang=='ar' else 'Logout' }}</a>
          {% else %}
            <a href="/login">🔐 {{ 'دخول الدكاترة / الإدارة' if lang=='ar' else 'Faculty / Admin Login' }}</a>
          {% endif %}
        </div>
      </header>

      <div class="container">
        <form class="filter-box" method="GET" action="/">
          <input class="search-input" type="text" name="q" value="{{ q }}" placeholder="{{ '🔍 ابحث بأي جزء من اسم الدكتور، رقم المكتب (مثل B-204)، أو البريد...' if lang=='ar' else '🔍 Search by doctor name (e.g. Ahmad, Maan, Zoubi), office (B-204), or email...' }}">
          <div class="multi-filters">
            <div class="filter-group">
              <h4>📚 {{ 'الأقسام الأكاديمية (يمكن اختيار أكثر من قسم)' if lang=='ar' else 'Departments (Multi-Select)' }}</h4>
              <div class="chk-list">
                {% for d in departments %}
                  <label class="chk-pill">
                    <input type="checkbox" name="dept" value="{{ d.department_id }}" {% if (d.department_id|string) in sel_depts %}checked{% endif %}>
                    <span>{{ tr_val(d.department_name, DEPT_EN) }}</span>
                  </label>
                {% endfor %}
              </div>
            </div>

            <div class="filter-group">
              <h4>🏢 {{ 'المباني الجامعية (A, B, C, D - متعدد)' if lang=='ar' else 'Buildings (A, B, C, D - Multi-Select)' }}</h4>
              <div class="chk-list">
                {% for b in buildings %}
                  <label class="chk-pill">
                    <input type="checkbox" name="bldg" value="{{ b.building_code }}" {% if b.building_code in sel_bldgs %}checked{% endif %}>
                    <span>{{ tr_val(b.building_name, BLDG_EN) }}</span>
                  </label>
                {% endfor %}
              </div>
            </div>

            <div class="filter-group">
              <h4>🪜 {{ 'الطوابق (يمكن اختيار أكثر من طابق)' if lang=='ar' else 'Floors (Multi-Select)' }}</h4>
              <div class="chk-list">
                {% for fl in floors_list %}
                  <label class="chk-pill">
                    <input type="checkbox" name="floor" value="{{ fl }}" {% if fl in sel_floors %}checked{% endif %}>
                    <span>{{ tr_val(fl, FLOOR_EN) }}</span>
                  </label>
                {% endfor %}
              </div>
            </div>

            <div class="filter-group">
              <h4>📅 {{ 'أيام الساعات المكتبية (اختر يوماً أو أكثر)' if lang=='ar' else 'Office Hours Days (Multi-Select)' }}</h4>
              <div class="chk-list">
                {% for code, ar_d, en_d in ALL_DAYS %}
                  <label class="chk-pill">
                    <input type="checkbox" name="day" value="{{ code }}" {% if code in sel_days %}checked{% endif %}>
                    <span>{{ ar_d if lang=='ar' else en_d }}</span>
                  </label>
                {% endfor %}
              </div>
            </div>
          </div>

          <div style="margin-top:12px; display:flex; gap:8px;">
            <button class="btn btn-primary" type="submit">🔍 {{ 'تطبيق الفلترة المتعددة والبحث' if lang=='ar' else 'Apply Multi-Filters & Search' }}</button>
            <a class="btn btn-dark" href="/">{{ 'إعادة ضبط الكل' if lang=='ar' else 'Reset All' }}</a>
          </div>
        </form>

        <div class="stats-bar">
          <span>{{ 'عدد النتائج المعروضة:' if lang=='ar' else 'Showing:' }} {{ doctors|length }} {{ 'من أصل' if lang=='ar' else 'of' }} {{ total_active }} {{ 'دكتور (مرقمين من 1 إلى 100)' if lang=='ar' else 'doctors (#1 to #100)' }}</span>
        </div>

        <div class="grid">
          {% for doc in doctors %}
            <div class="card">
              <div>
                <div style="display:flex; justify-content:space-between; gap:6px; margin-bottom:6px; flex-wrap:wrap;">
                  <span class="badge">{{ tr_val(doc.department_name, DEPT_EN) }}</span>
                  <span class="badge badge-bldg">{{ doc.building_code }} | #{{ doc.doctor_id }}</span>
                </div>
                <h3 style="margin-bottom:3px; color:#0f2942; font-size:1.03rem;">{{ tr_name(doc.name) }}</h3>
                <div style="font-size:0.78rem; color:#64748b; margin-bottom:8px;">{{ tr_val(doc.rank, RANK_EN) }}</div>
                <div class="meta">📍 <b>{{ 'المبنى:' if lang=='ar' else 'Building:' }}</b> {{ tr_val(doc.building_name, BLDG_EN) }}</div>
                <div class="meta">🚪 <b>{{ 'الطابق والمكتب:' if lang=='ar' else 'Floor & Office:' }}</b> {{ tr_val(doc.floor, FLOOR_EN) }} — <b>{{ doc.office_number }}</b></div>
                <div class="meta">✉️ {{ doc.email }}</div>
                <div class="hours-pill">🕒 {{ format_days_badge(doc.days) }}<br>⏰ {{ doc.start_time }} - {{ doc.end_time }}</div>
              </div>
              <div style="margin-top:10px;">
                <a class="btn btn-dark" style="width:100%;" href="/doctor/{{ doc.doctor_id }}">{{ 'عرض التفاصيل والجدول' if lang=='ar' else 'View Profile & Schedule' }} ←</a>
              </div>
            </div>
          {% endfor %}
        </div>
      </div>
      """ + CHATBOT_WIDGET + """
    </body></html>
    """
    return render_template_string(
        html, lang=lang, doctors=doctors, departments=departments, buildings=buildings,
        floors_list=floors_list, ALL_DAYS=ALL_DAYS, q=q, sel_depts=sel_depts,
        sel_bldgs=sel_bldgs, sel_floors=sel_floors, sel_days=sel_days,
        total_active=total_active, tr_val=tr_val, tr_name=tr_name, DEPT_EN=DEPT_EN,
        BLDG_EN=BLDG_EN, RANK_EN=RANK_EN, FLOOR_EN=FLOOR_EN, format_days_badge=format_days_badge
    )


@app.route("/doctor/<int:doc_id>")
def doctor_detail(doc_id):
    lang = get_lang()
    conn = get_db()
    doc = conn.execute("""
        SELECT f.*, d.department_name, b.building_code, b.building_name,
               o.days, o.start_time, o.end_time
        FROM FacultyMembers f
        JOIN Departments d ON f.department_id = d.department_id
        JOIN Buildings b ON f.building_id = b.building_id
        LEFT JOIN OfficeHours o ON f.doctor_id = o.doctor_id
        WHERE f.doctor_id = ? AND f.is_deleted = 0
    """, (doc_id,)).fetchone()
    conn.close()
    if not doc:
        return redirect(url_for("home"))

    html = """
    <!DOCTYPE html>
    <html lang="{{ lang }}">
    <head><meta charset="UTF-8"><title>{{ tr_name(doc.name) }}</title>""" + BASE_STYLE + """</head>
    <body>
      <header>
        <a class="brand" href="/">🎓 {{ 'دليل الساعات المكتبية ومواقع الدكاترة الذكي' if lang=='ar' else 'Smart Faculty Office Hours Directory' }}</a>
        <div class="nav-links">
          <a class="lang-btn" href="/lang/{{ 'en' if lang=='ar' else 'ar' }}">🌐 {{ 'English' if lang=='ar' else 'العربية' }}</a>
          <a href="/">🏠 {{ 'العودة للدليل' if lang=='ar' else 'Back to Directory' }}</a>
        </div>
      </header>
      <div class="container" style="max-width:780px;">
        <div class="card" style="padding:1.8rem;">
          <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <span class="badge">{{ tr_val(doc.department_name, DEPT_EN) }}</span>
            <span class="badge badge-bldg">#{{ doc.doctor_id }} | {{ doc.building_code }}</span>
          </div>
          <h2 style="color:#0f2942; margin-bottom:4px;">{{ tr_name(doc.name) }}</h2>
          <p style="color:#64748b; margin-bottom:16px;">{{ tr_val(doc.rank, RANK_EN) }}</p>
          <table>
            <tr><th>{{ 'المبنى الجامعي' if lang=='ar' else 'Building' }}</th><td>{{ tr_val(doc.building_name, BLDG_EN) }}</td></tr>
            <tr><th>{{ 'الطابق' if lang=='ar' else 'Floor' }}</th><td>{{ tr_val(doc.floor, FLOOR_EN) }}</td></tr>
            <tr><th>{{ 'رقم المكتب' if lang=='ar' else 'Office Number' }}</th><td><b>{{ doc.office_number }}</b></td></tr>
            <tr><th>{{ 'البريد الإلكتروني' if lang=='ar' else 'Email' }}</th><td>{{ doc.email }}</td></tr>
            <tr><th>{{ 'أيام الساعات المكتبية' if lang=='ar' else 'Office Hours Days' }}</th><td><b>{{ format_days_badge(doc.days) }}</b></td></tr>
            <tr><th>{{ 'التوقيت' if lang=='ar' else 'Time' }}</th><td><b>{{ doc.start_time }} - {{ doc.end_time }}</b></td></tr>
          </table>
        </div>
      </div>
    </body></html>
    """
    return render_template_string(
        html, lang=lang, doc=doc, tr_val=tr_val, tr_name=tr_name, DEPT_EN=DEPT_EN,
        BLDG_EN=BLDG_EN, RANK_EN=RANK_EN, FLOOR_EN=FLOOR_EN,
        format_days_badge=format_days_badge
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    lang = get_lang()
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM Users WHERE LOWER(username)=LOWER(?) AND password_hash=?",
            (username, password)
        ).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["doctor_id"] = user["doctor_id"]
            return redirect(url_for("dashboard"))
        error = "اسم المستخدم أو كلمة المرور غير صحيحة" if lang == "ar" else "Invalid username or password"

    html = """
    <!DOCTYPE html>
    <html lang="{{ lang }}">
    <head><meta charset="UTF-8"><title>{{ 'تسجيل الدخول' if lang=='ar' else 'Login' }}</title>""" + BASE_STYLE + """</head>
    <body>
      <header>
        <a class="brand" href="/">🎓 {{ 'دليل الساعات المكتبية ومواقع الدكاترة الذكي' if lang=='ar' else 'Smart Faculty Office Hours Directory' }}</a>
        <div class="nav-links">
          <a class="lang-btn" href="/lang/{{ 'en' if lang=='ar' else 'ar' }}">🌐 {{ 'English' if lang=='ar' else 'العربية' }}</a>
          <a href="/">🏠 {{ 'الرئيسية' if lang=='ar' else 'Home' }}</a>
        </div>
      </header>
      <div class="container" style="max-width:440px; margin-top:3.5rem;">
        <div class="card" style="padding:2rem;">
          <h2 style="margin-bottom:18px; color:#0f2942; text-align:center;">🔐 {{ 'تسجيل الدخول' if lang=='ar' else 'Sign In' }}</h2>
          {% if error %}
            <div style="background:#fee2e2; color:#991b1b; padding:10px; border-radius:8px; margin-bottom:12px; font-weight:700;">{{ error }}</div>
          {% endif %}
          <form method="POST">
            <label style="display:block; margin-bottom:5px; font-weight:700;">{{ 'اسم المستخدم' if lang=='ar' else 'Username' }}</label>
            <input type="text" name="username" required style="width:100%; padding:10px; margin-bottom:14px;">
            <label style="display:block; margin-bottom:5px; font-weight:700;">{{ 'كلمة المرور' if lang=='ar' else 'Password' }}</label>
            <input type="password" name="password" required style="width:100%; padding:10px; margin-bottom:18px;">
            <button class="btn btn-primary" type="submit" style="width:100%; padding:11px;">{{ 'دخول' if lang=='ar' else 'Login' }}</button>
          </form>
        </div>
      </div>
    </body></html>
    """
    return render_template_string(html, lang=lang, error=error)


@app.route("/logout")
def logout():
    lang = session.get("lang", "ar")
    session.clear()
    session["lang"] = lang
    return redirect(url_for("home"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    lang = get_lang()
    role = session.get("role")
    conn = get_db()
    msg = request.args.get("msg", "")

    if role == "Faculty":
        doc_id = session.get("doctor_id")
        if request.method == "POST":
            building_id = int(request.form.get("building_id", 1))
            floor = request.form.get("floor", "").strip()
            office_number = request.form.get("office_number", "").strip()
            picked_days = request.form.getlist("days")
            days_csv = ",".join(picked_days) if picked_days else "Sun,Tue,Thu"
            start_time = request.form.get("start_time", "10:00").strip()
            end_time = request.form.get("end_time", "11:00").strip()
            raw_s = f"{days_csv} ({start_time} - {end_time})"

            conn.execute(
                "UPDATE FacultyMembers SET building_id=?, floor=?, office_number=? WHERE doctor_id=?",
                (building_id, floor, office_number, doc_id)
            )
            conn.execute(
                "UPDATE OfficeHours SET days=?, start_time=?, end_time=?, raw_schedule=? WHERE doctor_id=?",
                (days_csv, start_time, end_time, raw_s, doc_id)
            )
            conn.commit()
            msg = "✅ تم حفظ تعديلات المكتب والأيام والساعات المكتبية بنجاح!" if lang == "ar" else "✅ Office & schedule updated!"

        doc = conn.execute("""
            SELECT f.*, d.department_name, b.building_name, o.days, o.start_time, o.end_time
            FROM FacultyMembers f
            JOIN Departments d ON f.department_id = d.department_id
            JOIN Buildings b ON f.building_id = b.building_id
            LEFT JOIN OfficeHours o ON f.doctor_id = o.doctor_id
            WHERE f.doctor_id = ?
        """, (doc_id,)).fetchone()
        buildings = conn.execute("SELECT * FROM Buildings ORDER BY building_code").fetchall()
        conn.close()

        doc_days = [x.strip() for x in (doc["days"] or "").split(",") if x.strip()]
        html = """
        <!DOCTYPE html>
        <html lang="{{ lang }}">
        <head><meta charset="UTF-8"><title>{{ 'لوحة تحكم الدكتور' if lang=='ar' else 'Faculty Dashboard' }}</title>""" + BASE_STYLE + """</head>
        <body>
          <header>
            <a class="brand" href="/">👨‍🏫 {{ 'لوحة تحكم عضو هيئة التدريس' if lang=='ar' else 'Faculty Dashboard' }}</a>
            <div class="nav-links">
              <a class="lang-btn" href="/lang/{{ 'en' if lang=='ar' else 'ar' }}">🌐 {{ 'English' if lang=='ar' else 'العربية' }}</a>
              <a href="/">🏠 {{ 'عرض الموقع' if lang=='ar' else 'View Site' }}</a>
              <a href="/logout">🚪 {{ 'خروج' if lang=='ar' else 'Logout' }}</a>
            </div>
          </header>
          <div class="container" style="max-width:680px;">
            {% if msg %}<div class="alert">{{ msg }}</div>{% endif %}
            <div class="card" style="padding:1.6rem;">
              <h2 style="margin-bottom:4px;">{{ tr_name(doc.name) }} (#{{ doc.doctor_id }})</h2>
              <p style="color:#64748b; margin-bottom:16px;">{{ tr_val(doc.rank, RANK_EN) }} — {{ tr_val(doc.department_name, DEPT_EN) }}</p>
              <form method="POST">
                <label style="display:block; margin-bottom:5px; font-weight:700;">{{ 'المبنى' if lang=='ar' else 'Building' }}</label>
                <select name="building_id" style="width:100%; padding:9px; margin-bottom:12px;">
                  {% for b in buildings %}
                    <option value="{{ b.building_id }}" {% if b.building_id==doc.building_id %}selected{% endif %}>{{ tr_val(b.building_name, BLDG_EN) }}</option>
                  {% endfor %}
                </select>
                <label style="display:block; margin-bottom:5px; font-weight:700;">{{ 'الطابق' if lang=='ar' else 'Floor' }}</label>
                <input type="text" name="floor" value="{{ doc.floor }}" required style="width:100%; padding:9px; margin-bottom:12px;">
                <label style="display:block; margin-bottom:5px; font-weight:700;">{{ 'رقم المكتب' if lang=='ar' else 'Office Number' }}</label>
                <input type="text" name="office_number" value="{{ doc.office_number }}" required style="width:100%; padding:9px; margin-bottom:12px;">
                <label style="display:block; margin-bottom:6px; font-weight:700;">{{ 'أيام الساعات المكتبية (اختر الأيام بحرية)' if lang=='ar' else 'Select Office Hours Days' }}</label>
                <div class="chk-list" style="margin-bottom:14px;">
                  {% for code, ar_d, en_d in ALL_DAYS %}
                    <label class="chk-pill">
                      <input type="checkbox" name="days" value="{{ code }}" {% if code in doc_days %}checked{% endif %}>
                      <span>{{ ar_d if lang=='ar' else en_d }}</span>
                    </label>
                  {% endfor %}
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px;">
                  <div>
                    <label style="display:block; margin-bottom:4px; font-weight:700;">{{ 'من الساعة' if lang=='ar' else 'Start Time' }}</label>
                    <input type="text" name="start_time" value="{{ doc.start_time }}" style="width:100%; padding:9px;">
                  </div>
                  <div>
                    <label style="display:block; margin-bottom:4px; font-weight:700;">{{ 'إلى الساعة' if lang=='ar' else 'End Time' }}</label>
                    <input type="text" name="end_time" value="{{ doc.end_time }}" style="width:100%; padding:9px;">
                  </div>
                </div>
                <button class="btn btn-primary" type="submit" style="width:100%; padding:11px;">💾 {{ 'حفظ التغييرات' if lang=='ar' else 'Save Changes' }}</button>
              </form>
            </div>
          </div>
        </body></html>
        """
        return render_template_string(
            html, lang=lang, doc=doc, buildings=buildings, doc_days=doc_days,
            ALL_DAYS=ALL_DAYS, msg=msg, tr_val=tr_val, tr_name=tr_name, DEPT_EN=DEPT_EN,
            BLDG_EN=BLDG_EN, RANK_EN=RANK_EN
        )

    # Admin Dashboard
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        rank = request.form.get("rank", "أستاذ مساعد").strip()
        department_id = int(request.form.get("department_id", 1))
        building_id = int(request.form.get("building_id", 1))
        floor = request.form.get("floor", "الطابق الأول").strip()
        office_number = request.form.get("office_number", "B-101").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip() or (email.split("@")[0] if "@" in email else "doc_user")
        password = request.form.get("password", "").strip() or "doctor123"
        picked_days = request.form.getlist("days")
        days_csv = ",".join(picked_days) if picked_days else "Sun,Tue,Thu"
        start_time = request.form.get("start_time", "10:00").strip()
        end_time = request.form.get("end_time", "11:00").strip()

        nxt = conn.execute("SELECT COALESCE(MAX(doctor_id), 0) + 1 FROM FacultyMembers").fetchone()[0]
        conn.execute(
            "INSERT INTO FacultyMembers VALUES (?,?,?,?,?,?,?,?,0)",
            (nxt, name, rank, department_id, building_id, floor, office_number, email)
        )
        conn.execute(
            "INSERT INTO OfficeHours (doctor_id, days, start_time, end_time, raw_schedule) VALUES (?,?,?,?,?)",
            (nxt, days_csv, start_time, end_time, f"{days_csv} ({start_time} - {end_time})")
        )
        conn.execute(
            "INSERT OR REPLACE INTO Users (username, password_hash, role, doctor_id) VALUES (?, ?, 'Faculty', ?)",
            (username, password, nxt)
        )
        conn.commit()
        return redirect(url_for("dashboard", msg=f"✅ تمت إضافة الدكتور #{nxt} ({name}) مع حساب الدخول بنجاح!"))

    doctors = conn.execute("""
        SELECT f.*, d.department_name, b.building_code, b.building_name,
               o.days, o.start_time, o.end_time,
               u.username, u.password_hash
        FROM FacultyMembers f
        JOIN Departments d ON f.department_id = d.department_id
        JOIN Buildings b ON f.building_id = b.building_id
        LEFT JOIN OfficeHours o ON f.doctor_id = o.doctor_id
        LEFT JOIN Users u ON f.doctor_id = u.doctor_id
        ORDER BY f.doctor_id ASC
    """).fetchall()
    departments = conn.execute("SELECT * FROM Departments ORDER BY department_id").fetchall()
    buildings = conn.execute("SELECT * FROM Buildings ORDER BY building_id").fetchall()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="{{ lang }}">
    <head><meta charset="UTF-8"><title>{{ 'لوحة تحكم المدير (Admin)' if lang=='ar' else 'Admin Dashboard' }}</title>""" + BASE_STYLE + """</head>
    <body>
      <header>
        <a class="brand" href="/">🛡️ {{ 'لوحة تحكم مدير النظام (Admin)' if lang=='ar' else 'System Admin Dashboard' }}</a>
        <div class="nav-links">
          <a class="lang-btn" href="/lang/{{ 'en' if lang=='ar' else 'ar' }}">🌐 {{ 'English' if lang=='ar' else 'العربية' }}</a>
          <a href="/">🏠 {{ 'استعراض الموقع' if lang=='ar' else 'View Site' }}</a>
          <a href="/logout">🚪 {{ 'خروج' if lang=='ar' else 'Logout' }}</a>
        </div>
      </header>

      <div class="container">
        {% if msg %}<div class="alert">{{ msg }}</div>{% endif %}

        <!-- Add Doctor with Flexible Days + Username & Password -->
        <div class="card" style="margin-bottom:1.2rem;">
          <h3 style="margin-bottom:10px; color:#0f2942;">➕ {{ 'إضافة دكتور جديد (مع تحديد الأيام بحرية واسم المستخدم وكلمة المرور)' if lang=='ar' else 'Add New Doctor (Flexible Days + Credentials)' }}</h3>
          <form method="POST" action="/dashboard" style="display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr)); gap:9px; align-items:end;">
            <div><label>{{ 'اسم الدكتور' if lang=='ar' else 'Name' }}</label><input type="text" name="name" required style="width:100%;"></div>
            <div><label>{{ 'الرتبة' if lang=='ar' else 'Rank' }}</label><input type="text" name="rank" value="أستاذ مساعد" style="width:100%;"></div>
            <div>
              <label>{{ 'القسم' if lang=='ar' else 'Department' }}</label>
              <select name="department_id" style="width:100%;">
                {% for d in departments %}<option value="{{ d.department_id }}">{{ tr_val(d.department_name, DEPT_EN) }}</option>{% endfor %}
              </select>
            </div>
            <div>
              <label>{{ 'المبنى (A, B, C, D)' if lang=='ar' else 'Building' }}</label>
              <select name="building_id" style="width:100%;">
                {% for b in buildings %}<option value="{{ b.building_id }}">{{ tr_val(b.building_name, BLDG_EN) }}</option>{% endfor %}
              </select>
            </div>
            <div><label>{{ 'الطابق' if lang=='ar' else 'Floor' }}</label><input type="text" name="floor" value="الطابق الأول" style="width:100%;"></div>
            <div><label>{{ 'رقم المكتب' if lang=='ar' else 'Office' }}</label><input type="text" name="office_number" value="B-105" style="width:100%;"></div>
            <div><label>{{ 'البريد الجامعي' if lang=='ar' else 'Email' }}</label><input type="email" name="email" required style="width:100%;"></div>
            <div><label>{{ 'اسم المستخدم (Username)' if lang=='ar' else 'Username' }}</label><input type="text" name="username" required placeholder="dr.user" style="width:100%;"></div>
            <div><label>{{ 'كلمة المرور (Password)' if lang=='ar' else 'Password' }}</label><input type="text" name="password" required value="doctor123" style="width:100%;"></div>
            <div><label>{{ 'من الساعة' if lang=='ar' else 'From' }}</label><input type="text" name="start_time" value="10:00" style="width:100%;"></div>
            <div><label>{{ 'إلى الساعة' if lang=='ar' else 'To' }}</label><input type="text" name="end_time" value="11:30" style="width:100%;"></div>
            <div style="grid-column:1/-1;">
              <label style="font-weight:700; display:block; margin-bottom:4px;">📅 {{ 'اختر أيام الساعات المكتبية (منفصلة ومرنة):' if lang=='ar' else 'Select Individual Days:' }}</label>
              <div class="chk-list">
                {% for code, ar_d, en_d in ALL_DAYS %}
                  <label class="chk-pill"><input type="checkbox" name="days" value="{{ code }}" {% if code in ['Sun','Tue'] %}checked{% endif %}><span>{{ ar_d if lang=='ar' else en_d }} ({{ code }})</span></label>
                {% endfor %}
              </div>
            </div>
            <div style="grid-column:1/-1;">
              <button class="btn btn-primary" type="submit">➕ {{ 'إضافة الدكتور وحفظ حسابه' if lang=='ar' else 'Add Doctor & Create Account' }}</button>
            </div>
          </form>
        </div>

        <!-- Manage Departments & Buildings (Add + Remove) -->
        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:1rem; margin-bottom:1.2rem;">
          <div class="card">
            <h3 style="margin-bottom:8px;">🏢 {{ 'إدارة الأقسام الأكاديمية (إضافة / إزالة)' if lang=='ar' else 'Manage Departments (Add / Remove)' }}</h3>
            <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px;">
              {% for d in departments %}
                <span class="badge" style="display:inline-flex; align-items:center; gap:6px; padding:5px 10px;">
                  {{ tr_val(d.department_name, DEPT_EN) }}
                  <form method="POST" action="/admin/delete_department/{{ d.department_id }}" style="display:inline;">
                    <button type="submit" style="background:none; border:none; color:#dc2626; font-weight:900; cursor:pointer;" title="حذف القسم">✕</button>
                  </form>
                </span>
              {% endfor %}
            </div>
            <form method="POST" action="/admin/add_department" style="display:flex; gap:8px;">
              <input type="text" name="department_name" required placeholder="{{ 'اسم القسم الجديد...' if lang=='ar' else 'New department...' }}" style="flex:1;">
              <button class="btn btn-dark" type="submit">+ {{ 'إضافة قسم' if lang=='ar' else 'Add' }}</button>
            </form>
          </div>

          <div class="card">
            <h3 style="margin-bottom:8px;">🏛️ {{ 'إدارة المباني الجامعية A, B, C, D (إضافة / إزالة)' if lang=='ar' else 'Manage Buildings (Add / Remove)' }}</h3>
            <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px;">
              {% for b in buildings %}
                <span class="badge badge-bldg" style="display:inline-flex; align-items:center; gap:6px; padding:5px 10px;">
                  {{ b.building_code }}: {{ tr_val(b.building_name, BLDG_EN) }}
                  <form method="POST" action="/admin/delete_building/{{ b.building_id }}" style="display:inline;">
                    <button type="submit" style="background:none; border:none; color:#dc2626; font-weight:900; cursor:pointer;" title="حذف المبنى">✕</button>
                  </form>
                </span>
              {% endfor %}
            </div>
            <form method="POST" action="/admin/add_building" style="display:flex; gap:6px;">
              <input type="text" name="building_code" required placeholder="E" style="width:70px;">
              <input type="text" name="building_name" required placeholder="{{ 'وصف المبنى وتخصصه...' if lang=='ar' else 'Building name...' }}" style="flex:1;">
              <button class="btn btn-dark" type="submit">+ {{ 'إضافة مبنى' if lang=='ar' else 'Add' }}</button>
            </form>
          </div>
        </div>

        <!-- Doctors Table (#1 to #100) with in-place Deleted Status, Restore, Flexible Days & Credentials -->
        <div class="card" style="overflow-x:auto;">
          <h3 style="margin-bottom:10px;">📋 {{ 'جدول إدارة الدكاترة (1 إلى 100) — تعديل المكتب، الأيام، اسم المستخدم، كلمة المرور، والحذف/الاستعادة' if lang=='ar' else 'Doctors Management Table (#1 to #100)' }}</h3>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>{{ 'الاسم والحالة' if lang=='ar' else 'Name & Status' }}</th>
                <th>{{ 'القسم / المبنى' if lang=='ar' else 'Dept / Bldg' }}</th>
                <th>{{ 'الطابق والمكتب' if lang=='ar' else 'Floor & Office' }}</th>
                <th>{{ 'الأيام (مرنة)' if lang=='ar' else 'Flexible Days' }}</th>
                <th>{{ 'الوقت' if lang=='ar' else 'Time' }}</th>
                <th>{{ 'اسم المستخدم وكلمة المرور' if lang=='ar' else 'Username & Password' }}</th>
                <th>{{ 'إجراءات' if lang=='ar' else 'Actions' }}</th>
              </tr>
            </thead>
            <tbody>
              {% for doc in doctors %}
                {% set row_days = (doc.days or '').split(',') %}
                <tr id="doc-{{ doc.doctor_id }}" class="{% if doc.is_deleted==1 %}deleted-row{% endif %}">
                  <td><b>#{{ doc.doctor_id }}</b></td>
                  <td>
                    <b>{{ tr_name(doc.name) }}</b><br>
                    <small style="color:#64748b;">{{ doc.email }}</small>
                    {% if doc.is_deleted == 1 %}
                      <div style="margin-top:4px;"><span class="del-badge">🚫 {{ 'تم حذفه (Deleted)' if lang=='ar' else 'Deleted' }}</span></div>
                    {% endif %}
                  </td>
                  <td>
                    <span class="badge">{{ tr_val(doc.department_name, DEPT_EN) }}</span><br>
                    <small><b>{{ doc.building_code }}</b> — {{ tr_val(doc.building_name, BLDG_EN) }}</small>
                  </td>
                  <form method="POST" action="/admin/edit/{{ doc.doctor_id }}">
                    <td>
                      <input type="text" name="floor" value="{{ doc.floor }}" style="width:95px; margin-bottom:3px;"><br>
                      <input type="text" name="office_number" value="{{ doc.office_number }}" style="width:80px; font-weight:700;">
                    </td>
                    <td>
                      <div style="display:flex; flex-wrap:wrap; gap:3px; max-width:190px;">
                        {% for code, ar_d, en_d in ALL_DAYS %}
                          <label style="font-size:0.72rem; background:#f8fafc; border:1px solid #cbd5e1; padding:1px 5px; border-radius:4px;">
                            <input type="checkbox" name="days" value="{{ code }}" {% if code in row_days %}checked{% endif %}>{{ ar_d if lang=='ar' else code }}
                          </label>
                        {% endfor %}
                      </div>
                    </td>
                    <td>
                      <input type="text" name="start_time" value="{{ doc.start_time }}" style="width:62px;"> -
                      <input type="text" name="end_time" value="{{ doc.end_time }}" style="width:62px;">
                    </td>
                    <td>
                      <input type="text" name="username" value="{{ doc.username or '' }}" placeholder="username" style="width:105px; margin-bottom:3px;"><br>
                      <input type="text" name="password" value="{{ doc.password_hash or 'doctor123' }}" placeholder="password" style="width:105px;">
                    </td>
                    <td style="white-space:nowrap;">
                      <button class="btn btn-primary" type="submit" style="padding:5px 9px; font-size:0.75rem;">💾 {{ 'حفظ' if lang=='ar' else 'Save' }}</button>
                  </form>
                      {% if doc.is_deleted == 0 %}
                        <form method="POST" action="/admin/delete/{{ doc.doctor_id }}" style="display:inline;">
                          <button class="btn btn-danger" type="submit" style="padding:5px 9px; font-size:0.75rem;">🗑 {{ 'حذف' if lang=='ar' else 'Delete' }}</button>
                        </form>
                      {% else %}
                        <form method="POST" action="/admin/restore/{{ doc.doctor_id }}" style="display:inline;">
                          <button class="btn btn-success" type="submit" style="padding:5px 9px; font-size:0.75rem;">↩ {{ 'استعادة' if lang=='ar' else 'Restore' }}</button>
                        </form>
                      {% endif %}
                    </td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </body></html>
    """
    return render_template_string(
        html, lang=lang, doctors=doctors, departments=departments,
        buildings=buildings, ALL_DAYS=ALL_DAYS, msg=msg,
        tr_val=tr_val, tr_name=tr_name, DEPT_EN=DEPT_EN, BLDG_EN=BLDG_EN
    )


@app.route("/admin/edit/<int:doc_id>", methods=["POST"])
def admin_edit_doctor(doc_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))
    floor = request.form.get("floor", "").strip()
    office_number = request.form.get("office_number", "").strip()
    picked_days = request.form.getlist("days")
    days_csv = ",".join(picked_days) if picked_days else "Sun,Tue,Thu"
    start_time = request.form.get("start_time", "10:00").strip()
    end_time = request.form.get("end_time", "11:00").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip() or "doctor123"

    conn = get_db()
    conn.execute("UPDATE FacultyMembers SET floor=?, office_number=? WHERE doctor_id=?", (floor, office_number, doc_id))
    conn.execute(
        "UPDATE OfficeHours SET days=?, start_time=?, end_time=?, raw_schedule=? WHERE doctor_id=?",
        (days_csv, start_time, end_time, f"{days_csv} ({start_time} - {end_time})", doc_id)
    )
    if username:
        existing = conn.execute("SELECT user_id FROM Users WHERE doctor_id=?", (doc_id,)).fetchone()
        if existing:
            conn.execute("UPDATE Users SET username=?, password_hash=? WHERE doctor_id=?", (username, password, doc_id))
        else:
            conn.execute("INSERT OR REPLACE INTO Users (username, password_hash, role, doctor_id) VALUES (?, ?, 'Faculty', ?)", (username, password, doc_id))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", msg=f"✅ تم تحديث بيانات وحساب الدكتور #{doc_id} بنجاح!") + f"#doc-{doc_id}")


@app.route("/admin/delete/<int:doc_id>", methods=["POST"])
def admin_delete_doctor(doc_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))
    conn = get_db()
    conn.execute("UPDATE FacultyMembers SET is_deleted=1 WHERE doctor_id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", msg=f"🚫 تم وضع الدكتور #{doc_id} في حالة (تم حذفه) وإخفاؤه من واجهة الطلاب.") + f"#doc-{doc_id}")


@app.route("/admin/restore/<int:doc_id>", methods=["POST"])
def admin_restore_doctor(doc_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))
    conn = get_db()
    conn.execute("UPDATE FacultyMembers SET is_deleted=0 WHERE doctor_id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", msg=f"↩ تمت استعادة الدكتور #{doc_id} لإظهاره في الدليل.") + f"#doc-{doc_id}")


@app.route("/admin/add_department", methods=["POST"])
def admin_add_department():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))
    dept_name = request.form.get("department_name", "").strip()
    if dept_name:
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO Departments (department_name) VALUES (?)", (dept_name,))
        conn.commit()
        conn.close()
    return redirect(url_for("dashboard", msg=f"✅ تمت إضافة القسم ({dept_name}) بنجاح!"))


@app.route("/admin/delete_department/<int:dept_id>", methods=["POST"])
def admin_delete_department(dept_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))
    conn = get_db()
    cnt = conn.execute("SELECT COUNT(*) FROM Departments").fetchone()[0]
    if cnt > 1:
        fallback = conn.execute("SELECT department_id FROM Departments WHERE department_id != ? LIMIT 1", (dept_id,)).fetchone()[0]
        conn.execute("UPDATE FacultyMembers SET department_id=? WHERE department_id=?", (fallback, dept_id))
        conn.execute("DELETE FROM Departments WHERE department_id=?", (dept_id,))
        conn.commit()
    conn.close()
    return redirect(url_for("dashboard", msg="🗑 تم حذف القسم بنجاح!"))


@app.route("/admin/add_building", methods=["POST"])
def admin_add_building():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))
    b_code = request.form.get("building_code", "").strip()
    b_name = request.form.get("building_name", "").strip()
    if b_code and b_name:
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO Buildings (building_code, building_name) VALUES (?, ?)", (b_code, b_name))
        conn.commit()
        conn.close()
    return redirect(url_for("dashboard", msg=f"✅ تمت إضافة المبنى ({b_code}) بنجاح!"))


@app.route("/admin/delete_building/<int:bldg_id>", methods=["POST"])
def admin_delete_building(bldg_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))
    conn = get_db()
    cnt = conn.execute("SELECT COUNT(*) FROM Buildings").fetchone()[0]
    if cnt > 1:
        fallback = conn.execute("SELECT building_id FROM Buildings WHERE building_id != ? LIMIT 1", (bldg_id,)).fetchone()[0]
        conn.execute("UPDATE FacultyMembers SET building_id=? WHERE building_id=?", (fallback, bldg_id))
        conn.execute("DELETE FROM Buildings WHERE building_id=?", (bldg_id,))
        conn.commit()
    conn.close()
    return redirect(url_for("dashboard", msg="🗑 تم حذف المبنى بنجاح!"))


if __name__ == "__main__":
    ensure_db_ready()
    print("🚀 السيرفر يعمل الآن على الرابط: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)