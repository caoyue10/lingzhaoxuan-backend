#!/usr/bin/python
#coding:utf-8

from pymongo import MongoClient
import hashlib, uuid
import bcrypt

import csv

from time import gmtime, strftime

import os, sys
from PIL import Image

from os import listdir
from os.path import isfile, join

import pdb


client = MongoClient('mongodb://localhost:27017/')

def get_hashed_password(plain_text_password):
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())
            
def check_password(plain_text_password, hashed_password):
    return bcrypt.checkpw(plain_text_password, hashed_password)


def current_time():
    return strftime("%Y-%m-%d %H:%M:%S", gmtime())


def check_user_password(user_name, passwd):
    user_table = client.database.user
    one_line = user_table.find_one({"user_name": user_name})
    
    return (check_password(passwd, one_line['password']))

def get_authority(user_name, passwd):
    user_table = client.database.user
    one_line = user_table.find_one({"user_name": user_name})
    
    passed = (check_password(passwd, one_line['password']))
    if passed:
        return one_line['authority']
    else:
        return "check failed"



def insert_one_user(user_name, passwd, added_user):
    # authority: super, modify, readonly
    authority = added_user['authority']
    assert(authority != "super" or authority != "modify" or authority != "readonly")
    
    user_table = client.database.user

    if get_authority(user_name, passwd) != 'super':
        return "authority check failed"
    if user_table.find({"user_name": added_user['user_name']}):
        return "user name already in use"
    
    # add salt in password
    hashed_password = get_hashed_password(added_user['passwd'])

    post = {"user_name": added_user['user_name'],
        "password": hashed_password,
        "authority": authority}
    
    
    post_id = user_table.insert_one(post).inserted_id
    return post_id


def delete_one_user(user_name, passwd, deleted_user_name):
    if get_authority(user_name, passwd) == "super":
        client.database.user.delete_one({"user_name":deleted_user_name})
    else:
        print "authority permission failed"

def delete_all_users(user_name, passwd):
    if get_authority(user_name, passwd) == "super":
        client.database.user.delete_many({})
    else:
        print "delete failed"



def add_csv_to_data(user_name, passwd, file_name):
    if get_authority(user_name, passwd) == "super":
        csv_file = open(file_name, 'rU')
        reader = csv.reader(csv_file)
        
        header = reader.next()
        #column_name_value = {'cur':header, 'old':[{'old':'', 'new':header, 'time': current_time(), 'user':user_name}]}
        #client.database.column_name.insert(column_name_value)
        
        for each_row in reader:
            row={}
            for i in xrange(len(header)):
                # cur: current value, old: list of {old:'', new:'', time:, user:}
                value = {'cur':each_row[i], 'old':[{'old':'', 'new':each_row[i], 'time': current_time(), 'user':user_name}]}
                row[header[i]]=value
                print value
            
            #print row
            #client.database.data.insert(row)
    else:
        print "authority permission failed"

def get_all_data(user_name, passwd):
    if get_authority(user_name, passwd) == "super":
        one_line = client.database.column_name.find_one({})
        header = one_line['cur']
        all_contents = []
        
        cursor = client.database.data.find({})
        for item in cursor:
            row = []
            for j in xrange(len(header)):
                row.append(item[header[j]]['cur'])
            
            all_contents.append(row)

        return {'header':header, 'content':all_contents}
    else:
        print "authority permission failed"
        return {}


def add_data_column(user_name, passwd, column_name):
    if get_authority(user_name, passwd) == "super":
        one_line = client.database.column_name.find_one({})
        all_column_name = one_line['cur']
        new_column_name = all_column_name + [column_name]

        old = one_line['old']
        old.append({'old':all_column_name, 'new':new_column_name, 'time': current_time(), 'user':user_name})
        
        column_name_value = {'cur':new_column_name, 'old':old}
        client.database.column_name.update({}, column_name_value)
    else:
        print "authority permission failed"

def del_data_column(user_name, passwd, column_name):
    if get_authority(user_name, passwd) == "super":
        one_line = client.database.column_name.find_one({})
        all_column_name = one_line['cur']
        new_column_name = [a for a in all_column_name if a != column_name]

        old = one_line['old']
        old.append({'old':all_column_name, 'new':new_column_name, 'time': current_time(), 'user':user_name})
        
        column_name_value = {'cur':new_column_name, 'old':old}
        client.database.column_name.update({}, column_name_value)
    else:
        print "authority permission failed"

def change_data_value(user_name, passwd, model_id, column_name, new_value):
    if get_authority(user_name, passwd) == "super":
        one_line = client.database.column_name.find_one({})
        all_column_name = one_line['cur']
        
        data_line = client.database.data.find_one({all_column_name[0]:model_id})
        old_value = data_line[column_name]['cur']
        new_line = {'cur':new_value, 'old':data_line[column_name]['old'].append({'old':old_value, 'new':new_value, 'time': current_time(), 'user':user_name})}
        
        client.database.data.update({all_column_name[0]:model_id}, {'$set':{column_name:new_line}}, {'upsert': False, 'multi': False})
    else:
        print "authority permission failed"


def add_folder_to_image_table(user_name, passwd, image_folder, prefix="/dist/images/"):
    if get_authority(user_name, passwd) == "super":
        client.database.images.delete_many({})

        # model level
        for model in listdir(image_folder):
            # category level
            model_dir = join(image_folder, model)
            if os.path.isfile(model_dir):
                continue
            
            row = {}
            row['model_id'] = model
            row['category'] = []
            for cat in listdir(model_dir):
                if 'DS_Store' in cat:
                    continue
                # image level
                cat_dir = join(model_dir, cat)
                if os.path.isfile(cat_dir):
                    continue

                row['category'].append(cat)

                images = []
                for img in listdir(cat_dir):
                    if 'DS_Store' in img:
                        continue
                    if 'thumbnail' not in img:
                        images.append(get_thumbnail_name(join(prefix, model, cat, img)))

                        if not os.path.isfile(get_thumbnail_name(join(cat_dir, img))):
                            make_thumbnail(join(cat_dir, img))
                        
                row[cat]=images
            
            print row
            client.database.images.insert(row)
                
    else:
        print "authority permission failed"


def get_images(user_name, passwd, model_id, cat_index):
    if get_authority(user_name, passwd) == "super":
        item = client.database.images.find_one({"model_id":model_id})
        header = item['category']
        row = item[header[int(cat_index)]]
        
        return {'header':header, 'content':row}
    else:
        print "authority permission failed"
        return {}

def add_image(user_name, passwd, model_id, category_name, image):
    pass

def del_image(user_name, passwd, model_id, category_name, image):
    pass


def get_thumbnail_name(infile):
    return os.path.splitext(infile)[0] + ".thumbnail.jpg"

def make_thumbnail(infile):
    base_width = 1024
    outfile = get_thumbnail_name(infile)
    if infile != outfile:
        try:
            im = Image.open(infile)
            wpercent = (base_width/float(im.size[0]))
            hsize = int((float(im.size[1])*float(wpercent)))
            im.thumbnail((base_width,hsize))
            im.save(outfile, "JPEG")
        except IOError:
            print "cannot create thumbnail for", infile

    


super_user_name = "admin"
super_passwd = "gugong"

# check passwd test
#print check_user_password(super_user_name, super_passwd)

# get authority test
#print get_authority(super_user_name, super_passwd)

# add csv test
#print add_csv_to_data(super_user_name, super_passwd, '灵沼轩数据库信息表1127.csv')

# add image folder
#add_folder_to_image_table(super_user_name, super_passwd, '../../dist/images')

# insert user test
#post_user = {"user_name": "caoyue",
        #"password": "caoyue",
        #"authority": "modify"}
#insert_one_user(super_user_name, super_passwd, post_user)

# thumbnail test
#make_thumbnail('./images/0/图纸/西立面.jpg')

#print get_all_data(super_user_name, super_passwd)
