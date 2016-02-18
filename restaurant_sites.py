from bs4 import BeautifulSoup, SoupStrainer
import json
import re
import mechanize
import urllib
import urllib2

class RestaurantGuide(object):

    def __init__(self, session):
        self.session = session
        self.browser = mechanize.Browser()
        self.url = "http://www.restaurant-guide.com"

    def search(self,query):
        req = mechanize.Request(self.url)
        req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5")
        self.browser.open(req)
        self.browser.select_form(nr=0)
        self.browser.form["restaurant"] = query
        self.browser.submit()
        res = self.browser.response()
        soup = BeautifulSoup(res,parse_only=SoupStrainer("div"),from_encoding="utf-8")
        results_no_header = soup.find(attrs={'id':'h2'})
        if results_no_header and re.match(r'^0',results_no_header.get_text()):
            return []
        self._grab_next_page_url(soup)
        return self._grab_json(soup)

    def _grab_next_page_url(self,soup):
        the_next_html_element = soup.find(attrs={'class':'next'})
        if the_next_html_element:
            url = self.url + the_next_html_element.a.get('href')
            self.session['next_page'] = url
        else:
            self.session['next_page'] = "__last__"

    def _grab_json(self,soup):
        soup.find(attrs={'class' : "special-offers"}).extract()

        restaurants = soup.find_all("div", "item")

        restaurant_dicts = []

        no_of_results = 0
        for restaurant in restaurants:
            if no_of_results == 10:
                break
            restaurant_dict = {}
            restaurant_title = restaurant.find_all('h3')[0]
            restaurant_dict['name'] = restaurant_name = restaurant_title.get_text()
            restaurant_dict['restaurant_guide_url'] = self.url + restaurant_title.find_all('a')[0]['href'].__str__()
            restaurant_address_title = restaurant.find_all('h4')[0]
            restaurant_dict['google_map'] = restaurant_address_title.find_all('a')[0]['href'].__str__()
            restaurant_address_title.a.extract()
            restaurant_dict['address'] = restaurant_address_title.get_text()
            restaurant_dicts.append(restaurant_dict)

            restaurant_dict['rating'] = self._grab_restaurant_rating(restaurant_dict['name'],restaurant_dict['address'])

            self._grab_more_json(restaurant_dict['restaurant_guide_url'],restaurant_dict)
            no_of_results += 1

        return restaurant_dicts

    def _grab_restaurant_rating(self,restaurant_name,restaurant_address):
        post_code = re.split(',',restaurant_address).pop()
        post_code = re.sub(r'^\s+','',post_code)
        post_code = re.sub(r'\s+$','',post_code)

        url_enc_post_code = urllib.quote(post_code)
        restaurant_name = re.sub(r'&','',restaurant_name)
        restaurant_name = re.sub(r'-.+','',restaurant_name)
        restaurant_name = re.sub(r'^\s+','',restaurant_name)
        restaurant_name = re.sub(r'\s+$','',restaurant_name)
        url_encoded_restuarant_name = urllib.quote(restaurant_name.encode('utf-8'))
        
        url = "http://ratings.food.gov.uk/search/en-GB/"+ url_encoded_restuarant_name + '/' + url_enc_post_code + '/json'

        response = urllib2.urlopen(url).read()

        rating = re.match(r'.+?"RatingValue":"(\d)"',response)
        if rating:
            rating = rating.group(1)
        else:
            rating = "0"
        return rating


    def _grab_more_json(self,url, restaurant_dict):
        res = self.browser.open(url)
        soup = BeautifulSoup(res)

        phone = soup.find(attrs={'class' : "phone"}).extract()
        if phone.b:
            phone.b.extract()
        if phone.label:
            phone.label.extract()
        if phone.b:
            phone.b.next_sibling.extract()
            phone.b.extract()
        restaurant_dict['phone'] = phone.get_text()

        cuisine = soup.find(attrs={'class' : "cuisine"}).extract()
        cuisine.label.extract()
        restaurant_dict['cuisine'] = cuisine.get_text()

        worktime = soup.find(attrs={'class' : "worktime"}).extract()
        worktime.label.extract()
        opening_times = worktime.get_text()

        restaurant_dict['opening_times'] = opening_times

        price = soup.find(attrs={'class' : "price"}).extract()
        price.label.extract()
        price.label.extract()
        price.label.extract()

        both_prices = re.split(r"\n",re.sub(r'[ \r\xa0\t]','',price.get_text()))
        restaurant_dict['avg_lunch_price'] = both_prices[0]
        restaurant_dict['avg_dinner_price'] = both_prices[1]

        res = self.browser.back()

    def more(self):
        next_page = self.session['next_page']
        if next_page == '__last__':
            return []
        res = self.browser.open(self.session['next_page'])
        res = self.browser.open(self.session['next_page'])
        soup = BeautifulSoup(res, parse_only=SoupStrainer("div"),from_encoding="utf-8")
        self._grab_next_page_url(soup)
        return self._grab_json(soup)
