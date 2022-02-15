#import libraries
import os
from notion_client import Client
from notion_client import APIErrorCode, APIResponseError
import notion_client
from pocket import Pocket
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.request
import shutil
import schedule
import time

#notion credentials for 2 databases
token = ""
NOTION_TOKEN = os.getenv(token, "")
#a database for a personal wishlist
id1 = ''
url = ""
#a database for gift ideas
id2 = ''
url2 = ''

#pocket credentials
pkt_consumer = ''
pkt_access = ''



## add to gift ideas
def add_to_gifts(token, url, id, pkt_consumer, pkt_access):
    client = Client(auth=NOTION_TOKEN)
    #create pocket instance
    p = Pocket(consumer_key=pkt_consumer, access_token=pkt_access)
    #retrieve all new things saved to pocket tagged 'gifts'
    gifts = p.retrieve(state="unread", tag="gifts")
    gifts = gifts['list']
    gifts_keys = list(gifts.keys())
    item_ids = []
    #loop through each new gift idea
    for key in gifts_keys:
        item = gifts[key]
        new_page = {
            #structure database entry for each gift idea
            "name": {"title": [{"text": {"content": item['resolved_title']}}]},
            "url": {"type": "url", "url": item['resolved_url']},
            "details": {"type": "text", "text": {"content": item['excerpt']}}
        }

        #image scraping
        link = item['resolved_url']
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")

        #collect all images
        aas = soup.find_all("img")
        #create empty list for image details
        image_info = []

        #loop through images
        for a in aas:
            ind = a.get('alt')
            #go through all the ways images might be indexed and select image
            #accordingly
            if ind:
                main = aas.index(a)
                if "image 0" in ind:
                    imagezero = a.get('data-src-zoom-image')
                    if imagezero:
                        image_info.append((imagezero))
                        break
                    else:
                        image_info.append((a.get('src')))
                else:
                    image_info.append((a.get('src')))
            else:
                image_info.append((a.get('src')))

        #save image to gift idea
        if not image_info:
            new_page['image'] = {"type": "file", "file": link}
        elif len(image_info) == 0:
            new_page['image'] = {"type": "file", "file": link}
        elif not image_info[0]:
            new_page['image'] = {"type": "file", "file": link}
        #etsy does its image placement a little strangely so special case
        elif "etsy" in image_info[0]:
            new_page['image'] = {"type": "file", "file": image_info[main]}
        elif len(image_info) > 1:
            new_page['image'] = {"type": "file", "file": image_info[1]}
        else:
            new_page['image'] = {"type": "file", "file": image_info[0]}
        item_ids.append(item['item_id'])

    #create database item for gift idea
    client.pages.create(parent={"database_id": id}, properties=new_page)

    #archive each newly added item so that we don't end up with a ton of repeats
    for id in item_ids:
        p.archive(int(id)).commit()



## add to wishlist
def add_to_wishlist(token, url, id, pkt_consumer, pkt_access):
    client = Client(auth=NOTION_TOKEN)
    cv = client.get_collection_view(url)
    p = Pocket(consumer_key=pkt_consumer, access_token=pkt_access)
    #select all newly added wishlist items by tag
    new_wishlist = p.retrieve(state="unread",tag="shopping")

    new_wishlist = new_wishlist['list']
    #get a list of new item keys
    new_wishlist_keys = list(new_wishlist.keys())

    item_ids = []
    #loop through new wishlist ideas
    for key in new_wishlist_keys:
        item = new_wishlist[key]

        row = cv.collection.add_row()
        row.name = item['resolved_title']
        row.url = item['resolved_url']
        row.details = item['excerpt']

        #image scraping
        #get image urls
        link = item['resolved_url']
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")

        aas = soup.find_all("img")
        image_info = []

        #loop through all images scraped from page
        for a in aas:
            ind = a.get('alt')
            if ind:
                main = aas.index(a)
                if "image 0" in ind:
                    imagezero = a.get('data-src-zoom-image')
                    if imagezero:
                        image_info.append((imagezero))
                        break
                    else:
                        image_info.append((a.get('src')))
                else:
                    image_info.append((a.get('src')))
            else:
                image_info.append((a.get('src')))

        if len(image_info) == 0:
            row.image = link
        elif "etsy" in image_info[0]:
            row.image = image_info[main]
        elif len(image_info) > 1:
            row.image = image_info[1]
        else:
            row.image = image_info[0]
        item_ids.append(item['item_id'])
    #archive all newly added items so we don't repeatedly add the same items
    for id in item_ids:
        print(id)
        p.archive(int(id)).commit()

#run both functions
add_to_gifts(token=token, url=url2, id=id2, pkt_consumer=pkt_consumer, pkt_access=pkt_access)
add_to_wishlist(token=token, url=url, id=id1, pkt_consumer=pkt_consumer, pkt_access=pkt_access)
