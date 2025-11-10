import streamlit as st
import numpy as np
import pandas as pd
import cv2
from PIL import Image
import tempfile
import os
from src.preprocess import preprocess_image, laplacian_variance, mean_brightness, batch_preprocess


# App Config
st.set_page_config(page_title="VisionPrep Web", layout="wide", page_icon="📸")
st.title("VisionPrep – Intelligent Image Preprocessing for Photogrammetry.")

st.markdown("""
            Enhance your photogrammetry images using AI-inspired preprocessing.
            Adjust lighting, contrast, and clarity interactively before reconstruction.
            """)

# Sidebar Controls
st.sidebar.header("Preprocessing Parameters")
clahe_enable = st.sidebar.checkbox("Enable CLAHE", True)
gamma_val = st.sidebar.slider("Gamma Correction", 0.5, 2.5, 1.2, 0.1)
denoise_enabled = st.sidebar.checkbox("Enable Bilateral Denoise", True)
sharpen_strength = st.sidebar.slider("Sharpen Strength", 0.0, 3.0, 1.0, 0.1)

mode = st.radio("Select Mode:", ["Single Image","Folder/Batch Mode"])

print(mode)
# If single Image
if mode.lower() =='single image':
    uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        img = np.array(Image.open(uploaded_file).convert("RGB"))[:, :, ::-1]
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), caption='Original',use_container_width=True)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            st.caption(f"Brightness: {mean_brightness(gray):.2f} | Sharpness: {laplacian_variance(gray):.2f}")

        enhanced_image = preprocess_image(img, clahe_enable, gamma_val, denoise_enabled, sharpen_strength)
        gray_enhanced = cv2.cvtColor(enhanced_image, cv2.COLOR_RGB2GRAY)
        
        with col2:
            st.image(cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2RGB), caption="Enhanced", use_container_width=True)
            st.caption(f"Brightness: {mean_brightness(gray_enhanced):.2f} | Sharpness: {laplacian_variance(gray_enhanced):.2f}")

        st.download_button(
            "Download Enhanced Image",
            data=cv2.imencode('.jpg', enhanced_image)[1].tobytes(),
            file_name="enhanced.jpg",
            mime="image/jpeg"
        )
        
else:
    # Batch /Folder 
    uploaded_files = st.file_uploader("Upload multiple images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        with st.spinner("Processing Images...."):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = os.path.join(tmpdir, "visionprep_output")
                stats, zip_path, elapsed = batch_preprocess(
                    [(f.name, Image.open(f)) for f in uploaded_files],
                    output_dir,
                    clahe_enable,
                    gamma_val, denoise_enabled,
                    sharpen_strength
                )
                
                df = pd.DataFrame(stats)
                st.success(f"Processed {len(uploaded_files)} images in {elapsed:.2f} seconds.")
                
                st.dataframe(df)
                
                # Download ZIP
                with open(zip_path, "rb") as f:
                    st.download_button(
                        "Download all Enhanced Images (ZIP)",
                        data = f,
                        file_name="visionprep_batch_output.zip",
                        mime="application/zip"
                        
                    )
        
            