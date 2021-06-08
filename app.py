from flask import Flask, render_template, request, jsonify
import sqlite3 as sql

# app - The flask application where all the magical things are configured.
app = Flask(__name__)

# Constants - Stuff that we need to know that won't ever change!
DATABASE_FILE = "database.db"
DEFAULT_BUGGY_ID = "1"
BUGGY_RACE_SERVER_URL = "https://rhul.buggyrace.net"


#------------------------------------------------------------
# Reading the costs from the files
#------------------------------------------------------------

# Dictionaries for file contents
power_costs_dict = {}
tyre_costs_dict = {}

# Power costs -------------------------
power_file = 'costs/power.txt' # contents: <type> <cost>

with open(power_file) as data_file:
    lines = data_file.readlines()

for line in lines:
    type, cost = line.split()
    power_costs_dict[type] = cost

# Tyre costs --------------------------
tyre_file = 'costs/tyre.txt' # contents <type> <cost>

with open(tyre_file) as data_file:
    lines = data_file.readlines()

for line in lines:
    type, cost = line.split()
    tyre_costs_dict[type] = cost

# Functions to calculate cost - clears up /new by being here
def power_cost_comparison(power_type, power_units):
    cost = (int(power_costs_dict[power_type]) * int(power_units))
    return cost

def tyre_cost_comparison(qty_wheels, tyres):
    cost = (int(tyre_costs_dict[type]) * int(qty_wheels))
    return cost

#------------------------------------------------------------
# the index page
#------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html', server_url=BUGGY_RACE_SERVER_URL)

#------------------------------------------------------------
# creating a new buggy:
#  if it's a POST request process the submitted data
#  but if it's a GET request, just show the form
#------------------------------------------------------------
@app.route('/new', methods = ['POST', 'GET'])
def create_buggy():
    con = sql.connect(DATABASE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM buggies")
    record = cur.fetchone();
    if request.method == 'GET':
        return render_template("buggy-form.html", buggy = None)
    elif request.method == 'POST':
        msg=""
        qty_wheels = request.form['qty_wheels']
        if not qty_wheels.isdigit():
            msg = f"Error: {qty_wheels} is not a number"
            return render_template('buggy-form.html', buggy = record, msg = msg)
        if int(qty_wheels) % 2 != 0:
            msg = f"Error: {qty_wheels} is not an even number"
            return render_template('buggy-form.html', buggy = record, msg = msg)
        power_type = request.form['power_type']
        power_units = request.form['power_units']
        power_cost = power_cost_comparison(power_type, power_units)
        flag_color = request.form['flag_color']
        flag_color_secondary = request.form['flag_color_secondary']
        flag_pattern = request.form['flag_pattern']
        buggy_id = request.form['id']
        total_cost = power_cost
        try:
            with sql.connect(DATABASE_FILE) as con:
                cur = con.cursor()
                if buggy_id:
                    cur.execute(
                        "UPDATE buggies SET qty_wheels=?, power_type=?, power_units=?, flag_color=?, 'flag_color_secondary'=?, 'flag_pattern'=? WHERE id=?",
                        (qty_wheels, power_type, power_units, flag_color, flag_color_secondary, flag_pattern, buggy_id)
                    )
                else:
                    cur.execute(
                        "INSERT INTO buggies (qty_wheels, power_type, power_units, flag_color, flag_color_secondary, flag_pattern) VALUES (?, ?, ?, ?, ?, ?)",
                        (qty_wheels, power_type, power_units, flag_color, flag_color_secondary, flag_pattern)
                    )
                con.commit()
                msg = f"Record successfully saved. The cost of this buggy is {total_cost}."
        except:
            con.rollback()
            msg = "error in update operation"
        finally:
            con.close()
        return render_template("updated.html", msg = msg)

#------------------------------------------------------------
# a page for displaying the buggy
#------------------------------------------------------------
@app.route('/buggy')
def show_buggies():
    con = sql.connect(DATABASE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM buggies")
    records = cur.fetchall();
    return render_template("buggy.html", buggies = records)

#------------------------------------------------------------
# a placeholder page for editing the buggy: you'll need
# to change this when you tackle task 2-EDIT
#------------------------------------------------------------
@app.route('/edit/<buggy_id>')
def edit_buggy(buggy_id):
    con = sql.connect(DATABASE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM buggies WHERE id=?", (buggy_id,))
    record = cur.fetchone();
    return render_template("buggy-form.html", buggy = record)

#------------------------------------------------------------
# deleting a buggy
# for task 3-del
#------------------------------------------------------------
@app.route('/delete/<buggy_id>', methods = ['GET', 'POST'])
def delete_buggy(buggy_id):
    con = sql.connect(DATABASE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    try:
        with sql.connect(DATABASE_FILE) as con:
            cur = con.cursor()
            if buggy_id:
                cur.execute(
                    "DELETE FROM buggies WHERE id=?",
                    (buggy_id)
                )
            else:
                msg = "error: no buggy ID"
            con.commit()
            msg = "Buggy successfully deleted"
    except:
        con.rollback()
        msg = "error in update operation"
    finally:
        con.close()
    return render_template("updated.html", msg = msg)

#------------------------------------------------------------
# You probably don't need to edit this... unless you want to ;)
#
# get JSON from current record
#  This reads the buggy record from the database, turns it
#  into JSON format (excluding any empty values), and returns
#  it. There's no .html template here because it's *only* returning
#  the data, so in effect jsonify() is rendering the data.
#------------------------------------------------------------
@app.route('/json')
def summary():
    con = sql.connect(DATABASE_FILE)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM buggies WHERE id=? LIMIT 1", (DEFAULT_BUGGY_ID))

    buggies = dict(zip([column[0] for column in cur.description], cur.fetchone())).items()
    return jsonify({ key: val for key, val in buggies if (val != "" and val is not None) })

# You shouldn't need to add anything below this!
if __name__ == '__main__':
    app.run(debug = True, host="0.0.0.0")
