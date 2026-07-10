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
st.write("上傳背景圖並輸入標題，一鍵生成與 **Figma 100% 相同視覺質感**、且檔案在 1MB 以下的專業封面。")

# --- 側邊欄：視覺參數微調 ---
st.sidebar.header("⚙️ 視覺參數設定")
max_size_mb = st.sidebar.slider("限制檔案大小 (MB)", 0.5, 5.0, 1.0, 0.1)

# --- 主畫面：內容輸入 ---
st.subheader("✍️ 輸入封面內容")
title_text = st.text_input("大標題文本", "被動元件是什麼？")
subtitle_text = st.text_input("副標題文本", "國巨、華新科上漲空間還有多大？")

bg_file = st.file_uploader("上傳背景圖片", type=["jpg", "jpeg", "png", "webp"])

# 預設的資產路徑
LOGO_PATH = "logo.png"
MASK_PATH = "mask.png"

if bg_file:
    if st.button("🚀 一鍵生成完美封面並壓縮"):
        try:
            if not os.path.exists(LOGO_PATH) or not os.path.exists(MASK_PATH):
                st.error("❌ 錯誤：在專案中找不到固定 logo.png 或 mask.png。請確認您已將這兩個檔案上傳至 GitHub 專案中。")
                st.stop()

            # 1. 讀取並強制縮放背景圖至 1280 * 832
            bg_img = Image.open(bg_file).convert("RGB")
            bg_img = bg_img.resize((1280, 832), Image.Resampling.LANCZOS)
            
            # 2. 直接讀取來自 Figma 的真實半透明漸層遮罩
            figma_mask = Image.open(MASK_PATH).convert("RGBA")
            figma_mask = figma_mask.resize((1280, 832), Image.Resampling.LANCZOS)
            
            # 分離出 Figma 遮罩的色彩圖層與 Alpha 頻道
            mask_rgb = figma_mask.convert("RGB")
            mask_alpha = figma_mask.split()[3]  
            
            # 將 Figma 遮罩完美疊加至背景圖上
            bg_img = Image.composite(mask_rgb, bg_img, mask_alpha)
            
            # 3. 繪製文字 (字體大小鎖定 59 px，座標精準依據 Figma：X=130)
            draw = ImageDraw.Draw(bg_img)
            fixed_font_size = 59  
            
            try:
                font = ImageFont.truetype(FONT_PATH, fixed_font_size)
            except:
                font = ImageFont.load_default()
                st.warning("⚠️ 字體載入失敗，使用系統預設字體")

            # 繪製大標題 (Figma 數據：X=130, Y=566)
            draw.text((130, 566), title_text, fill="#FFFFFF", font=font)
            # 繪製副標題 (Figma 數據：X=130, Y=652)
            draw.text((130, 652), subtitle_text, fill="#FFFFFF", font=font)
            
            # 4. 讀取並貼上內建 Logo (精準還原 Figma：X=130, Y=459, 尺寸 286x98)
            logo = Image.open(LOGO_PATH).convert("RGBA")
            
            # 強制鎖定寬度為 286 px，高度為 98 px，完全對齊 Figma 容器大小
            logo_w = 286
            logo_h = 98
            logo_resized = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
            
            # 精準蓋印在 X=130, Y=459 處
            bg_img.paste(logo_resized, (130, 459), mask=logo_resized)
            
            # 5. 動態二分搜尋法壓縮，確保檔案在 1MB 以下
            max_size_bytes = max_size_mb * 1024 * 1024
            low, high = 10, 95
            best_quality = 90
            
            img_buffer = io.BytesIO()
            bg_img.save(img_buffer, "JPEG", quality=high)
            
            if img_buffer.tell() > max_size_bytes:
                while low <= high:
                    mid = (low + high) // 2
                    img_buffer = io.BytesIO()
                    bg_img.save(img_buffer, "JPEG", quality=mid)
                    file_size = img_buffer.tell()
                    
                    if file_size <= max_size_bytes:
                        best_quality = mid
                        low = mid + 1
                    else:
                        high = mid - 1

                img_buffer = io.BytesIO()
                bg_img.save(img_buffer, "JPEG", quality=best_quality)

            final_size_mb = img_buffer.tell() / (1024 * 1024)
            
            # 6. 呈現成品與下載
            st.write("---")
            st.subheader("✨ 產出成品預覽")
            st.image(bg_img, use_container_width=True)
            st.success(f"✅ 封面生成成功！檔案大小已精準控制在: {final_size_mb:.2f} MB")
            
            st.download_button(
                label="📥 下載高畫質封面圖片",
                data=img_buffer.getvalue(),
                file_name=f"cover_{title_text[:10]}.jpg",
                mime="image/jpeg")
            
        except Exception as e:
            st.error(f"❌ 圖片生成失敗，錯誤訊息: {e}")
else:
    st.info("💡 網頁已內建品牌 Logo 與 Figma 漸層。現在只需輸入標題並上傳背景圖即可產圖！")
