import pandas as pd
from shapely.geometry import Point
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
from operator import index

# combine dataframes
def create_pharmacy_df():
    df1 = pd.read_csv('cvs.csv')
    df1['Pharmacy'] = 'CVS'
    df2 = pd.read_csv('riteaid.csv')
    df2['Pharmacy'] = 'Riteaid'
    df3 = pd.read_csv('walgreens.csv')
    df3['Pharmacy'] = 'Walgreens'
    df_list = [df1, df2, df3[['latitude', 'longitude', 'Pharmacy']]]
    df = pd.concat(df_list, ignore_index=True)
    df['state'] = 'Pennsylvania'
    return df

# plot pharmacy location on map
def plot_pharmacy_map():
    df = create_pharmacy_df()
    fig = px.scatter_geo(df, lat='latitude', lon='longitude', hover_name="zip", color='Pharmacy', locationmode='USA-states')
    fig.update_geos(fitbounds="locations", showsubunits=True)
    fig.update_layout(title='Pharmacies', title_x=0.5, geo_scope='usa')
    fig.show()
    
    
def preprocess(data):
    nrows = data.shape[0]
    is_city = True
    #if there's only 1 zipcode(say one city one zipcode), verbal summary statistics 
    #on maine page is sufficient
    if (nrows < 2):
        print("There is only one zipcode associated with the desired city. Please refer to summary output of your zipcode.\n")
    else: 
        #if there's more than 100 rows of zipcode for recommendation, it's a recommendation on a state level
        if (data.loc[0]['city'] != data.loc[1]['city']):
            is_city = False
            
    return (data,is_city)

# prepare and display other result visuals
def display(df,is_city):


    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2,3,figsize=(17,9))

    
    index = np.arange(len(df.index))
    width = 0.35
    label = df['zipcode'].tolist()

    non_minor_pop = df['population'].values - df['young_population'].values - df['old_population'].values
    minor_pop = df['young_population'].values + df['old_population'].values

    #get the name of the city 
    city = df.loc[0]['city']
    zipcode = df.loc[0]['zipcode']

    #show population younger than 5
    sub_title = "Proportion of population younger than 5 years"
    ax1.pie(df['young_population'], labels = label, shadow = True, autopct='%1.0f%%')
    ax1.set_title(sub_title)
    # plt.show()

    #show population over 65
    sub_title = "Proportion of population over 65 years"
    ax2.pie(df['old_population'], labels = label, shadow = True, autopct='%1.0f%%')
    ax2.set_title(sub_title)
    # plt.show()

    ax3.bar(index, df['income_median'], width = width, label = label)
    ax3.set_ylabel('Median Income($)')
    ax3.set_xlabel('Descending Ranked Zipcodes')
    ax3.set_ylim([df['income_median'].min() - 1000, df['income_median'].max() + 1000])
    ax3.set_xticks(index)
    ax3.set_xticklabels(label)
    ax3.set_title('Buying Power based on Median Income')

    #show population of the comibned targeted
    sub_title = "Proportion of Total targeted population"
    ax4.pie(df['young_population'].values + df['old_population'].values, labels = label, shadow = True, autopct='%1.0f%%')
    ax4.set_title(sub_title)

    ax5.bar(index, non_minor_pop, width, label = 'General Population')
    ax5.bar(index, minor_pop, width, label = 'Special care Population', bottom=non_minor_pop)

    ax5.set_ylabel('Population')
    ax5.set_title('Stacked bar plot of Total Population')
    ax5.set_xlabel('Zipcodes')
    ax5.set_xticks(index)
    ax5.set_xticklabels(label)
    ax5.legend()

    ax6.barh(df['zipcode'].values.astype('str')[::-1] ,df['no_of_competitors'].values, color = 'red')
    ax6.set_xlabel('Number of Operating Competitors')
    ax6.set_ylabel('Descending Ranked Zipcodes')
    ax6.set_title('Number of Operating Competitors by Zipcode')


    if (is_city == True):
        fig.suptitle(city + ' (1st Rank = ' + str(label[0]) + ')'+'\'s Data Visualization ',fontweight="bold", size=20)
    else:
        fig.suptitle('Pennsylvania\'s Data Visualization ',fontweight="bold", size=20)
    plt.show()
