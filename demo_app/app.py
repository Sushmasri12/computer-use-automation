from flask import Flask, render_template, request

app = Flask(__name__)

# Fake member data for the local banking demo.
# No real customer information is used.
MEMBERS = {
    "12345": {
        "name": "Alex Johnson",
        "checking_balance": "$2,450.25",
        "savings_balance": "$8,720.50",
        "status": "Active",
    },
    "67890": {
        "name": "Taylor Smith",
        "checking_balance": "$1,120.00",
        "savings_balance": "$5,340.75",
        "status": "Active",
    },
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/member/search", methods=["POST"])
def search_member():
    member_id = request.form.get("member_id", "").strip()

    if not member_id:
        return render_template(
            "not_found.html",
            message="Member ID is required.",
            member_id=member_id,
        ), 400

    member = MEMBERS.get(member_id)

    if member is None:
        return render_template(
            "not_found.html",
            message="Member not found.",
            member_id=member_id,
        ), 404

    return render_template(
        "member.html",
        member_id=member_id,
        member=member,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)