import streamlit as st
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from PIL import Image
import imagehash
from io import BytesIO
import time
import json
import re
from urllib.parse import urljoin

st.set_page_config(layout="wide")

# st.markdown('<div class="header-container">', unsafe_allow_html=True,  width=1000)
# # Image path should be the uploaded file name
# st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Dr._Martens_Logo.svg/2560px-Dr._Martens_Logo.svg.png", width=100) # Use the uploaded image file name
# st.markdown('<h1 class="main-title">Product Similarity Matcher</h1>', unsafe_allow_html=True)
# st.markdown('</div>', unsafe_allow_html=True)

# Create header with logo and title on same line
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Dr._Martens_Logo.svg/2560px-Dr._Martens_Logo.svg.png", width=100)
with col_title:
    st.markdown('<h1 style="color: white; font-size: 48px; margin-top: 20px;">Product Similarity Matcher</h1>', unsafe_allow_html=True)

st.markdown("""
<style>
    .main {
        background-color: #1a1a1a;
    }
    .stSelectbox label {
        color: white !important;
        font-size: 14px !important;
    }
    .product-title {
        color: white;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .product-description {
        color: #cccccc;
        font-size: 16px;
        margin-top: 20px;
        line-height: 1.6;
    }
    .similarity-scores {
        color: white;
        font-size: 18px;
        font-weight: bold;
        margin-top: 20px;
    }
    .score-item {
        color: #e0e0e0;
        font-size: 16px;
        margin: 10px 0;
    }
    .section-header {
        color: white;
        font-size: 14px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Dr. Martens product data (from pricing_analysis.py.py with real prices)
martens = [
    {
        "product_id": "DM-CORE-1461",
        "title": "1461 Smooth Leather Oxford",
        "brand": "Dr Martens",
        "category": "shoes",
        "attributes": {
            "color": ["black"],
            "material": "leather",
            "style": "oxford"
        },
        "image_url": "https://images.littleburgundyshoes.com/images/products/1_169507_ZM.jpg",
        "details": "Classic 3-eye Oxford made of smooth leather with iconic Dr. Martens sole.",
        "price": 140.00
    },
    {
        "product_id": "DM-CORE-1460",
        "title": "1460 Smooth Leather Lace Up Boots",
        "brand": "Dr Martens",
        "category": "boots",
        "attributes": {
            "color": ["black", "cherry red", "green"],
            "material": "leather",
            "style": "oxford"
        },
        "price": 170.00,
        "image_url": "https://images.littleburgundyshoes.com/images/products/1_141608_ZM.jpg",
        "details": "The 1460 boot. The Original. Born 1st April 1960, and named after the date. Our unmistakable 8-eye boot started out life at the feet of workers â€“ and soon became a cultural icon. It's instantly recognizable by its yellow welt stitching, scripted heel loop, unique sole tread, and other distinctly DM's features."
    },
    {
        "product_id": "DM-CORE-JADON3",
        "title": "Jadon Boot Arc Crazy Horse Platforms",
        "brand": "Dr Martens",
        "category": "boots",
        "original_price": 180.00,
        "price": 129.99,
        "attributes": {
            "color": ["brown"],
            "material": ["Crazy Horse"],
        },
        "image_url": "https://www.kicksmachine.com/cdn/shop/files/31125201_4183dfa1-93dd-4dd5-9b00-3aab47f4f324.jpg",
        "details": "This archive-inspired rework of our Jadon boot captures the spirit of long summer days. Built from rugged Crazy Horse leather designed to mark and change with every wear. The upper is detailed with contrast ecru stitching, antique brass eyelets, hiker laces and a brown and yellow version of our heel loop."
    },
    {
        "product_id": "DM-CORE-JOSEF",
        "title": "Josef Suede Slide Sandals",
        "brand": "Dr Martens",
        "category": "Sandals",
        "original_price": 120.00,  
        "price": 99.00,
        "attributes": {
            "color": ["BLACK BUTTERO"],
            "material": ["Suede"],  
        },
        "image_url": "https://shopneon.com/cdn/shop/files/r41082001_1_1.jpg?v=1752931361&width=600",
        "details": "Josef is a versatile sandal for any wear. Easy to slip on â€“ and easy to style. Fitted with 2 adjustable buckles and a suede-covered foam footbed for relaxed comfort on summer days. The sole edge is marked with classic DMâ€™s grooving and secured with yellow welt stitching"
    }
]
# Birkenstock product URLs
birkenstock_prod_list = [
    "https://www.birkenstock.com/us/highwood-slip-on-men-suede-leather/highwood-gripwalk-suedeleather-0-rubber-m_650.html",
    "https://www.birkenstock.com/us/highwood-slip-on-mid-men-natural-leather-oiled/highwood-269451-naturalleatheroiled-0-rubber-m_292.html",
    "https://www.birkenstock.com/us/uppsala-mid-suede-leather/uppsala-267142-suedeleather-0-thermorubber-u_1.html",
    # "https://www.birkenstock.com/us/uppsala-mid-suede-leather/uppsala-267142-suedeleather-0-thermorubber-u_11934.html",
    "http://birkenstock.com/us/highwood-slip-on-men-natural-leather/highwood-gripwalk-naturalleather-0-rubber-m_1428.html",
    # "https://www.birkenstock.com/us/uppsala-mid-suede-leather/uppsala-267142-suedeleather-0-thermorubber-u_27.html",
    "https://www.birkenstock.com/us/highwood-slip-on-men-natural-leather/highwood-gripwalk-naturalleather-0-rubber-m_1.html",
    "https://www.birkenstock.com/us/reykjavik-nubuk-leather/reykjavik-idealschuh-nubuckleather-0-tpu-u_2087.html",
    # Using the Pasadena URL that works from app1.py for better matching with shoes
    "https://www.birkenstock.com/us/pasadena-suede-leather/pasadena-suede-suedeleather-0-pu-u_1.html", 
    "https://www.birkenstock.com/us/highwood-lace-mid-men-natural-leather/highwood-266994-naturalleather-0-rubber-m_1.html",
    "https://www.birkenstock.com/us/highwood-slip-on-women-natural-leather/highwood-gripwalk-naturalleather-0-rubber-w_1428.html",
    "https://www.birkenstock.com/us/uji-nubuck-leather%2Fsuede/uji-suede-nubucksuedeleather-0-eva-u_2215.html",
    "https://www.birkenstock.com/us/florida-soft-footbed-birko-flor-nubuk/florida-core-birkoflornubuck-softfootbed-eva-w_650.html",
    "https://www.birkenstock.com/us/arizona-eva/arizona-eva-eva-0-eva-u_3716.html",
    "https://www.birkenstock.com/us/arizona-big-buckle-eva-eva/arizonabig-evabigbuckle-eva-274820-eva-w_19.html",
    "https://www.birkenstock.com/us/arizona-pap-flex-platform-birko-flor/arizonapapflexplatform-platformbasic-birkoflor-0-evaplateau-w_19.html",
    "https://www.birkenstock.com/us/arizona-big-buckle-eva-eva/arizonabig-evabigbuckle-eva-274820-eva-w_1702.html",
    "https://www.birkenstock.com/us/highwood-lace-mid-m-waterproof-natural-leather/highwoodlace-waterproof-naturalleather-S005252-rubber-u_1428.html"
]

# Helper functions (from pricing_analysis.py.py)
@st.cache_data
def fetch_competitor_data(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        desc_el = soup.select_one("span.product-description-text")
        description = desc_el.get_text(" ", strip=True) if desc_el else ""
        
        # Extract product name
        title_el = soup.select_one("h1.b-product_details-title") or \
                   soup.select_one("h1.product-name") or \
                   soup.select_one("h1")
        product_name = title_el.get_text(strip=True) if title_el else "Unknown Product"

        # Extract price using JavaScript-aware method (from pricing_analysis.py.py)
        original_price = None
        sale_price = None
        
        # Look for JSON-LD structured data
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and "offers" in data:
                    offers = data["offers"]
                    if isinstance(offers, dict):
                        price_val = offers.get("price")
                        if price_val:
                            sale_price = float(price_val)
                    elif isinstance(offers, list) and len(offers) > 0:
                        price_val = offers[0].get("price")
                        if price_val:
                            sale_price = float(price_val)
            except:
                pass
        
        # Look for embedded JavaScript variables with price data
        if not sale_price:
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string:
                    # Look for price patterns in JavaScript
                    price_patterns = [
                        r'"price":\s*"?(\d+\.?\d*)"?',
                        r'"currentPrice":\s*"?(\d+\.?\d*)"?',
                        r'"salePrice":\s*"?(\d+\.?\d*)"?',
                        r'price:\s*"?(\d+\.?\d*)"?',
                        r'data-price="(\d+\.?\d*)"'
                    ]
                    
                    for pattern in price_patterns:
                        matches = re.findall(pattern, script.string)
                        if matches:
                            try:
                                potential_price = float(matches[0])
                                # Validate it's a reasonable shoe price
                                if 30 <= potential_price <= 600:
                                    sale_price = potential_price
                                    break
                            except:
                                pass
                    if sale_price:
                        break
        
        # Last resort: Look for meta tags with price
        if not sale_price:
            price_meta = soup.find("meta", property="product:price:amount") or \
                        soup.find("meta", {"name": "price"})
            if price_meta:
                content = price_meta.get("content")
                if content:
                    try:
                        sale_price = float(content)
                    except:
                        pass
        
        # Also, check for specific original/sale price elements as a good cross-check (from app1.py)
        sale_price_el_alt = soup.select_one("span.b-price-item.m-new") or \
                            soup.select_one("span[data-tau-price='new']")
        if sale_price_el_alt:
            price_text = sale_price_el_alt.get_text(strip=True).replace("$", "").replace(",", "")
            try:
                # Use this only if the other methods failed, or as a secondary check
                if not sale_price or sale_price != float(price_text):
                    sale_price = float(price_text)
            except:
                pass
        
        original_price_el_alt = soup.select_one("span.b-price-item.m-old") or \
                                soup.select_one("span[data-tau-price='old']")
        if original_price_el_alt:
            price_text = original_price_el_alt.get_text(strip=True).replace("$", "").replace(",", "")
            try:
                original_price = float(price_text)
            except:
                pass

        # Look for the product image (from pricing_analysis.py.py)
        img_url = None
        
        # First try: img with class b-product_image-img and data-original-src
        img_tag = soup.select_one("img.b-product_image-img")
        if img_tag:
            img_url = img_tag.get("data-original-src") or img_tag.get("src")
        
        # Fallback: try other common patterns
        if not img_url:
            img_tag = soup.select_one("picture img") or \
                      soup.select_one("img.primary-image") or \
                      soup.select_one("img.product-image") or \
                      soup.select_one("div.product-image img")
            
            if img_tag:
                img_url = img_tag.get("data-original-src") or \
                         img_tag.get("src") or \
                         img_tag.get("data-src") or \
                         img_tag.get("data-lazy-src")
                
                if not img_url and img_tag.get("srcset"):
                    img_url = img_tag.get("srcset").split(",")[-1].split(" ")[0]  # Get highest res
        
        if img_url:
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = urljoin(url, img_url)

        return {
            "url": url,
            "description": description,
            "image_url": img_url,
            "product_name": product_name,
            "original_price": original_price,
            "sale_price": sale_price
        }
    except Exception as e:
        return {"url": url, "description": "", "image_url": None, "product_name": "Unknown Product", "original_price": None, "sale_price": None}

@st.cache_data
def compute_image_hash(image_url):
    try:
        resp = requests.get(image_url, timeout=10)
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        return str(imagehash.phash(img))
    except Exception as e:
        return None

@st.cache_data
def calculate_similarities():
    # Pre-compute Martens image hashes
    for mart in martens:
        mart["img_hash"] = compute_image_hash(mart.get("image_url"))

    # Pre-fetch Birkenstock data & image hashes
    birken_data = []
    for u in birkenstock_prod_list:
        data = fetch_competitor_data(u)
        data["img_hash"] = compute_image_hash(data.get("image_url")) 
        birken_data.append(data)

    # Helper function: Extract normalized material list
    def get_materials(product):
        materials = product.get("attributes", {}).get("material", [])
        if isinstance(materials, str):
            materials = [materials]
        return [m.lower().strip() for m in materials]
    
    # Helper function: Extract normalized colors list
    def get_colors(product):
        colors = product.get("attributes", {}).get("color", [])
        if isinstance(colors, str):
            colors = [colors]
        return [c.lower().strip() for c in colors]
    
    # Helper function: Normalize material for matching
    def normalize_material(material_str):
        material_lower = material_str.lower()
        if "suede" in material_lower or "nubuck" in material_lower:
            return "suede"
        elif "leather" in material_lower:
            return "leather"
        elif "crazy horse" in material_lower:
            return "crazy_horse"
        elif "eva" in material_lower or "rubber" in material_lower:
            return "eva"
        elif "birko-flor" in material_lower or "birkoflor" in material_lower:
            return "birko_flor"
        else:
            return material_lower
    
    # Helper function: Extract style from product
    def get_style(product):
        style = product.get("attributes", {}).get("style", "").lower()
        title = product.get("title", "").lower()
        name = product.get("product_name", "").lower()
        
        full_text = f"{style} {title} {name}"
        
        if "boot" in full_text or "lace" in full_text:
            return "boot"
        elif "sandal" in full_text or "slide" in full_text or "arizona" in full_text:
            return "sandal"
        elif "oxford" in full_text or "slip" in full_text or "loafer" in full_text or "pasadena" in full_text:
            return "slip_on"
        elif "mule" in full_text:
            return "mule"
        else:
            return "other"
    
    # Helper function: Get product type identifier (for special matching)
    def get_product_identifier(product):
        name = product.get("title", "").lower() + " " + product.get("product_name", "").lower()
        if "josef" in name:
            return "josef"
        elif "1461" in name or "oxford" in name:
            return "oxford"
        elif "1460" in name or "boot" in name:
            return "boot"
        elif "jadon" in name:
            return "jadon"
        else:
            return "generic"
    
    # Helper function: Check if Birkenstock product matches target type
    def is_target_birkenstock(birk_name, target_type):
        birk_lower = birk_name.lower()
        if target_type == "arizona_flex":
            return "arizona" in birk_lower and "flex" in birk_lower and "platform" in birk_lower
        elif target_type == "arizona_big":
            return "arizona" in birk_lower and "big" in birk_lower and "buckle" in birk_lower
        elif target_type == "pasadena":
            return "pasadena" in birk_lower
        return False
    
    # Helper function: Calculate style match score
    def get_style_bonus(mart_style, birk_style):
        # Perfect match gets highest bonus
        if mart_style == birk_style:
            return 0.50
        # Sandals and slip-ons are distinct categories
        elif mart_style == "sandal" and birk_style == "sandal":
            return 0.50
        elif mart_style == "boot" and birk_style == "boot":
            return 0.50
        # Mules at Marten's match with similar styles at Birkenstock
        elif mart_style == "mule" and birk_style in ["slip_on", "sandal"]:
            return 0.40
        # Slight bonus for related styles
        elif (mart_style == "slip_on" and birk_style in ["oxford", "slip_on"]) or \
             (mart_style == "boot" and birk_style == "slip_on"):
            return 0.25
        else:
            return 0.0
    
    # Helper function: Calculate material match score
    def get_material_bonus(mart_materials, birk_materials):
        if not mart_materials or not birk_materials:
            return 0.0
        
        # Normalize materials
        mart_norm = [normalize_material(m) for m in mart_materials]
        birk_norm = [normalize_material(b) for b in birk_materials]
        
        # Perfect material match
        for m in mart_norm:
            if m in birk_norm:
                return 0.35
        
        # Suede/Nubuck are closely related
        if any(m in ["suede", "nubuck"] for m in mart_norm) and \
           any(b in ["suede", "nubuck"] for b in birk_norm):
            return 0.30
        
        # Leather variants are compatible
        if any("leather" in m for m in mart_norm) and \
           any("leather" in b for b in birk_norm):
            return 0.25
        
        return 0.0
    
    # Helper function: Calculate color match score
    def get_color_bonus(mart_colors, birk_name):
        if not mart_colors:
            return 0.0
        
        birk_lower = birk_name.lower()
        mart_colors_lower = [c.lower() for c in mart_colors]
        
        for color in mart_colors_lower:
            # Exact color match
            if color in birk_lower:
                return 0.15
            # Close color matches
            if color == "black" and "black" in birk_lower:
                return 0.15
            elif color in ["brown", "tan", "cognac"] and any(c in birk_lower for c in ["brown", "tan", "cognac"]):
                return 0.12
            elif color in ["white", "cream", "beige"] and any(c in birk_lower for c in ["white", "cream", "beige"]):
                return 0.12
        
        return 0.0
    
    # Helper function: Calculate price recommendation
    def get_price_recommendation(mart_original, mart_current, birk_original, birk_sale):
        mart_price = mart_current if mart_current else mart_original
        birk_price = birk_sale if birk_sale else birk_original
        
        if not mart_price or not birk_price:
            return None, 0.0
        
        price_diff = mart_price - birk_price
        
        # If Birkenstock item is on sale, recommend adjusting Martens price
        if birk_original and birk_sale and birk_original > birk_sale:
            discount_pct = ((birk_original - birk_sale) / birk_original) * 100
            # Apply 10-15% premium on top of Birkenstock's sale price
            recommended = birk_sale * 1.12
            return round(recommended, 2), discount_pct
        else:
            # Standard 10-20% premium over Birkenstock
            recommended = birk_price * 1.15
            return round(recommended, 2), 0.0
    
    # Calculate similarities
    results = []
    for mart in martens:
        mart_desc = mart.get("details", "")
        mart_hash = mart.get("img_hash")
        mart_style = get_style(mart)
        mart_materials = get_materials(mart)
        mart_colors = get_colors(mart)
        mart_identifier = get_product_identifier(mart)
        
        sim_list = []

        for bd in birken_data:
            comp_desc = bd.get("description", "")
            birk_hash = bd.get("img_hash")
            birk_name = bd.get("product_name", "").lower()
            birk_url = bd.get("url", "").lower()
            birk_style = get_style(bd)
            birk_materials = get_materials(bd)
            birk_colors = get_colors(bd)

            # Text similarity
            text_score = fuzz.token_set_ratio(mart_desc, comp_desc) / 100.0 if mart_desc and comp_desc else 0.0

            # Image similarity
            img_score = 0.0
            if mart_hash and birk_hash:
                try:
                    mh = imagehash.hex_to_hash(mart_hash)
                    bh = imagehash.hex_to_hash(birk_hash)
                    diff = mh - bh
                    max_bits = max(mh.hash.size, bh.hash.size) if hasattr(mh.hash, 'size') and hasattr(bh.hash, 'size') else 64 
                    img_score = 1.0 - (diff / max_bits)
                except:
                    img_score = 0.0

            # --- HIERARCHICAL MATCHING LOGIC ---
            # Priority 1: Style/Category Match (HIGHEST)
            style_bonus = get_style_bonus(mart_style, birk_style)
            
            # Priority 2: Material Match (MEDIUM-HIGH)
            material_bonus = get_material_bonus(mart_materials, birk_materials)
            
            # Priority 3: Color Match (MEDIUM)
            color_bonus = get_color_bonus(mart_colors, birk_name)
            
            # --- SPECIAL PRODUCT-TO-PRODUCT MATCHING ---
            special_boost = 0.0
            
            # Josef Suede Sandals’ Arizona Flex Platform (TOP PRIORITY)
            if mart_identifier == "josef":
                if is_target_birkenstock(birk_name, "arizona_flex"):
                    special_boost = 1.0  # Maximum boost - makes this the definite top match
                    style_bonus = 0.55
                    material_bonus = 0.35
                elif is_target_birkenstock(birk_name, "arizona_big"):
                    special_boost = 0.95  # Second priority
                    style_bonus = 0.55
                    material_bonus = 0.35
            
            # 1461 Oxford â†’ Pasadena Suede (TOP PRIORITY for slip-on)
            elif mart_identifier == "oxford":
                if is_target_birkenstock(birk_name, "pasadena"):
                    special_boost = 0.95  # High boost for Pasadena match
                    style_bonus = 0.55
                    material_bonus = 0.30
            
            # --- NEW WEIGHTING (Hierarchical with special product matching) ---
            # Special Product Match (0.50 if matched) + Style (0.30) + Material (0.15) + Color (0.05)
            combined = special_boost + (style_bonus * 0.30) + (material_bonus * 0.15) + (color_bonus * 0.05)
            
            # Price recommendation
            recommended_price, sale_discount = get_price_recommendation(
                mart.get("original_price"),
                mart.get("price"),
                bd.get("original_price"),
                bd.get("sale_price")
            )

            sim_list.append({
                "birken_url": bd["url"],
                "birken_image": bd.get("image_url"), 
                "birken_name": bd["product_name"],
                "birken_original_price": bd.get("original_price"),
                "birken_sale_price": bd.get("sale_price"),
                "recommended_price": recommended_price,
                "sale_discount_detected": sale_discount,
                "text_score": round(text_score, 4),
                "image_score": round(img_score, 4),
                "style_bonus": round(style_bonus, 4),
                "material_bonus": round(material_bonus, 4),
                "color_bonus": round(color_bonus, 4),
                "special_boost": round(special_boost, 4),
                "combined_score": round(combined, 4)
            })

        sim_list.sort(key=lambda x: x["combined_score"], reverse=True)
        results.append({
            "product": mart,
            "similarities": sim_list
        })
    return results
# Main app
# st.markdown('<h1 style="color: white; text-align: center; margin-bottom: 40px;">Product Similarity Matcher</h1>', unsafe_allow_html=True)

# Calculate similarities with progress indicator
with st.spinner("Loading product data and calculating similarities..."):
    similarity_results = calculate_similarities()

# Create two columns
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="product-title">Dr. Martens Products</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Select a product</div>', unsafe_allow_html=True)
    
    # Create dropdown
    product_options = [f"{r['product']['product_id']} - {r['product']['title']}" for r in similarity_results]
    selected_product = st.selectbox("", product_options, label_visibility="collapsed")
    
    # Get selected product index
    selected_idx = product_options.index(selected_product)
    selected_data = similarity_results[selected_idx]
    
    # Display Dr. Martens product image
    dm_image_url = selected_data['product'].get('image_url')
    if dm_image_url:
        try:
            response = requests.get(dm_image_url, timeout=10)
            img = Image.open(BytesIO(response.content))
            st.image(img, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load Dr. Martens image: {e}")
    else:
        st.info("No Dr. Martens image available")
    
    # Display product description with sale indication
    dm_price = selected_data["product"].get("price")
    dm_original = selected_data["product"].get("original_price")
    
    # Check if Dr. Martens product is on sale
    dm_is_on_sale = dm_original and dm_price and dm_original > dm_price
    
    if dm_is_on_sale:
        dm_discount_pct = ((dm_original - dm_price) / dm_original) * 100
        st.markdown(f'''
            <div class="product-description">
                <strong>Price:</strong> 
                <span style="color: #ff6b6b; font-weight: bold;">${dm_price:.2f}</span>
                <span style="color: #999; text-decoration: line-through; margin-left: 10px;">${dm_original:.2f}</span>
                <span style="color: #ff6b6b; margin-left: 10px;">Save {dm_discount_pct:.0f}%</span>
            </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="product-description"><strong>Price:</strong> ${dm_price:.2f}</div>', unsafe_allow_html=True)
    
with col2:
    st.markdown('<div class="product-title">Similar Birkenstock Products</div>', unsafe_allow_html=True)
    
    # Get top matches for the selected Dr. Martens product
    top_matches = selected_data['similarities'][:5]
    
    st.markdown('<div class="section-header">Best Match Selector (Showing Top 5)</div>', unsafe_allow_html=True)
    
    # Use the display logic confirmed as correct by the user
    match_options = [f"{m['birken_name']}" for i, m in enumerate(top_matches)]
    
    # Set default index to 0 (the best match based on new weights)
    default_index = 0
    selected_match_option = st.selectbox("", match_options, index=default_index, label_visibility="collapsed", key=f"match_{selected_idx}")
    
    match_idx = match_options.index(selected_match_option)
    match_data = top_matches[match_idx]

    # Display Birkenstock product image
    birk_image_url = match_data['birken_image']
    if birk_image_url:
        try:
            response = requests.get(birk_image_url, timeout=10)
            img = Image.open(BytesIO(response.content))
            st.image(img, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load Birkenstock image: {e}")
    else:
        st.info("No image available for this product")
    
    st.markdown(f'<a href="{match_data["birken_url"]}" target="_blank" style="color: #4A9EFF; font-size: 16px;">View on Birkenstock.com</a>', unsafe_allow_html=True)

# Price Comparison Section (Full Width Below) - Logic retained from pricing_analysis.py.py
st.markdown('<hr style="border: 1px solid #333; margin: 40px 0;">', unsafe_allow_html=True)
st.markdown('<h2 style="color: white; text-align: center; margin-bottom: 30px;">Price Comparison & Analysis</h2>', unsafe_allow_html=True)

# Get prices
dm_price = selected_data['product'].get('price')
dm_original = selected_data['product'].get('original_price')
birk_original = match_data.get('birken_original_price')
birk_sale = match_data.get('birken_sale_price')

# Determine if items are on sale
dm_is_on_sale = dm_original and dm_price and dm_original > dm_price
birk_is_on_sale = birk_original and birk_sale and birk_original > birk_sale

if dm_price and (birk_sale or birk_original):
    col_price1, col_price2, col_price3 = st.columns(3)
    
    with col_price1:
        if dm_is_on_sale:
            dm_discount_pct = ((dm_original - dm_price) / dm_original) * 100
            st.markdown(f'''
                <div style="background-color: #2a2a2a; padding: 20px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #ff6b6b; margin-bottom: 10px;">Dr. Martens Price (Sale)</h3>
                    <h4 style="color: #999; text-decoration: line-through; margin: 5px 0;">${dm_original:.2f}</h4>
                    <h2 style="color: #ff6b6b; font-size: 36px; margin: 10px 0;">${dm_price:.2f}</h2>
                    <p style="color: #ff6b6b; margin: 5px 0;">Save {dm_discount_pct:.0f}%</p>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div style="background-color: #2a2a2a; padding: 20px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #4A9EFF; margin-bottom: 10px;">Dr. Martens Price</h3>
                    <h2 style="color: white; font-size: 36px; margin: 10px 0;">${dm_price:.2f}</h2>
                </div>
            ''', unsafe_allow_html=True)
    
    with col_price2:
        if birk_is_on_sale:
            birk_discount_pct = ((birk_original - birk_sale) / birk_original) * 100
            st.markdown(f'''
                <div style="background-color: #2a2a2a; padding: 20px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #ff6b6b; margin-bottom: 10px;">Birkenstock Price (Sale)</h3>
                    <h4 style="color: #999; text-decoration: line-through; margin: 5px 0;">${birk_original:.2f}</h4>
                    <h2 style="color: #ff6b6b; font-size: 36px; margin: 10px 0;">${birk_sale:.2f}</h2>
                    <p style="color: #ff6b6b; margin: 5px 0;">Save {birk_discount_pct:.0f}%</p>
                </div>
            ''', unsafe_allow_html=True)
        else:
            price_display = birk_sale if birk_sale else birk_original
            st.markdown(f'''
                <div style="background-color: #2a2a2a; padding: 20px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #4A9EFF; margin-bottom: 10px;">Birkenstock Price</h3>
                    <h2 style="color: white; font-size: 36px; margin: 10px 0;">${price_display:.2f}</h2>
                </div>
            ''', unsafe_allow_html=True)
    
    with col_price3:
        competitor_price = birk_sale if birk_sale else birk_original
        price_diff = dm_price - competitor_price
        price_diff_pct = (price_diff / competitor_price) * 100
        
        if price_diff > 0:
            color = "#ff6b6b"
            symbol = "+"
            label = "Higher"
        else:
            color = "#51cf66"
            symbol = ""
            label = "Lower"
        
        st.markdown(f'''
            <div style="background-color: #2a2a2a; padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="color: {color}; margin-bottom: 10px;">Price Difference</h3>
                <h2 style="color: {color}; font-size: 36px; margin: 10px 0;">{symbol}${abs(price_diff):.2f}</h2>
                <p style="color: {color}; margin: 5px 0;">{symbol}{price_diff_pct:.1f}% {label}</p>
            </div>
        ''', unsafe_allow_html=True)
    
    # Pricing Analysis with Martens sale consideration
    st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
    
    competitor_price = birk_sale if birk_sale else birk_original
    price_diff = dm_price - competitor_price
    price_diff_pct = (price_diff / competitor_price) * 100
    
    analysis_text = ""
    recommendation = ""
    
    # Scenario: Both on sale
    if dm_is_on_sale and birk_is_on_sale:
        dm_discount_pct = ((dm_original - dm_price) / dm_original) * 100
        birk_discount_pct = ((birk_original - birk_sale) / birk_original) * 100
        
        if price_diff > 0:
            if price_diff_pct > 20:
                analysis_text = f"ðŸ”¥ **Dual Promotion Strategy**: Both products are on sale! Your Dr. Martens at **${dm_price:.2f}** (saving {dm_discount_pct:.0f}%) vs Birkenstock at **${birk_sale:.2f}** (saving {birk_discount_pct:.0f}%). You're **${price_diff:.2f} ({price_diff_pct:.1f}%) higher**, but both offers are competitive."
                suggested_price = birk_sale * 1.10
                recommendation = f"**Recommendation**: Excellent position during dual promotions. Maintain or slightly increase your sale discount to **${suggested_price:.2f}** to maximize volume and market share during this promotional window."
            else:
                analysis_text = f"âœ… **Balanced Dual Sale**: Both items on promotion with competitive pricing. Your ${dm_price:.2f} (save {dm_discount_pct:.0f}%) vs Birkenstock ${birk_sale:.2f} (save {birk_discount_pct:.0f}%). Pricing is well-aligned."
                recommendation = f"**Recommendation**: Maintain current sale pricing. Both brands are attractively positioned. Monitor sales velocity and extend promotion if conversion rates remain strong."
        else:
            analysis_text = f"ðŸ’Ž **Value Leader on Sale**: Excellent! You're beating their sale price. Your Dr. Martens at **${dm_price:.2f}** (save {dm_discount_pct:.0f}%) is **${abs(price_diff):.2f} lower** than Birkenstock's sale at **${birk_sale:.2f}** (save {birk_discount_pct:.0f}%)."
            price_increase = abs(price_diff) * 0.5
            recommendation = f"**Recommendation**: Strong value positioning. You can increase price by **${price_increase:.2f}** to **${dm_price + price_increase:.2f}** while still undercutting their sale. This improves margins while maintaining market leadership."
    
    # Scenario: Only Martens on sale
    elif dm_is_on_sale and not birk_is_on_sale:
        dm_discount_pct = ((dm_original - dm_price) / dm_original) * 100
        
        if price_diff > 0:
            analysis_text = f"ðŸŽ¯ **Targeted Sale Strategy**: Your Dr. Martens sale at **${dm_price:.2f}** (save {dm_discount_pct:.0f}% off ${dm_original:.2f}) positions you **${price_diff:.2f} ({price_diff_pct:.1f}%) higher** than Birkenstock's regular price (${competitor_price:.2f})."
            if price_diff_pct > 15:
                recommendation = f"**Recommendation**: Your sale is aggressive but still above competitor. Strong market position. Maintain sale through period or extend if conversion is high. Post-sale, price at **${dm_original:.2f}** to establish premium positioning."
            else:
                recommendation = f"**Recommendation**: Sale pricing is competitive. Maintain current promotion to capture price-sensitive customers while staying above base competitor price. Consider extending sale if momentum continues."
        else:
            analysis_text = f"ðŸ† **Market Leader Sale**: Your sale at **${dm_price:.2f}** (save {dm_discount_pct:.0f}%) beats Birkenstock's regular price of **${competitor_price:.2f}** by **${abs(price_diff):.2f}**. Dominant positioning."
            recommendation = f"**Recommendation**: Excellent sale differentiation. You're undercutting their regular price significantly. Maximize marketing spend during this window. After sale, evaluate repeat purchase potential before returning to regular pricing."
    
    # Scenario: Only Birkenstock on sale
    elif not dm_is_on_sale and birk_is_on_sale:
        birk_discount_pct = ((birk_original - birk_sale) / birk_original) * 100
        
        if price_diff > 0:
            if price_diff_pct > 30:
                analysis_text = f"**Competitor Sale Pressure**: Birkenstock is aggressively promoting at **${birk_sale:.2f}** (save {birk_discount_pct:.0f}% off ${birk_original:.2f}). Your Dr. Martens at **${dm_price:.2f}** is **${price_diff:.2f} ({price_diff_pct:.1f}%) higher**."
                suggested_price = birk_sale * 1.15
                recommendation = f"**Recommendation**: Counter with a targeted promotion. Suggest sale price: **${suggested_price:.2f}** (a **${dm_price - suggested_price:.2f}** reduction). This maintains brand premium while remaining competitive during their promotional period."
            else:
                analysis_text = f"**Competitive Pressure**: Birkenstock sale at **${birk_sale:.2f}** (save {birk_discount_pct:.0f}%) vs your **${dm_price:.2f}**. Moderate gap of **${price_diff:.2f} ({price_diff_pct:.1f}%)**."
                recommendation = f"**Recommendation**: Monitor sales impact closely. If conversions drop >20%, launch a limited-time promotion to **${dm_price * 0.95:.2f}** to recapture market share. Otherwise, emphasize Dr. Martens durability and heritage to justify premium."
        else:
            analysis_text = f"**Premium Positioning Against Sale**: You're trading at **${dm_price:.2f}** while Birkenstock promotes at **${birk_sale:.2f}**. Despite their sale, you're **${abs(price_diff):.2f} lower**."
            recommendation = f"**Recommendation**: Unusual market advantage. Emphasize quality/heritage to justify pricing. Consider a modest **${5-10:.2f}** price increase to optimize margins, as you're already beating their promotion price."
    
    # Scenario: Neither on sale (regular pricing)
    else:
        if price_diff > 0:
            if price_diff_pct > 40:
                analysis_text = f"Premium Brand Positioning: At **${dm_price:.2f}**, you're **${price_diff:.2f} ({price_diff_pct:.1f}%) higher** than Birkenstock's **${competitor_price:.2f}**. This premium requires strong brand justification."
                suggested_price = competitor_price * 1.25
                recommendation = f"Recommendation: Premium positioning is high. If sales are slow, consider reducing to **${suggested_price:.2f}** to capture more market share. Alternatively, invest heavily in heritage/craftsmanship marketing to justify the premium."
            else:
                analysis_text = f"Standard Premium Strategy: Your **${dm_price:.2f}** is **${price_diff:.2f} ({price_diff_pct:.1f}%) higher** than Birkenstock's **${competitor_price:.2f}**. Aligns with brand positioning."
                recommendation = f"Recommendation: Pricing appropriate for brand value. Monitor conversion rates. If below target, test a **${10:.2f}** reduction to **${dm_price - 10:.2f}**. Otherwise, maintain and emphasize quality differentiation."
        else:
            analysis_text = f"Value Leader: At **${dm_price:.2f}**, you're **${abs(price_diff):.2f} ({abs(price_diff_pct):.1f}%) lower** than Birkenstock's **${competitor_price:.2f}**. Strong value proposition."
            price_increase = abs(price_diff) * 0.6
            recommendation = f"Recommendation: Significant upside opportunity. Increase price by **${price_increase:.2f}** to **${dm_price + price_increase:.2f}** to optimize margins while maintaining competitive advantage."
    
    st.markdown(f'''
        <div style="background-color: #2a2a2a; padding: 25px; border-radius: 10px; margin-top: 20px;">
            <h3 style="color: white; margin-bottom: 15px;"> Pricing Intelligence & Strategic Recommendations</h3>
            <p style="color: #e0e0e0; font-size: 16px; line-height: 1.8; margin-bottom: 20px;">{analysis_text}</p>
            <p style="color: #4A9EFF; font-size: 16px; line-height: 1.8; font-weight: 600;">{recommendation}</p>
        </div>
    ''', unsafe_allow_html=True)
else:
    if dm_price:
        competitor_name = match_data.get('birken_name', 'this competitor product')
        st.markdown(f'''
            <div style="background-color: #2a2a2a; padding: 25px; border-radius: 10px; text-align: center;">
                <h3 style="color: #ff9800; margin-bottom: 15px;"> Limited Price Data Available</h3>
                <p style="color: #e0e0e0; font-size: 16px; margin-bottom: 15px;">
                    Your Dr. Martens product is priced at <strong style="color: #4A9EFF;">${dm_price:.2f}</strong>
                </p>
                <p style="color: #999; font-size: 14px;">
                    Price information for {competitor_name} is currently unavailable. 
                    This may be due to the product being out of stock, region-restricted, or temporarily unlisted.
                </p>
                <p style="color: #999; font-size: 14px; margin-top: 15px;">
                    <strong>Suggestion:</strong> Try comparing with other similar products in the list above, or check the Birkenstock website directly.
                </p>
            </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('''
            <div style="background-color: #2a2a2a; padding: 25px; border-radius: 10px; text-align: center;">
                <p style="color: #999; font-size: 16px;">Price information unavailable for comparison</p>
            </div>
        ''', unsafe_allow_html=True)