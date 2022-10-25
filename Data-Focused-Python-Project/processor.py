import pandas as pd
import numpy as np
import os
    
'''
Function to merge all the scraped pharmacy location data
'''
def merge_data(cvs_csv, riteaid_csv, walgreens_csv):
    cvs_df = pd.read_csv(cvs_csv)
    cvs_df['type'] = 'cvs'
    
    riteaid_df = pd.read_csv(riteaid_csv)
    riteaid_df['type'] = 'riteaid'
    
    walgreens_df = pd.read_csv(walgreens_csv)
    walgreens_df['type'] = 'walgreens'
    
    merged_df = pd.concat([cvs_df, riteaid_df, walgreens_df])
    
    return merged_df


'''
Function to rank all zip codes within each city by number of competitors
'''
def rank_zips_by_competitors(df):
    df = df[['city', 'zip', 'type']].copy()
    
    df['city'] = df['city'].str.upper()
    
    grouped = df.groupby(['city','zip'], as_index=False)['type'].count()
    
    grouped.columns = ['city', 'zip', 'no_of_competitors']
    
    grouped['rank_in_city'] = grouped.groupby('city')['no_of_competitors'].rank(ascending=True, method='dense')
    grouped['overall_rank'] = grouped['no_of_competitors'].rank(ascending=True, method='dense')
    
    # print(grouped.to_string())
    
    grouped.to_csv('competitors_ranked.csv', index=False)
    
    return grouped


# add zipcodes and city names that only appear in population dataframe to competitor dataframe with rank 0.5;
# remove zipcodes that only appear in population dataframe
def prepare_merge():
    competitors_with_rank_file_name = 'competitors_ranked.csv'
    total_pop_with_rank_file_name = 'total_population_df_for_rec.csv'
    path = os.getcwd()
    
    competitors_df = pd.read_csv(path + competitors_with_rank_file_name)
    pop_df = pd.read_csv(path + total_pop_with_rank_file_name)

    # find zipcodes that exist in population dataframe but not in competitors' dataframe, and remove them
    competitor_missing_zipcodes = list(set(pop_df.Zip_code)-(set(competitors_df.zip)))
    competitor_missing_zipcodes.sort()
    competitor_missing_zipcodes_and_city = pop_df[pop_df['Zip_code'].isin(competitor_missing_zipcodes)][['Zip_code','city']]
    
    # add these missing zipcodes to competitor dataframe
    missing_rows = np.zeros(len(competitor_missing_zipcodes)* competitors_df.shape[1]).reshape(len(competitor_missing_zipcodes), competitors_df.shape[1])
    missing_rows[:,1] = competitor_missing_zipcodes
    num_rows_of_original_competitors_df = competitors_df.shape[0]
    competitors_df = competitors_df.append(pd.DataFrame(missing_rows, 
                                   columns = competitors_df.columns.to_list()))
    # add the cities of the missing zipcodes to competitor dataframe
    competitors_df.iloc[num_rows_of_original_competitors_df:,0] = list(competitor_missing_zipcodes_and_city['city'])
    competitors_df['city'] = competitors_df['city'].str.capitalize()

    # make weighted score for these missing zipcodes 0.5 because there is no competitor in this zipcode
    competitors_df.iloc[num_rows_of_original_competitors_df:,4] = 0.5
    # remove zipcode duplicates 
    competitors_df_with_no_duplicates = competitors_df[~competitors_df['zip'].duplicated()]

    # find zipcodes that are in competitors but not in population dataframe, and remove them
    zips_not_in_pop = list(set(competitors_df_with_no_duplicates.zip)-set(pop_df.Zip_code))

    competitors_df_with_no_duplicates = competitors_df_with_no_duplicates[~competitors_df_with_no_duplicates['zip'].isin(zips_not_in_pop)]
    competitors_df_with_no_duplicates = competitors_df_with_no_duplicates.sort_values('zip').reset_index(drop=True)
    competitors_df_with_no_duplicates.to_csv('competitor_df_for_rec.csv', index = False)
    return competitors_df_with_no_duplicates


def merge_and_rank_competitors(cvs_csv, riteaid_csv, walgreens_csv):
    df = merge_data(cvs_csv, riteaid_csv, walgreens_csv)
    
    rank_zips_by_competitors(df)
    prepare_merge()