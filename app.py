from flask import Flask, render_template, request, redirect, url_for

from db import init_db, get_db
from logic import split_random, pick_student

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    return render_template("index.html", title="Кворум")


@app.route("/students")
def students():
    conn = get_db()
    rows = conn.execute("SELECT * FROM student ORDER BY name").fetchall()
    conn.close()
    return render_template("students.html", students=rows, title="Ученики")


@app.route("/students/add", methods=["POST"])
def students_add():
    text = request.form.get("names", "")
    conn = get_db()
    for line in text.splitlines():
        name = line.strip()
        if name:
            conn.execute("INSERT INTO student (name, present) VALUES (?, 1)", (name,))
    conn.commit()
    conn.close()
    return redirect(url_for("students"))


@app.route("/students/delete/<int:sid>", methods=["POST"])
def students_delete(sid):
    conn = get_db()
    conn.execute("DELETE FROM student WHERE id = ?", (sid,))
    conn.execute("DELETE FROM group_member WHERE student_id = ?", (sid,))
    conn.commit()
    conn.close()
    return redirect(url_for("students"))


@app.route("/students/presence", methods=["POST"])
def students_presence():
    present = set(int(x) for x in request.form.getlist("present"))
    conn = get_db()
    rows = conn.execute("SELECT id FROM student").fetchall()
    for r in rows:
        val = 1 if r["id"] in present else 0
        conn.execute("UPDATE student SET present = ? WHERE id = ?", (val, r["id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("students"))


@app.route("/groups/fragment", methods=["POST"])
def groups_fragment():
    n = int(request.form.get("n_groups", 3))

    conn = get_db()
    conn.execute("DELETE FROM group_member")
    conn.execute("DELETE FROM grp")

    rows = conn.execute("SELECT id FROM student WHERE present = 1").fetchall()
    present = [r["id"] for r in rows]

    if not present:
        conn.commit()
        conn.close()
        return "<p class='text-muted'>Нет отмеченных учеников.</p>"

    groups = split_random(present, n)

    for i, g in enumerate(groups, start=1):
        cur = conn.execute("INSERT INTO grp (name) VALUES (?)", (f"Команда {i}",))
        gid = cur.lastrowid
        for sid in g:
            conn.execute(
                "INSERT INTO group_member (group_id, student_id) VALUES (?, ?)",
                (gid, sid),
            )
    conn.commit()

    result = []
    for i, g in enumerate(groups, start=1):
        names = []
        for sid in g:
            row = conn.execute("SELECT name FROM student WHERE id = ?", (sid,)).fetchone()
            if row:
                names.append(row["name"])
        result.append({"name": f"Команда {i}", "members": names})

    conn.close()
    return render_template("_teams_fragment.html", groups=result)


@app.route("/lesson/start", methods=["POST"])
def lesson_start():
    conn = get_db()
    cur = conn.execute("INSERT INTO lesson DEFAULT VALUES")
    lid = cur.lastrowid

    groups = conn.execute("SELECT * FROM grp").fetchall()
    for g in groups:
        conn.execute(
            "INSERT INTO lesson_score (lesson_id, group_id, points) VALUES (?, ?, 0)",
            (lid, g["id"]),
        )
    conn.commit()
    conn.close()
    return redirect(url_for("lesson_view", lid=lid))


@app.route("/lesson/<int:lid>")
def lesson_view(lid):
    conn = get_db()
    lesson = conn.execute("SELECT * FROM lesson WHERE id = ?", (lid,)).fetchone()
    groups = conn.execute("SELECT * FROM grp ORDER BY id").fetchall()
    scores_rows = conn.execute(
        "SELECT group_id, points FROM lesson_score WHERE lesson_id = ?", (lid,)
    ).fetchall()
    scores = {r["group_id"]: r["points"] for r in scores_rows}

    last_pick = conn.execute(
        "SELECT student_id FROM lesson_pick WHERE lesson_id = ? ORDER BY id DESC LIMIT 1",
        (lid,),
    ).fetchone()
    last_name = None
    if last_pick:
        row = conn.execute(
            "SELECT name FROM student WHERE id = ?", (last_pick["student_id"],)
        ).fetchone()
        if row:
            last_name = row["name"]

    conn.close()

    return render_template(
        "lesson.html",
        lesson=lesson,
        groups=groups,
        scores=scores,
        last_name=last_name,
        title="Урок",
    )


@app.route("/lesson/<int:lid>/pick", methods=["POST"])
def lesson_pick(lid):
    conn = get_db()
    rows = conn.execute("SELECT id FROM student WHERE present = 1").fetchall()
    ids = [r["id"] for r in rows]
    sid = pick_student(ids)
    if sid is not None:
        conn.execute(
            "INSERT INTO lesson_pick (lesson_id, student_id) VALUES (?, ?)", (lid, sid)
        )
        conn.commit()
    conn.close()
    return redirect(url_for("lesson_view", lid=lid))


@app.route("/lesson/<int:lid>/score", methods=["POST"])
def lesson_score(lid):
    gid = int(request.form.get("group_id"))
    delta = int(request.form.get("delta", 1))
    conn = get_db()
    conn.execute(
        "UPDATE lesson_score SET points = points + ? WHERE lesson_id = ? AND group_id = ?",
        (delta, lid, gid),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("lesson_view", lid=lid))


@app.route("/lesson/<int:lid>/note", methods=["POST"])
def lesson_note(lid):
    note = request.form.get("note", "")
    conn = get_db()
    conn.execute("UPDATE lesson SET note = ? WHERE id = ?", (note, lid))
    conn.commit()
    conn.close()
    return redirect(url_for("lesson_view", lid=lid))


@app.route("/lesson/<int:lid>/finish")
def lesson_result(lid):
    conn = get_db()
    lesson = conn.execute("SELECT * FROM lesson WHERE id = ?", (lid,)).fetchone()
    rows = conn.execute(
        """
        SELECT g.name AS group_name, s.points
        FROM lesson_score s
        JOIN grp g ON g.id = s.group_id
        WHERE s.lesson_id = ?
        ORDER BY s.points DESC
        """,
        (lid,),
    ).fetchall()
    picks = conn.execute(
        """
        SELECT st.name, p.picked_at
        FROM lesson_pick p
        JOIN student st ON st.id = p.student_id
        WHERE p.lesson_id = ?
        ORDER BY p.id
        """,
        (lid,),
    ).fetchall()
    conn.close()
    return render_template(
        "lesson_result.html",
        lesson=lesson,
        scores=rows,
        picks=picks,
        title="Итог урока",
    )


if __name__ == "__main__":
    app.run(debug=True)