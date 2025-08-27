import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, time

# 🌐 Thiết lập giao diện
st.set_page_config(page_title="Nhập đơn hàng Instagram", layout="centered")
st.markdown("""
    <style>
        .main { padding: 1rem; }
        .block-container { padding-top: 2rem; }
        textarea { font-size: 16px; }
        button[kind="primary"] {
            background-color: #4CAF50;
            color: white;
            border-radius: 10px;
            padding: 0.75em 2em;
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# 🔑 Kết nối Google Sheets
def connect_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("Instagram Orders").worksheet("Đơn Hàng")
    return sheet

# 📖 Đọc dữ liệu
def read_orders(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# ➕ Ghi đơn mới
def append_order(sheet, order_data):
    sheet.append_row(order_data)

# 🔄 Cập nhật toàn bộ sheet
def update_sheet(sheet, dataframe):
    sheet.clear()
    sheet.append_row(dataframe.columns.tolist())
    for row in dataframe.itertuples(index=False):
        sheet.append_row(list(row))

# 🧾 Giao diện nhập
st.title("📦 Nhập đơn hàng Instagram")
st.markdown("Dán tin nhắn tổng hợp nội dung từ Instagram vào ô bên dưới:")

input_text = st.text_area("📩 Tin nhắn đơn hàng", height=220)
giao_ngay = st.date_input("📅 Ngày giao hàng")
giao_gio = st.time_input("⏰ Giờ giao hàng", value=time(9, 0))

# 👉 Ghi dữ liệu
if st.button("✅ Ghi vào Google Sheets"):
    if not input_text.strip():
        st.warning("⚠️ Vui lòng nhập nội dung đơn hàng!")
    else:
        try:
            lines = input_text.strip().split("\n")
            if len(lines) < 6:
                st.error("❌ Thiếu dòng trong tin nhắn. Đơn hàng cần ít nhất 6 dòng.")
            else:
                sheet = connect_gsheet()
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
                    "Giá":lines[6].split(":")[1].strip(),
                    "Cọc":lines[7].split(":")[1].strip(),
                    "Note": lines[8].split(":")[1].strip() if len(lines) > 8 and ":" in lines[8] else ""
                }
                append_order(sheet, list(data.values()))
                st.success("✅ Đã ghi đơn hàng vào Google Sheets!")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")

# 📋 Danh sách đơn đã lưu
st.divider()
st.subheader("📑 Danh sách đơn hàng đã lưu")

try:
    sheet = connect_gsheet()
    df = read_orders(sheet)

    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("💾 Cập nhật đơn hàng"):
        update_sheet(sheet, edited_df)
        st.success("✅ Cập nhật Google Sheets thành công!")

except Exception as e:
    st.error(f"Không thể tải dữ liệu từ Google Sheet. Vui lòng kiểm tra cấu hình.\n\n{e}")
