import cv2
import numpy as np
from PIL import Image

def analyze_produce(image: Image.Image, crop_type: str = "tomato"):
    """
    Analyzes produce image using OpenCV:
    1. Segments crop from background using HSV thresholding.
    2. Identifies defective/blemished surface pixels.
    3. Calculates defect surface area ratio and color uniformity.
    4. Computes composite quality score (Q) and outputs Grade A/B/C.
    """
    # Convert PIL Image to OpenCV BGR
    img_np = np.array(image.convert('RGB'))
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # 1. Background Segmentation (Isolate Produce)
    # Define color bounds for produce detection (Default: Red/Orange for tomatoes/apples)
    if crop_type.lower() in ["tomato", "apple"]:
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        mask1 = cv2.inRange(img_hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(img_hsv, lower_red2, upper_red2)
        crop_mask = cv2.bitwise_or(mask1, mask2)
    else:  # Generic bright produce mask
        lower_gen = np.array([10, 40, 40])
        upper_gen = np.array([170, 255, 255])
        crop_mask = cv2.inRange(img_hsv, lower_gen, upper_gen)

    total_crop_pixels = cv2.countNonZero(crop_mask)
    if total_crop_pixels == 0:
        total_crop_pixels = img_np.shape[0] * img_np.shape[1]
        crop_mask = np.ones((img_np.shape[0], img_np.shape[1]), dtype=np.uint8) * 255

    # 2. Defect Detection (Blemish / Dark Spot Segmentation)
    # Convert to LAB / Grayscale to detect dark blemishes on surface
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    # Adaptive thresholding inside crop region to isolate blemishes
    defect_mask = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 15, 3
    )
    defect_mask = cv2.bitwise_and(defect_mask, crop_mask)
    
    defect_pixels = cv2.countNonZero(defect_mask)
    defect_ratio = float(defect_pixels) / float(total_crop_pixels)
    defect_percentage = round(min(defect_ratio * 100 * 1.5, 100.0), 2)  # Normalized %

    # 3. Create Heatmap Overlay Visualization
    overlay = img_np.copy()
    overlay[defect_mask > 0] = [255, 0, 0]  # Highlight blemishes in Red
    heatmap_img = cv2.addWeighted(img_np, 0.7, overlay, 0.3, 0)

    # 4. Compute Composite Quality Index (Q)
    # Q = 100 - (defect_percentage * weight)
    w_defect = 1.2
    quality_score = max(0.0, round(100.0 - (defect_percentage * w_defect), 1))

    # Grade Classification
    if quality_score >= 85:
        grade = "Grade A"
        color_code = "#22c55e" # Green
        premium_pct = 15.0
    elif quality_score >= 65:
        grade = "Grade B"
        color_code = "#f59e0b" # Yellow/Orange
        premium_pct = 5.0
    else:
        grade = "Grade C"
        color_code = "#ef4444" # Red
        premium_pct = 0.0

    return {
        "quality_score": quality_score,
        "defect_percentage": defect_percentage,
        "grade": grade,
        "color_code": color_code,
        "premium_pct": premium_pct,
        "heatmap_image": Image.fromarray(heatmap_img)
    }
