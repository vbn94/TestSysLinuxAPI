# app.py
from flask import Flask, request, jsonify
import subprocess
import os
import filecmp
from flask_cors import CORS
import mysql.connector
import json
import io

# Establish a connection to the database
cnx = mysql.connector.connect(
    host='localhost', 
    user='testuser',
    password='1234',
    database='TestSys'
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.post("/test/<int:ex_id>")
def test_code(ex_id):
    request_data = request.get_json()
    code = request_data.get('code')
    cursor = cnx.cursor()
    query = "SELECT task, answer, test_type FROM exercises WHERE id = %s"
    cursor.execute(query, (ex_id,))
    row = cursor.fetchone()
    if row is None:
        return f'Invalid exercise'
    cursor.close()
    if row[2] == "bash":
        with open("answer.sh", "w") as f:
            f.write(row[1])

        with open("student.sh", "w") as f:
            f.write(code)
    
        with open('resS.txt','w') as f_obj:
            completed_process = subprocess.run(["docker", "run", "--rm", "-v", "/usr/share/dict/words:/usr/share/dict/words", "-v", "/home/vnachev/testsystemos/answer.sh:/answer.sh", "ubuntu", "bash", "answer.sh" ],stdout=f_obj, text=True)
            #completed_process = subprocess.run(["bash", "answer.sh"],stdout=f_obj, text=True)
            if completed_process.returncode != 0:
                return jsonify("result", 'Compile error')
        with open('resT.txt','w') as f_obj:
            #completed_process = subprocess.run(["bash", "student.sh"],stdout=f_obj, text=True)
            completed_process = subprocess.run(["docker", "run", "--rm", "-v", "/usr/share/dict/words:/usr/share/dict/words", "-v", "/home/vnachev/testsystemos/student.sh:/student.sh", "ubuntu", "bash", "student.sh" ],stdout=f_obj, text=True)
            if completed_process.returncode != 0:
                return jsonify("result", 'Compile error')
        status = False
        if filecmp.cmp("resT.txt", "resS.txt"):
            status = True

        subprocess.run(["rm", "-rf", "*.txt|*.sh"])
    elif row[2] == 'string compare':
        status = code == row[1]
    elif row[2] == 'directory compare':
        with open("answer.sh", "w") as f:
            f.write(row[1])
            f.write("\ntree")


        with open("student.sh", "w") as f:
            f.write(code)
            f.write("\ntree")
    
        with open('resS.txt','w') as f_obj:
            completed_process = subprocess.run(["docker", "run", "--rm" ,"-v", "/home/vnachev/testsystemos/answer.sh:/answer.sh", "ubuntu-tree", "bash", "answer.sh" ],stdout=f_obj, text=True)
            #completed_process = subprocess.run(["bash", "answer.sh"],stdout=f_obj, text=True)
            if completed_process.returncode != 0:
                return f'Compile error answ'
        with open('resT.txt','w') as f_obj:
            #completed_process = subprocess.run(["bash", "student.sh"],stdout=f_obj, text=True)
            completed_process = subprocess.run(["docker", "run", "--rm", "-v", "/home/vnachev/testsystemos/student.sh:/student.sh", "ubuntu-tree", "bash", "student.sh" ],stdout=f_obj, text=True)
            if completed_process.returncode != 0:
                return f'Compile error st'
        status = False
        if filecmp.cmp("resT.txt", "resS.txt"):
            status = True
    if status:        
        return jsonify("result", f'ok')
    return jsonify("result", f'not ok')


@app.post("/task")
def add_task():
    request_data = request.get_json()
    heading = request_data.get('heading')
    task = request_data.get('task')
    answer = request_data.get('answer')
    test_type = request_data.get('test_type')
    cursor = cnx.cursor()
    query = "INSERT INTO exercises (heading, task, answer, test_type) VALUES (%s, %s, %s, %s)"
    values = (heading, task, answer, test_type)
    cursor.execute(query, values)
    cnx.commit()
    cursor.close()
    return jsonify("result", f'task saved')


@app.get("/tasks")
def get_tasks():
    cursor = cnx.cursor()
    query = "SELECT * FROM exercises"
    cursor.execute(query)
    result = cursor.fetchall()
    if len(result) == 0:
        return jsonify("result", f'no such exercise')
    data = [dict(zip(cursor.column_names, row)) for row in result]
    return jsonify(data)


@app.get("/task/<int:ex_id>")
def ex_usl(ex_id):
    cursor = cnx.cursor()
    query = "SELECT * FROM exercises WHERE id = %s"
    values = (ex_id,)
    cursor.execute(query, values)    
    result = cursor.fetchone()
    if result is None:
        return jsonify("result", f'no such exercise')
    data = dict(zip(cursor.column_names, result))
    return jsonify(data)


@app.get("/task/delete/<int:ex_id>")
def task_delete(ex_id):
    request_data = request.get_json()
    cursor = cnx.cursor()
    query = "DELETE FROM exercises WHERE id = %s"
    values = (ex_id,)
    cursor.execute(query, values)
    cnx.commit()
    cursor.close()
    return jsonify("result", f'task deleted')


if __name__ == '__main__':
    app.run(host="0.0.0.0")
