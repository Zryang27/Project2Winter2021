#################################
##### Name:       Zhaorui Yang
##### Uniqname:         zryang
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

API_KEY = secrets.API_KEY


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''

    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        '''Returns a string representation of the national
        site instance's information.

        The string representation is in the format of
        '<name> (<category>): <address> <zip>'.

        Parameters
        ----------
        none

        Returns
        -------
        string
            A string representation of the national site
        instance. It's in the format of '<name> (<category>)
        : <address> <zip>'.
        '''
        information = self.name + ' (' + self.category + '): ' + self.address + ' ' + self.zipcode
        return information


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page
    url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    dict_state_name_url = {}
    url = 'https://www.nps.gov/index.htm'
    state_url_head = 'https://www.nps.gov'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    state_list_parent = soup.find('div', class_='SearchBar-keywordSearch input-group input-group-lg')
    state_list = state_list_parent.find('ul', class_='dropdown-menu SearchBar-keywordSearch').find_all('li')
    for state in state_list:
        state_name = state.find('a').text
        state_url = state.find('a')['href']
        dict_state_name_url[state_name.lower()] = state_url_head + state_url
    return dict_state_name_url


def get_site_instance(site_url):
    '''Make an instances from a national site URL.

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    Returns
    -------
    instance
        a national site instance
    '''
    if site_url in cache['site_page']:
        print('Using Cache')
        site_category = cache['site_page'][site_url]['site_category']
        site_name = cache['site_page'][site_url]['site_name']
        site_address = cache['site_page'][site_url]['site_address']
        site_zipcode = cache['site_page'][site_url]['site_zipcode']
        site_phone = cache['site_page'][site_url]['site_phone']
    else:
        print('Fetching')
        response = requests.get(site_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        site_category = soup.find('span', class_='Hero-designation').text.strip()
        site_name = soup.find('a', class_='Hero-title').text.strip()
        site_add_parent = soup.find('p', class_='adr')
        site_address_local = site_add_parent.find('span', itemprop='addressLocality').text.strip()
        site_address_region = site_add_parent.find('span', itemprop='addressRegion').text.strip()
        site_address = site_address_local + ', ' + site_address_region
        site_zipcode = site_add_parent.find('span', class_='postal-code').text.strip()
        site_phone = soup.find('span', class_='tel').text.strip()
        cache['site_page'][site_url] = {
            'site_category': site_category,
            'site_name': site_name,
            'site_address': site_address,
            'site_zipcode': site_zipcode,
            'site_phone': site_phone
        }
    return NationalSite(category=site_category, name=site_name,
                        address=site_address, zipcode=site_zipcode,
                        phone=site_phone)


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    '''
    list_of_site_instances = []
    site_url_list = []
    #state_url = 'https://www.nps.gov/state/al/index.htm'
    if state_url in cache['state_page']:
        print('Using Cache')
        site_url_list = cache['state_page'][state_url]
        for site_url in site_url_list:
            site = get_site_instance(site_url)
            list_of_site_instances.append(site)
    else:
        print('Fetching')
        response = requests.get(state_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        national_park_divs = soup.find_all('div', class_='col-md-9 col-sm-9 col-xs-12 table-cell list_left')
        site_url_head = 'https://www.nps.gov'
        site_url_tail = 'index.htm'
        for national_park_div in national_park_divs:
            national_park_url = national_park_div.find('a')['href']
            site_url = site_url_head + national_park_url + site_url_tail
            site_url_list.append(site_url)
            site = get_site_instance(site_url)
            list_of_site_instances.append(site)
        cache['state_page'][state_url] = site_url_list
    return list_of_site_instances


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    if site_object.name in cache['nearby_places']:
        print('Using Cache')
        results = cache['nearby_places'][site_object.name]
    else:
        print('Fetching')
        base_url_head = 'https://www.mapquestapi.com/search/v2/radius?origin='
        base_url_tail = '&radius=10&maxMatches=10&ambiguities=ignore&outFormat=json&key=' + API_KEY
        base_url_zipcode = site_object.zipcode
        new_url = base_url_head + base_url_zipcode + base_url_tail
        response = requests.get(new_url)
        results = response.json()
        cache['nearby_places'][site_object.name] = results
    return results


def load_cache():
    '''load cache file into python, return dict with
    the information in cache

    If there is not cache file (first time run the
    code), print 'Fetching', and create one with 4 keys:
    'main_page', 'state_page', 'site_page', 'nearby_places'.
    'main_page' is initialized as the dict return by
    function build_state_url_dict(). For more
    information please check the docstring of
    build_state_url_dict(). The values for other 3 keys
    are initialized as enpty dictionary. Return the newly
    created 4-keys-dictionary.
    If there has been cache file, load the file, process it
    and return the information in the cache file (which is
    a dict)

    Parameters
    ----------
    none

    Returns
    -------
    dict
        cache
    '''
    try:
        cache_file = open('data_cache.json', 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
        print('Using cache')
    except:
        cache = {'main_page': build_state_url_dict(),
                'state_page': {},
                'site_page': {},
                'nearby_places': {}
                }
        print('Fetching')
    return cache


def save_cache(cache):
    '''save cache into outside file

    Save the parameter cache (dict of information
    saved in web scraping) into outside file in
    format of json.

    Parameters
    ----------
    cache: dict
        4-keys dictionary save all the information
    scraped from different web site to avoid repeat visit.
    for the details of the dictionary, please refer to
    the docstring of function 'load_cache()'

    Returns
    -------
    none
    '''
    cache_file = open('data_cache.json', 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def print_results(results):
    '''print information in parameter 'results' in
    specific format

    process the raw data scrape from MapQuest API and
    get the information of nearby places of a national
    site. Print the information out in format of: '<name>
    (<category>): <strret address>, <city name>.

    Parameters
    ----------
    results: dictionary
        The dictionary return from MapQuest API

    Returns
    -------
    none
    '''
    for result in results['searchResults']:
        name = result['name']
        category = result['fields']['group_sic_code_name']
        address = result['fields']['address']
        city = result['fields']['city']
        place = Places(name=name, category=category, address=address, city=city)
        print('- ' + place.info())


class Places:
    '''a nearby places of a national site

    Instance Attributes
    -------------------
    name: string
        the name of a nearby place of a national site
        (e.g. 'Pilot Travel Center #284')

    category: string
        the category of a nearby place (e.g. 'Real Estate Agents')
        if no category information found, recorded as 'no category'

    address: string
        the address of a nearby place (e.g. '1669 Mall Rd')
        if no address information found, recorded as 'no address'

    city: string
        the city of a nearby place. (e.g. 'Monroe')
        if no city information found, recorded as 'no city'
    '''

    def __init__(self, name, category, address, city):
        self.name = name
        if category != '':
            self.category = category
        else:
            self.category = 'no category'
        if address != '':
            self.address = address
        else:
            self.address = 'no address'
        if city != '':
            self.city = city
        else:
            self.city = 'no city'

    def info(self):
        '''Returns a string representation of the national
        site instance's information.

        The string representation is in the format of
        '<name> (<category>): <address> <zip>'.

        Parameters
        ----------
        none

        Returns
        -------
        string
            A string representation of the national site
        instance. It's in the format of '<name> (<category>)
        : <address> <zip>'.
        '''
        return (self.name + ' (' + self.category + '): ' + self.address + ', ' + self.city)


cache = load_cache()

if __name__ == "__main__":
    flag = 0
    while True:
        ipt = input('Enter a state name (e.g. Michigan, michigan) or "exit"')
        if ipt == 'exit':
            break
        elif ipt.lower() in cache['main_page']:
            state_url = cache['main_page'][ipt.lower()]
            list_of_site_instances = get_sites_for_state(state_url)
            length_of_line = 26 + len(ipt)
            print('-' * length_of_line)
            print('List of national sites in ' + ipt.lower())
            print('-' * length_of_line)
            for idx, site in enumerate(list_of_site_instances):
                print('[' + str(idx+1) + ']', site.info())
            print('-' * length_of_line)
            while True:
                ipt_2 = input('Choose the number for detail search or "exit" or "back"')
                if ipt_2 == 'back':
                    break
                elif ipt_2 == 'exit':
                    flag = 1
                    break
                elif ipt_2.isnumeric() is True:
                    if int(ipt_2) <= len(list_of_site_instances) and int(ipt_2) > 0:
                        results = get_nearby_places(list_of_site_instances[int(ipt_2)-1])
                        length_of_line_2 = 12 + len(list_of_site_instances[int(ipt_2)-1].name)
                        print('-' * length_of_line_2)
                        print('Places near ' + list_of_site_instances[int(ipt_2)-1].name)
                        print('-' * length_of_line_2)
                        print_results(results)
                        print('-' * length_of_line_2)
                    else:
                        print('[Error] Invalid input')
                else:
                    print('[Error] Invalid input')
        else:
            print('[Error] Please enter proper state name')
        if flag == 1:
            break
    save_cache(cache)
