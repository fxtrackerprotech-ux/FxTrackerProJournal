from flask import Flask, request, jsonify
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# -------------------------
# Google Sheets setup
# -------------------------
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds_json = os.environ.get("GOOGLE_CREDS_JSON")
sheet_id = os.environ.get("SHEET_ID")

sheet = None
if creds_json and sheet_id:
    try:
        creds_dict = eval(creds_json)  # JSON string from environment variable
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1
    except Exception as e:
        print("Google Sheets authorization failed:", e)

# -------------------------
# Email setup
# -------------------------
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
BLANK_JOURNAL_LINK = os.environ.get("BLANK_JOURNAL_LINK")
DEMO_JOURNAL_LINK = os.environ.get("DEMO_JOURNAL_LINK")
LOGO_URL = os.environ.get("LOGO_URL")

# -------------------------
# Send branded HTML email
# -------------------------
def send_email(first_name, to_email):
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your FxTracker Pro Journal™ is Ready!"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Your FxTracker Pro Journal™ is Ready!</title>
</head>
<body style="margin:0; padding:0; font-family: Arial, sans-serif; background-color:#f4f6f8; color:#333;">
<table align="center" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; background:#ffffff; margin:20px auto; border-radius:10px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1);">

<tr>
<td align="center" style="padding:20px; background-color:#0a2a43; color:#ffffff;">
<img src="{LOGO_URL}" alt="FxTracker Pro Tech Logo" width="100" style="margin-bottom:10px;">
<h1 style="margin:0; font-size:22px;">FxTracker Pro Journal™ Delivery</h1>
<p style="margin:5px 0 0; font-size:14px; font-style:italic;">Smart Tracking, Powered by Innovations 💡</p>
</td>
</tr>

<tr>
<td style="padding:20px;">
<p style="font-size:16px;">Hi <strong>{first_name}</strong>,</p>
<p style="font-size:15px; line-height:1.6;">
Congratulations on taking a big step toward improving your trading journey! 🚀<br><br>
Your purchase of the <strong>FxTracker Pro Journal™ V1.0</strong> has been successfully confirmed. We’re excited to deliver your files and help you trade smarter, with more structure, discipline, and confidence.
</p>
</td>
</tr>

<tr>
<td style="padding:20px; text-align:center;">
<h2 style="font-size:18px; margin-bottom:15px;">📂 Your Downloads</h2>
<a href="{BLANK_JOURNAL_LINK}" style="display:inline-block; background:#1e88e5; color:#ffffff; padding:12px 24px; margin:8px; border-radius:6px; text-decoration:none; font-size:15px; font-weight:bold;">
📘 Download Blank Journal
</a>
<a href="{DEMO_JOURNAL_LINK}" style="display:inline-block; background:#43a047; color:#ffffff; padding:12px 24px; margin:8px; border-radius:6px; text-decoration:none; font-size:15px; font-weight:bold;">
📗 Download Demo Journal
</a>
<p style="margin-top:15px; font-size:13px; color:#666;">
*Both links will open instantly. Please save a copy to your Google Drive for lifetime use.*
</p>
</td>
</tr>

<tr>
<td style="padding:20px;">
<h3 style="font-size:16px;">💡 Why These Files Matter</h3>
<ul style="font-size:14px; line-height:1.6; padding-left:20px;">
<li><strong>Blank Journal</strong> → Your personal trading companion. Log trades, track performance, manage risk, and improve consistency.</li>
<li><strong>Demo Journal</strong> → See how professionals use it. The 100 filled sample trades highlight how each section works, giving you a clear roadmap to follow.</li>
</ul>
</td>
</tr>

<tr>
<td style="padding:20px; background:#f9fafb;">
<p style="font-size:15px; line-height:1.6;">
🌟 <strong>A Word of Encouragement:</strong><br>
Trading success is built on discipline and consistency—not luck. FxTracker Pro Journal™ is designed to keep you accountable, help you spot patterns, and grow into a more profitable trader over time.<br><br>
Remember: <em>“What gets measured, gets improved.”</em><br><br>
You’ve now joined a growing community of traders who choose innovation over guesswork. 💪
</p>
</td>
</tr>

<tr>
<td style="padding:20px;">
<h3 style="font-size:16px;">🛠️ Support & Updates</h3>
<p style="font-size:14px; line-height:1.6;">
You’ll receive all future updates <strong>100% free</strong> as part of your lifetime access.<br>
If you need help setting up or have any questions, just reply to this email—we’ve got your back.
</p>
</td>
</tr>

<tr>
<td style="padding:20px; text-align:left;">
<p style="font-size:15px;">
Warm regards,<br>
<strong>The FxTracker Pro Tech Team</strong><br>
<em>Smart Tracking, Powered by Innovations 💡</em>
</p>
</td>
</tr>

<tr>
<td style="padding:15px; text-align:center; background:#0a2a43; color:#ffffff; font-size:12px;">
© 2025 FxTracker Pro Tech. All rights reserved.<br>
This email and its attachments are intended solely for the buyer. Do not share or resell without authorization.
</td>
</tr>

</table>
</body>
</html>
"""

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print("Email error:", e)
        return False

# -------------------------
# Tally.so webhook
# -------------------------
@app.route("/tally-webhook", methods=["POST"])
def tally_webhook():
    data = request.json
    submission_id = data.get("submissionId")
    first_name = data.get("firstName")
    buyer_email = data.get("email")

    if sheet:
        try:
            sheet.append_row([submission_id, first_name, buyer_email, "pending"])
        except Exception as e:
            print("Error updating sheet:", e)

    return jsonify({"status": "pending", "submissionId": submission_id})

# -------------------------
# CryptoCloud webhook
# -------------------------
@app.route("/cryptocloud-webhook", methods=["POST"])
def cryptocloud_webhook():
    data = request.json
    status = data.get("status")
    buyer_email = data.get("email")

    if sheet:
        try:
            cell = sheet.find(buyer_email)
            if cell:
                sheet.update_cell(cell.row, 4, status)
                if status.lower() == "paid":
                    first_name = sheet.cell(cell.row, 2).value
                    send_email(first_name, buyer_email)
        except Exception as e:
            print("Error updating sheet on CryptoCloud webhook:", e)

    return jsonify({"status": status, "buyer": buyer_email})

# -------------------------
# Root route
# -------------------------
@app.route("/")
def home():
    return "🚀 FxTracker Pro Tech Middleware is running!"

# -------------------------
# Start Flask using Render's PORT
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
