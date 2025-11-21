import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="النظام الموحد - مصنع بيل يارن",
    page_icon="🏭",
    layout="wide"
)

# ملف المستخدمين
USERS_FILE = "unified_users.json"

# تحميل المستخدمين
def load_users():
    if not os.path.exists(USERS_FILE):
        # إنشاء مستخدمين افتراضيين
        default_users = {
            "admin": {
                "password": "admin123",
                "role": "super_admin",
                "department": "all",
                "full_name": "المسؤول العام",
                "created_at": datetime.now().isoformat()
            },
            "cotton_admin": {
                "password": "cotton123", 
                "role": "department_admin",
                "department": "cotton",
                "full_name": "مدير مكبس القطن",
                "created_at": datetime.now().isoformat()
            },
            "cmms_admin": {
                "password": "cmms123",
                "role": "department_admin", 
                "department": "cmms",
                "full_name": "مدير الصيانة",
                "created_at": datetime.now().isoformat()
            },
            "production_admin": {
                "password": "production123",
                "role": "department_admin",
                "department": "production", 
                "full_name": "مدير المحطات",
                "created_at": datetime.now().isoformat()
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=4, ensure_ascii=False)
        return default_users
    
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# حفظ المستخدمين
def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

# واجهة تسجيل الدخول
def login_section():
    st.sidebar.title("🔐 تسجيل الدخول")
    
    users = load_users()
    
    username = st.sidebar.text_input("اسم المستخدم")
    password = st.sidebar.text_input("كلمة المرور", type="password")
    
    if st.sidebar.button("تسجيل الدخول", use_container_width=True):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_role = users[username]["role"]
            st.session_state.user_department = users[username]["department"]
            st.session_state.user_fullname = users[username]["full_name"]
            st.sidebar.success(f"مرحباً {users[username]['full_name']}!")
            st.rerun()
        else:
            st.sidebar.error("اسم المستخدم أو كلمة المرور غير صحيحة")
    
    return False

# تسجيل الخروج
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.user_department = None
    st.rerun()

# إدارة المستخدمين (للمسؤولين فقط)
def user_management_section():
    st.header("👥 إدارة المستخدمين")
    
    users = load_users()
    
    # عرض المستخدمين الحاليين
    st.subheader("المستخدمين الحاليين")
    user_data = []
    for username, info in users.items():
        user_data.append({
            "اسم المستخدم": username,
            "الاسم الكامل": info["full_name"],
            "الدور": info["role"],
            "القسم": info["department"],
            "تاريخ الإنشاء": info["created_at"][:10]
        })
    
    if user_data:
        st.dataframe(user_data, use_container_width=True)
    else:
        st.info("لا يوجد مستخدمين مسجلين")
    
    # إضافة مستخدم جديد
    st.subheader("إضافة مستخدم جديد")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_username = st.text_input("اسم المستخدم الجديد")
        new_fullname = st.text_input("الاسم الكامل")
        new_password = st.text_input("كلمة المرور", type="password")
    
    with col2:
        new_role = st.selectbox("الدور", ["super_admin", "department_admin", "editor", "viewer"])
        
        # تحديد القسم بناءً على الدور والصلاحيات
        if new_role == "super_admin":
            new_department = "all"
        elif st.session_state.user_role == "super_admin":
            new_department = st.selectbox("القسم", ["cotton", "cmms", "production"])
        else:
            new_department = st.session_state.user_department
        
        st.info(f"سيتم تعيين المستخدم في قسم: {new_department}")
    
    if st.button("إضافة المستخدم", type="primary"):
        if not new_username or not new_password:
            st.error("يرجى ملء جميع الحقول المطلوبة")
        elif new_username in users:
            st.error("اسم المستخدم موجود مسبقاً")
        else:
            users[new_username] = {
                "password": new_password,
                "role": new_role,
                "department": new_department,
                "full_name": new_fullname,
                "created_at": datetime.now().isoformat(),
                "created_by": st.session_state.username
            }
            
            if save_users(users):
                st.success(f"تم إضافة المستخدم {new_username} بنجاح")
                st.rerun()
            else:
                st.error("حدث خطأ أثناء حفظ البيانات")

# الواجهة الرئيسية
def main_dashboard():
    st.title("🏭 النظام الموحد - مصنع بيل يارن")
    st.write(f"مرحباً **{st.session_state.user_fullname}** - {st.session_state.user_role}")
    
    # التطبيقات المتاحة
    APPS = {
        "🛠 نظام CMMS - إدارة الصيانة": {
            "url": "https://belyarn-bcrsa3jbnnf9zxcckgamay.streamlit.app",
            "department": "cmms",
            "description": "نظام متكامل لإدارة صيانة الماكينات والمعدات"
        },
        "📦 نظام مكبس القطن - LUVA": {
            "url": "https://n6bzfju5rcafprtxvaiaqj.streamlit.app",
            "department": "cotton", 
            "description": "نظام متخصص لمتابعة إنتاج مكبس القطن وإدارة البالات"
        },
        "🏭 نظام محطات الإنتاج - Maintain Luva": {
            "url": "https://maintain-luva-lpm83s3ivkpmudngvjy2zz.streamlit.app",
            "department": "production",
            "description": "نظام شامل لمتابعة محطات الإنتاج المختلفة"
        }
    }
    
    st.subheader("🎯 التطبيقات المتاحة")
    
    # تصفية التطبيقات بناءً على صلاحيات المستخدم
    available_apps = {}
    for app_name, app_info in APPS.items():
        if (st.session_state.user_role == "super_admin" or 
            st.session_state.user_department == "all" or
            st.session_state.user_department == app_info["department"]):
            available_apps[app_name] = app_info
    
    # عرض التطبيقات المتاحة
    cols = st.columns(min(3, len(available_apps)))
    
    for i, (app_name, app_info) in enumerate(available_apps.items()):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 10px; text-align: center; margin: 10px 0;">
                <h3>{app_name}</h3>
                <p>{app_info['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"الدخول إلى {app_name}", key=f"app_{i}", use_container_width=True):
                st.success(f"جاري تحويلك إلى {app_name}...")
                st.markdown(f'<meta http-equiv="refresh" content="0; url={app_info["url"]}">', unsafe_allow_html=True)
                st.markdown(f"[اضغط هنا إذا لم يتم التوجيه تلقائياً]({app_info['url']})")
    
    if not available_apps:
        st.warning("⚠ لا توجد تطبيقات متاحة لصلاحياتك الحالية")

# تبويب الدعم الفني
def tech_support_section():
    st.header("📞 الدعم الفني")
    
    st.markdown("""
    ### 🛠 معلومات التطوير والدعم
    
    **تم تطوير هذا النظام بواسطة:**
    - **م. محمد عبدالله**
    - **رئيس قسم الكرد والمحطات** 
    - **مصنع بيل يارن للغزل**
    
    ---
    
    ### 📞 معلومات الاتصال:
    - 📧 البريد الإلكتروني: medotatch124@gmail.com
    - 📞 هاتف: 01274424062
    - 🏢 الموقع: مصنع بيل يارن للغزل
    
    ---
    
    ### 🔧 خدمات الدعم الفني:
    - صيانة وتحديث النظام
    - تطوير تقارير إضافية
    - إصلاح الأخطاء والمشكلات
    - استشارات فنية وتقنية
    
    ---
    
    ### 📋 إصدار النظام:
    - الإصدار: 2.0 (النظام الموحد)
    - آخر تحديث: 2024
    - النظام: نظام إدارة بيل يارن المتكامل
    """)
    
    # معلومات إضافية
    st.subheader("🔍 حالة النظام")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        users = load_users()
        st.metric("عدد المستخدمين", len(users))
    
    with col2:
        st.metric("عدد التطبيقات", "3 تطبيقات")
    
    with col3:
        st.metric("حالة النظام", "🟢 يعمل بشكل طبيعي")

# التهيئة الأولية
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.user_department = None
    st.session_state.user_fullname = None

# الواجهة الرئيسية
if not st.session_state.logged_in:
    # عرض واجهة تسجيل الدخول
    st.title("🏭 النظام الموحد - مصنع بيل يارن")
    st.write("### 🔐 يرجى تسجيل الدخول للوصول إلى النظام")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/869/869636.png", width=150)
        
        # معلومات النظام
        st.markdown("""
        ### ℹ️ معلومات سريعة:
        - 3 تطبيقات متكاملة
        - نظام مستخدمين متقدم
        - دعم فني متكامل
        - تحديثات مستمرة
        """)
    
    with col2:
        login_section()
        
        # معلومات المستخدمين الافتراضيين (للتجربة فقط)
        with st.expander("👥 معلومات المستخدمين الافتراضيين (للتجربة)"):
            st.code("""
            المسؤول العام:
            - المستخدم: admin
            - كلمة المرور: admin123
            
            مدير مكبس القطن:
            - المستخدم: cotton_admin  
            - كلمة المرور: cotton123
            
            مدير الصيانة:
            - المستخدم: cmms_admin
            - كلمة المرور: cmms123
            
            مدير المحطات:
            - المستخدم: production_admin
            - كلمة المرور: production123
            """)
    
    # تذييل الصفحة
    st.markdown("---")
    st.caption("مصنع بيل يارن للغزل © 2024 | نظام الإدارة المتكامل")

else:
    # الشريط الجانبي للمستخدم المسجل
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_fullname}")
        st.write(f"**الدور:** {st.session_state.user_role}")
        st.write(f"**القسم:** {st.session_state.user_department}")
        
        st.markdown("---")
        
        # قائمة التنقل
        st.subheader("🔍 التنقل")
        page = st.radio("اختر الصفحة:", ["🏠 الرئيسية", "👥 إدارة المستخدمين", "📞 الدعم الفني"])
        
        st.markdown("---")
        
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            logout()
    
    # عرض الصفحة المختارة
    if page == "🏠 الرئيسية":
        main_dashboard()
    elif page == "👥 إدارة المستخدمين":
        # التحقق من الصلاحيات
        if st.session_state.user_role in ["super_admin", "department_admin"]:
            user_management_section()
        else:
            st.warning("⚠ ليس لديك صلاحية للوصول إلى إدارة المستخدمين")
    elif page == "📞 الدعم الفني":
        tech_support_section()
    
    # تذييل الصفحة
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    with footer_col1:
        st.caption(f"👤 {st.session_state.user_fullname}")
    with footer_col2:
        st.caption(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    with footer_col3:
        st.caption("مصنع بيل يارن للغزل © 2024")
