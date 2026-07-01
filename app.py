from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import csv
import os
from datetime import datetime

app = Flask(__name__)

JOBS_CSV = "data/jobs.csv"
APPLICATIONS_CSV = "data/applications.csv"


def load_jobs():
    if not os.path.exists(JOBS_CSV):
        return pd.DataFrame()

    df = pd.read_csv(JOBS_CSV)
    df = df.fillna("")
    return df


@app.route("/")
def home():
    return render_template("search.html")


@app.route("/search")
def search_jobs():
    keyword = request.args.get("keyword", "").strip().lower()
    df = load_jobs()

    if df.empty:
        jobs = []
    elif keyword == "":
        jobs = df.to_dict(orient="records")
    else:
        mask = (
            df["title"].astype(str).str.lower().str.contains(keyword, na=False)
            | df["company"].astype(str).str.lower().str.contains(keyword, na=False)
            | df["description"].astype(str).str.lower().str.contains(keyword, na=False)
            | df["location"].astype(str).str.lower().str.contains(keyword, na=False)
        )
        jobs = df[mask].to_dict(orient="records")

    return render_template("search.html", jobs=jobs, keyword=keyword)


@app.route("/job/<job_id>")
def job_detail(job_id):
    df = load_jobs()

    job_row = df[df["id"].astype(str) == str(job_id)]

    if job_row.empty:
        return "Job not found", 404

    job = job_row.iloc[0].to_dict()
    return render_template("job_detail.html", job=job)

@app.route("/apply", methods=["POST"])
def apply():
    data = request.get_json()

    job_id = data.get("job_id", "")
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()

    if not name or not email or not phone:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    df = load_jobs()
    job_row = df[df["id"].astype(str) == str(job_id)]

    if job_row.empty:
        return jsonify({"success": False, "message": "Job not found"}), 404

    job = job_row.iloc[0].to_dict()

    file_exists = os.path.exists(APPLICATIONS_CSV)
    file_empty = (not file_exists) or os.path.getsize(APPLICATIONS_CSV) == 0

    # Ensure existing file ends with newline before appending
    if file_exists and not file_empty:
        with open(APPLICATIONS_CSV, "rb+") as f:
            f.seek(-1, os.SEEK_END)
            last_char = f.read(1)
            if last_char != b"\n":
                f.write(b"\n")

    with open(APPLICATIONS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if file_empty:
            writer.writerow([
                "timestamp",
                "job_id",
                "job_title",
                "company",
                "name",
                "email",
                "phone"
            ])

        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            job_id,
            job.get("title", ""),
            job.get("company", ""),
            name,
            email,
            phone
        ])

    return jsonify({"success": True, "message": "Application saved"})


if __name__ == "__main__":
    app.run(debug=True)