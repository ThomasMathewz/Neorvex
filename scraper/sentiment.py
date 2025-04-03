from io import StringIO
from django.core.management.base import BaseCommand
from textblob import TextBlob
from math import log,exp
from .models import Review, Product

class Analyse(BaseCommand):
    
    def add_arguments(self, parser):
        parser.add_argument('PID', type=str)

    def handle(self, *args, **options):
        self.PID = options['PID']
        self.predictRating()

    def getRating(self,pid):
        try:
            return Product.objects.get(PID=pid).rating
        except:
            return 0

    def _sigmoidal(self,value):
        retval = ( 1 + exp(-value))**-1
        return retval

    def _sentimentFactor(self,up,down):
        try:
            normalize = log(int(up)-int(down),10)
            return self._sigmoidal(normalize)
        except:
            return 0

    def averageSentiment(self):
        retval = []
        dic={}
        PID=""
        for review in Review.objects.all():
            try:
                PID=review.PID
                string  =  str(review.heading)+' '+str(review.review)
                sentiment = TextBlob(string).sentiment.polarity
                print(sentiment)
                factor = self._sentimentFactor(review.up,review.down)
                retval.append(sentiment + sentiment*factor)
            except:
                pass
        try:
            at_10=sum(retval)/len(retval)
            dic['NLP']=at_10
            dic['PID']=PID
            return dic
        except:
            dic['NLP']=0
            dic['PID']=PID
            return dic

    def predictRating(self):
        dic = self.averageSentiment()       #at_10=sum(retval)/len(retval)
        at_10=dic['NLP']
        PID=dic['PID']
        to_5 = at_10*5                      #0<=at_10<=1
        
        if at_10 == 0:                      #NLP rating generated from reviews=0
            to_5 = self.getRating(PID)         #no reviews  to_5=only ratings on the product
        rating = self.getRating(PID)           #if reviews, actual rating -> rating
        print("Results--------")
        print("Flipkart Rating Out of 5: " + str(rating))
        print("Customer Reviews NLP Rating: "+str(to_5) )
        print("Average: " +str((to_5+rating)/2))
        if rating == 0:                     #Actual rating=0
            return to_5
        else:
            return (to_5+rating)/2