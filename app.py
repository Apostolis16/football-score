
from flask import Flask, redirect, render_template, flash, request, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
import time
import threading
import requests
import os

load_dotenv()

app = Flask(__name__)

cluster = MongoClient("mongodb://localhost:27017/footballScoreDB")
db = cluster["footballScorePy"]

collection = db["footballScore"]
tm_collection = db["footballScoreTm"]

        
def get_matches(league):

    status = ["FINISHED", "LIVE", "SCHEDULED"]
    keys = [os.getenv("key1"), os.getenv("key2"), os.getenv("key3")]
    x = 0

    while(x < 3):
        

        uri = "https://api.football-data.org/v4/competitions/" + league + "/matches?status=" + status[x]
        headers = { 'X-Auth-Token': keys }

        response = requests.get(uri, headers=headers)   


        matches = response.json()["matches"]

       

        length = response.json()["resultSet"]["count"]
        i=0


        collection.delete_many({"league": league , "status": status[x]})

        while(i != length): 
            
            print(matches[i])

            awayTeam = matches[i]["awayTeam"]["name"]   
            homeTeam = matches[i]["homeTeam"]["name"]
            homeTeamCrest = matches[i]["homeTeam"]["crest"]
            awayTeamCrest = matches[i]["awayTeam"]["crest"]

            date = matches[i]["utcDate"]
            winner = matches[i]["score"]["winner"]

            awayScore = matches[i]["score"]["fullTime"]["away"]
            awayHalfTimeScore = matches[i]["score"]["halfTime"]["away"]

            homeScore = matches[i]["score"]["fullTime"]["home"]
            homeHalfTimeScore = matches[i]["score"]["halfTime"]["home"]
    

            if status == "FINISHED":
 
                post = {
                    "homeTeam": homeTeam,
                    "awayTeam": awayTeam,
                    "date": date,
                    "homeScore": homeScore,
                    "awayScore": awayScore,
                    "homeHalfTimeScore": homeHalfTimeScore,
                    "awayHalfTimeScore": awayHalfTimeScore,
                    "winner": winner,
                    "status": status[x],
                    "league": league,
                    "awayTeamCrest": awayTeamCrest,
                    "homeTeamCrest": homeTeamCrest
                }

            elif status == "LIVE":  

                    post = {
                        "homeTeam": homeTeam,
                        "awayTeam": awayTeam,
                        "date": "LIVE",
                        "homeScore": homeScore,
                        "awayScore": awayScore,
                        "homeHalfTimeScore": 0,
                        "awayHalfTimeScore": 0,
                        "winner": 0,
                        "status": status[x],
                        "league": league,
                        "awayTeamCrest": awayTeamCrest,
                        "homeTeamCrest": homeTeamCrest
                    }

            else :

                    post = {
                        "homeTeam": homeTeam,
                        "awayTeam": awayTeam,
                        "date": date,
                        "homeScore": 0,
                        "awayScore": 0,
                        "homeHalfTimeScore": 0,
                        "awayHalfTimeScore": 0,
                        "winner": 0,
                        "status": status[x],
                        "league": league,
                        "awayTeamCrest": awayTeamCrest,
                        "homeTeamCrest": homeTeamCrest
                    }
                    
            if collection.find_one(post) == False :
                collection.insert_one(post)
                
            

            i+=1

        x+=1   

def get_todays_matches(): 

    tm_collection.delete_many({})

    uri = "https://api.football-data.org/v4/matches"
    headers = { 'X-Auth-Token': 'a7858fea2d74477fb3583fcffc696dc3' }

    response = requests.get(uri, headers=headers).json()  



    matches = response['matches']
    length = response["resultSet"]["count"]

    i=0

    while(i != length): 

        awayTeam = matches[i]["awayTeam"]["name"]   
        homeTeam = matches[i]["homeTeam"]["name"]
        homeTeamCrest = matches[i]["homeTeam"]["crest"]
        awayTeamCrest = matches[i]["awayTeam"]["crest"]
        date = matches[i]["utcDate"]
        winner = matches[i]["score"]["winner"]
        awayScore = matches[i]["score"]["fullTime"]["away"]
        homeScore = matches[i]["score"]["fullTime"]["home"]

        post = {
        "awayTeam": awayTeam,
        "homeTeam": homeTeam,
        "homeTeamCrest": homeTeamCrest,
        "awayTeamCrest": awayTeamCrest,
        "date": date,
        "winner": winner,
        "awayScore": awayScore,
        "homeScore": homeScore,
        }   

        tm_collection.insert_one(post)

        i+=1
    time.sleep(86401)

def main():
    @app.route("/", methods=["GET", "POST"])
    def home():

        live_matches = collection.find({"status": "LIVE"})
        todays_matches = tm_collection.find()

        live_matches = list(live_matches)
        todays_matches = list(todays_matches)

        if request.method == "POST":
            league = request.form["submit-button"]
            return redirect(url_for(league))


        return render_template("main.html" , live_matches=live_matches, todays_matches=todays_matches)


    @app.route("/<league>")
    def score(league):

        league = league.upper()

        scheduled_matches = list(collection.find({"status": "SCHEDULED", "league": league}))
        finished_matches = list(collection.find({"status": "FINISHED", "league": league}))
        live_matches = list(collection.find({"status": "LIVE", "league": league}))

        return render_template("league.html", scheduled_matches=scheduled_matches, live_matches=live_matches, finished_matches=finished_matches)

threading.Thread(target=main).start()
threading.Thread(target=get_matches, args="PL").start()
threading.Thread(target=get_todays_matches).start()


if __name__ == "__main__":
    app.run(debug=True)


