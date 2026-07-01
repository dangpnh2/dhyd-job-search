from flask import Flask, render_template, request, jsonify
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_jobs_from_supabase():
    response = supabase.table("jobs").select("*").execute()
    return response.data


@app.route("/")
def home():
    return render_template("search.html")


@app.route("/search")
def search_jobs():
    keyword = request.args.get("keyword", "").strip().lower()

    jobs = load_jobs_from_supabase()
    if keyword:
        jobs = [
            job for job in jobs
            if keyword in str(job.get("title", "")).lower()
            or keyword in str(job.get("company", "")).lower()
            or keyword in str(job.get("location", "")).lower()
            or keyword in str(job.get("description", "")).lower()
        ]

    return render_template("search.html", jobs=jobs, keyword=keyword)


@app.route("/job/<job_id>")
def job_detail(job_id):
    response = (
        supabase
        .table("jobs")
        .select("*")
        .eq("id", job_id)
        .single()
        .execute()
    )

    job = response.data

    if not job:
        return "Job not found", 404

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

    job_response = (
        supabase
        .table("jobs")
        .select("*")
        .eq("id", job_id)
        .single()
        .execute()
    )

    job = job_response.data

    if not job:
        return jsonify({"success": False, "message": "Job not found"}), 404

    supabase.table("applications").insert({
        "job_id": str(job_id),
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "name": name,
        "email": email,
        "phone": phone
    }).execute()

    return jsonify({"success": True, "message": "Application saved"})


if __name__ == "__main__":
    app.run(debug=True)