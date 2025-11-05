from flask import Flask, request, render_template
import os
from extractor import extract_payment_info

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["pdf"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        info = extract_payment_info(path)

        return render_template("index.html", info=info)

    return render_template("index.html", info=None)


if __name__ == "__main__":
    app.run(debug=True)
