import pandas as pd
import numpy as np

# based on the city the user inputs, this function returns
# a dataframe with top most num_rows of zipcodes within the city to users
# if city is None, this function turns top most num_rows of zipcodes across
# the state
def make_recommendation(city, ratio, num_rows = 5):
    
    # read the files
    income_df = pd.read_csv('income_df_for_rec.csv')
    targeted_pop_df = pd.read_csv('targeted_pop_df_for_rec.csv')
    competitors_df = pd.read_csv('competitor_df_for_rec.csv')
    pop_df = pd.read_csv('total_population_df_for_rec.csv')
    
    # make sure num_rows is not too large. If it is, it will return None
    if num_rows > pop_df.shape[0]:
        print("The number of rows for display is too large, please select a number that is smaller than ", pop_df.shape[0])
        return None
    
    # change pandas dataframe to numpy for easier calculations to get final 
    # weighted score
    income_rank = income_df['rank'].to_numpy()
    targeted_pop_rank = targeted_pop_df['rank'].to_numpy()
    competitor_rank = competitors_df['overall_rank'].to_numpy()
    total_population_rank = pop_df['rank'].to_numpy()

    # calculate the final weighted score
    overall_rank = np.zeros(pop_df.shape[0])
    overall_rank += ratio['income'] * income_rank
    overall_rank += ratio['target_pop'] * targeted_pop_rank
    overall_rank += ratio['competitors'] * competitor_rank
    overall_rank += ratio['pop'] * total_population_rank

    # make a pandas dataframe of all zipcodes with their weighted scores 
    # as a new column, and sort by the weighted scores from small to large  
    rec_df = pd.DataFrame()
    rec_df['city'] = income_df['city']
    rec_df['zipcode'] = income_df['zipcode']
    rec_df['population'] = pop_df['Total population']
    rec_df['young_population'] = pop_df['Population < 5 years']
    rec_df['old_population'] = pop_df['Population between 65 to 74 years'] + pop_df['Population between 75 to 84 years'] + pop_df['Population >= 85']
    rec_df['income_median'] = income_df['weighted median']
    rec_df['no_of_competitors'] = competitors_df['no_of_competitors']
    rec_df['weighted_scores'] = overall_rank
    rec_df['rank'] = rec_df["weighted_scores"].rank(ascending=True)
    
    rec_df = rec_df.sort_values('rank')
    
    # If city is not specified, output top zipcodes(smallest weighted score) 
    # across state 
    if city == None:
        return rec_df[0:num_rows].reset_index(drop=True)

    # otherwise, return the top zipcodes within the city
    city_df = rec_df[rec_df['city'] == city.capitalize()]
    if num_rows <= city_df.shape[0]:
        return city_df[0:num_rows].reset_index(drop=True)
    else:
        return city_df.sort_values('rank').reset_index(drop=True)