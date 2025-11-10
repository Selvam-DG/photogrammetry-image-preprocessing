"""
VisionPrep - Intelligent Image Preprocessing for Photogrammetry
Author: Selvam-DG
Description:
    Enhances raw photogrammetry images via lighting, contrast, and clarity enhancements.
    Includes CLAHE, gamma correction, bilateral denoising, unsharp masking and blur detection.
    Outputs enhanced images + CSV summary for photogrammetry optimization studies.
"""

import os
import cv2
import numpy as np
import time
import pandas as pd
from zipfile import ZipFile


# UTILITY Functions

def laplacian_variance(img_gray):
    """
    Returns variance of Laplacian - higher = sharper image.
    """
    return cv2.Laplacian(img_gray, cv2.CV_64F).var()

def mean_brightness(img_gray):
    """Returns mean brightness(0-255). """
    return np.mean(img_gray)

## Image Enhancement Modules

def apply_CLAHE(img):
    """
    Contrast Limited Adaptive Histogram Equalization.
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l_clahe = clahe.apply(l)
    lab_clahe = cv2.merge((l_clahe, a, b))
    return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

def gamma_correction(img, gamma=1.2):
    """
    Adjust image gamma to control overall brightness.
    """
    inv_gamma = 1.0 / gamma
    table = np.array([ (i/255.0) ** inv_gamma * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(img, table)

def bilateral_denoise(img):
    """
    Preserve edges while reducing noise.
    """
    return cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

def unsharp_mask(img, strength=1.0):
    """
    Sharpen details by subtracting Gaussian blur.
    """
    blurred = cv2.GaussianBlur(img, (0,0), 3)
    return cv2.addWeighted(img, 1+strength, blurred, -strength, 0)

def preprocess_image(img, clahe=True, gamma_val=1.2, denoise=True, sharp_strength=1.0):
    """
    Full Preprocess pipeline for one image.
    """
    if clahe:
        img = apply_CLAHE(img)
    img = gamma_correction(img, gamma=gamma_val)
    if denoise:
        img = bilateral_denoise(img)
    img = unsharp_mask(img, strength=sharp_strength)
    
    return img

def batch_preprocess(images, output_dir, clahe, gamma_val, denoise, sharp_strength):
    os.makedirs(output_dir, exist_ok=True)
    stats = []
    start_total = time.time()
    
    for file, img in images:
        img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray_before = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        sharp_before = laplacian_variance(gray_before)
        bright_before = mean_brightness(gray_before)
        
        enhanced_img = preprocess_image(img_bgr, clahe, gamma_val, denoise, sharp_strength)
        gray_after = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2GRAY)
        sharp_after = laplacian_variance(gray_after)
        bright_after = mean_brightness(gray_after)
        
        out_path = os.path.join(output_dir, os.path.basename(file))
        cv2.imwrite(out_path, enhanced_img)
        
        stats.append({
            "filename" : os.path.basename(file),
            "sharp_before" : round(sharp_before, 2),
            "sharp_after" : round(sharp_after, 2),
            "brightness_before" : round(bright_before, 2),
            "brightness_after" : round(bright_after, 2)
        })
    elapsed = time.time() - start_total
    
    zip_path = output_dir + ".zip"
    with ZipFile(zip_path, "w") as zf:
        for f in os.listdir(output_dir):
            zf.write(os.path.join(output_dir,f), arcname=f)
            
    return stats, zip_path, elapsed
        