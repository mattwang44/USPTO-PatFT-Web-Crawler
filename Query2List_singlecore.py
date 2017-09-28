from bs4 import BeautifulSoup
import html5lib
import re, copy
import csv
import urllib
import requests
from collections import Counter
import sys
import string
from time import *
import numpy as np
import multiprocessing as mp
from PyQt5.QtWidgets import QApplication

def URL2Soup( search_page ):
    requested = urllib.request.urlopen(search_page)
    soup = BeautifulSoup(requested.read(), "html5lib")
    return soup

def getInfofromQuery_1st_page(query, db):
    #PTXT PALL
    search_page = "http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&p=1&f=S&l=50&Query="+query+"&d=" + db
    soup_1st_page = URL2Soup( search_page )
    i = 0
    for aa in soup_1st_page.find_all('strong'):
        i = i + 1
        if i == 3:
            total_PTnumber = int(aa.next_element)
            return total_PTnumber, soup_1st_page, []
    # no patent: find only one 'strong' tag
    if i != 3:
        for aa in soup_1st_page.find_all('span'):
            if 'patents' in aa.next_element.next_element:
                return 0, [], 'Error: No patent can be found with the query!'
            else:
                return 0, [], 'Error: Wrong syntax of query! Please check again.'
        
def getPNfromSoup_one_page(soup):
    j = 0
    PN_list = []
    for aa in soup.find_all('td', attrs={'valign':'top'}):
        j = j + 1
        if j%3 == 2:
            PN_list.append(aa.next_element.next_element.replace(',', ''))
    return PN_list


    # patents exist and more than 50 (one core)
def getPNfromQuery_multi_pages(total_PTnumber, soup_1st_page, query, db):
    PN_list = getPNfromSoup_one_page(soup_1st_page)
    del soup_1st_page
    pages = int(total_PTnumber/50)+1

    search_pages = [('http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&p='+str(i+1)+'&f=S&l=50&Query='+query+'&d='+db) for i in range(1,pages)]
    for link in search_pages:
        list_one_page = getPNfromSoup_one_page(URL2Soup(link))
        PN_list =  PN_list + list_one_page
        del list_one_page
    return PN_list

def getPNfromQuery(Query, db):
    total_PTnumber, soup_1st_page, mes = getInfofromQuery_1st_page(query, db)
    if total_PTnumber == 0:
        return False, mes
    elif total_PTnumber <= 50:
        PN_list = getPNfromSoup_one_page(soup_1st_page)
        return True, PN_list
    else:
        PN_list = getPNfromQuery_multi_pages(total_PTnumber, soup_1st_page, query, db)
        return True, PN_list


def getPNfromQuery_repeat(Query, db):
    try:
        return getPNfromQuery(Query, db)
    except:
        return getPNfromQuery_repeat(Query, db)

        
if __name__ == '__main__':
    """
    query = '(((((CPC/A62B$ OR CPC/B65H$) OR CPC/F16D$) AND (brake AND lock)) AND ("safety line" OR cable)) AND slot)'.replace(' ', '%20')
    query = 'fire'
    search_page = "http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&p=1&f=S&l=50&Query="+query+"&d=PTXT"
    print(getPNfromQuery_SinglePage(search_page))
    """
    #print(getPNfromQuery('(((((CPC/A62B$ OR CPC/B65H$) OR CPC/F16D$) OR CPC/B66D$) AND ((brak$ OR lock$) OR (retract$ OR rewind$))) AND (((lifeline OR lanyard) OR "safety line") OR cable))', 'PTXT'))
    import multiprocessing as mp
    query = sys.argv[1]
    DB = sys.argv[2]
    fcsv = sys.argv[3]
    if DB == '0':
        db = 'PTXT'
    elif DB == '1':
        db = 'PALL'
    query = str(query).replace(' ', '%20')
    status, result = getPNfromQuery_repeat(query,db)
    if status:  #result is a list of PN
        with open(fcsv,'w', newline='') as f:
            writer = csv.writer(f)
            for pt in result:
                writer.writerow([pt])
        print('successful')
    else: # result is error message
        print(result)
    
    

#print(getPNfromQuery('FMID/37034349', 'PALL'))

