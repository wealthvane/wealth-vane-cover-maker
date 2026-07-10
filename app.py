import os
import io
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# 1. 自動下載開源的思源黑體 (Noto Sans TC Bold)
FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Bold.otf"
FONT_PATH = "NotoSansCJKtc-Bold.otf"

@st.cache_data
def download_font():
    if not os.path.exists(FONT_PATH):
        with st.spinner("首次啟動正在載入繁體中文字體，請稍候..."):
            response = requests.get(FONT_URL)
            with open(FONT_PATH, "wb") as f:
                f.write(response.content)

download_font()

# 網頁基本設定
st.set_page_config(page_title="Wealth Vane 封面生成器", layout="centered")
st.title("🎨 專業社群封面自動生成器")
st.write("上傳背景圖並輸入標題，一鍵生成帶有**經典藍色漸層遮罩、精準排版與內建 Logo** 的 1280x832 專業封面。")

# --- 側邊欄：視覺參數微調 ---
st.sidebar.header("⚙️ 視覺參數設定")
gradient_color = st.sidebar.color_picker("漸層主色調", "#1A15A5")
font_size = st.sidebar.slider("字體大小 (px)", 40, 80, 59)

# --- 主畫面：內容輸入 ---
st.subheader("✍️ 輸入封面內容")
title_text = st.text_input("大標題文本", "被動元件是什麼？")
subtitle_text = st.text_input("副標題文本", "國巨、華新科上漲空間還有多大？")

bg_file = st.file_uploader("上傳背景圖片", type=["jpg", "jpeg", "png", "webp"])

# 預設的 Logo 路徑 (讀取專案內的 logo.png)
LOGO_PATH = "logo.png"

if bg_file:
    if st.button("🚀 一鍵生成完美封面"):
        try:
            # 檢查內建 Logo 是否存在
            if not os.path.exists(LOGO_PATH):
                st.error("❌ 錯誤：在專案中找不到固定 Logo 檔案。請確認您已將 'logo.png' 上傳至 GitHub 專案根目錄中。")
                st.stop()

            # 1. 讀取並強制縮放背景圖至 1280 * 832
            bg_img = Image.open(bg_file).convert("RGB")
            bg_img = bg_img.resize((1280, 832), Image.Resampling.LANCZOS)
            
            # 2. 建立漸層遮罩 (左下至右上的線性漸層)
            mask = Image.new("L", (1280, 832), 0)
            for y in range(832):
                for x in range(1280):
                    weight = (832 - y) / 832 * 0.7 + (1280 - x) / 1280 * 0.3
                    if weight > 0.65:
                        alpha = 255
                    elif weight < 0.20:
                        alpha = 0
                    else:
                        alpha = int((weight - 0.20) / (0.65 - 0.20) * 255)
                    mask.putpixel((x, y), alpha)
            
            # 建立純色圖層並結合遮罩疊加到背景上
            gradient_layer = Image.new("RGB", (1280, 832), gradient_color)
            bg_img = Image.composite(gradient_layer, bg_img, mask)
            
            # 3. 繪製文字 (依據 Figma 數據：X=130)
            draw = ImageDraw.Draw(bg_img)
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except:
                font = ImageFont.load_default()
                st.warning("⚠️ 字體載入失敗，使用系統預設字體")

            # 繪製大標題 (Figma 數據：Y=566)
            draw.text((130, 566), title_text, fill="#FFFFFF", font=font)
            # 繪製副標題 (Figma 數據：Y=652)
            draw.text((130, 652), subtitle_text, fill="#FFFFFF", font=font)
            
            # 4. 讀取並貼上內建 Logo (依據 Figma 最新數據：X=130, Y=459, 尺寸 286x98)
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo_w = 286
            logo_h = 98
            logo_resized = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
            
            # 精準蓋印在 X=130, Y=459 處
            bg_img.paste(logo_resized, (130, 459), mask=logo_resized)
            
            # 5. 輸出成品並提供下載
            st.write("---")
            st.subheader("✨ 產出成品預覽")
            st.image(bg_img, use_container_width=True)
            
            # 轉為記憶體緩衝區提供下載
            img_buffer = io.BytesIO()
            bg_img.save(img_buffer, "JPEG", quality=95)
            
            st.download_button(
                label="📥 下載高畫質封面圖片",
                data=img_buffer.getvalue(),
                file_name=f"cover_{title_text[:10]}.jpg",
                mime="image/jpeg" )
            
        except Exception as e:
            st.error(f"❌ 圖片生成失敗，錯誤訊息: {e}")
else:
    st.info("💡 網頁已內建品牌 Logo。現在只需在中央上傳背景圖、輸入標題，即可開始自動產圖！")
