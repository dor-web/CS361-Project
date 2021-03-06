from google.cloud import datastore
from flask import Flask, render_template, url_for, redirect, request
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId

#connect to the local database
myclient = MongoClient("mongodb+srv://ord_cs361:VN5gkORCB5w76rPS@cluster0.wmpj3.mongodb.net/CS361?retryWrites=true&w=majority")
db = myclient["CS361"]
collection = db['fish_entries']     #collect fish entries
rule_collection = db['rules']       #collect rules made by judge
leader_board = db['leader_board']

app = Flask(__name__)
client = datastore.Client()

#display the leader board
@app.route("/", methods=['POST','GET'])
def home_page():
    if request.method == "GET":

        show_entry = collection.find().sort("length", -1)
    
    return render_template("home.html", entries = show_entry)

#implement the mircoservice
@app.route("/search", methods=['POST'])
def search():
    fish = request.form["fish"]
    session = requests.Session()
    response = session.post("https://cs-361-microservice-348603.uw.r.appspot.com", json={"fish": f"{fish}"})
    data = response.json()
    return render_template("fish_info.html", info=data)

#show rules for the tourament
@app.route("/rules")
def display_rules():
    show_rules = rule_collection.find()
    return render_template("rules.html", rules = show_rules)

#display the entries made
@app.route("/competitor")
def competitor_page():
    show_entry = collection.find()
    return render_template("competitor_page.html", entries = show_entry)

#create the html page to add fish into entry
@app.route("/competitor/entry")
def competitor_entry_button():
    return render_template("add_entry.html")

#Send info to the database
@app.route("/competitor/add_entry", methods=['POST'])
def competitor_add_entry():
    if request.method == 'POST':
        name = request.form["name"]
        species = request.form["species"]
        length = request.form["length"]
        response = " "
        if not name and not species and not length:
            return("please enter your catch")

        else:
            collection.insert_one({"name": name, "species": species, "length": int(length), "response": response})
            return redirect(url_for('competitor_page'))

#log in for the judge
@app.route("/judge", methods = ['GET', 'POST'])
def judge_page():
    error = None
    if request.method == "POST":
        if request.form['username'] != 'judge' or request.form['password'] != 'judge':
            error = 'Invade Creadentials. Please try again.'
        else:
            return redirect(url_for('judge_approve_page'))
    return render_template("judge.html", error = error)

#display the contestant entries for approval
@app.route("/judge/approve")
def judge_approve_page():
    show_entry = collection.find()
    return render_template("judge_page.html", entries = show_entry)

#update database with judge's approval
@app.route('/judge/approve/<id>', methods = ['GET', 'POST', 'PATCH'])
def approve_button(id):
    if request.method == 'POST':
        judge_response = request.form['response']
        if judge_response == 'yes':
            collection.find_one_and_update({"_id": ObjectId(id)}, {'$set': {"response": judge_response }})
            # leader_board.insert_one({"_id": ObjectId(id)})
            return redirect(url_for('judge_approve_page'))
        elif  judge_response == 'no':
            collection.find_one_and_update({"_id": ObjectId(id)}, {'$set': {"response": judge_response }})
            return redirect(url_for('judge_approve_page'))

#remove entry in the judge page
@app.route('/judge/approve/remove/<id>', methods = ['POST'])
def remove_entry(id):
    if request.method == 'POST':
        collection.delete_one({"_id": ObjectId(id)})
        return redirect(url_for('judge_approve_page'))

#render the judge_rule page
@app.route("/judge/rules")
def judge_rule():
    show_rules = rule_collection.find()
    return render_template("judge_rules.html", rules = show_rules)

#render the create_rule page
@app.route("/judge/add_rules")
def rule_page():
    return render_template("create_rules.html")

#add rule
@app.route("/judge/add_rules", methods=['POST'])
def add_rules():
    if request.method == 'POST':
        rule = request.form["rule"]
        apply = " "
        if not rule:
            return("please create rule")

        else:
            rule_collection.insert_one({"rule": rule, "apply": apply})
            return redirect(url_for('judge_rule'))

#remove rule
@app.route('/judge/rules/remove/<id>', methods = ['GET', 'POST', 'PATCH'])
def remove_button(id):
    if request.method == 'POST':
        rule_collection.delete_one({"_id": ObjectId(id)})

        return redirect(url_for('judge_rule'))

#determine if the rules should apply current touranment
@app.route('/judge/rules/change/<id>', methods = ['POST'])
def rule_apply_button(id):
    if request.method == 'POST':
        judge_response = request.form['apply']
        if judge_response == 'yes':
            rule_collection.find_one_and_update({"_id": ObjectId(id)}, {'$set': {"apply": judge_response }})
            return redirect(url_for('judge_rule'))
        elif  judge_response == 'no':
            rule_collection.find_one_and_update({"_id": ObjectId(id)}, {'$set': {"apply": judge_response }})
            return redirect(url_for('judge_rule'))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)


    