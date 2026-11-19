
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

    print("Remote address:", request.remote_addr)
    print("Forwarded header aanwezig:",
          bool(request.headers.get("X-Forwarded-For")))

    print("Bezoeker heeft toestemming gegeven.")
    print("Publiek IP-adres:", ip)

    return """
    <h1>Bedankt!</h1>
    <p>Je toestemming is geregistreerd.</p>
    """

if __name__ == "__main__":
    app.run()
