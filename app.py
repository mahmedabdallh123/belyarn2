import streamlit as st
import pandas as pd
import json
import os
import io
import requests
import shutil
import re
from datetime import datetime, timedelta
from base64 import b64decode

# محاولة استيراد PyGithub (لرفع التعديلات)
try:
    from github import Github
    GITHUB_AVAILABLE = True
except Exception:
    GITHUB_AVAILABLE = False

# ===============================
# ⚙ إعدادات التطبيق المتكامل
# ===============================
APP_CONFIG = {
    # إعدادات التطبيق العامة
    "APP_TITLE": "نظام إدارة بيل يارن المتكامل",
    "APP_ICON": "🏭",
    
    # إعدادات الأمان
    "MAX_ACTIVE_USERS": 10,
    "SESSION_DURATION_MINUTES": 240,
    
    # إعدادات الواجهة
    "SHOW_TECH_SUPPORT_TO_ALL": True,
    "MAIN_TABS": ["🏭 مكبس القطن", "🛠 CMMS", "🏗 محطات الإنتاج", "👥 إدارة النظام", "📞 الدعم الفني"],
    
    # إعدادات الحفظ التلقائي
    "AUTO_SAVE": True,
    
    # إعدادات GitHub للملفات المختلفة
    "REPOS": {
        "cotton": {
            "REPO_NAME": "mahmedabdallh123/luva",
            "FILE_PATH": "luva.xlsx",
            "LOCAL_FILE": "luva.xlsx"
        },
        "cmms": {
            "REPO_NAME": "mahmedabdallh123/BELYARN", 
            "FILE_PATH": "Machine_Service_Lookup.xlsx",
            "LOCAL_FILE": "Machine_Service_Lookup.xlsx"
        },
        "production": {
            "REPO_NAME": "mahmedabdallh123/Maintain-luva",
            "FILE_PATH": "station.xlsx",
            "LOCAL_FILE": "station.xlsx"
        }
    },
    
    # إعدادات الورديات لمكبس القطن
    "SHIFTS": {
        "الاولي": {"start": 8, "end": 16},
        "الثانيه": {"start": 16, "end": 24},
        "الثالثه": {"start": 0, "end": 8}
    },
    
    # الأعمدة الإلزامية لمحطات الإنتاج
    "MANDATORY_COLUMNS": ["الحدث", "التصحيح الفني", "التاريخ"]
}

# ===============================
# 🗂 إعدادات الملفات العامة
# ===============================
USERS_FILE = "users.json"
STATE_FILE = "state.json"
SESSION_DURATION = timedelta(minutes=APP_CONFIG["SESSION_DURATION_MINUTES"])
MAX_ACTIVE_USERS = APP_CONFIG["MAX_ACTIVE_USERS"]

# -------------------------------
# 🧩 دوال مساعدة للملفات والحالة
# -------------------------------
def load_users():
    """تحميل بيانات المستخدمين من ملف JSON"""
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {
                "password": "1111", 
                "role": "admin", 
                "created_at": datetime.now().isoformat(),
                "permissions": ["all"],
                "full_name": "المسؤول الرئيسي",
                "department": "all"
            },
            "user1": {
                "password": "12345", 
                "role": "data_entry", 
                "created_at": datetime.now().isoformat(),
                "permissions": ["data_entry"],
                "full_name": "مستخدم مكبس القطن",
                "department": "cotton"
            },
            "user2": {
                "password": "99999", 
                "role": "viewer", 
                "created_at": datetime.now().isoformat(),
                "permissions": ["view_stats"],
                "full_name": "مستخدم CMMS",
                "department": "cmms"
            },
            "user3": {
                "password": "88888", 
                "role": "editor", 
                "created_at": datetime.now().isoformat(),
                "permissions": ["view", "edit"],
                "full_name": "مستخدم محطات الإنتاج",
                "department": "production"
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=4, ensure_ascii=False)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
            for username, info in users.items():
                if "department" not in info:
                    info["department"] = "all"
                if "full_name" not in info:
                    info["full_name"] = username
            return users
    except Exception as e:
        st.error(f"❌ خطأ في ملف users.json: {e}")
        return {
            "admin": {
                "password": "1111", 
                "role": "admin", 
                "permissions": ["all"], 
                "created_at": datetime.now().isoformat(),
                "full_name": "المسؤول الرئيسي",
                "department": "all"
            }
        }

def save_users(users):
    """حفظ بيانات المستخدمين إلى ملف JSON"""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"❌ خطأ في حفظ ملف users.json: {e}")
        return False

def load_state():
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

def cleanup_sessions(state):
    now = datetime.now()
    changed = False
    for user, info in list(state.items()):
        if info.get("active") and "login_time" in info:
            try:
                login_time = datetime.fromisoformat(info["login_time"])
                if now - login_time > SESSION_DURATION:
                    info["active"] = False
                    info.pop("login_time", None)
                    changed = True
            except:
                info["active"] = False
                changed = True
    if changed:
        save_state(state)
    return state

def remaining_time(state, username):
    if not username or username not in state:
        return None
    info = state.get(username)
    if not info or not info.get("active"):
        return None
    try:
        lt = datetime.fromisoformat(info["login_time"])
        remaining = SESSION_DURATION - (datetime.now() - lt)
        if remaining.total_seconds() <= 0:
            return None
        return remaining
    except:
        return None

# -------------------------------
# 🔐 تسجيل الخروج
# -------------------------------
def logout_action():
    state = load_state()
    username = st.session_state.get("username")
    if username and username in state:
        state[username]["active"] = False
        state[username].pop("login_time", None)
        save_state(state)
    keys = list(st.session_state.keys())
    for k in keys:
        st.session_state.pop(k, None)
    st.rerun()

# -------------------------------
# 🧠 واجهة تسجيل الدخول
# -------------------------------
def login_ui():
    users = load_users()
    state = cleanup_sessions(load_state())
    
    # تهيئة session_state إذا لم تكن موجودة
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.session_state.user_permissions = []
        st.session_state.user_fullname = None
        st.session_state.user_department = None

    st.title(f"{APP_CONFIG['APP_ICON']} تسجيل الدخول - {APP_CONFIG['APP_TITLE']}")

    username_input = st.selectbox("👤 اختر المستخدم", list(users.keys()))
    password = st.text_input("🔑 كلمة المرور", type="password")

    active_users = [u for u, v in state.items() if v.get("active")]
    active_count = len(active_users)
    st.caption(f"🔒 المستخدمون النشطون الآن: {active_count} / {MAX_ACTIVE_USERS}")

    if not st.session_state.logged_in:
        if st.button("تسجيل الدخول", type="primary"):
            if username_input in users and users[username_input]["password"] == password:
                if username_input == "admin":
                    pass
                elif username_input in active_users:
                    st.warning("⚠ هذا المستخدم مسجل دخول بالفعل.")
                    return False
                elif active_count >= MAX_ACTIVE_USERS:
                    st.error("🚫 الحد الأقصى للمستخدمين المتصلين حالياً.")
                    return False
                state[username_input] = {"active": True, "login_time": datetime.now().isoformat()}
                save_state(state)
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.session_state.user_role = users[username_input].get("role", "viewer")
                st.session_state.user_permissions = users[username_input].get("permissions", ["view_stats"])
                st.session_state.user_fullname = users[username_input].get("full_name", username_input)
                st.session_state.user_department = users[username_input].get("department", "all")
                st.success(f"✅ تم تسجيل الدخول: {st.session_state.user_fullname}")
                st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة.")
        return False
    else:
        username = st.session_state.username
        user_fullname = st.session_state.get("user_fullname", username)  # استخدام get للسلامة
        user_role = st.session_state.user_role
        st.success(f"✅ مسجل الدخول كـ: {user_fullname} ({user_role})")
        rem = remaining_time(state, username)
        if rem:
            mins, secs = divmod(int(rem.total_seconds()), 60)
            st.info(f"⏳ الوقت المتبقي: {mins:02d}:{secs:02d}")
        else:
            st.warning("⏰ انتهت الجلسة، سيتم تسجيل الخروج.")
            logout_action()
        if st.button("🚪 تسجيل الخروج"):
            logout_action()
        return True

# -------------------------------
# 🔄 دوال جلب الملفات من GitHub
# -------------------------------
def get_github_url(department):
    """إنشاء رابط GitHub تلقائياً من الإعدادات"""
    repo_config = APP_CONFIG["REPOS"][department]
    return f"https://github.com/{repo_config['REPO_NAME'].split('/')[0]}/{repo_config['REPO_NAME'].split('/')[1]}/raw/main/{repo_config['FILE_PATH']}"

def fetch_from_github_requests(department):
    """تحميل بإستخدام رابط RAW (requests)"""
    try:
        repo_config = APP_CONFIG["REPOS"][department]
        github_url = get_github_url(department)
        response = requests.get(github_url, stream=True, timeout=15)
        response.raise_for_status()
        with open(repo_config["LOCAL_FILE"], "wb") as f:
            shutil.copyfileobj(response.raw, f)
        try:
            st.cache_data.clear()
        except:
            pass
        return True
    except Exception as e:
        st.error(f"⚠ فشل التحديث من GitHub: {e}")
        return False

def fetch_from_github_api(department):
    """تحميل عبر GitHub API"""
    if not GITHUB_AVAILABLE:
        return fetch_from_github_requests(department)
    
    try:
        token = st.secrets.get("github", {}).get("token", None)
        if not token:
            return fetch_from_github_requests(department)
        
        repo_config = APP_CONFIG["REPOS"][department]
        g = Github(token)
        repo = g.get_repo(repo_config["REPO_NAME"])
        file_content = repo.get_contents(repo_config["FILE_PATH"], ref="main")
        content = b64decode(file_content.content)
        with open(repo_config["LOCAL_FILE"], "wb") as f:
            f.write(content)
        try:
            st.cache_data.clear()
        except:
            pass
        return True
    except Exception as e:
        st.error(f"⚠ فشل تحميل الملف من GitHub: {e}")
        return False

# -------------------------------
# 📂 دوال تحميل البيانات للأقسام المختلفة
# -------------------------------
@st.cache_data(show_spinner=False)
def load_cotton_data():
    """تحميل بيانات مكبس القطن"""
    repo_config = APP_CONFIG["REPOS"]["cotton"]
    if not os.path.exists(repo_config["LOCAL_FILE"]):
        return pd.DataFrame()
    
    try:
        df = pd.read_excel(repo_config["LOCAL_FILE"])
        return df
    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_all_sheets(department):
    """تحميل جميع الشيتات من ملف Excel"""
    repo_config = APP_CONFIG["REPOS"][department]
    if not os.path.exists(repo_config["LOCAL_FILE"]):
        return None
    
    try:
        sheets = pd.read_excel(repo_config["LOCAL_FILE"], sheet_name=None)
        if not sheets:
            return None
        
        for name, df in sheets.items():
            df.columns = df.columns.astype(str).str.strip()
        
        return sheets
    except Exception as e:
        return None

@st.cache_data(show_spinner=False)
def load_sheets_for_edit(department):
    """تحميل جميع الشيتات للتحرير"""
    repo_config = APP_CONFIG["REPOS"][department]
    if not os.path.exists(repo_config["LOCAL_FILE"]):
        return None
    
    try:
        sheets = pd.read_excel(repo_config["LOCAL_FILE"], sheet_name=None, dtype=object)
        if not sheets:
            return None
        
        for name, df in sheets.items():
            df.columns = df.columns.astype(str).str.strip()
        
        return sheets
    except Exception as e:
        return None

# -------------------------------
# 🔁 دوال حفظ البيانات للأقسام المختلفة
# -------------------------------
def save_cotton_data(df, commit_message="تحديث بيانات مكبس القطن"):
    """حفظ البيانات إلى ملف Excel والرفع إلى GitHub"""
    try:
        repo_config = APP_CONFIG["REPOS"]["cotton"]
        df.to_excel(repo_config["LOCAL_FILE"], index=False)
        
        try:
            st.cache_data.clear()
        except:
            pass

        token = st.secrets.get("github", {}).get("token", None)
        if token and GITHUB_AVAILABLE:
            try:
                g = Github(token)
                repo = g.get_repo(repo_config["REPO_NAME"])
                with open(repo_config["LOCAL_FILE"], "rb") as f:
                    content = f.read()

                try:
                    contents = repo.get_contents(repo_config["FILE_PATH"], ref="main")
                    result = repo.update_file(
                        path=repo_config["FILE_PATH"], 
                        message=commit_message, 
                        content=content, 
                        sha=contents.sha, 
                        branch="main"
                    )
                    st.success("✅ تم الحفظ والرفع إلى GitHub بنجاح")
                except:
                    result = repo.create_file(
                        path=repo_config["FILE_PATH"], 
                        message=commit_message, 
                        content=content, 
                        branch="main"
                    )
                    st.success("✅ تم إنشاء ملف جديد على GitHub")
            except Exception as e:
                st.warning(f"⚠ تم الحفظ محلياً فقط: {e}")
        
        return True
    except Exception as e:
        st.error(f"❌ خطأ في حفظ البيانات: {e}")
        return False

def save_local_excel_and_push(sheets_dict, department, commit_message="Update from Streamlit"):
    """دالة محسنة للحفظ التلقائي المحلي والرفع إلى GitHub"""
    repo_config = APP_CONFIG["REPOS"][department]
    
    try:
        with pd.ExcelWriter(repo_config["LOCAL_FILE"], engine="openpyxl") as writer:
            for name, sh in sheets_dict.items():
                try:
                    sh.to_excel(writer, sheet_name=name, index=False)
                except Exception:
                    sh.astype(object).to_excel(writer, sheet_name=name, index=False)
    except Exception as e:
        st.error(f"⚠ خطأ أثناء الحفظ المحلي: {e}")
        return None

    try:
        st.cache_data.clear()
    except:
        pass

    token = st.secrets.get("github", {}).get("token", None)
    if not token:
        st.warning("⚠ لم يتم العثور على GitHub token. سيتم الحفظ محلياً فقط.")
        return load_sheets_for_edit(department)

    if not GITHUB_AVAILABLE:
        st.warning("⚠ PyGithub غير متوفر. سيتم الحفظ محلياً فقط.")
        return load_sheets_for_edit(department)

    try:
        g = Github(token)
        repo = g.get_repo(repo_config["REPO_NAME"])
        with open(repo_config["LOCAL_FILE"], "rb") as f:
            content = f.read()

        try:
            contents = repo.get_contents(repo_config["FILE_PATH"], ref="main")
            result = repo.update_file(path=repo_config["FILE_PATH"], message=commit_message, content=content, sha=contents.sha, branch="main")
            st.success(f"✅ تم الحفظ والرفع إلى GitHub بنجاح: {commit_message}")
            return load_sheets_for_edit(department)
        except Exception as e:
            try:
                result = repo.create_file(path=repo_config["FILE_PATH"], message=commit_message, content=content, branch="main")
                st.success(f"✅ تم إنشاء ملف جديد على GitHub: {commit_message}")
                return load_sheets_for_edit(department)
            except Exception as create_error:
                st.error(f"❌ فشل إنشاء ملف جديد على GitHub: {create_error}")
                return None

    except Exception as e:
        st.error(f"❌ فشل الرفع إلى GitHub: {e}")
        return None

def auto_save_to_github(sheets_dict, department, operation_description):
    """دالة الحفظ التلقائي المحسنة"""
    username = st.session_state.get("username", "unknown")
    commit_message = f"{operation_description} by {username} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    result = save_local_excel_and_push(sheets_dict, department, commit_message)
    if result is not None:
        st.success("✅ تم حفظ التغييرات تلقائياً في GitHub")
        return result
    else:
        st.error("❌ فشل الحفظ التلقائي")
        return sheets_dict

# -------------------------------
# 🧮 دوال مساعدة للنظام
# -------------------------------
def get_current_shift():
    """تحديد الوردية الحالية تلقائياً"""
    now = datetime.now()
    current_hour = now.hour
    
    for shift_name, shift_times in APP_CONFIG["SHIFTS"].items():
        if shift_times["start"] <= current_hour < shift_times["end"]:
            return shift_name
    return "الثالثه"

def get_supervisors():
    """قائمة المشرفين"""
    return ["T.A", "T.B", "T.C", "T.D"]

def get_bale_types():
    """أنواع البالات"""
    return ["قماش", "تراب", "هبوه دست", "اسطبات تدویر", "برم", "برم انفاق", "بلاستيك",
        "هبوه تنظيف", "انفاق", "شرق الغزل", "تمشيط غير مغلف", 
        "تمشيط مغلف", "مكس", "كرد", "قطن خام","ملح"
    ]

def add_new_record(df, supervisor, bale_type, weight, notes="", manual_date=None, manual_shift=None):
    """إضافة سجل جديد لمكبس القطن"""
    now = datetime.now()
    
    if manual_date:
        record_date = manual_date
    else:
        record_date = now.date()
    
    if manual_shift:
        record_shift = manual_shift
    else:
        record_shift = get_current_shift()
    
    new_record = {
        'التاريخ': record_date,
        'الوقت': now.time(),
        'الوردية': record_shift,
        'المشرف': supervisor,
        'نوع البالة': bale_type,
        'وزن البالة': weight,
        'ملاحظات': notes
    }
    
    new_df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    return new_record, new_df

def generate_advanced_statistics(df, start_date, end_date, selected_shifts, selected_bale_types, calculate_percentage=False):
    """توليد إحصائيات متقدمة لمكبس القطن"""
    if df.empty:
        return pd.DataFrame()
    
    df['التاريخ'] = pd.to_datetime(df['التاريخ']).dt.date
    mask = (df['التاريخ'] >= start_date) & (df['التاريخ'] <= end_date)
    filtered_df = df[mask]
    
    if selected_shifts:
        filtered_df = filtered_df[filtered_df['الوردية'].isin(selected_shifts)]
    
    if selected_bale_types:
        filtered_df = filtered_df[filtered_df['نوع البالة'].isin(selected_bale_types)]
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    stats = filtered_df.groupby('نوع البالة').agg({
        'وزن البالة': ['count', 'sum', 'mean'],
        'المشرف': 'first'
    }).round(2)
    
    stats.columns = ['عدد البالات', 'إجمالي الوزن', 'متوسط الوزن', 'المشرف']
    stats = stats.reset_index()
    
    if calculate_percentage:
        cotton_weight = 0
        cotton_mask = (df['التاريخ'] >= start_date) & (df['التاريخ'] <= end_date)
        if selected_shifts:
            cotton_mask = cotton_mask & (df['الوردية'].isin(selected_shifts))
        cotton_data = df[cotton_mask & (df['نوع البالة'] == 'قطن خام')]
        
        if not cotton_data.empty:
            cotton_weight = cotton_data['وزن البالة'].sum()
        
        if cotton_weight > 0:
            stats['النسبة المئوية %'] = ((stats['إجمالي الوزن'] / cotton_weight) * 100).round(2)
        else:
            stats['النسبة المئوية %'] = 0
    
    return stats

def normalize_name(s):
    """تطبيع الأسماء للبحث"""
    if s is None: return ""
    s = str(s).replace("\n", "+")
    s = re.sub(r"[^0-9a-zA-Z\u0600-\u06FF\+\s_/.-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

def split_needed_services(needed_service_str):
    """تقسيم الخدمات المطلوبة"""
    if not isinstance(needed_service_str, str) or needed_service_str.strip() == "":
        return []
    parts = re.split(r"\+|,|\n|;", needed_service_str)
    return [p.strip() for p in parts if p.strip() != ""]

def check_machine_status(card_num, current_tons, all_sheets):
    """فحص حالة الماكينة لـ CMMS"""
    if not all_sheets:
        st.error("❌ لم يتم تحميل أي شيتات.")
        return
    
    if "ServicePlan" not in all_sheets:
        st.error("❌ الملف لا يحتوي على شيت ServicePlan.")
        return
    
    service_plan_df = all_sheets["ServicePlan"]
    card_sheet_name = f"Card{card_num}"
    
    if card_sheet_name not in all_sheets:
        st.warning(f"⚠ لا يوجد شيت باسم {card_sheet_name}")
        return
    
    card_df = all_sheets[card_sheet_name]

    if "view_option" not in st.session_state:
        st.session_state.view_option = "الشريحة الحالية فقط"

    st.subheader("⚙ نطاق العرض")
    view_option = st.radio(
        "اختر نطاق العرض:",
        ("الشريحة الحالية فقط", "كل الشرائح الأقل", "كل الشرائح الأعلى", "نطاق مخصص", "كل الشرائح"),
        horizontal=True,
        key="view_option"
    )

    min_range = st.session_state.get("min_range", max(0, current_tons - 500))
    max_range = st.session_state.get("max_range", current_tons + 500)
    if view_option == "نطاق مخصص":
        col1, col2 = st.columns(2)
        with col1:
            min_range = st.number_input("من (طن):", min_value=0, step=100, value=min_range, key="min_range")
        with col2:
            max_range = st.number_input("إلى (طن):", min_value=min_range, step=100, value=max_range, key="max_range")

    if view_option == "الشريحة الحالية فقط":
        selected_slices = service_plan_df[(service_plan_df["Min_Tones"] <= current_tons) & (service_plan_df["Max_Tones"] >= current_tons)]
    elif view_option == "كل الشرائح الأقل":
        selected_slices = service_plan_df[service_plan_df["Max_Tones"] <= current_tons]
    elif view_option == "كل الشرائح الأعلى":
        selected_slices = service_plan_df[service_plan_df["Min_Tones"] >= current_tons]
    elif view_option == "نطاق مخصص":
        selected_slices = service_plan_df[(service_plan_df["Min_Tones"] >= min_range) & (service_plan_df["Max_Tones"] <= max_range)]
    else:
        selected_slices = service_plan_df.copy()

    if selected_slices.empty:
        st.warning("⚠ لا توجد شرائح مطابقة حسب النطاق المحدد.")
        return

    all_results = []
    for _, current_slice in selected_slices.iterrows():
        slice_min = current_slice["Min_Tones"]
        slice_max = current_slice["Max_Tones"]
        needed_service_raw = current_slice.get("Service", "")
        needed_parts = split_needed_services(needed_service_raw)
        needed_norm = [normalize_name(p) for p in needed_parts]

        mask = (card_df.get("Min_Tones", 0).fillna(0) <= slice_max) & (card_df.get("Max_Tones", 0).fillna(0) >= slice_min)
        matching_rows = card_df[mask]

        if not matching_rows.empty:
            for _, row in matching_rows.iterrows():
                done_services_set = set()
                
                metadata_columns = {
                    "card", "Tones", "Min_Tones", "Max_Tones", "Date", 
                    "Other", "Servised by", "Event", "Correction",
                    "Card", "TONES", "MIN_TONES", "MAX_TONES", "DATE",
                    "OTHER", "EVENT", "CORRECTION", "SERVISED BY",
                    "servised by", "Servised By", 
                    "Serviced by", "Service by", "Serviced By", "Service By",
                    "خدم بواسطة", "تم الخدمة بواسطة", "فني الخدمة"
                }
                
                all_columns = set(card_df.columns)
                service_columns = all_columns - metadata_columns
                
                final_service_columns = set()
                for col in service_columns:
                    col_normalized = normalize_name(col)
                    metadata_normalized = {normalize_name(mc) for mc in metadata_columns}
                    if col_normalized not in metadata_normalized:
                        final_service_columns.add(col)
                
                for col in final_service_columns:
                    val = str(row.get(col, "")).strip()
                    if val and val.lower() not in ["nan", "none", "", "null", "0"]:
                        if val.lower() not in ["no", "false", "not done", "لم تتم", "x", "-"]:
                            done_services_set.add(col)

                current_date = str(row.get("Date", "")).strip() if pd.notna(row.get("Date")) else "-"
                current_tones = str(row.get("Tones", "")).strip() if pd.notna(row.get("Tones")) else "-"
                
                event_value = "-"
                event_columns = ["Event", "EVENT", "event", "Events", "events", "الحدث", "الأحداث"]
                
                for potential_col in event_columns:
                    if potential_col in card_df.columns:
                        value = row.get(potential_col)
                        if pd.notna(value) and str(value).strip() != "":
                            event_value = str(value).strip()
                            break
                
                correction_value = "-"
                correction_columns = ["Correction", "CORRECTION", "correction", "Correct", "correct", "تصحيح", "تصويب"]
                
                for potential_col in correction_columns:
                    if potential_col in card_df.columns:
                        value = row.get(potential_col)
                        if pd.notna(value) and str(value).strip() != "":
                            correction_value = str(value).strip()
                            break
                
                servised_by_value = "-"
                servised_by_columns = [
                    "Servised by", "SERVISED BY", "servised by", "Servised By",
                    "Serviced by", "Service by", "Serviced By", "Service By",
                    "خدم بواسطة", "تم الخدمة بواسطة", "فني الخدمة"
                ]
                
                for potential_col in servised_by_columns:
                    if potential_col in card_df.columns:
                        value = row.get(potential_col)
                        if pd.notna(value) and str(value).strip() != "":
                            servised_by_value = str(value).strip()
                            break

                done_services = sorted(list(done_services_set))
                done_norm = [normalize_name(c) for c in done_services]
                
                not_done = []
                for needed_part, needed_norm_part in zip(needed_parts, needed_norm):
                    if needed_norm_part not in done_norm:
                        not_done.append(needed_part)

                all_results.append({
                    "Card Number": card_num,
                    "Min_Tons": slice_min,
                    "Max_Tons": slice_max,
                    "Service Needed": " + ".join(needed_parts) if needed_parts else "-",
                    "Service Done": ", ".join(done_services) if done_services else "-",
                    "Service Didn't Done": ", ".join(not_done) if not_done else "-",
                    "Tones": current_tones,
                    "Event": event_value,
                    "Correction": correction_value,
                    "Servised by": servised_by_value,
                    "Date": current_date
                })
        else:
            all_results.append({
                "Card Number": card_num,
                "Min_Tons": slice_min,
                "Max_Tons": slice_max,
                "Service Needed": " + ".join(needed_parts) if needed_parts else "-",
                "Service Done": "-",
                "Service Didn't Done": ", ".join(needed_parts) if needed_parts else "-",
                "Tones": "-",
                "Event": "-",
                "Correction": "-",
                "Servised by": "-",
                "Date": "-"
            })

    result_df = pd.DataFrame(all_results).dropna(how="all").reset_index(drop=True)

    st.markdown("### 📋 نتائج الفحص - جميع الأحداث")
    st.dataframe(result_df, use_container_width=True)

    buffer = io.BytesIO()
    result_df.to_excel(buffer, index=False, engine="openpyxl")
    st.download_button(
        label="💾 حفظ النتائج كـ Excel",
        data=buffer.getvalue(),
        file_name=f"Service_Report_Card{card_num}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def separate_mandatory_columns(all_columns):
    """فصل الأعمدة الإلزامية عن الأعمدة العادية"""
    mandatory_cols = [col for col in APP_CONFIG["MANDATORY_COLUMNS"] if col in all_columns]
    regular_cols = [col for col in all_columns if col not in APP_CONFIG["MANDATORY_COLUMNS"]]
    return mandatory_cols, regular_cols

def get_user_permissions(user_role, user_permissions, user_department, current_department):
    """الحصول على صلاحيات المستخدم بناءً على الدور والقسم"""
    if user_department == "all" or user_department == current_department:
        if "all" in user_permissions:
            return {
                "can_input": True,
                "can_view_stats": True,
                "can_edit": True,
                "can_manage_users": True,
                "can_see_tech_support": True
            }
        elif "data_entry" in user_permissions:
            return {
                "can_input": True,
                "can_view_stats": False,
                "can_edit": False,
                "can_manage_users": False,
                "can_see_tech_support": False
            }
        elif "view_stats" in user_permissions:
            return {
                "can_input": False,
                "can_view_stats": True,
                "can_edit": False,
                "can_manage_users": False,
                "can_see_tech_support": False
            }
        elif "edit" in user_permissions:
            return {
                "can_input": True,
                "can_view_stats": True,
                "can_edit": True,
                "can_manage_users": False,
                "can_see_tech_support": False
            }
        elif "view" in user_permissions:
            return {
                "can_input": False,
                "can_view_stats": True,
                "can_edit": False,
                "can_manage_users": False,
                "can_see_tech_support": False
            }
    
    # إذا لم يكن المستخدم مصرح له لهذا القسم
    return {
        "can_input": False,
        "can_view_stats": False,
        "can_edit": False,
        "can_manage_users": False,
        "can_see_tech_support": False
    }

# -------------------------------
# 🖥 الواجهة الرئيسية
# -------------------------------
st.set_page_config(page_title=APP_CONFIG["APP_TITLE"], layout="wide")

# شريط تسجيل الدخول
with st.sidebar:
    st.header("👤 الجلسة")
    if not st.session_state.get("logged_in"):
        if not login_ui():
            st.stop()
    else:
        state = cleanup_sessions(load_state())
        username = st.session_state.username
        
        # استخدام get() للسلامة لتجنب AttributeError
        user_fullname = st.session_state.get("user_fullname", username)
        user_role = st.session_state.get("user_role", "مستخدم")
        user_department = st.session_state.get("user_department", "غير محدد")
        
        rem = remaining_time(state, username)
        if rem:
            mins, secs = divmod(int(rem.total_seconds()), 60)
            st.success(f"👋 {user_fullname} | الدور: {user_role} | ⏳ {mins:02d}:{secs:02d}")
        else:
            logout_action()

    st.markdown("---")
    st.header("🔧 أدوات النظام")
    
    # أزرار التحديث لجميع الأقسام
    st.subheader("🔄 تحديث الملفات")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("مكبس القطن", use_container_width=True):
            if fetch_from_github_requests("cotton"):
                st.success("✅ تم تحديث مكبس القطن")
            else:
                st.error("❌ فشل تحديث مكبس القطن")
    with col2:
        if st.button("CMMS", use_container_width=True):
            if fetch_from_github_requests("cmms"):
                st.success("✅ تم تحديث CMMS")
            else:
                st.error("❌ فشل تحديث CMMS")
    
    if st.button("محطات الإنتاج", use_container_width=True):
        if fetch_from_github_requests("production"):
            st.success("✅ تم تحديث محطات الإنتاج")
        else:
            st.error("❌ فشل تحديث محطات الإنتاج")
    
    if st.button("🗑 مسح الكاش", use_container_width=True):
        try:
            st.cache_data.clear()
            st.success("✅ تم مسح الكاش بنجاح")
            st.rerun()
        except Exception as e:
            st.error(f"❌ خطأ في مسح الكاش: {e}")
    
    st.markdown("---")
    
    # معلومات النظام
    st.header("ℹ معلومات النظام")
    user_department = st.session_state.get("user_department", "غير محدد")
    st.info(f"القسم: {user_department}")
    
    st.markdown("---")
    
    if st.button("🚪 تسجيل الخروج", use_container_width=True, type="primary"):
        logout_action()

# الواجهة الرئيسية
st.title(f"{APP_CONFIG['APP_ICON']} {APP_CONFIG['APP_TITLE']}")

# الحصول على معلومات المستخدم
username = st.session_state.get("username")
user_role = st.session_state.get("user_role", "viewer")
user_permissions = st.session_state.get("user_permissions", [])
user_department = st.session_state.get("user_department", "all")

# إنشاء التبويبات الرئيسية
main_tabs = st.tabs(APP_CONFIG["MAIN_TABS"])

# -------------------------------
# Tab 1: مكبس القطن
# -------------------------------
with main_tabs[0]:
    st.header("🏭 نظام إدارة مكبس القطن")
    
    # التحقق من صلاحيات القسم
    cotton_permissions = get_user_permissions(user_role, user_permissions, user_department, "cotton")
    
    if not cotton_permissions["can_view_stats"] and not cotton_permissions["can_input"]:
        st.warning("⚠ ليس لديك صلاحية للوصول إلى قسم مكبس القطن")
    else:
        # تحميل بيانات القطن
        cotton_df = load_cotton_data()
        
        # إنشاء تبويبات فرعية
        if cotton_permissions["can_input"]:
            cotton_tabs = st.tabs(["📥 إدخال البيانات", "📊 عرض الإحصائيات"])
        else:
            cotton_tabs = st.tabs(["📊 عرض الإحصائيات"])
        
        # تبويب إدخال البيانات
        if cotton_permissions["can_input"] and len(cotton_tabs) > 0:
            with cotton_tabs[0]:
                st.header("📥 إدخال بيانات البالات")
                
                current_shift = get_current_shift()
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                st.info(f"الوردية الحالية: {current_shift} | الوقت: {current_time}")
                
                st.subheader("⚙ إعدادات التاريخ والوردية")
                
                col_set1, col_set2 = st.columns(2)
                
                with col_set1:
                    use_auto_date = st.checkbox("استخدام التاريخ التلقائي", value=True)
                
                with col_set2:
                    use_auto_shift = st.checkbox("استخدام الوردية التلقائية", value=True)
                
                with st.form("data_entry_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        supervisor = st.selectbox("👨‍💼 اختر المشرف:", get_supervisors(), key="supervisor_select")
                        bale_type = st.selectbox("📦 اختر نوع البالة:", get_bale_types(), key="bale_type_select")
                        
                        if not use_auto_date:
                            manual_date = st.date_input("📅 اختر التاريخ:", value=datetime.now().date())
                        else:
                            manual_date = None
                    
                    with col2:
                        weight = st.number_input("⚖ وزن البالة (كجم):", min_value=0.0, step=0.1, key="weight_input")
                        notes = st.text_input("📝 ملاحظات (اختياري):", key="notes_input")
                        
                        if not use_auto_shift:
                            manual_shift = st.selectbox("🕐 اختر الوردية:", list(APP_CONFIG["SHIFTS"].keys()))
                        else:
                            manual_shift = None
                    
                    submitted = st.form_submit_button("💾 حفظ البيانات")
                    
                    if submitted:
                        if weight <= 0:
                            st.error("❌ يرجى إدخال وزن صحيح للبالة")
                        else:
                            new_record, updated_df = add_new_record(
                                cotton_df, supervisor, bale_type, weight, notes, 
                                manual_date, manual_shift
                            )
                            
                            commit_msg = f"إضافة بالة {bale_type} وزن {weight} كجم بواسطة {supervisor}"
                            if save_cotton_data(updated_df, commit_msg):
                                st.success(f"✅ تم حفظ بيانات البالة بنجاح!")
                                st.json({
                                    "نوع البالة": new_record['نوع البالة'],
                                    "الوزن": f"{new_record['وزن البالة']} كجم",
                                    "المشرف": new_record['المشرف'],
                                    "الوردية": new_record['الوردية'],
                                    "التاريخ": str(new_record['التاريخ']),
                                    "الوقت": str(new_record['الوقت'])
                                })
                                st.rerun()
        
        # تبويب عرض الإحصائيات
        if len(cotton_tabs) > (0 if cotton_permissions["can_input"] else 0):
            stats_tab_index = 1 if cotton_permissions["can_input"] else 0
            
            with cotton_tabs[stats_tab_index]:
                st.header("📊 عرض الإحصائيات المتقدمة")
                
                if cotton_df.empty:
                    st.warning("⚠ لا توجد بيانات لعرضها")
                else:
                    st.subheader("🔍 تصفية البيانات")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        start_date = st.date_input("من تاريخ:", value=datetime.now().date() - timedelta(days=7), key="cotton_start_date")
                        end_date = st.date_input("إلى تاريخ:", value=datetime.now().date(), key="cotton_end_date")
                        
                        st.write("### 🕐 اختيار الورديات:")
                        all_shifts = st.checkbox("جميع الورديات", value=True, key="cotton_all_shifts")
                        if all_shifts:
                            selected_shifts = list(APP_CONFIG["SHIFTS"].keys())
                        else:
                            selected_shifts = st.multiselect(
                                "اختر الورديات:",
                                list(APP_CONFIG["SHIFTS"].keys()),
                                default=list(APP_CONFIG["SHIFTS"].keys()),
                                key="cotton_shifts"
                            )
                    
                    with col2:
                        st.write("### 📦 اختيار أنواع البالات:")
                        all_bales = st.checkbox("جميع أنواع البالات", value=True, key="cotton_all_bales")
                        if all_bales:
                            selected_bale_types = get_bale_types()
                        else:
                            selected_bale_types = st.multiselect(
                                "اختر أنواع البالات:",
                                get_bale_types(),
                                default=get_bale_types(),
                                key="cotton_bale_types"
                            )
                        
                        st.write("### ⚙ خيارات إضافية:")
                        calculate_percentage = st.checkbox(
                            "حساب النسبة المئوية مقابل قطن خام", 
                            value=True,
                            help="سيتم حساب نسبة كل نوع من البالات مقابل إجمالي وزن قطن الخام",
                            key="cotton_percentage"
                        )
                    
                    if st.button("🔄 توليد الإحصائيات", type="primary", key="cotton_generate_stats"):
                        stats_df = generate_advanced_statistics(
                            cotton_df, start_date, end_date, 
                            selected_shifts, selected_bale_types, 
                            calculate_percentage
                        )
                        
                        if not stats_df.empty:
                            st.subheader(f"📈 الإحصائيات للفترة من {start_date} إلى {end_date}")
                            
                            st.info(f"""
                            معلومات التصفية:
                            - الورديات: {', '.join(selected_shifts) if selected_shifts else 'جميع الورديات'}
                            - أنواع البالات: {len(selected_bale_types)} نوع
                            - حساب النسبة المئوية: {'نعم' if calculate_percentage else 'لا'}
                            """)
                            
                            st.dataframe(stats_df, use_container_width=True)
                            
                            total_bales = stats_df['عدد البالات'].sum()
                            total_weight = stats_df['إجمالي الوزن'].sum()
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("🔄 إجمالي عدد البالات", f"{total_bales:,}")
                            with col2:
                                st.metric("⚖ إجمالي الوزن", f"{total_weight:,.1f} كجم")
                            with col3:
                                avg_weight = total_weight / total_bales if total_bales > 0 else 0
                                st.metric("📊 متوسط الوزن للبالة", f"{avg_weight:.1f} كجم")

# -------------------------------
# Tab 2: CMMS
# -------------------------------
with main_tabs[1]:
    st.header("🛠 نظام CMMS - إدارة صيانة الماكينات")
    
    # التحقق من صلاحيات القسم
    cmms_permissions = get_user_permissions(user_role, user_permissions, user_department, "cmms")
    
    if not cmms_permissions["can_view_stats"] and not cmms_permissions["can_edit"]:
        st.warning("⚠ ليس لديك صلاحية للوصول إلى قسم CMMS")
    else:
        # تحميل بيانات CMMS
        cmms_sheets = load_all_sheets("cmms")
        cmms_sheets_edit = load_sheets_for_edit("cmms")
        
        # إنشاء تبويبات فرعية
        cmms_tabs = st.tabs(["📊 فحص الماكينات", "🛠 تعديل البيانات"])
        
        # تبويب فحص الماكينات
        with cmms_tabs[0]:
            st.header("📊 فحص حالة الماكينات")
            
            if cmms_sheets is None:
                st.warning("❗ الملف المحلي غير موجود. استخدم زر التحديث في الشريط الجانبي لتحميل الملف من GitHub.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    card_num = st.number_input("رقم الماكينة:", min_value=1, step=1, key="cmms_card_num")
                with col2:
                    current_tons = st.number_input("عدد الأطنان الحالية:", min_value=0, step=100, key="cmms_current_tons")

                if st.button("عرض الحالة", key="cmms_check_status"):
                    st.session_state["cmms_show_results"] = True

                if st.session_state.get("cmms_show_results", False):
                    check_machine_status(card_num, current_tons, cmms_sheets)
        
        # تبويب تعديل البيانات
        if cmms_permissions["can_edit"]:
            with cmms_tabs[1]:
                st.header("🛠 تعديل وإدارة البيانات CMMS")

                if not cmms_sheets_edit:
                    st.warning("⚠ لا توجد بيانات متاحة. يرجى تحديث الملف من GitHub.")
                else:
                    available_sheets = list(cmms_sheets_edit.keys())
                    selected_sheet = st.selectbox(
                        "📋 اختر الشيت للتعديل:",
                        available_sheets,
                        key="cmms_edit_sheet"
                    )
                    
                    if selected_sheet:
                        df = cmms_sheets_edit[selected_sheet].astype(str)
                        
                        st.subheader(f"تعديل بيانات {selected_sheet}")
                        
                        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, 
                                                 key=f"cmms_editor_{selected_sheet}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("💾 حفظ التغييرات", type="primary", key=f"cmms_save_{selected_sheet}"):
                                if not edited_df.equals(df):
                                    cmms_sheets_edit[selected_sheet] = edited_df.astype(object)
                                    new_sheets = auto_save_to_github(
                                        cmms_sheets_edit, "cmms",
                                        f"تعديل تلقائي في شيت {selected_sheet} - CMMS"
                                    )
                                    if new_sheets is not None:
                                        cmms_sheets_edit = new_sheets
                                        st.success("✅ تم الحفظ بنجاح على GitHub")
                                        st.rerun()
                                else:
                                    st.info("⚠ لم يتم إجراء أي تغييرات للحفظ")
                        
                        with col2:
                            if st.button("🔄 إعادة تحميل", key=f"cmms_reload_{selected_sheet}"):
                                st.rerun()

# -------------------------------
# Tab 3: محطات الإنتاج
# -------------------------------
with main_tabs[2]:
    st.header("🏗 نظام إدارة محطات الإنتاج")
    
    # التحقق من صلاحيات القسم
    production_permissions = get_user_permissions(user_role, user_permissions, user_department, "production")
    
    if not production_permissions["can_view_stats"] and not production_permissions["can_edit"]:
        st.warning("⚠ ليس لديك صلاحية للوصول إلى قسم محطات الإنتاج")
    else:
        # تحميل بيانات محطات الإنتاج
        production_data = load_all_sheets("production")
        production_sheets_edit = load_sheets_for_edit("production")
        
        # إنشاء تبويبات فرعية
        production_tabs = st.tabs(["📊 عرض المحطات", "✏ تعديل البيانات"])
        
        # تبويب عرض المحطات
        with production_tabs[0]:
            st.header("📊 عرض بيانات المحطات")
            
            if not production_data:
                st.warning("⚠ لا توجد بيانات متاحة. يرجى تحديث الملف من GitHub أو إضافة بيانات جديدة.")
            else:
                available_sheets = list(production_data.keys())
                selected_sheet = st.selectbox(
                    "📋 اختر المحطة أو القسم:",
                    available_sheets,
                    key="production_view_sheet"
                )
                
                if selected_sheet:
                    df = production_data[selected_sheet]
                    
                    st.subheader(f"بيانات {selected_sheet}")
                    
                    # تخصيص الأعمدة المعروضة
                    st.subheader("🎛 تخصيص الأعمدة المعروضة")
                    
                    all_columns = list(df.columns)
                    mandatory_columns, regular_columns = separate_mandatory_columns(all_columns)
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        show_all_columns = st.checkbox("عرض جميع الأعمدة", value=True, key="production_show_all")
                    
                    with col2:
                        custom_columns = st.checkbox("تخصيص الأعمدة", value=False, key="production_custom_cols")
                    
                    with col3:
                        if st.button("🔄 إعادة تعيين", use_container_width=True, key="production_reset"):
                            if 'production_selected_columns' in st.session_state:
                                del st.session_state.production_selected_columns
                            st.rerun()
                    
                    if show_all_columns:
                        display_columns = all_columns
                        st.success("🔍 يتم عرض جميع الأعمدة")
                    elif custom_columns:
                        selected_regular_columns = st.multiselect(
                            "الأعمدة المتاحة:",
                            options=regular_columns,
                            default=regular_columns[:min(5, len(regular_columns))] if 'production_selected_columns' not in st.session_state else st.session_state.production_selected_columns,
                            key="production_column_selector",
                            placeholder="اختر الأعمدة التي تريد عرضها...",
                            label_visibility="collapsed"
                        )
                        
                        display_columns = mandatory_columns + selected_regular_columns
                        st.session_state.production_selected_columns = selected_regular_columns
                        
                        if not display_columns:
                            st.warning("⚠ لم تختر أي أعمدة للعرض. سيتم عرض جميع الأعمدة.")
                            display_columns = all_columns
                    else:
                        display_columns = all_columns
                    
                    if display_columns:
                        ordered_columns = [col for col in display_columns if col in mandatory_columns] + \
                                        [col for col in display_columns if col not in mandatory_columns]
                        
                        st.subheader("📄 البيانات المعروضة")
                        st.dataframe(
                            df[ordered_columns], 
                            use_container_width=True, 
                            height=400,
                            hide_index=True
                        )
        
        # تبويب تعديل البيانات
        if production_permissions["can_edit"]:
            with production_tabs[1]:
                st.header("✏ تعديل بيانات المحطات")
                
                if not production_sheets_edit:
                    st.warning("⚠ لا توجد بيانات متاحة. يرجى تحديث الملف من GitHub.")
                else:
                    available_sheets = list(production_sheets_edit.keys())
                    selected_sheet = st.selectbox(
                        "📋 اختر المحطة أو القسم للتعديل:",
                        available_sheets,
                        key="production_edit_sheet"
                    )
                    
                    if selected_sheet:
                        original_df = production_sheets_edit[selected_sheet]
                        
                        st.subheader(f"تعديل بيانات {selected_sheet}")
                        
                        all_columns = list(original_df.columns)
                        mandatory_columns, regular_columns = separate_mandatory_columns(all_columns)
                        
                        ordered_columns = mandatory_columns + [col for col in all_columns if col not in mandatory_columns]
                        df_reordered = original_df[ordered_columns]
                        
                        edited_df = st.data_editor(
                            df_reordered,
                            use_container_width=True,
                            height=500,
                            num_rows="dynamic",
                            key=f"production_editor_{selected_sheet}",
                            column_config={
                                col: st.column_config.TextColumn(
                                    col,
                                    help=f"يمكنك إدخال أي نوع من البيانات في عمود {col}"
                                ) for col in df_reordered.columns
                            }
                        )
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("💾 حفظ التغييرات", type="primary", key=f"production_save_{selected_sheet}"):
                                production_sheets_edit[selected_sheet] = edited_df
                                new_sheets = auto_save_to_github(
                                    production_sheets_edit, "production",
                                    f"تعديل تلقائي في شيت {selected_sheet} - محطات الإنتاج"
                                )
                                if new_sheets is not None:
                                    production_sheets_edit = new_sheets
                                    st.success("✅ تم الحفظ بنجاح على GitHub")
                                    st.rerun()
                        
                        with col2:
                            if st.button("🔄 إعادة تحميل", key=f"production_reload_{selected_sheet}"):
                                st.rerun()

# -------------------------------
# Tab 4: إدارة النظام
# -------------------------------
with main_tabs[3]:
    st.header("👥 إدارة النظام والمستخدمين")
    
    # التحقق من صلاحيات إدارة النظام
    if user_role != "admin" and "all" not in user_permissions:
        st.warning("⚠ ليس لديك صلاحية للوصول إلى إدارة النظام")
    else:
        users = load_users()
        
        st.subheader("📋 المستخدمين الحاليين")
        if users:
            user_data = []
            for username, info in users.items():
                user_data.append({
                    "اسم المستخدم": username,
                    "الاسم الكامل": info.get("full_name", username),
                    "الدور": info.get("role", "user"),
                    "القسم": info.get("department", "all"),
                    "الصلاحيات": ", ".join(info.get("permissions", [])),
                    "تاريخ الإنشاء": info.get("created_at", "غير معروف")
                })
            
            users_df = pd.DataFrame(user_data)
            st.dataframe(users_df, use_container_width=True)
        
        st.subheader("➕ إضافة مستخدم جديد")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_username = st.text_input("اسم المستخدم الجديد:", key="new_username")
            new_fullname = st.text_input("الاسم الكامل:", key="new_fullname")
        with col2:
            new_password = st.text_input("كلمة المرور:", type="password", key="new_password")
            confirm_password = st.text_input("تأكيد كلمة المرور:", type="password", key="confirm_password")
        with col3:
            user_role = st.selectbox("الدور:", ["admin", "data_entry", "editor", "viewer"], key="new_user_role")
            user_department = st.selectbox("القسم:", ["all", "cotton", "cmms", "production"], key="new_user_department")
        
        if st.button("إضافة مستخدم", type="primary", key="add_user_btn"):
            if not new_username.strip():
                st.warning("⚠ يرجى إدخال اسم المستخدم.")
            elif not new_password.strip():
                st.warning("⚠ يرجى إدخال كلمة المرور.")
            elif new_password != confirm_password:
                st.warning("⚠ كلمتا المرور غير متطابقتين.")
            elif new_username in users:
                st.warning("⚠ هذا المستخدم موجود بالفعل.")
            else:
                # تحديد الصلاحيات بناءً على الدور
                if user_role == "admin":
                    permissions_list = ["all"]
                elif user_role == "data_entry":
                    permissions_list = ["data_entry"]
                elif user_role == "editor":
                    permissions_list = ["view", "edit"]
                else:  # viewer
                    permissions_list = ["view_stats"]
                
                users[new_username] = {
                    "password": new_password,
                    "role": user_role,
                    "permissions": permissions_list,
                    "created_at": datetime.now().isoformat(),
                    "full_name": new_fullname or new_username,
                    "department": user_department
                }
                if save_users(users):
                    st.success(f"✅ تم إضافة المستخدم '{new_username}' بنجاح.")
                    st.rerun()
        
        st.subheader("🗑 حذف مستخدم")
        
        if len(users) > 1:
            user_to_delete = st.selectbox(
                "اختر مستخدم للحذف:",
                [u for u in users.keys() if u != "admin"],
                key="delete_user_select"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                confirm_delete = st.checkbox("✅ تأكيد الحذف", key="confirm_user_delete")
            with col2:
                if st.button("حذف المستخدم", key="delete_user_btn"):
                    if not confirm_delete:
                        st.warning("⚠ يرجى تأكيد الحذف أولاً.")
                    elif user_to_delete == "admin":
                        st.error("❌ لا يمكن حذف المستخدم admin.")
                    elif user_to_delete == st.session_state.get("username"):
                        st.error("❌ لا يمكن حذف حسابك أثناء تسجيل الدخول.")
                    else:
                        if user_to_delete in users:
                            del users[user_to_delete]
                            if save_users(users):
                                st.success(f"✅ تم حذف المستخدم '{user_to_delete}' بنجاح.")
                                st.rerun()

# -------------------------------
# Tab 5: الدعم الفني
# -------------------------------
with main_tabs[4]:
    st.header("📞 الدعم الفني")
    
    st.markdown("## 🛠 معلومات التطوير والدعم")
    st.markdown("تم تطوير هذا التطبيق بواسطة:")
    st.markdown("### م. محمد عبدالله")
    st.markdown("### رئيس قسم الكرد والمحطات")
    st.markdown("### مصنع بيل يارن للغزل")
    
    st.markdown("---")
    st.markdown("### معلومات الاتصال:")
    st.markdown("- 📧 البريد الإلكتروني: medotatch124@gmail.com")
    st.markdown("- 📞 هاتف: 01274424062")
    st.markdown("- 🏢 الموقع: مصنع بيل يارن للغزل")
    
    st.markdown("---")
    st.markdown("### خدمات الدعم الفني:")
    st.markdown("- 🔧 صيانة وتحديث النظام")
    st.markdown("- 📊 تطوير تقارير إضافية")
    st.markdown("- 🐛 إصلاح الأخطاء والمشكلات")
    st.markdown("- 💡 استشارات فنية وتقنية")
    
    st.markdown("---")
    st.markdown("### إصدار النظام:")
    st.markdown("- الإصدار: 4.0 (متكامل)")
    st.markdown("- آخر تحديث: 2024")
    st.markdown("- النظام: نظام إدارة بيل يارن المتكامل")
    
    st.success("""
    مميزات النظام المتكامل:
    - ✅ نظام مكبس القطن - إدارة البالات والإنتاج
    - ✅ نظام CMMS - إدارة صيانة الماكينات
    - ✅ نظام محطات الإنتاج - إدارة المحطات والأقسام
    - ✅ إدارة مستخدمين متقدمة مع صلاحيات لكل قسم
    - ✅ الحفظ التلقائي على GitHub
    - ✅ دعم كامل للغة العربية
    """)
    
    # أزرار فنية
    st.markdown("### 🔧 أدوات فنية")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("فحص اتصال GitHub", use_container_width=True):
            if fetch_from_github_requests("cotton"):
                st.success("✅ الاتصال مع GitHub يعمل بشكل صحيح")
            else:
                st.error("❌ هناك مشكلة في الاتصال مع GitHub")
    with col2:
        if st.button("فحص المستخدمين", use_container_width=True):
            users = load_users()
            st.success(f"✅ تم تحميل {len(users)} مستخدم")
    with col3:
        if st.button("معلومات الجلسة", use_container_width=True):
            st.json({
                "المستخدم": st.session_state.get("username"),
                "الدور": st.session_state.get("user_role"),
                "القسم": st.session_state.get("user_department"),
                "الصلاحيات": st.session_state.get("user_permissions")
            })

# -------------------------------
# تذييل الصفحة
# -------------------------------
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption(f"👤 {st.session_state.get('user_fullname', 'زائر')}")
with footer_col2:
    st.caption(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with footer_col3:
    st.caption("مصنع بيل يارن للغزل © 2024")
