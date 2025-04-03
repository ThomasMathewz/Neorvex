from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("Neorvex-Product Recommendation Engine")