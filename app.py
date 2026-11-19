
from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <title>Netwerkdiagnostiek</title>
    </head>
    <body>
        <h1>Welkom!</h1>
        <p>
        Deze website telt het aantal bezoekers op
        per dag kunt u toesteming geven voor 
        meer het aantal bezoekers
        </p>
        <form method="POST" action="/akkoord">
            <button type="submit">
                Ik geef toestemming
            </button>
        </form>
    </body>
    </html>
    """

@app.route("/akkoord", methods=["POST"])
def akkoord():
    ip = request.remote_addr
print("Remote:", request.remote_addr)
print("X-Forwarded-For aanwezig:",
      bool(request.headers.get("X-Forwarded-For")))
print("X-Real-IP aanwezig:",
      bool(request.headers.get("X-Real-IP")))
    print("Remote address:", request.remote_addr)
    print("Aantal doorgestuurde IP-adressen:",
      len(request.headers.getlist("X-Forwarded-For")))

    print("Bezoeker heeft toestemming gegeven.")
    print("Proxy-header aanwezig:", bool(request.headers.get("X-Forwarded-For")))

    return """
    <h1>Bedankt!</h1>
    <p>Je toestemming is geregistreerd.</p>
    """

if __name__ == "__main__":
    app.run()
