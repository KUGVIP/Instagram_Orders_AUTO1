import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, time
import unicodedata

st.set_page_config(page_title="Instagram Orders", layout="wide")

st.markdown("""
    <style>
        textarea, input, select, .stTextInput>div>div>input {
            font-size: 16px !important;
            padding: 6px 8px !important;
        }
        [data-testid="column"] {
            padding: 0.5rem;
        }
        .st-bd { border-radius: 12px; }
        .stButton > button {
            background-color: #4CAF50; color: white;
            border-radius: 10px; padding: 0.5em 1.5em; font-size: 15px;
        }
    </style>
""", unsafe_allow_html=True)

def connect_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Instagram Orders").worksheet("Đơn Hàng")

def read_orders(sheet):
    return pd.DataFrame(sheet.get_all_records())

def append_order(sheet, data):
    sheet.append_row(data)

def update_sheet(sheet, df):
    sheet.clear()
    sheet.append_row(df.columns.tolist())
    for row in df.itertuples(index=False):
        sheet.append_row(list(row))

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

st.title("🌸 Instagram Orders Manager")
with st.expander("📘 Hướng dẫn sử dụng", expanded=False):
    st.markdown("""
    ** Để có thể thực hiện bạn cần thực hiện theo quy trình này nhé Bà Chủ giàu <3:**
                
    **B1: Tạo tin nhắn sẵn theo cầu trúc sẵn trên IG để khi tư vấn khách sẽ chốt với khách theo các thông tin sau (ảnh có thể không cần cho vì a chưa update kịp :)))**
    - Tên 
    - IG: @hoa.kem
    - SĐT: 0987654321
    - Địa chỉ: 123 Lê Lợi, Quận 1
    - Ảnh mẫu: https://www.instagram.com/p/abc123/
    - Số lượng bó: 2
    - giá: 20294
    - Cọc: 9237049725
    - Note yêu cầu khách hàng: Giao buổi sáng, tránh gọi
    - Trạng thái:
                
    **B2: sau khi chốt đơn với khách theo cấu trúc kia thì coppy tin nhắn đó dán vào trong app**
                
    **B3: Done nhé Phương bé :V**
                
    **🌼 Cách nhập đơn hàng mới:**
    - Dán nội dung tin nhắn vào ô 📩
    - Chọn ngày giao, giờ giao, trạng thái
    - Bấm ✅ *Ghi vào Google Sheet*

    **🔍 Cách lọc đơn hàng:**
    - Chọn ngày hoặc giờ giao nếu muốn
    - Lọc theo trạng thái, IG, người nhận, địa chỉ, ghi chú...
    - Bấm 🔄 *Reset bộ lọc* để xóa tất cả

    **📝 Cách chỉnh sửa đơn hàng:**
    - Chỉnh trực tiếp bảng ở dưới
    - Sau khi chỉnh, bấm 📏 *Cập nhật thay đổi vào Google Sheets*

    > App hiển thị tốt trên cả điện thoại và máy tính.
    """)

with st.expander("➕ Nhập đơn mới", expanded=True):
    input_text = st.text_area("📩 Dán nội dung tin nhắn đơn hàng", height=200)
    giao_ngay = st.date_input("📅 Ngày giao hàng")
    giao_gio = st.time_input("⏰ Giờ giao", value=time(9, 0))
    trang_thai = st.selectbox("📦 Trạng thái", ["Chưa giao", "Đã giao"])

    if st.button("✅ Ghi vào Google Sheet"):
        if not input_text.strip():
            st.warning("⚠️ Bạn chưa nhập nội dung đơn!")
        else:
            try:
                lines = input_text.strip().split("\n")
                data = {
                    "Thời gian đặt hàng": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Ngày giao hàng": giao_ngay.strftime("%d/%m/%Y"),
                    "Giờ giao hàng": giao_gio.strftime("%H:%M"),
                    "Tên IG": lines[0].split(":")[1].strip() if "Tên IG" in lines[0] else "",
                    "Tên người nhận": lines[1].split(":")[1].strip(),
                    "SĐT": lines[2].split(":")[1].strip(),
                    "Địa chỉ": lines[3].split(":")[1].strip(),
                    "Ảnh mẫu": f'=IMAGE("{lines[4].split(":")[1].strip()}")',
                    "Số lượng bó": lines[5].split(":")[1].strip(),
                    "Giá": lines[6].split(":")[1].strip(),
                    "Cọc": lines[7].split(":")[1].strip(),
                    "Note": lines[8].split(":")[1].strip() if len(lines) > 8 else "",
                    "Trạng thái": trang_thai
                }
                sheet = connect_gsheet()
                append_order(sheet, list(data.values()))
                st.success("✅ Đã ghi đơn vào Google Sheets!")
            except Exception as e:
                st.error(f"❌ Lỗi ghi dữ liệu: {e}")

st.subheader("📝 Chỉnh sửa & Lưu đơn hàng")
try:
    sheet = connect_gsheet()
    df = read_orders(sheet)

    if "reset_trigger" not in st.session_state:
        st.session_state.reset_trigger = False

    def reset_filters():
        st.session_state.selected_date = ""
        st.session_state.enable_time_range = False
        st.session_state.from_time = time(0, 0)
        st.session_state.to_time = time(23, 59)
        st.session_state.status_filter = []
        st.session_state.ig_filter = []
        st.session_state.keyword_note = ""
        st.session_state.keyword_address = ""
        st.session_state.keyword_name = ""

    with st.expander("🔍 Bộ lọc nâng cao (độc lập)", expanded=True):
        if st.button("🔄 Reset tất cả bộ lọc"):
            reset_filters()

        selected_date = st.selectbox("📅 Chọn ngày giao hàng", options=[""] + sorted(df["Ngày giao hàng"].unique().tolist()), key="selected_date")
        enable_time_range = st.checkbox("📍 Lọc theo giờ giao hàng", key="enable_time_range")
        if enable_time_range:
            from_time = st.time_input("Từ giờ", value=st.session_state.get("from_time", time(0, 0)), key="from_time")
            to_time = st.time_input("Đến giờ", value=st.session_state.get("to_time", time(23, 59)), key="to_time")
        else:
            from_time, to_time = None, None

        status_all = df["Trạng thái"].dropna().unique().tolist()
        ig_all = df["Tên IG"].dropna().unique().tolist()
        ten_all = df["Tên người nhận"].dropna().unique().tolist()

        status_filter = st.multiselect("Trạng thái", status_all, key="status_filter")
        ig_filter = st.multiselect("Tên IG", ig_all, key="ig_filter")

        keyword_note = st.text_input("🔍 Tìm trong ghi chú (Note)", key="keyword_note")
        keyword_address = st.text_input("🔍 Tìm trong địa chỉ", key="keyword_address")
        keyword_name = st.selectbox("🔍 Tìm trong tên người nhận", options=[""] + sorted(ten_all), key="keyword_name")

    filtered_df = df.copy()

    if st.session_state.selected_date:
        filtered_df = filtered_df[filtered_df["Ngày giao hàng"] == st.session_state.selected_date]

    if enable_time_range:
        filtered_df = filtered_df[
            (filtered_df["Giờ giao hàng"] >= from_time.strftime("%H:%M")) &
            (filtered_df["Giờ giao hàng"] <= to_time.strftime("%H:%M"))
        ]

    if st.session_state.status_filter:
        filtered_df = filtered_df[filtered_df["Trạng thái"].isin(st.session_state.status_filter)]
    if st.session_state.ig_filter:
        filtered_df = filtered_df[filtered_df["Tên IG"].isin(st.session_state.ig_filter)]

    if st.session_state.keyword_note:
        filtered_df = filtered_df[filtered_df["Note"].str.contains(st.session_state.keyword_note, case=False, na=False)]
    if st.session_state.keyword_address:
        filtered_df = filtered_df[filtered_df["Địa chỉ"].str.contains(st.session_state.keyword_address, case=False, na=False)]
    if st.session_state.keyword_name:
        keyword_no_accent = remove_accents(st.session_state.keyword_name)
        filtered_df = filtered_df[
            filtered_df["Tên người nhận"].apply(lambda x: keyword_no_accent in remove_accents(x))
        ]

    def add_colored_status(row):
        if row == "Đã giao":
            return "🟢 Đã giao"
        elif row == "Chưa giao":
            return "🔴 Chưa giao"
        else:
            return row

    df_display = filtered_df.copy()
    df_display["Trạng thái"] = df_display["Trạng thái"].apply(add_colored_status)

    st.markdown("### 📂 Danh sách sau khi lọc (không được ghi lại)")
    st.dataframe(df_display, use_container_width=True)

    st.markdown("### 📝 Chỉnh sửa toàn bộ đơn (ghi lại tất cả)")
    df["Trạng thái"] = df["Trạng thái"].apply(add_colored_status)

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Trạng thái": st.column_config.SelectboxColumn(
                "Trạng thái",
                options=["🟢 Đã giao", "🔴 Chưa giao"],
                required=True
            )
        }
    )

    edited_df["Trạng thái"] = edited_df["Trạng thái"].replace({
        "🟢 Đã giao": "Đã giao",
        "🔴 Chưa giao": "Chưa giao"
    })

    if st.button("📏 Cập nhật thay đổi vào Google Sheets"):
        update_sheet(sheet, edited_df)
        st.success("✅ Đã cập nhật thành công!")

except Exception as e:
    st.error(f"❌ Không thể tải Google Sheets: {e}")
