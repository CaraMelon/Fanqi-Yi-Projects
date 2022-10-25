from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
import json

def getCity(locationList):
    
    result = []
    store_count = 0

    #for each store
    for store in locationList.find_all('a'):

        storeString = store.get_text().split()
        
        #extract city name
        city = storeString[2:len(storeString)-1] #a list of city name with one or more words
        numStore = int(storeString[-1][1:len(storeString[-1])-1]) #number of store in given city
        full_name = ""

        #put words together to make full city name
        for word in city:
            full_name += word + "-"
        
        result.append(full_name[:len(full_name)-1]) #strip trailing "-"
        store_count += numStore

    return result, store_count


def getStore(cityList, store_count,url):

    #initialize cvs dataframe
    # cvs_df = pd.DataFrame(index=range(store_count),columns=['City','StoreID','Address','Number']) 
    cvs_df = pd.DataFrame(index=range(store_count),columns=['street','city','state','zip','phone','store_id']) 
    df_index = 0

    # use list of cities to create url to get list of cvs stores in that city
    for city in cityList:

        #get cityUrl
        cityUrl = url + "/" + city
        request = requests.get(cityUrl)
        soup = BeautifulSoup(request.text, 'lxml')
        storeList = soup.find_all('div',class_ = 'each-store') #find all stores with tags 'each-store'
        
        # print("city = ", city)
        #for each store
        for store in storeList:
            
            temp_city = city.replace("-"," ")
            address = store.find('p', class_= 'store-address').get_text().strip()
            split_address = address.split(" " + temp_city + ", ")

            street = split_address[0]
            state = split_address[1].split()[0]
            zipcode = split_address[1].split()[1]

            phone_num = store.find('p', class_ = 'phone-number').get_text().strip()
            store_ID = store.find('span', class_ = 'store-number').get_text().strip()
            

            #if phone_num and store_ID values are the same
            if phone_num == store_ID:
                #then phone_num doesn't exist
                phone_num = ""

            cvs_df.loc[df_index]['city'] = city
            cvs_df.loc[df_index]['street'] = street
            cvs_df.loc[df_index]['state'] = state 
            cvs_df.loc[df_index]['zip'] = zipcode
            cvs_df.loc[df_index]['phone'] = phone_num
            cvs_df.loc[df_index]['store_id'] = store_ID

            df_index += 1 #increment index 

    return cvs_df


def get_geodata(df):
    #example of full url https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key=YOUR_API_KEY
    url = "https://maps.googleapis.com/maps/api/geocode/json?address="
    key = "AIzaSyB5KTrv3i5pkK5ErKNFLD20sKaEc_f97uQ"

    #returning csv file 
    cvs_loc_df = pd.DataFrame(index = range(df.shape[0]), columns = ['latitude','longitude','place_id','street','city','state','zip','phone','store_id'])

    for i in range(df.shape[0]):
        store = df.loc[i]
        street,city,state = store['street'].replace(' ', '+'),store['city'].replace(' ', '+'),store['state']
        address = street + ",+" + city + ",+" + state

        storeURL = url + address + "&key=" + key

        #get request
        response = requests.request("GET", storeURL)
        response_dict = json.loads(response.content)
        # print("Covered " , (i+1) , " many stores...")
        #if the request was succesful
        if response_dict["status"] == "OK":

            result = response_dict['results']

            location = result[0]['geometry']['location']
            place_id = result[0]['place_id']
            lat, lng = location['lat'], location['lng']

            cvs_loc_df.loc[i]['latitude'] = lat
            cvs_loc_df.loc[i]['longitude'] = lng
            cvs_loc_df.loc[i]['place_id'] = place_id
            

            cvs_loc_df.loc[i]['city'] = store['city']
            cvs_loc_df.loc[i]['street'] = store['street']
            cvs_loc_df.loc[i]['state'] = store['state'] 
            cvs_loc_df.loc[i]['zip'] = store['zip']
            cvs_loc_df.loc[i]['phone'] = store['phone']
            cvs_loc_df.loc[i]['store_id'] = store['store_id']

    cvs_loc_df.to_csv("cvs.csv")


def scrape():
    url = "https://www.cvs.com/store-locator/cvs-pharmacy-locations/Pennsylvania"

    request = requests.get(url)
    soup = BeautifulSoup(request.text, 'lxml')
    locationList = soup.find('div', class_ = 'states')

    #get list of cities in pennsylvania
    cityList,store_count = getCity(locationList)

    # print("store_count = ", store_count)
    #get list of stores in different cities in dataframe
    cvs_df = getStore(cityList,store_count,url)

    return get_geodata(cvs_df)

