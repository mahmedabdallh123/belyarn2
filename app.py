import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="النظام الموحد - مصنع بيل يارن",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص التصميم
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e86ab;
        text-align: center;
        margin-bottom: 2rem;
    }
    .app-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .app-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-online {
        background-color: #00ff00;
    }
    .status-offline {
        background-color: #ff4444;
    }
    .feature-list {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
st.markdown('<h1 class="main-header">🏭 النظام الموحد - مصنع بيل يارن</h1>', unsafe_allow_html=True)
st.markdown('<h2 class="sub-header">منصة إدارة متكاملة لجميع أقسام المصنع</h2>', unsafe_allow_html=True)

# معلومات النظام في الشريط الجانبي
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/869/869636.png", width=100)
    st.title("معلومات النظام")
    
    st.metric("التاريخ والوقت", datetime.now().strftime("%Y-%m-%d %H:%M"))
    st.metric("عدد التطبيقات", "3 تطبيقات")
    
    st.markdown("---")
    st.subheader("📞 الدعم الفني")
    st.write("""
    **م. محمد عبدالله**  
    رئيس قسم الكرد والمحطات  
    📧 medotatch124@gmail.com  
    📞 01274424062
    """)
    
    st.markdown("---")
    st.subheader("🔄 تحديثات النظام")
    st.info("""
    - الإصدار: 2.0 (الواجهة الموحدة)
    - آخر تحديث: 2024
    - جميع الحقوق محفوظة ©
    """)

# تعريف التطبيقات مع معلومات موسعة
APPS = {
    "🛠 نظام CMMS - إدارة الصيانة": {
        "url": "https://belyarn-bcrsa3jbnnf9zxcckgamay.streamlit.app",
        "description": "نظام متكامل لإدارة صيانة الماكينات والمعدات في المصنع",
        "features": [
            "فحص حالة الماكينات",
            "إدارة خطط الصيانة الدورية", 
            "تسجيل أعمال الصيانة",
            "متابعة قطع الغيار",
            "تقارير أداء المعدات"
        ],
        "department": "قسم الصيانة",
        "icon": "🛠️",
        "color": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    "📦 نظام مكبس القطن - LUVA": {
        "url": "https://n6bzfju5rcafprtxvaiaqj.streamlit.app",
        "description": "نظام متخصص لمتابعة إنتاج مكبس القطن وإدارة البالات",
        "features": [
            "تسجيل بيانات البالات",
            "إدارة الورديات والإنتاج",
            "إحصائيات متقدمة",
            "متابعة المخزون", 
            "تقارير الجودة"
        ],
        "department": "قسم مكبس القطن",
        "icon": "📦",
        "color": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
    },
    "🏭 نظام محطات الإنتاج - Maintain Luva": {
        "url": "https://maintain-luva-lpm83s3ivkpmudngvjy2zz.streamlit.app", 
        "description": "نظام شامل لمتابعة محطات الإنتاج المختلفة وإدارة العمليات التشغيلية",
        "features": [
            "مراقبة محطات الإنتاج",
            "إدارة العمليات التشغيلية",
            "متابعة الجودة",
            "تقارير الأداء",
            "إدارة الطاقة الإنتاجية"
        ],
        "department": "قسم التشغيل",
        "icon": "🏭",
        "color": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
    }
}

# دالة للتحقق من حالة التطبيق
def check_app_status(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

# قسم اختيار التطبيق
st.subheader("🎯 اختر التطبيق الذي تريد الدخول إليه")

# استخدام أعمدة لعرض التطبيقات
cols = st.columns(3)

for i, (app_name, app_info) in enumerate(APPS.items()):
    with cols[i]:
        # التحقق من حالة التطبيق
        is_online = check_app_status(app_info["url"])
        
        # بطاقة التطبيق
        st.markdown(f"""
        <div class="app-card" style="background: {app_info['color']};">
            <h3>{app_info['icon']} {app_name}</h3>
            <p><strong>القسم:</strong> {app_info['department']}</p>
            <div class="feature-list">
                <strong>المميزات:</strong>
                <ul>
                    {"".join([f"<li>{feature}</li>" for feature in app_info['features']])}
                </ul>
            </div>
            <p>
                <span class="status-indicator {'status-online' if is_online else 'status-offline'}"></span>
                الحالة: {'🟢 متصل' if is_online else '🔴 غير متصل'}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # زر الدخول
        if st.button(f"الدخول إلى {app_name}", key=f"btn_{i}", use_container_width=True):
            st.success(f"جاري تحويلك إلى {app_name}...")
            st.markdown(f'<meta http-equiv="refresh" content="0; url={app_info["url"]}">', unsafe_allow_html=True)
            st.markdown(f"[اضغط هنا إذا لم يتم التوجيه تلقائياً]({app_info['url']})")

# قسم إضافي للمعلومات
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 إحصائيات سريعة")
    st.metric("إجمالي التطبيقات", "3")
    st.metric("التطبيقات النشطة", f"{sum(1 for app in APPS.values() if check_app_status(app['url']))}")
    st.metric("الأقسام المغطاة", "3 أقسام")

with col2:
    st.subheader("🎯 مميزات النظام الموحد")
    st.write("""
    - ✅ واجهة موحدة لجميع التطبيقات
    - 🔄 تحديث فوري لحالة التطبيقات  
    - 🛠 دعم فني متكامل
    - 📱 تصميم متجاوب لجميع الأجهزة
    - 🔒 أمن وسرية البيانات
    """)

with col3:
    st.subheader("🚀 دليل سريع")
    st.write("""
    1. اختر التطبيق المناسب من الأعلى
    2. اضغط على زر 'الدخول إلى التطبيق'
    3. سيتم تحويلك تلقائياً
    4. في حالة وجود مشكلة، استخدم رابط البديل
    """)

# رسالة تذكير في الأسفل
st.markdown("---")
st.info("""
💡 **ملاحظة مهمة**: تأكد من أنك مسجل الدخول في النظام وأن لديك الصلاحيات المناسبة للوصول إلى التطبيقات. 
في حالة مواجهة أي مشاكل تقنية، يرجى التواصل مع الدعم الفني.
""")

# تذييل الصفحة
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("🏭 مصنع بيل يارن للغزل")
with footer_col2:
    st.caption(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with footer_col3:
    st.caption("جميع الحقوق محفوظة © 2024")
