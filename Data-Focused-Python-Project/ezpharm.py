import pandas as pd
import riteaid_scraper
import walgreens_scraper
import cvs_scraper
import make_rec as rec
import processor
import plotter


MENU_TEXT = '''

*** EzPharm Recommendation Engine ***
      
1 - Find the best area in the whole of Pennsylvannia to open up a new pharmacy
2 - Find the best area in a specific city in Pennsylvannia to open up a new pharmacy
Q - Quit
      
Choose an option above, or enter Q to quit:
>  '''

SCRAPE_CHOICE_TEXT = '''
Would you like the recommendation engine to make use of saved data, or run the scraping scripts again?

1 - Use Saved Data (default)
2 - Run Scraping Scripts (can take up to 30 minutes to finish executing)
>  '''

WEIGHT = {
    'competitors': 0.25,
    'income': 0.25,
    'pop': 0.25,
    'target_pop': 0.25
    }

def generate_weights_text(WEIGHT):
    return '''
Below are the assigned weights for each decision factor:

{:46s} {:>6s}
-----------------------------------------------------
{:46s} {:>6.2f}
{:46s} {:>6.2f}
{:46s} {:>6.2f}
{:46s} {:>6.2f}
'''.format('Factor', 'Weight', 
            'Number of Competitors in Zipcode', WEIGHT['competitors'],
            'Median Household Income', WEIGHT['income'],
            'Total Population', WEIGHT['pop'],
            'Total Target Population (Ages < 5 and > 65)', WEIGHT['target_pop']
            )

    
''' 
Function that generates the recommendation text
'''
def generate_result_text(result, city=None):
    text = '\n\n***********************************************************************************************************************************************************************\n\n'
    
    best = result.loc[0]
    
    if city == None:
        city = 'Pennsylvania'
        text += 'Based on the weights assigned to the factors above, the best zipcode to open a new pharmacy in {:s} is {:d} located in {:s}.\n\n'.format(city, int(best['zipcode']), best['city'])
    else:
        text += 'Based on the weights assigned to the factors above, the best zipcode to open a new pharmacy in {:s} is {:d}.\n\n'.format(best['city'], int(best['zipcode']))
    
    text += 'There are currently {:d} competitors in the area.\n\n'.format(int(best['no_of_competitors']))
            
    text += 'Overall, there are approximately {:,d} people living in zipcode {:d} with a total {:,d} people that would potentially need special care'.format(int(best['population']), int(best['zipcode']), int(best['young_population'] + best['old_population']))
    text += ' ({:,d} below the age of 6 and {:,d} over the age of 64).\n\n'.format(int(best['young_population']), int(best['old_population']))
            
    text += 'The median income in zipcode {:d} is ${:,.2f}.\n\n'.format(int(best['zipcode']), best['income_median'])
    
    if result.shape[0] > 1:
        text += ('Below is a list of other top ranked locations in ' + city + ' to open a new pharmacy:\n\n' +
                 result.iloc[1:, :8].to_string()
                 )
        
    return text
        

'''
Function to display main menu and prompt user for their choice 
'''
def get_menu_choice():
    menu_choice = ''
    
    while menu_choice != 'Q' or menu_choice != 'q':
        menu_choice = input(MENU_TEXT)
              
        if menu_choice == '1' or menu_choice == '2':
            return menu_choice
        elif menu_choice == 'Q' or menu_choice == 'q':
            return 'q'
        else:
            print('Please choose one of the options provided.\n')
            

'''
Function to prompt user to either use the default factor weights or enter new weights
'''
def display_factor_weights_prompt():
    prompt = generate_weights_text(WEIGHT) + "\nDo you want to change the default assigned weights? (Y/N)>  "
    
    change_weight_choice = input(prompt)
    
    if change_weight_choice == 'Y' or change_weight_choice == 'y':
        update_factor_weights()
        print(generate_weights_text(WEIGHT))
    else:
        print('\nProceeding with default assigned weights...')


'''
Function to update the factor weights
'''
def update_factor_weights():
    print('\nPlease note that the weights of all factors must add up to 1!\n')
   
    competitors_weight_str = input('Enter preferred weight for Number of Competitors factor: ')
    income_weight_str = input('Enter preferred weight for Median Household Income factor: ')
    pop_weight_str = input('Enter preferred weight for Total Population factor: ')
    
    try:
        WEIGHT['competitors'] = float(competitors_weight_str)
        WEIGHT['income'] = float(income_weight_str)
        WEIGHT['pop'] = float(pop_weight_str)

        difference = WEIGHT['competitors'] + WEIGHT['income'] + WEIGHT['pop']

        if difference < 1:
            WEIGHT['target_pop'] = 1 - WEIGHT['competitors'] - WEIGHT['income'] - WEIGHT['pop']
        else:
            WEIGHT['competitors'] = 0.25
            WEIGHT['income'] = 0.25
            WEIGHT['pop'] = 0.25
            WEIGHT['target_pop'] = 0.25
            
            print('\nYou entered an invalid value. Proceeding with default assigned weights...')
    except:
        print('\nYou entered an invalid value. Proceeding with default assigned weights...')
        

'''
Function to prompt user to either scrape again or used saved data
'''
def display_scrape_choice_prompt():
    scrape_choice = input(SCRAPE_CHOICE_TEXT)
    
    if scrape_choice == '2': # if user chooses to scrape again
        print('\nRunning the scraping scripts. This will take some time...')
        
        riteaid_scraper.scrape()
        
        walgreens_scraper.scrape()
        
        cvs_scraper.scrape()
        
        print('\nFinished scraping data.')
        
        print('\nMerging data...')
        
        # read output file of scraping scripts
        cvs_csv = 'cvs.csv'
        riteaid_csv = 'riteaid.csv'
        walgreens_csv = 'walgreens.csv'
        
        # merge all pharmacy locations
        processor.merge_and_rank_competitors(cvs_csv, riteaid_csv, walgreens_csv)
        
        print('\nFinished merging data.')
    else:
        print('\nProceeding with saved data...')


'''
Function to check if city entered by user is valid
'''
def isValidCity(city):
    df = pd.read_csv('final_df_with_rank.csv')

    cities = set(df['city'].str.title())

    if city != None:
        return city.title() in cities

'''
Main method
'''
def main():
    city = None
    
    # display main menu and get user's choice of use case
    choice = get_menu_choice()

    while choice != 'q':
        if choice != '1':
            while not isValidCity(city):
                city = input('\nEnter the name of a city in Pennsylvannia: ')

                if not isValidCity(city):
                    print('\nYou did not enter the name of a city in Pennsylvannia. Please try again.')
        
        # prompt user to scrape live or use previously scraped data
        display_scrape_choice_prompt()
        
        # get confirmation on default factor weights or get weights from user
        display_factor_weights_prompt()

        result = rec.make_recommendation(city, WEIGHT)

        # display results of recommendation engine
        print(generate_result_text(result, city))
        
        # plot pharmacies map
        plotter.plot_pharmacy_map()

        if result.shape[0] > 1:
            processed_result = plotter.preprocess(result)
            
            plotter.display(processed_result[0], processed_result[1])

        prompt = input('\n\nWould you like to run the recommendation engine again? (Y/N)\n>  ')

        if prompt == 'Y' or prompt == 'y':
            choice = get_menu_choice()
        else:
            print('\n\nThank you for using EzPharm Recommendation Engine.\n\nQuitting now...')
            choice = 'q'


if __name__ == '__main__':
    main()
