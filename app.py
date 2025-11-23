import streamlit as st

st.set_page_config(
    page_title="Unified Dashboard",
    page_icon="🧭",
    layout="centered"
)

st.title("🧭 النظام الموحد لتطبيقات المصنع")
st.write("اختر القسم الذي تريد الدخول إليه 👇")

APPS = {
    "🛠 BELYARN – نظام الصيانة": 
        "https://belyarn-bcrsa3jbnnf9zxcckgamay.streamlit.app",

    "📦 نظام مكبس القطن (LUVA)": 
        "https://n6bzfju5rcafprtxvaiaqj.streamlit.app",

    "🏭 نظام محطات الإنتاج (Maintain-Luva)": 
        "https://maintain-luva-lpm83s3ivkpmudngvjy2zz.streamlit.app",
}

choice = st.selectbox("اختر التطبيق:", list(APPS.keys()))

if st.button("فتح التطبيق"):
    st.success("جاري الفتح...")
    st.markdown(f"[اضغط هنا للدخول إلى التطبيق →]({APPS[choice]})")
