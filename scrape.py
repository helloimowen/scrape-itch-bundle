import yaml 
import time
import json
import csv
from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def restore_bundle_info(file_loc):
    results = open(file_loc, 'r')
    return json.load(results)


def make_diff(old_bundle, new_bundle):
    old_games = [] 
    for link, game_list in old_bundle.items():
            old_games += [game['title'] for game in game_list]

    #print (old_games)
    diff = {}
    for link, game_list in new_bundle.items():
        new_list = [game for game in game_list if game['title'] not in old_games]
        
        diff[link] = new_list

    print(diff)
    
    return diff



def get_constants(yaml_file_name): # Grabs the initial constants from contants.yml
    yaml_file = open(yaml_file_name, 'r')
    contents = yaml.load(yaml_file, Loader=yaml.FullLoader)
    return contents 


def splice_and_increment(url,element): # moves to next page 
    index = url.find(element)
    page_num = int(url[index+len(element):])
    page_num += 1
    return url[:index+len(element)] + str(page_num), page_num


def check_redirect(driver):
    try: # Looking for alternatives to this try/except.
        elements = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".promotion_title")))
        return True
    except: 
        return False 


def check_404(driver):
    try: # Looking for alternatives to this try/except.
        elements = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".not_found_page")))
        return True
    except: 
        return False 


def grab_page(full_url, page_num, driver, user, password): # makes request for page.  

    print("Grabbing ", full_url)

    driver.get(full_url)

    if check_404(driver):
        print('Hit 404 page. Finishing process.')
        return True, None
    if check_redirect(driver):
        print('Redirected. Need to authenticate user.')
        authenticate(driver, user, password)
        driver.get(full_url)

    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".game_title")))
    finally:
        result_dict = parse_page(driver.page_source.encode('utf-8'), full_url, page_num)

    return False, result_dict

def authenticate(driver, user, password): # Authentication step if you've registered the bundle 
    print('Authenticating...')

    driver.get('https://itch.io/login')

    time.sleep(0.5)

    driver.find_element_by_name('username').send_keys(user)
    driver.find_element_by_name('password').send_keys(password)
    driver.find_element_by_css_selector('button.button').click() 
    print('Done.')

    return 

# Loops through the pages. Pass in True to test to just get the first page. 
def loop_pages(base, secret, element, user, password, driver, test=False):
    page_num = 1
    parse_url = base + secret + element + str(page_num)
    not_found_page=False
    results_list = {}
    while not_found_page == False:
        not_found_page,results = grab_page(parse_url, page_num, driver, user, password)
        if results:
            results_list.update(results)
            parse_url,page_num = splice_and_increment(parse_url,element)

        if test:
            break
    return results_list
    
# parses DOM for game names and descriptions. Outputs dictionary of page content. 
def parse_page(page_contents, url, page_num): 
    page_object = BeautifulSoup(page_contents, features="html.parser")
    titles = page_object.find_all(class_='game_row_data')
    page_dict = {}
    game_list = []
    for title in titles:
        single_game = {}
        single_game['title'] = title.find(class_='game_title').get_text()
        single_game['author'] = title.find(class_='game_author').get_text().replace('by ', '')
        single_game['description'] = title.find(class_='game_short_text').get_text()
        single_game['link'] = title.find('a').get('href')
        platforms = title.find_all('span')
        clean = map(lambda x : x.get('title').replace('Available for ', ''), platforms)
        single_game['platforms'] = ', '.join(list(clean))
        single_game['pg'] = page_num # provides the page number on each item, and splits things up visually 
        game_list.append(single_game)

    page_dict[url] = game_list
    return page_dict


def name_dict_to_yaml(results): 
    return yaml.dump(results, default_flow_style=False,encoding='utf-8',allow_unicode=True,sort_keys=False)

def flatten_for_csv(structure):
    #print(structure)
    flat_list = []
    for link, game_lists in structure.items():
        for game in game_lists:
            game['example_download_link'] = link
            flat_list.append(game)
    return flat_list

def write_page_to_files(json_content, yaml_content, csv_content, append):
    print('writing json file')
    f = open(append + "_game_list.json", "w")
    f.write(json.dumps(json_content))
    f.close()

    print('writing yaml file')
    f = open(append + "_current_game_list.yml", "w")
    f.write(yaml_content.decode("utf-8") )
    f.close()

    print('writing csv file')
    f = open(append + "_current_game_list.csv", "w")
    dict_writer = csv.DictWriter(f, csv_content[0].keys())
    dict_writer.writeheader()
    dict_writer.writerows(csv_content)
    f.close()

def run_scrape_process():
    page_pieces = get_constants('constants.yml')

    print("Starting webdriver...")
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")
    options.add_argument('user-agent=' + page_pieces['user_agent'])
    driver = webdriver.Chrome(options=options, 
                            executable_path=page_pieces['web_driver_location']) # start selenium driver once. 

    print("Done.")

    results = loop_pages(page_pieces['url_base'], 
                        page_pieces['bundle_secret'], 
                        page_pieces['page_element'], 
                        page_pieces['itch_user'], 
                        page_pieces['itch_pw'], 
                        driver, test=False)

    yaml_content = name_dict_to_yaml(results)

    csv_content = flatten_for_csv(results)

    write_page_to_files(results, yaml_content, csv_content, 'current')



    driver.quit()

def create_and_write_diff():
    old = restore_bundle_info('bundle_for_racial_justice_and_equality_first_release/game_list.json')
    new = restore_bundle_info('current_game_list.json')

    diff = make_diff(old, new)  

    yaml_content = name_dict_to_yaml(diff)

    csv_content = flatten_for_csv(diff)

    write_page_to_files(diff, yaml_content, csv_content, 'new')


create_and_write_diff()