from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
import google.generativeai as genai
import uuid

app = Flask(__name__)

# Load API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# ---------------- In-memory stores ----------------
tasks = []
courses = []
feedbacks = []

# ---------------- Home ----------------
@app.route("/")
def index():
    return render_template("index.html")   # make sure your HTML is inside templates/index.html

# ---------------- TASK CRUD ----------------
@app.route("/get_tasks", methods=["GET"])
def get_tasks():
    return jsonify(tasks)

@app.route("/add_task", methods=["POST"])
def add_task():
    data = request.json
    new_task = {
        "id": str(uuid.uuid4()),
        "text": data.get("text", ""),
        "completed": False
    }
    tasks.append(new_task)
    return jsonify({"status": "success", "task": new_task})

@app.route("/update_task", methods=["POST"])
def update_task():
    data = request.json
    task_id = data.get("id")
    new_text = data.get("text")
    completed = data.get("completed")

    for task in tasks:
        if task["id"] == task_id:
            if new_text is not None:
                task["text"] = new_text
            if completed is not None:
                task["completed"] = completed
            return jsonify({"status": "success", "task": task})

    return jsonify({"status": "error", "message": "Task not found"}), 404

@app.route("/delete_task", methods=["POST"])
def delete_task():
    data = request.json
    task_id = data.get("id")
    global tasks
    tasks = [task for task in tasks if task["id"] != task_id]
    return jsonify({"status": "success"})

# ---------------- COURSE CRUD ----------------
@app.route("/get_courses", methods=["GET"])
def get_courses():
    return jsonify(courses)

@app.route("/add_course", methods=["POST"])
def add_course():
    data = request.json
    new_course = {
        "id": str(uuid.uuid4()),
        "title": data.get("title", ""),
        "description": data.get("description", "")
    }
    courses.append(new_course)
    return jsonify({"status": "success", "course": new_course})

# ---------------- FEEDBACK CRUD ----------------
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    title = data.get("title")
    comment = data.get("comment")
    if title and comment:
        feedbacks.append({"id": str(uuid.uuid4()), "title": title, "comment": comment})
    return jsonify(feedbacks)  # <-- important: return updated list

@app.route("/get_feedback", methods=["GET"])
def get_feedback():
    return jsonify(feedbacks)

@app.route("/add_feedback", methods=["POST"])
def add_feedback():
    data = request.json
    new_feedback = {
        "id": str(uuid.uuid4()),
        "text": data.get("text", "")
    }
    feedbacks.append(new_feedback)
    return jsonify({"status": "success", "feedback": new_feedback})

# ---------------- AI INTEGRATION ----------------
@app.route("/generate_suggestions", methods=["GET"])
def generate_suggestions():
    """AI task suggestions based on current tasks"""
    try:
        if not tasks:
            return jsonify({"suggestions": "Add some tasks first!"})
        
        task_texts = [task["text"] for task in tasks]
        prompt = f"Based on these tasks:\n{', '.join(task_texts)}\n\nSuggest 3 actionable and simple productivity improvements. Use bullets."

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Return as single string
        return jsonify({"suggestions": text})
    except Exception as e:
        return jsonify({"suggestions": f"Error: {str(e)}"})

@app.route("/ai/courses", methods=["GET"])
def ai_courses():
    try:
        if not courses:
            return jsonify({"recommendations": ["Add some courses first!"]})
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        course_texts = [c["title"] + ": " + c["description"] for c in courses]
        prompt = f"Based on these courses: {', '.join(course_texts)}\nSuggest a new course with title and short description (use bullets)."

        response = model.generate_content(prompt)
        text = response.text.strip()
        recommendations = [line.strip("-• ") for line in text.split("\n") if line.strip()]
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        return jsonify({"error": str(e)})



@app.route("/ai/feedback", methods=["GET"])
def ai_feedback():
    """AI feedback summary"""
    try:
        if not feedbacks:
            return jsonify({"summary": "No feedback available yet."})

        combined = " ".join([fb["title"] + ". " + fb["comment"] for fb in feedbacks])

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Summarize this student feedback in 3-4 sentences:\n\n{combined}"
        response = model.generate_content(prompt)
        text = response.text.strip()
        return jsonify({"summary": text})
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route("/delete_course", methods=["POST"])
def delete_course():
    data = request.json
    course_id = data.get("id")
    global courses
    courses = [c for c in courses if c["id"] != course_id]
    return jsonify({"status": "success"})

@app.route("/delete_feedback", methods=["POST"])
def delete_feedback():
    data = request.json
    fb_id = data.get("id")
    global feedbacks
    feedbacks = [f for f in feedbacks if f["id"] != fb_id]
    return jsonify({"status": "success"})


# ---------------- Run ----------------
if __name__ == "__main__":
    app.run(debug=True)
