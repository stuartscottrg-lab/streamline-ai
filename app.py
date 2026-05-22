"""
Stu Legal — Flask Backend
Handles: lead capture, AI chat qualification, email notifications
"""
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
import anthropic

app = Flask(__name__, static_folder='static')

# ── CONFIG (set these as environment variables) ──────────────────────────────
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
SMTP_HOST         = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT         = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER         = os.getenv('SMTP_USER', '')          # your Gmail address
SMTP_PASS         = os.getenv('SMTP_PASS', '')          # Gmail app password
NOTIFY_EMAIL      = os.getenv('NOTIFY_EMAIL', '')       # where to send lead alerts
CALENDLY_URL      = os.getenv('CALENDLY_URL', 'https://calendly.com/your-link')

# ── AI CLIENT ─────────────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

SYSTEM_PROMPT = """You are the Stu Legal assistant — a helpful, professional sales qualifier for a UK-based AI automation agency that works exclusively with professional services firms (law firms, financial advisors, and accountancy practices).

Your job is to:
1. Understand the prospect's business and pain points
2. Qualify whether they're a good fit for AI automation
3. Build interest in booking a free AI audit call
4. Answer questions about services honestly and helpfully

Key services:
- Done-For-You AI System: from £2,500 one-time — chatbot, booking automation, email sequences, CRM setup, deployed in 72 hours
- AI Retainer: from £750/month — ongoing builds, optimisation, monthly strategy
- AI Business Course: £497 — self-implement everything yourself

Tone: confident, professional, warm — not pushy. You're an expert advisor, not a salesperson.
Keep responses concise (2-4 sentences max). If someone asks to book a call, direct them to scroll up to the booking section.
If someone seems interested, ask a qualifying question: how many new enquiries do they get per week, what's their biggest time drain, etc.

Never make up specific stats or claim results you can't verify. Be honest."""


# ── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


@app.route('/api/lead', methods=['POST'])
def capture_lead():
    """Capture lead from free checklist form, send notification email."""
    data = request.get_json(silent=True) or {}
    name      = data.get('name', '').strip()
    email     = data.get('email', '').strip()
    firm_type = data.get('firm_type', '').strip()

    if not name or not email:
        return jsonify({'error': 'Name and email required'}), 400

    # Log to file as simple CRM
    _log_lead(name, email, firm_type)

    # Send notification to you
    if NOTIFY_EMAIL and SMTP_USER:
        _send_lead_notification(name, email, firm_type)

    # Send welcome email to lead
    if SMTP_USER:
        _send_welcome_email(name, email, firm_type)

    return jsonify({'status': 'ok'}), 200


@app.route('/api/chat', methods=['POST'])
def chat():
    """AI chat qualification endpoint."""
    data = request.get_json(silent=True) or {}
    messages = data.get('messages', [])

    if not messages:
        return jsonify({'reply': 'Hello! How can I help you today?'}), 200

    # Sanitise — keep only role/content, max last 20 turns
    safe_messages = [
        {'role': m['role'], 'content': str(m['content'])[:1000]}
        for m in messages[-20:]
        if m.get('role') in ('user', 'assistant') and m.get('content')
    ]

    if not client:
        return jsonify({'reply': (
            "Thanks for reaching out! Our AI assistant is being configured. "
            "In the meantime, please email hello@stulegal.co.uk or book a call above."
        )}), 200

    try:
        response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=safe_messages,
        )
        reply = response.content[0].text
        return jsonify({'reply': reply}), 200
    except Exception as e:
        app.logger.error(f'Chat error: {e}')
        return jsonify({'reply': (
            "I'm having a brief technical issue. Please email hello@stulegal.co.uk "
            "or book a call — we'd love to chat."
        )}), 200


@app.route('/api/leads', methods=['GET'])
def list_leads():
    """Simple internal endpoint to view captured leads (protect in production)."""
    secret = request.args.get('secret', '')
    if secret != os.getenv('ADMIN_SECRET', 'changeme'):
        return jsonify({'error': 'Unauthorised'}), 401
    try:
        with open('leads.jsonl', 'r') as f:
            leads = [json.loads(l) for l in f if l.strip()]
        return jsonify({'leads': leads, 'count': len(leads)}), 200
    except FileNotFoundError:
        return jsonify({'leads': [], 'count': 0}), 200


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _log_lead(name, email, firm_type):
    entry = {
        'name': name,
        'email': email,
        'firm_type': firm_type,
        'timestamp': datetime.utcnow().isoformat(),
    }
    with open('leads.jsonl', 'a') as f:
        f.write(json.dumps(entry) + '\n')


def _send_lead_notification(name, email, firm_type):
    subject = f"New Stu Legal Lead: {name} ({firm_type})"
    body = f"""New lead captured on Stu Legal website!

Name:      {name}
Email:     {email}
Firm Type: {firm_type}
Time:      {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

They downloaded the AI Automation Audit Checklist.
Follow up within 24 hours.

Calendly: {CALENDLY_URL}
"""
    _send_email(NOTIFY_EMAIL, subject, body)


def _send_welcome_email(name, email, firm_type):
    first_name = name.split()[0] if name else 'there'
    subject = "Your AI Automation Audit Checklist — Stu Legal"
    body = f"""Hi {first_name},

Thanks for downloading the Stu Legal Automation Audit Checklist!

You'll find the 47-point checklist attached. Work through each section to identify every automation opportunity in your {firm_type or 'practice'}.

While you're reviewing it, here are the three highest-impact areas we see in most {firm_type or 'professional services'} firms:

1. Enquiry Response — most firms respond to new enquiries 4–24 hours late. AI can respond in seconds, 24/7.
2. Booking & Scheduling — phone tag and back-and-forth emails cost 3–5 hours a week. Automated booking eliminates this entirely.
3. Client Onboarding — manual intake forms and document chasing is the #1 time drain we hear about. It's also the easiest to automate.

If you'd like to discuss what this could look like for your specific firm, I'd be happy to do a free 30-minute AI Audit call — no obligation, just a clear picture of what's possible.

Book here: {CALENDLY_URL}

Best,
The Stu Legal Team

---
Stu Legal | AI Automation for Professional Services
hello@stulegal.co.uk
Unsubscribe: reply with "unsubscribe"
"""
    _send_email(email, subject, body)


def _send_email(to, subject, body):
    if not SMTP_USER or not SMTP_PASS:
        app.logger.warning(f'Email not configured — would have sent to {to}: {subject}')
        return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Stu Legal <{SMTP_USER}>'
        msg['To']      = to
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to, msg.as_string())
    except Exception as e:
        app.logger.error(f'Email error to {to}: {e}')


if __name__ == '__main__':
    app.run(debug=True, port=5050)
