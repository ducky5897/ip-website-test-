
import os
import secrets
import logging
from datetime import datetime, timezone
from ipaddress import ip_address

import psycopg
from flask import (
    Flask, request, session, redirect,
    url_for, render_template_string, jsonify
)
from werkzeug.security import (
    check_password_hash, generate_password_hash
)
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

app.secret_key = os.environ["SECRET_KEY"]

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.environ["DATABASE_URL"]
ADMIN_PASSWORD_HASH = os.environ["ADMIN_PASSWORD_HASH"]

# Alleen aanzetten als Render de inkomende
# X-Forwarded-For-header veilig overschrijft.
if os.getenv("TRUST_PROXY") == "1":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)


def db():
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg.connect(url)


def initialize_database():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consents (
                id BIGSERIAL PRIMARY KEY,
                ip_address TEXT NOT NULL,
                consented_at TIMESTAMPTZ NOT NULL,
                purpose TEXT NOT NULL
            )
        """)


def get_client_ip():
    raw = request.remote_addr

    if not raw:
        return None

    try:
        return str(ip_address(raw))
    except ValueError:
        return None


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def valid_csrf():
    return secrets.compare_digest(
        session.get("csrf", ""),
        request.form.get("csrf", "")
    )


@app.route("/")
def home():
    return """
    <h1>Welkom op mijn website</h1>
    <p>Bekijk ons privacybeleid voordat je toestemming geeft.</p>
    <a href="/consent">Toestemming bekijken</a>
    """


@app.route("/consent", methods=["GET", "POST"])
def consent():
    if request.method == "GET":
        return render_template_string("""
        <h2>Toestemming</h2>
        <p>Wij willen het aantal mensen optellen 
        die deze site dagelijks komen zou u 
        toestemming kunnen geven?.</p>
        <form method="POST">
            <input type="hidden" name="csrf" value="{{ token }}">
            <label>
                <input type="checkbox" name="agree"
                       value="yes" required>
                Ik geef toestemming voor deze verwerking.
            </label>
            <br><br>
            <button type="submit">Toestemming geven</button>
        </form>
        """, token=csrf_token())

    if not valid_csrf():
        return "Ongeldig verzoek", 400

    if request.form.get("agree") != "yes":
        return "Geen toestemming gegeven", 400

    client_ip = get_client_ip()

    if not client_ip:
        return "IP-adres kon niet veilig worden vastgesteld", 400

    with db() as conn:
        conn.execute("""
            INSERT INTO consents
            (ip_address, consented_at, purpose)
            VALUES (%s, %s, %s)
        """, (
            client_ip,
            datetime.now(timezone.utc),
            "Websitebeveiliging"
        ))

    session.pop("csrf", None)

    return """
    <h2>Bedankt!</h2>
    <p>Je toestemming is geregistreerd.</p>
    """


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template_string("""
        <h2>Beheerderslogin</h2>
        <form method="POST">
            <input type="hidden" name="csrf" value="{{ token }}">
            <input type="password" name="password"
                   placeholder="Wachtwoord" required>
            <button type="submit">Inloggen</button>
        </form>
        """, token=csrf_token())

    if not valid_csrf():
        return "Ongeldig verzoek", 400

    password = request.form.get("password", "")

    if check_password_hash(ADMIN_PASSWORD_HASH, password):
        session.clear()
        session["admin"] = True
        session["csrf"] = secrets.token_urlsafe(32)
        return redirect(url_for("admin"))

    return "Onjuist wachtwoord", 401


@app.route("/admin", methods=["GET"])
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    with db() as conn:
        records = conn.execute("""
            SELECT id, ip_address, consented_at, purpose
            FROM consents
            ORDER BY consented_at DESC
            LIMIT 500
        """).fetchall()

    return render_template_string("""
    <h1>Admin dashboard</h1>
    <p>Geregistreerde toestemmingen: {{ records|length }}</p>

    <table border="1" cellpadding="8">
        <tr>
            <th>ID</th>
            <th>IP-adres</th>
            <th>Datum en tijd (UTC)</th>
            <th>Doel</th>
        </tr>
        {% for r in records %}
        <tr>
            <td>{{ r[0] }}</td>
            <td>{{ r[1] }}</td>
            <td>{{ r[2] }}</td>
            <td>{{ r[3] }}</td>
        </tr>
        {% endfor %}
    </table>

    <br>
    <form method="POST" action="/admin/logout">
        <input type="hidden" name="csrf" value="{{ token }}">
        <button type="submit">Uitloggen</button>
    </form>
    """, records=records, token=csrf_token())


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    if not session.get("admin") or not valid_csrf():
        return "Ongeldig verzoek", 403

    session.clear()
    return redirect(url_for("admin_login"))


@app.errorhandler(500)
def internal_error(error):
    app.logger.exception("Interne serverfout")
    return "Er is een serverfout opgetreden.", 500


initialize_database()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
