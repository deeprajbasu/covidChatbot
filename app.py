
# importing the necessary dependencies
from flask import Flask, render_template, request
from flask_cors import cross_origin

import camelot
import pandas as pd
import requests
import json
import googlemaps
import plotly.graph_objects as go
import numpy as np
from difflib import SequenceMatcher
import plotly.express as px
import csv
from bs4 import BeautifulSoup
#from flask import render_template
#import webbrowser


gmaps = googlemaps.Client(key='XXXX')

app = Flask(__name__) # initializing a flask app

@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")


@app.route("/getdata", methods=['POST'])
@cross_origin()

def dataUpdate():
    if request.method == 'POST':
        try:
            website_url = requests.get('https://www.mohfw.gov.in/').text  # website link
            soup = BeautifulSoup(website_url, 'html.parser')  # parsing the html info

            def getStateData():
                My_table = soup.find('table', {'class': 'table table-striped'})  # table html we require

                rows = My_table.findAll("tr")

                with open("editors.csv", "wt+", newline="") as f:
                    writer = csv.writer(f)
                    for row in rows:
                        csv_row = []
                        for cell in row.findAll(["td", "th"]):
                            csv_row.append(cell.get_text())
                        writer.writerow(csv_row)

                df = pd.read_csv('editors.csv')
                df['Name of State / UT'][23] = "Orissa"
                df['Name of State / UT'][
                    30] = 'Uttaranchal'  # these states are named differently in our map so we need to match with that

                df = df.drop(df.index[16])  # remove ladakh
                df = df.drop(df.index[27])  # remove telangana
                # we dont have the info for these states in our map as they were formed recently

                df = df.reset_index(drop=True)  # reset the index
                with open('i2.json') as f:
                    data = json.load(f)

                # using sequence matcher"
                #sim = SequenceMatcher()

                for n in range(0, len(df)):

                    for i in range(0, len(data['features'])):
                        x = SequenceMatcher(None, str(df['Name of State / UT'][n]),str(data['features'][i]['properties']['NAME_1'])).ratio()
                        # metric for name matching
                        if (x >= 0.8222):  # if name matches well

                            if (df['Name of State / UT'][n][0] == data['features'][i]['properties']['NAME_1'][0]):
                                # print (x)
                                df['S. No.'][n] = data['features'][i]['properties'][
                                    'ID_1']  # then match the serial number by changing our data serial number column value
                            else:
                                continue
                        else:
                            continue

                df.to_csv('StateData.csv')
                print("Saved State Data")






            def getDistrictData ():
                links = soup.find('ul', {'class': 'nav clearfix'})
                link = links.find('a', {'target': '_blank'})['href']
                link  # link of the pdf we require

                url = link
                r = requests.get(url)  # create HTTP response object

                with open("data.pdf", 'wb') as f:
                    f.write(r.content)

                d = camelot.read_pdf("data.pdf", pages="all", lattice=True)

                frames = [d[i].df for i in range(0, len(d))]  # combine all the pages of pdf

                df = pd.concat(frames)  # combine all the seperate csvs

                # df = df.drop(df.head(2).index)
                # df = df.drop(df.tail(1).index)
                df = df.replace(r'^\s*$', 0, regex=True)  # replace blanks with 0
                df = df.replace('', 0)
                df = df.reset_index(drop=True)  # making the indexing simple by reetting
                # df = df.set_index(0)

                # drop rows with 0 in district column
                indexNames = df[df[2] == 0].index
                #indexNames

                df = df.drop(indexNames)

                df = df.reindex(index=df.index[::-1])  # reset index again
                df = df.reset_index(drop=True)
                # df = df[1:]
                # df[171:198]

                df = df.drop(df.tail(1).index)  # drop last row as it labels for the columns
                #df

                a = {}  # Dictionary to store our data in the end
                num = 0
                start = 0
                d_names = []  # district name
                d_values = []  # district values

                #gmaps = googlemaps.Client(key='AIzaSyAzBeSZaeOn-B9alsP_aoA1pQqHMFISh4A')

                for i in range(1, df.shape[0]):

                    if df[0][i] != 0:

                        # print (df[0][i] )
                        state = df[0][i]  # state name

                        a[num] = {}

                        a[num]['State'] = state  # add state name to dict
                        a[num]['affected districts'] = df[1][i]  # add total number of affected districts

                        d_names = list(df[2][start:i])  # all the districts for that state
                        d_values = list(df[3][start:i])  # number of cases for each district

                        #         d_for_api = d_names# data to send to google api
                        # we are sending "district, state" to google and extracting the coordinates
                        corrs = []  # list to store the coordinates

                        for l in d_names:  # for every district in that state

                            data = gmaps.geocode(str(l + ", " + state))  # get response from google

                            if len(data) == 0:  # some of the data google doesnt have a response for so we will skip these

                                continue
                            else:

                                corrs.append(data[0]['geometry']['location'])  # extract and store the location data

                        count_corr = zip(d_values, corrs)  # tie district count and coordinate

                        a[num]["districts"] = dict(zip(d_names, count_corr))  # tie district name count and coordinate

                        start = i
                        num = num + 1  # loop on

                # Serializing json
                json_object = json.dumps(a)

                # Writing to sample.json
                with open("District.json", "w") as outfile:
                    outfile.write(json_object)
                    print("successfully got district data")

            getDistrictData()
            getStateData()

            return 'UPDATED DATA SUCCESSFULLY'







        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'
    # return render_template('results.html')
    else:
        return render_template('index.html')



@app.route("/map", methods=['GET'])
@cross_origin()
def mappp():
    return render_template("map.html")



@app.route('/predict',methods=['POST','GET']) # route to show the predictions in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            df = pd.read_csv("StateData.csv")

            with open('i2.json') as f:
                mapp = json.load(f)

            f = open('District.json', )
            dff = json.load(f)

            #  reading the inputs given by the user

            # build a request object
            req = request.get_json(force=True)

            # fetch action from json
            action = req.get('queryResult').get('outputContexts')[0].get('parameters').get('location1.original')

            print(action)
            print(type(action))
            # return a fulfillment response

            data = gmaps.geocode(action)

            data = data[0]
            print(data)



            lat = []  # Latitudes for scatter
            lng = []  # longitude for scatter

            size = []  # size of the dots
            textS = []  # what to show as text
            for i in range(0, len(dff)):
                for l in list(dff[str(i)]['districts'].keys()):
                    lat.append(dff[str(i)]['districts'][l][1]['lat'])  # add lattitude
                    lng.append(dff[str(i)]['districts'][l][1]['lng'])  # add longitude
                    size.append(float(dff[str(i)]['districts'][l][0]))  # add size info
                    textS.append(l + " cases : " + dff[str(i)]['districts'][l][0])  # add text info
                    # we want to show district name and cases



            size = np.interp(size, (min(size), max(size)), (55, 2000))
            # scale the size so that it doesnt appear to small



            choro = px.choropleth(df,
                                  geojson=mapp,
                                  locations='S. No.',
                                  color='Death',
                                  color_continuous_scale="greys",
                                  range_color=(0, 67),
                                  featureidkey="properties.ID_1",
                                  # mapbox_style="carto-positron",
                                  # zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                                  # opacity=0.5,
                                  scope="asia",
                                  hover_data=["Name of State / UT", "Cured/Discharged/Migrated", "Death"]
                                  )

            # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

            fig = go.Figure(data=choro)

            fig.add_trace(

                go.Scattergeo(
                    lon=list(lng),
                    lat=list(lat),
                    text=textS,

                    marker=dict(
                        size=size,
                        color="crimson",
                        sizemode='area'))
            )

            fig.update_layout(
                height=700,
                title_text='Indian districts with covid19',
                showlegend=False,
                geo=dict(
                    showsubunits=True,
                    scope='asia',  # subunitcolor="Blue",
                    landcolor='rgb(217, 189, 217)'),
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )





            lat_range = [data['geometry']['bounds']['northeast']['lat'], data['geometry']['bounds']['southwest']['lat']
                         ]

            lon_range = [data['geometry']['bounds']['northeast']['lng'], data['geometry']['bounds']['southwest']['lng']
                         ]




            fig.update_geos(
                ##### CENTER MAP TO INPUT
                center=dict(lon=np.mean(lon_range), lat=np.mean(lat_range)),
                lataxis_range=lat_range,
                lonaxis_range=lon_range,
            )

            fig.write_html("templates/map.html")

            #webbrowser.open_new_tab('C:/Users/Deepr/5555/coronaCHATBOTproject/webappPrototype/templates/map.html')


            return {"fulfillmentText": "your data is ready, please click the MAP link"}


        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'
    # return render_template('results.html')
    else:
        return render_template('index.html')

if __name__ == "__main__":

    #app.run(host='127.0.0.1', port=8001, debug=True)
	app.run(debug=True) # running the app
