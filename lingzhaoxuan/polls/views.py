# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

import json

from django.views.decorators.csrf import csrf_exempt

import pdb
import db_ops

@csrf_exempt
def init(request):
    if request.method == "POST":
        return_dict = db_ops.get_all_data(request.POST['username'], request.POST['password'])
        return_dict["Access-Control-Allow-Origin"] = "http://localhost:8000"
        
        response = HttpResponse(json.dumps(return_dict), content_type='application/json')
        response['Access-Control-Allow-Origin'] = '*'
        
        return response
    else:
        response = HttpResponse(json.dumps(None), content_type='application/json')
        response['Access-Control-Allow-Origin'] = '*'
        return response
