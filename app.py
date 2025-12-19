from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    mood_color = None
    mood_text = None

    if request.method == "POST":
        mood_color = request.form.get("mood_color")
        mood_text = request.form.get("mood_text")

    return render_template("index.html", mood_color=mood_color, mood_text=mood_text)

if __name__ == "__main__":
    app.run(debug=True)
