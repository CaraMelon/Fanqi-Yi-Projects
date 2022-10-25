from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
import time
import pandas as pd
import requests
import json

# create column lists
street_col = []
city_col = []
state_col = []
zipcode_col = []
phone_col = []
store_id_col = []

'''
Function to scrape data from a city page that
contains just one store location
'''
def scrape_single_location_from_page(driver):
    name = driver.find_element(By.ID, "location-name").text
    
    street = driver.find_element(By.XPATH, "//span[@class='c-address-street-1']").text
    city = driver.find_element(By.XPATH, "//span[@itemprop='addressLocality']").text
    state = driver.find_element(By.XPATH, "//abbr[@itemprop='addressRegion']").text
    zipcode = driver.find_element(By.XPATH, "//span[@itemprop='postalCode']").text
    
    phone = driver.find_element(By.ID, "telephone").text
    
    store_id_col.append(name)
    street_col.append(street)
    city_col.append(city)
    state_col.append(state)
    zipcode_col.append(zipcode)
    phone_col.append(phone)
    
'''
Function to scrape data from a city page that
contains multiple store locations
'''
def scrape_multiple_locations_from_page(driver):
    locations = driver.find_elements(By.XPATH, "//div[@class='c-location-grid-item']")
    
    for location in locations:
        name = location.find_element(By.XPATH, ".//a[@itemprop='url']").text
        
        street = location.find_element(By.XPATH, ".//span[@class='c-address-street-1']").text
        city = location.find_element(By.XPATH, ".//span[@class='c-address-city']/span[1]").text
        state = location.find_element(By.XPATH, ".//abbr[@class='c-address-state']").text
        zipcode = location.find_element(By.XPATH, ".//span[@class='c-address-postal-code']").text
        
        phone = location.find_element(By.XPATH, ".//span[@class='c-phone-number-span c-phone-main-number-span']").text
        
        store_id_col.append(name)
        street_col.append(street)
        city_col.append(city)
        state_col.append(state)
        zipcode_col.append(zipcode)
        phone_col.append(phone)
        

'''
Function to remove Rite Aid stores that have closed in their label
'''
def drop_closed_stores(df):
    df = df[df['store_id'].str.contains('Closed')==False]

    return df
    
'''
Function to get latitude and longitude data for each rite aid store location
'''
def get_geo_data(df):
    #example of full url https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key=YOUR_API_KEY
    url = "https://maps.googleapis.com/maps/api/geocode/json?address="
    key = "AIzaSyB5KTrv3i5pkK5ErKNFLD20sKaEc_f97uQ"
    
    lon_col = []
    lat_col = []
    place_id_col =[]
    
    for i, store in df.iterrows():
        address = (store['street'].replace(' ', '+') + ",+" + 
                   store['city'].replace(' ', '+') + ",+" + 
                   store['state'].replace(' ', '+'))
        
        store_url = url + address + "&key=" + key
        
        response = requests.request("GET", store_url)
        response_dict = json.loads(response.content)
        
        #if the request was succesful
        if response_dict["status"] == "OK":
            place_id = response_dict['results'][0]['place_id']
            lat = response_dict['results'][0]['geometry']['location']['lat']
            lon = response_dict['results'][0]['geometry']['location']['lng']
            
            # print(place_id, lat, lon)
            
            lon_col.append(lon)
            lat_col.append(lat)
            place_id_col.append(place_id)

        else:
            print("API Retrieval Failed.")
            
    df['place_id'] = place_id_col
    df['latitude'] = lat_col
    df['longitude'] = lon_col
    
    # print(df)
    return df


def scrape():
    # open website
    url = "https://www.riteaid.com/locations/pa.html"
    webdriverPath = 'msedgedriver.exe'

    service = Service(executable_path=webdriverPath)

    driver = webdriver.Edge(service=service)
    
    driver.get(url)
    
    # get the links to all city pages
    city_links = driver.find_elements(By.XPATH, '//a[@class="c-directory-list-content-item-link"]')
        
        
    for city in city_links:
        city_url = city.get_attribute("href")
        
        # open page with city's location in a new tab and scrape
        driver.execute_script("window.open('')")
        driver.switch_to.window(driver.window_handles[1])
        
        driver.get(city_url)
        
        # check if the canvas element exists (this indicates that there is only one address on the page)
        try:
            canvas = driver.find_element(By.XPATH, "//canvas")
            scrape_single_location_from_page(driver)
        except:
            scrape_multiple_locations_from_page(driver)
          
        # Switch back to old tab
        driver.close()
        
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(2)
    
    # quit driver    
    driver.quit()
        
    # create data frame with scraped data
    df = pd.DataFrame({
        'store_id': store_id_col,
        'street': street_col,
        'city': city_col,
        'state': state_col,
        'zip': zipcode_col,
        'phone': phone_col
        })
    
    # clean data
    df = drop_closed_stores(df)
    
    # get geo data from google API
    df = get_geo_data(df)
    
    # write data to csv
    file_name = 'riteaid.csv'
    df.to_csv(file_name, index=False)