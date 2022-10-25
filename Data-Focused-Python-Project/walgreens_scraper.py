from bs4 import BeautifulSoup
from urllib.request import urlopen
import csv
import requests
import json
import pandas as pd
import numpy as np

filename = 'walgreens.csv'
# get latitude and longitude for walgreens address
def get_geo_data(scrape_df):
    url = "https://maps.googleapis.com/maps/api/geocode/json?address="
    key = "AIzaSyB5KTrv3i5pkK5ErKNFLD20sKaEc_f97uQ"
    data = [] #lat, lng, id
    for i in range(scrape_df.shape[0]):
        row = []
        store = scrape_df.loc[i]

        street, city, state = store['street'].replace(" ", "+"), store['city'].replace(" ", "+") ,store['state'].replace(" ", "+")
        address = street + ",+" + city + ",+" + state
        storeURL = url + address + "&key=" + key
        response = requests.request("GET", storeURL)
        response_dict = json.loads(response.content)
        
        lat, lng = response_dict['results'][0]['geometry']['location']['lat'], response_dict['results'][0]['geometry']['location']['lng']
        place_id = response_dict['results'][0]['place_id']
        
        row.append(lat)
        row.append(lng)
        row.append(place_id)
        data.append(row)

        if response_dict["status"] != "OK":
            print("API Retrieval ", address, "Failed.")

        api_df = pd.DataFrame(np.array(data),columns = ['latitude', 'longitude', 'place_id'])
        api_df["street"] = scrape_df["street"]
        api_df["city"] = scrape_df["city"]
        api_df["state"] = scrape_df["state"]
        api_df["zip"] = scrape_df["zipcode"]
        api_df["phone"] = scrape_df["phone"]

        return api_df

# get walgreens locaiton in PA from walgreens website        
def scrape(state = 'PA'):
    url = "https://www.walgreens.com/storelistings/storesbycity.jsp?requestType=locator&state=" + state
    html = urlopen(url)

    soup = BeautifulSoup(html.read(), "lxml")
    locationList = soup.findAll('ul', class_ = "col-xl-4 col-lg-4 col-md-4")
    data = []

    for col in locationList:
        links = col.findAll("a")

        for link in links:
            curCity = link.get("name")
            curUrl = 'https://www.walgreens.com' + link.get("href")


            curHtml = urlopen(curUrl.replace(" ", "%20"))
            page = BeautifulSoup(curHtml.read(), "lxml") 
            allInfos = page.findAll('div', class_="address")
            phones = page.findAll('a', class_="phone")
            for i in range(len(allInfos)):
                row = [0 for i in range(5)] # street, city, state, zipcode, phone
                allInfo = allInfos[i]

                row[0] = allInfo.find("strong").get_text() #street
                cityState = allInfo.findAll("span")[-1].text.strip()
                row[1] = cityState.split(",")[0]#city
                row[2] = cityState.split(",")[1].split(" ")[1] #state
                row[3] = cityState.split(",")[1].split(" ")[2] #zipcode
                if (row[2] != 'PA'):
                    continue

                row[4] = phones[i].get("href")[4:-1]
                data.append(row)
        scrape_df = pd.DataFrame(np.array(data), columns = ["street", "city", "state", "zipcode", "phone"])        
        walgreens_geo_location_df = get_geo_data(scrape_df)
        walgreens_geo_location_df.to_csv(filename)