import streamlit as st
from PIL import Image
from cv_engine import analyze_produce
from bidding_engine import GOVT_MSP_DATA, calculate_legal_price_floor, process_buyer_bid

st.set_page_config(page_title="AgriChain Trust Prototype", page_icon="🌾", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: bold; color: #1e3a8a; }
    .sub-title { font-size: 1.1rem; color: #475569; margin-bottom: 20px; }
    .badge { padding: 8px 16px; border-radius: 8px; font-weight: bold; color: white; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🌾 AgriChain Trust</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI Produce Quality Grading & Statutory Policy-Compliant Marketplace</div>', unsafe_allow_html=True)

# Tabs Navigation
tab1, tab2 = st.tabs(["👨‍🌾 Farmer Portal (AI Quality Grading)", "🏬 Wholesale Buyer Marketplace"])

# ---------------- TAB 1: FARMER PORTAL ----------------
with tab1:
    st.subheader("1. AI Produce Quality Assessment")
    col1, col2 = st.columns([1, 1])

    with col1:
        crop_selected = st.selectbox("Select Crop Type", list(GOVT_MSP_DATA.keys()))
        uploaded_file = st.file_uploader("Upload Produce Photo / Camera Capture", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Crop Sample", use_container_width=True)

    with col2:
        if uploaded_file is not None:
            st.markdown("### AI Diagnostic Results")
            with st.spinner("Analyzing surface defect area and color distribution..."):
                res = analyze_produce(image, crop_selected)
                pricing = calculate_legal_price_floor(crop_selected, res["quality_score"], res["premium_pct"])

            # Results Display
            st.markdown(f"#### Overall Grade: <span style='color:{res['color_code']}; font-size:1.8rem; font-weight:bold;'>{res['grade']}</span>", unsafe_allow_html=True)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Quality Score", f"{res['quality_score']}/100")
            m2.metric("Defect Surface Area", f"{res['defect_percentage']}%")
            m3.metric("Govt MSP Floor", f"₹{pricing['msp']}")

            st.markdown("---")
            st.markdown("### 🏛️ Policy-Compliant Valuation")
            st.success(f"**Guaranteed Statutory Price Floor:** ₹{pricing['legal_price_floor']} / Quintal")
            st.caption("No buyer can place a bid below this price floor under agricultural support mandates.")

            st.markdown("### Blemish & Defect Segmentation Heatmap")
            st.image(res["heatmap_image"], caption="Red areas highlight identified surface blemishes/defects", use_container_width=True)
        else:
            st.info("Upload a crop photo on the left to generate the AI Quality Scorecard and statutory price floor.")

# ---------------- TAB 2: BUYER PORTAL ----------------
with tab2:
    st.subheader("2. Statutory Bidding Terminal for Wholesale Buyers")
    
    col_b1, col_b2 = st.columns([1, 1])
    
    with col_b1:
        st.markdown("#### Select Verified Crop Batch")
        batch_crop = st.selectbox("Crop Batch", list(GOVT_MSP_DATA.keys()), key="buyer_crop")
        batch_grade = st.radio("Verified AI Grade", ["Grade A (90% Quality)", "Grade B (72% Quality)"])
        
        q_score = 90.0 if "Grade A" in batch_grade else 72.0
        prem = 15.0 if "Grade A" in batch_grade else 5.0
        floor_details = calculate_legal_price_floor(batch_crop, q_score, prem)
        
        st.info(f"**Batch Details:** 50 Quintals | **Govt Price Floor:** ₹{floor_details['legal_price_floor']} / Quintal")

    with col_b2:
        st.markdown("#### Place Purchase Bid")
        buyer_bid = st.number_input("Your Bid Amount (₹ / Quintal)", value=float(floor_details['legal_price_floor']), step=50.0)
        
        if st.button("Submit Verified Bid"):
            bid_res = process_buyer_bid(buyer_bid, floor_details['legal_price_floor'])
            if bid_res["valid"]:
                st.success(f"✅ {bid_res['message']}")
                st.balloons()
            else:
                st.error(f"❌ {bid_res['message']}")
