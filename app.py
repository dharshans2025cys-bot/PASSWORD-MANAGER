from flask import Flask, render_template, request, redirect, session
import base64
import os
import re

app = Flask(__name__)
app.secret_key = "secret123"

PASS_FILE = "pass.txt"
PIN_FILE = "pin.txt"

# Ensure files exist
for f in [PASS_FILE, PIN_FILE]:
    if not os.path.exists(f):
        open(f, "w").close()


# HOME
@app.route("/")
def home():
    return render_template("index.html")


# REGISTER
@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/save", methods=["POST"])
def save():
    username = request.form["username"]
    password = request.form["password"]

    encoded = base64.b64encode(password.encode()).decode()

    with open(PASS_FILE, "a") as f:
        f.write(f"{username}:{encoded}\n")

    return redirect("/register")


# ---------------- PIN SYSTEM ---------------- #

def get_saved_pin():
    if os.path.getsize(PIN_FILE) == 0:
        return None
    with open(PIN_FILE, "r") as f:
        return f.read().strip()


@app.route("/pin", methods=["GET", "POST"])
def pin():
    saved_pin = get_saved_pin()

    # First-time PIN setup
    if saved_pin is None:
        if request.method == "POST":
            new_pin = request.form["pin"]
            encoded = base64.b64encode(new_pin.encode()).decode()

            with open(PIN_FILE, "w") as f:
                f.write(encoded)

            session["auth"] = True
            return redirect("/view_data")

        return render_template("pin.html", setup=True)

    # Normal PIN check
    if request.method == "POST":
        entered = request.form["pin"]
        decoded = base64.b64decode(saved_pin).decode()

        if entered == decoded:
            session["auth"] = True
            return redirect("/view_data")
        else:
            return render_template("pin.html", error="Wrong PIN")

    return render_template("pin.html", setup=False)


# CHANGE PIN
@app.route("/change_pin", methods=["POST"])
def change_pin():
    new_pin = request.form["new_pin"]
    encoded = base64.b64encode(new_pin.encode()).decode()

    with open(PIN_FILE, "w") as f:
        f.write(encoded)

    return redirect("/view_data")


# 🔥 UPDATED: ALWAYS ASK PIN
@app.route("/view")
def view():
    session.pop("auth", None)   # remove access every time
    return redirect("/pin")


# 🔥 NEW: ACTUAL VIEW PAGE
@app.route("/view_data")
def view_data():
    if not session.get("auth"):
        return redirect("/pin")

    data = []

    with open(PASS_FILE, "r") as f:
        for line in f:
            try:
                username, encoded = line.strip().split(":")
                decoded = base64.b64decode(encoded).decode()
                data.append((username, decoded))
            except:
                pass

    return render_template("view.html", data=data)


# LOGOUT
@app.route("/logout")
def logout():
    session.pop("auth", None)
    return redirect("/")


# DECODE
@app.route("/decode")
def decode_page():
    return render_template("decode.html")


@app.route("/decode_result", methods=["POST"])
def decode_result():
    encoded = request.form["encoded"]

    try:
        decoded = base64.b64decode(encoded).decode()
    except:
        decoded = "Invalid input"

    return render_template("decode.html", result=decoded)


# STRENGTH
@app.route("/strength")
def strength():
    return render_template("strength.html")


@app.route("/check_strength", methods=["POST"])
def check_strength():
    password = request.form["password"]

    strength = 0
    if len(password) >= 6: strength += 1
    if re.search(r"[A-Z]", password): strength += 1
    if re.search(r"[0-9]", password): strength += 1
    if re.search(r"[^A-Za-z0-9]", password): strength += 1

    levels = ["Very Weak", "Weak", "Medium", "Strong", "Very Strong"]
    result = levels[strength]

    return render_template("strength.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
