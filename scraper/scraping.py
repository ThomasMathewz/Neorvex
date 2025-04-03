from django.core.management.base import BaseCommand
from selenium import webdriver
from .models import Product, Review
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from requests import get
from bs4 import BeautifulSoup as bs
from pprint import pprint
from .sentiment import Analyse
import scrapy
import json

class ChromeSource:
    def getSource(self, URL):
        options = Options()
        options.add_argument('headless')
        options.add_argument('log-level=3')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(URL)
        retval = driver.page_source
        driver.quit()
        return retval

class toDB(BaseCommand):
    prodID = ""

    def add_arguments(self, parser):
        parser.add_argument('PID', type=str)
        parser.add_argument('title', type=str)
        parser.add_argument('rating', type=float)
        parser.add_argument('specifications', type=str)

    def handle(self, product_data):
        self.prodID = product_data['PID']

    def insertSpecs(self, product_data):
        Product.objects.create(
            PID=product_data['PID'],
            title=product_data['title'],
            rating=float(product_data.get('rating', 0)),
            url=product_data['link'],
            image=product_data.get('image', None),
            price=float(product_data.get('price', 0)),
            specifications=product_data.get('specs', '')
        )

    def insertReviews(self, reviews_data):
        for review_data in reviews_data:
            Review.objects.create(
                id=review_data['id'],
                PID=review_data['PID'],
                heading=review_data['heading'],
                review=review_data['review'],
                up=review_data['up'],
                down=review_data['down']
            )

class ScrapeFL(BaseCommand):
    globalPID = 0
    URL_Base = "https://www.flipkart.com"
    limit_pages = 1
    limit_reviews = 10

    def __init__(self):
        self.toDB = toDB()

    def getPID(self, string):
        try:
            start = string.index("pid=")
            end = string.index('&')
            return string[start + 4:end]
        except:
            return ''

    def scrapeProduct(self, string):
        print("Scraping product:", string)
        URL = "https://www.flipkart.com/search?q=" + string
        soup = bs(get(URL).text, 'lxml')
        final_output = {}
        p_no = 0
        for i in range(min(self.limit_pages, p_no + 1)):
            print("Extracting product names from page", i + 1)
            data = self.extractProductNames(URL + "&page=" + str(i + 1))
            for inp in range(min(len(data),5)):  # Loop through all products
                print("Scraping individual product:", data[inp]['title'])
                data_individual = self.scrapeIndividual(data[inp])
                output = {
                    'product': data_individual[0],  # dic
                    'reviews': data_individual[1]  # lis-lis-dic
                }
                final_output = {
                    'PID': data[inp]['PID'],
                    'title': data[inp]['title'],
                    'price': data[inp]['price'],
                    'link': data[inp]['link'],
                    'image': data[inp]['image'],
                    'rating': data_individual[0]['rating'],
                    'specs': data_individual[0]['specs'],
                    'product_data': {'PID': data[inp]['PID'], 'title': data[inp]['title'], 'rating': float(data_individual[0]['rating']), 'specifications': data_individual[0]['specs']}
                }
                print(json.dumps(output, indent=4))
                print(json.dumps(final_output, indent=4))
                self.toDB.handle(final_output['product_data'])
                self.toDB.insertSpecs(final_output)
                if output['reviews']:  # Check if there are reviews
                    self.toDB.insertReviews(output['reviews'])
                product = Product.objects.get(PID=data[0]['PID'])
                predicted_rating = Analyse(self).predictRating()
                product = Product.objects.get(PID=data[0]['PID'])
                product.predicted_rating = predicted_rating
                product.save()
                Review.objects.all().delete()

    def extractProductNames(self, URL_product):
        print("Extracting product names from URL:", URL_product)
        all_results = []
        rectify = "CGtC98"
        soup = bs(get(URL_product).text, 'lxml')
        title_class = "KzDlHZ"
        image_class = "DByuf4"
        price_class = "Nx9bqj _4b5DiR"
        for i in soup.findAll('a', {'class': rectify}):
            title = i.find('div', {'class': title_class})
            image = i.find('img', {'class': image_class})
            price = i.find('div', {'class': price_class})
            if title and image and price:
                all_results.append({
                    'title': title.text,
                    'link': self.URL_Base + i['href'],
                    'PID': self.getPID(i['href']),
                    'image': image['src'],
                    'price': price.text.strip()[1:].replace(',', '')
                })
            else:
                print("Skipping product due to missing information")
        print(all_results)
        return all_results

    def scrapeIndividual(self, Object_individual):
        print("Scraping individual product:", Object_individual['title'])
        soup = bs(get(Object_individual['link']).text, 'lxml')
        PID = Object_individual['PID']
        P_name = Object_individual['title']
        in_spec_class = "xFVion"
        in_spec_name = "_7eSDEz"
        review_class = "_23J90q RcXBOT"
        rating_class = "ipqd2A"

        retval = {}

        try:
            URL_review = soup.find('div', {'class': review_class}).parent['href']
        except AttributeError:
            URL_review = None

        try:
            rating = soup.find('div', {'class': rating_class}).text
        except:
            rating = 0

        spec_div = soup.find('div', {'class': in_spec_class})
        specs = []
        if spec_div:  # Ensure spec_div is not None
            for li in spec_div.findAll('li', {'class': in_spec_name}):
                specs.append(li.text.strip())
        else:
            print(f"Specifications not found for product {P_name}")

        retval['title'] = P_name
        retval['PID'] = PID
        retval['rating'] = rating
        retval['specs'] = ','.join(specs)
        return [retval, self.getReviews(self.URL_Base + URL_review, PID) if URL_review else []]

    def getReviews(self, reviewURL, PID):
        print("Getting reviews for product:", PID)
        retval = []
        soup = bs(ChromeSource().getSource(reviewURL), 'lxml')
        temp_url = reviewURL.split('?')[0]
        URL = temp_url + "?page=" + str(1)
        print("Getting reviews from page:", URL)
        retval += self.getReviewPerPage(URL, PID)
        return retval

    def getReviewPerPage(self, reviewURL, PID):
        print("Getting reviews from URL:", reviewURL)
        soup = bs(ChromeSource().getSource(reviewURL), 'lxml')
        box_class = "col EPCmJX Ma1fCG"
        heading_class = "z9E0IG"
        review_class = "ZmyHeo"
        span_class = "tl9VpF"

        blocks = soup.findAll('div', {'class': box_class})
        blocks.sort(key=lambda x: int(x.find('span', {'class': span_class}).text), reverse=True)  # sort by helpful reviews
        reviews = []
        n=1
        for block in blocks[:self.limit_reviews]:
            heading = block.find('p', {'class': heading_class}).text
            review = block.find('div', {'class': review_class}).div.div.text
            thumbs_up = block.findAll('span', {'class': span_class})[0].text
            thumbs_down = block.findAll('span', {'class': span_class})[1].text
            review_data = {
                'id':n,
                'PID': PID,
                'heading': heading,
                'review': review,
                'up': thumbs_up,
                'down': thumbs_down
            }
            reviews.append(review_data)
            n+=1
        return reviews

    def add_arguments(self, parser):
        parser.add_argument('product', type=str)

    def handle(self, *args, **options):
        self.globalPID = options['product']
        self.scrapeProduct(self.globalPID)