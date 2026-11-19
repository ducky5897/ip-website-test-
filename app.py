
from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import BadRequest
from ipaddress import ip_address
from datetime import datetime, timezone
import os
import logging

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Render reverse proxy:
# Alleen inschakelen als je deployment daadwerkelijk
# achter precies één vertrouwde proxylaag staat.
TRUST_PROXY = os.getenv("TRUST_PROXY", "false").lower() == "true"

if TRUST_PROXY:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=0,
        x_port=0,
        x_prefix=0
    )


def get_client_ip():
    """
    Haalt het IP-adres op dat door de vertrouwde
    proxyconfiguratie aan Flask is doorgegeven.
    """

    raw_ip = request.remote_addr

    if not raw_ip:
        return None

    try:
        return str(ip_address(raw_ip))
    except ValueError:
        logger.warning("Ongeldig client-IP ontvangen")
        return None


@app.route("/")
def home():
    return """
    <h1>Mijn website</h1>
    <p>Welkom!</p>
    <a href="/consent">IP-toestemming bekijken</a>
    """


@app.route("/consent", methods=["GET"])
def consent():
    return """
    <h2>Privacy en IP-adres</h2>
    <p>Deze website kan je IP-adres verwerken voor
    beveiligingsdoeleinden.</p>

    <form action="/consent" method="POST">
        <label>
            <input type="checkbox" name="agree" value="yes" required>
            Ik geef toestemming voor deze verwerking.
        </label>
        <br><br>
        <button type="submit">Toestemming geven</button>
    </form>
    """


@app.route("/consent", methods=["POST"])
def save_consent():
    if request.form.get("agree") != "yes":
        return jsonify({"error": "Geen toestemming gegeven"}), 400

    client_ip = get_client_ip()

    if not client_ip:
        return jsonify({"error": "IP kon niet worden vastgesteld"}), 400

    # Bewaar toestemming alleen met een passende,
    # beveiligde opslag en een duidelijk privacybeleid.
    logger.info(
        "Toestemming geregistreerd op %s",
        datetime.now(timezone.utc).isoformat()
    )

    return jsonify({
        "success": True,
        "message": "Toestemming geregistreerd."
    })


@app.route("/api/my-ip")
def my_ip():
    client_ip = get_client_ip()

    if not client_ip:
        return jsonify({"error": "IP niet beschikbaar"}), 400

    return jsonify({
        "ip": client_ip,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Pagina niet gevonden"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Interne serverfout"}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
