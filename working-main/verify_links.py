
import os
import re
from urllib.parse import urlparse

BASE_DIR = r"c:\Users\HIMU\OneDrive\Desktop\working"
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Flask Routes Definition (from app.py)
ROUTES = {
    "/": "front.html",
    "/main": "Main-page.html",
    "/signup": "signupcommon.html",
    "/get-started": "get-started.html",
    "/connection": "connection.html",
    "/unityhub/auth": "stu-ngo-login.html",
    "/signup/patient": "patient-signup.html",
    "/signup/guardian": "create-user.html",
    "/after-signup": "aftergardian.html",
    "/login": "logincommon.html",
    "/login/guardian": "gardianlogin.html",
    "/login/patient": "patient-login.html",
    "/guardian-dashboard": "guardian-dashboard.html",
    "/patient-dashboard": "patient-dashboard.html",
    "/notifications": "notifications.html"
}

# Assume these static assets exist based on previous checks
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def check_file(filepath):
    """Parses HTML file and checks href/src links."""
    if not os.path.exists(filepath):
        print(f"[ERROR] Template not found: {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all href="..." and src="..."
    links = re.findall(r'(href|src)=["\'](.*?)["\']', content)

    print(f"\nChecking: {os.path.basename(filepath)}")
    for attr, link in links:
        # Ignore external links, anchors, and scripts/css cdns
        if link.startswith("http") or link.startswith("#") or link.startswith("mailto:") or link.startswith("tel:"):
            continue
        
        # Check if it's a Flask route
        if link in ROUTES or link.startswith("/trigger-") or link.startswith("/upload-") or link == "/api/create-account" or link == "/check-emergency" or link == "/signup-patient":
            # Valid route
            continue
        
        # Check if it's a static asset
        if link.startswith("/assets/"):
            asset_name = link.replace("/assets/", "")
            asset_path = os.path.join(ASSETS_DIR, asset_name)
            if not os.path.isfile(asset_path):
                 print(f"  [MISSING ASSET] {link}")
            continue

        # Suspicious relative path or unknown route
        print(f"  [WARNING] Suspicious link: {link}")

if __name__ == "__main__":
    print("Starting Static Link Verification...")
    for route, template in ROUTES.items():
        fullpath = os.path.join(TEMPLATES_DIR, template)
        check_file(fullpath)
    print("\nVerification Complete.")
