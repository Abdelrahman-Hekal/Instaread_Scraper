from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
import pandas as pd
import time
import csv
import sys
import numpy as np
import calendar

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options  = webdriver.ChromeOptions()
    # suppressing output messages from the driver
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    # adding user agents
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # running the driver with no browser window
    chrome_options.add_argument('--headless')
    # disabling images rendering 
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.page_load_strategy = 'normal'
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    driver.set_page_load_timeout(10000)
    driver.maximize_window()

    return driver

def scrape_instaread(path):

    start = time.time()
    print('-'*75)
    print('Scraping instaread.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()

    # if no books links provided then get the links
    if path == '':
        name = 'instaread_data.xlsx'
        # getting the books under each category
        links = []  
        homepage = "https://instaread.co/books/allBooks"
        nbooks = 0
        driver.get(homepage)
        while True: 
            titles = wait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.ir-book-title-href")))

            for title in titles:
                try:                                  
                    link = title.get_attribute('href')
                    links.append(link)
                    nbooks += 1 
                    print(f'Scraping the url for title  {nbooks}')
                except Exception as err:
                    pass

            # checking the next page
            try:
                button = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//li[@class='page-next']")))
                driver.execute_script("arguments[0].click();", button)
                time.sleep(3)
            except:
                break
                    
        # saving the links to a csv file
        print('-'*75)
        print('Exporting links to a csv file ....')
        with open('instaread_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link'])
            for row in links:
                writer.writerow([row])

    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
        name = path.split('\\')[-1][:-4]
        name = name + '_data.xlsx'
    else:
        df_links = pd.read_csv('instaread_links.csv')

    links = df_links['Link'].values.tolist()

    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass

    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    print('-'*75)
    n = len(links)
    for i, link in enumerate(links):
        try:
            if link in scraped: continue
            driver.get(link) 
            time.sleep(3)
            details = {}
            print(f'Scraping the info for book {i+1}\{n}')            
            # title and title link
            title_link, title = '', ''    
            for _ in range(3):
                try:
                    title_link = link
                    title = wait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME,"h1"))).get_attribute('textContent').replace('\n', '').strip().title() 
                    break
                except:
                    driver.refresh()  
                    time.sleep(5)
                
            details['Title'] = title
            details['Title Link'] = title_link                          
            # Author
            author = ''
            try:
                author = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.book_author"))).get_attribute('textContent').replace('\n', '').strip().title()  
            except:
                pass

            details['Author'] = author
             
            # categories
            cat = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ir-category-h4")))
                spans = wait(div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "span")))
                for span in spans:
                    cat += span.get_attribute('textContent').strip() + ', '
                cat = cat[:-2]
            except:
                pass

            details['Category'] = cat         
         
            # rating
            rating = ''
            try:
                rating = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.ir-rating-value"))).get_attribute('textContent').strip()
            except:
                 pass
             
            details['Rating'] = rating
            
            # number of ratings
            nrevs = ''
            try:
                nrevs = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ir-overall-ratings"))).get_attribute('textContent').strip().replace('\n', ' ').split()[0]
            except:
                pass

            details['Number of Ratings'] = nrevs 
 
            # reading time
            read_time = ''
            try:
                read_time = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.ir-book-preview-meta-txt.ir-meta-read-duration"))).get_attribute('textContent').replace('read', ' ').replace('mins', 'min').strip()
            except:
                pass

            details['Reading Time'] = read_time

            # appending the output to the datafame       
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data ...')
                data.to_excel(name, index=False)
        except Exception as err:
            print(str(err))
            driver.quit()
            driver = initialize_bot()

    # optional output to excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'instaread.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":
    
    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_instaread(path)

