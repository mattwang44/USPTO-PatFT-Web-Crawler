# Web Crawling
from bs4 import BeautifulSoup, Comment
import html5lib, re, urllib, requests
# Data processing
import csv, string, datetime
from time import *
import numpy as np
# Path 
import sys, os
# PDF
from PyPDF2 import PdfFileMerger, PdfFileReader

Item = range(15)

# Delete repeat word in list
def unique_list(l):
    ulist = []
    [ulist.append(x) for x in l if x not in ulist]
    return ulist

# Title
def TTL(soup):
    for tl in soup.find_all('font', attrs={'size':'+1'}):
        return tl.string.replace("\n","")
    
# Abstract
def ABST(soup):
    for abs in soup.find_all("b"):
        if abs.next_element == "Abstract":
            AbsContent = abs.next_element.next_element.next_element.string.replace("\n","").replace("     "," ")
    return AbsContent

# Application date
def APD(soup):
    ad = ''
    for date in soup.find_all('th', attrs={'scope':'row', 'valign':'top', 'align':'left', 'width':'10%'}):
       if "Filed" in date.next_element:
            for ad in date.next_element.next_element.find('b'):
                return ad.string
    return ad

# Issue date
def ISD(soup):
    d_str = ''
    try:
        for date in soup.find_all('td', attrs={'align':'right', 'width':'50%'}):
            d_str = (str(date))[40:].replace("\n</b></td>","")
            if len(d_str) < 25:
                #print(datetime.strptime(date, '%B %d, %Y'))
                return d_str
        return d_str
    # old patents
    except:
        for date in soup.find_all('td', attrs={'valign':'top', 'align':'left', 'width':'40%'}):
            if "Issue Date" in str(date.next_element):
                d_str = str(date.next_element.next_element.next_element.next_element.next_element.next_element).replace('\n','')
                return d_str
        return d_str

# Family ID                
def FMID(soup):
    for ID in soup.find_all('th', attrs={'scope':'row', 'valign':'top', 'align':'left', 'width':'10%'}):
        if "Family ID" in ID.next_element:
            for fmid in ID.next_element.next_element.find('b'):
                return fmid.string.replace('\n',"")
# Appl. No.
def ApNo(soup):
    for Apno in soup.find_all('th', attrs={'scope':'row', 'valign':'top', 'align':'left', 'width':'10%'}):
        if "Appl. No." in Apno.next_element:
            for no in Apno.next_element.next_element.find('b'):
                return str(no)

# CPC subclass
def CPCs(soup):
    for td in soup.find_all('td', attrs={'valign':'top', 'align':'right', 'width':'70%'}):
        if "Current CPC Class" in td.previous_element.previous_element:
            str = td.next_element.encode("utf8").decode("cp950", "ignore")
            str = str.replace("; ",">").replace(" ","<")+">"
            cpcs = ', '.join(unique_list((re.sub('<[^>]+>', ' ', str).split())))
            return cpcs

# CPC
def CPC(soup):
    for td in soup.find_all('td', attrs={'valign':'top', 'align':'right', 'width':'70%'}):
        if "Current CPC Class" in td.previous_element.previous_element:
            str = td.next_element.encode("utf8").decode("cp950", "ignore")
            str = (str.replace("); ",">").replace("(","<")+">").replace(" ","")
            cpc = ', '.join(unique_list((re.sub('<[^>]+>', ' ', str).split())))
            return cpc

# IPC subclass
def IPCs(soup):
    for td in soup.find_all('td', attrs={'valign':'top', 'align':'right', 'width':'70%'}):
        if "Current International Class" in td.previous_element.previous_element:
            str = td.next_element.encode("utf8").decode("cp950", "ignore")
            str = str.replace("; ",">").replace(" ","<")+">"
            ipcs = ', '.join(unique_list((re.sub('<[^>]+>', ' ', str).split())))
            return ipcs

# IPC 
def IPC(soup):
    for td in soup.find_all('td', attrs={'valign':'top', 'align':'right', 'width':'70%'}):
        if "Current International Class" in td.previous_element.previous_element:
            str = td.next_element.encode("utf8").decode("cp950", "ignore")
            str = (str.replace("); ",">").replace("(","<")+">").replace(" ","")
            ipc = ', '.join(unique_list((re.sub('<[^>]+>', ' ', str).split())))
            return ipc
        
# Inventor 
def IN(soup):
    for invtr in soup.find_all('th', attrs={'scope':'row', 'valign':'top', 'align':'left', 'width':'10%'}):
        if invtr.next_element == "Inventors:":
            invt_str = invtr.next_element.next_element.next_element.encode("utf8").decode("cp950", "ignore")
            return invt_str.replace("<b>","").replace("</b>","").replace('<td align="left" width="90%">',"").replace("</td>","").replace("\n","")
# REF
def REF(PN):
    page = 'http://patft.uspto.gov/netacgi/nph-Parser?Sect2=PTO1&Sect2=HITOFF&p=1&u=/netahtml/PTO/search-bool.html&r=1&f=G&l=50&d=PALL&RefSrch=yes&Query=ref/'+str(PN)
    soup = url2soup(page)
    i = 0
    for aa in soup.find_all('strong'):
        if i == 1:
            return str(aa.next_element.next_element)
        else:
            i +=1
    return str(0)

# Applicant
def AANM(soup):
    aanms = ''
    for c in soup.find_all(string=lambda text:isinstance(text,Comment)):
        if 'AANM' in c:
            for aanm in c.split('\n'):
                if '~AANM' in aanm:
                    aanms = aanms + str(aanm[6:]) + ', '
    if len(aanms)>0:
        return aanms[:-2]
    else:
        return "Not listed"

# Assignee
def AN(soup):
    for an in soup.find_all('th', attrs={'scope':'row', 'valign':'top', 'align':'left', 'width':'10%'}):
        if an.next_element == "Assignee:":
            an_str = an.next_element.next_element.next_element.encode("utf8").decode("cp950", "ignore")
            return an_str.replace("<b>","").replace("</b>","").replace('<td align="left" width="90%">',"").replace("</td>","").replace("\n","").replace("<br/>","")
        else:
            continue
    return "Not listed"
    
def Soup2Info(Item, soup, PatFT_link, PDF_link,):
    result = []
    if 0 in Item:
        result.append(TTL(soup))
    if 1 in Item:
        result.append(ISD(soup))
    if 2 in Item:
        result.append(APD(soup))
    if 3 in Item:
        result.append(IN(soup))
    if 4 in Item:
        result.append(AANM(soup))
    if 5 in Item:
        result.append(AN(soup))
    if 6 in Item:
        result.append(CPC(soup))
    if 7 in Item:
        result.append(CPCs(soup))
    if 8 in Item:
        result.append(IPC(soup))
    if 9 in Item:
        result.append(IPCs(soup))
    if 10 in Item:
        result.append(FMID(soup))
    if 11 in Item:
        result.append(ABST(soup))
    if 12 in Item:
        result.append(' ')###
    if 13 in Item:
        result.append('=HYPERLINK("'+PatFT_link+'")')                                                                                                                                                                                                                                                                    
    if 14 in Item:
        result.append('=HYPERLINK("'+PDF_link+'")')
    return result
def PN_str_and_url(PN):
    # clean pn string
    if type(PN) is str:
        PN = PN.replace(',', '').replace('"', '').replace(' ', '')
    else:
        PN = str(PN)

    # URL of PatFT
    PatFT_link = "http://patft.uspto.gov/netacgi/nph-Parser?Sect2=PTO1&Sect2=HITOFF&p=1&u=/netahtml/PTO/search-bool.html&r=1&f=G&l=50&d=PALL&RefSrch=yes&Query=PN/"+PN

    # PN_PDF: PN in 8 digits format
    if len(PN)>=2:
        if PN[1].isalpha(): #RE/RX/PP/AI
            PN_PDF = PN[0:2]+'0'*(8-len(PN))+PN[2:]
        elif PN[0].isalpha(): #X/D/T/H
            PN_PDF = PN[0:1]+'0'*(8-len(PN))+PN[1:]
        else:
            PN_PDF = '0'*(8-len(PN))+PN
    else:
        PN_PDF = '0'*(8-len(PN))+PN

    # URL of PDF
    PDF_link_full = 'http://pimg-fpiw.uspto.gov/fdd/'+PN_PDF[6:8]+'/'+PN_PDF[3:6]+'/'+PN_PDF[0:3]+'/0.pdf'
    PDF_link_page = 'http://pdfpiw.uspto.gov/'+PN_PDF[6:8]+'/'+PN_PDF[3:6]+'/'+PN_PDF[0:3]+'/'

    return PN, PatFT_link, PN_PDF, PDF_link_full, PDF_link_page

# Filter -- Patent type (PNtype_limit: np.array([1,0,1,0]))
def PNtype_filter(PN, PNtype_limit):
    # Don't show Utility Patent: X- or start with digit
    if PNtype_limit[0] != 1: 
        if PN[0] in {'x', 'X'} or PN[0].isdigit():
            return False
    # Don't show Design Patent: D-
    if PNtype_limit[1] != 1: 
        if PN[0] in {'d', 'D'}:
            return False
    # Don't show Plant Patent: PP-
    if PNtype_limit[2] != 1: 
        if PN[0:2].lower() == 'pp':
            return False        
    # Don't show other patent: RE/RX/T/H/AI
    if PNtype_limit[3] != 1: 
        if PN[0:2].lower() in {'re','rx','ai'} or PN[0].lower() in {'t','h'}:
            return False
    # Not filtered
    return True 

def url2soup(search_page):             
    try:
        requested = urllib.request.urlopen(search_page)
        response = requested.read()
    except:
        result = requests.get(search_page)
        response = result.content
    soup = BeautifulSoup(response, "html5lib")
    return soup

def Date_filter(Date_str, Date_limit): #Date_limit: np.array([1976,1,1,2017,1,1])
    start_date = datetime.datetime(Date_limit[0],Date_limit[1],Date_limit[2])
    end_date = datetime.datetime(Date_limit[3],Date_limit[4],Date_limit[5])
    try:
        Date = datetime.datetime.strptime(Date_str, '%B %d, %Y')
    except: 
        return True #can't find App Date
    if Date > end_date or Date < start_date:
        return False
    else:
        return True

# fetch info (repeat if fail in case of bad network connection)
# return PDF status & result to save in csv
def info_fetcher(PN, Item, soup, PatFT_link, PDF_link):
    try:
        for _ in range(5):
            try:
                result = [PN] + Soup2Info(Item, soup, PatFT_link, PDF_link)
                return True, result
            except:# Distinguish error type
                # PatFT has no data but PDF is available
                if 'Full text is not available' in str(soup) and len(soup.find_all('font', attrs={'color': 'FF0000'}))>0:
                    return True, [PN, 'Full text is not available. Please see PDF file:', '=HYPERLINK("'+PDF_link+'")']
                # Not a proper PN format: find 0 patent or unparseable
                elif ('The Query' and 'was unparseable' in str(soup)) or 'No patents have matched your query' in str(soup):
                    return False, [PN, 'Not a proper patent number. Please check again.']
                else:
                    return False, [PN, 'Not a proper patent number. Please check again.']

    except:
        return False, [PN, 'Fail to info fetching. Please check inserted data and Internet connection or contact author.']



def PDF_download_single_link(PDF_link, filename):
    response = urllib.request.urlopen(PDF_link)
    file = open(filename, 'wb')
    file.write(response.read())
    file.close()


def PDF_download_multiple_links(PDF_links, filename):
    file = open(filename, 'wb')
    content = bytearray()
    amount = len(PDF_links)
    merger = PdfFileMerger()
    names = [filename[0:-4]+str(i)+'.pdf' for i in range(amount)]
    for i in range(amount):
        name = names[i]
        PDF_download_single_link(PDF_links[i], name)
        with open(name, "rb") as page:
            merger.append(PdfFileReader(page))
    merger.write(filename)

    for i in range(amount):
        os.remove(names[i])
        
def PDF_section_pageNo(section_link):
    requested = urllib.request.urlopen(section_link)
    source = requested.read()
    soup = BeautifulSoup(source, "html5lib")
    for c in soup.find_all('font', attrs={'color':'#000000'}):
        if 'pages' in c.next_element.next_element.string:
            no = int(c.next_element.next_element.string.index('o'))-1
            return int(c.next_element.next_element.string[0:no])

# PDF download
def PDF_download(PN, PatFT_link, PN_PDF, PDF_link_full, PDF_link_page, PDF_download_demand):
    try:
        if PDF_download_demand == 0: # Don't need to download PDF
            return True, 0 

        if PDF_download_demand == 1 : # Download complete file
            PDF_download_single_link(PDF_link_full, 'US'+PN.upper()+'.pdf')
            return True, 'Full text PDF is downloaded.'

        if PDF_download_demand in [2, 3]: # Download picture only
            if PDF_download_demand == 3:
                PDF_download_single_link(PDF_link_full, 'US'+PN.upper()+'.pdf')
            PDF_access = 'http://pdfpiw.uspto.gov/.piw?Docid='+ PN_PDF
            # "Drawings" section
            start_page = PDF_section_pageNo(PDF_access+'&SectionNum=2')
            # "Pecifications" section
            end_page = PDF_section_pageNo(PDF_access+'&SectionNum=3')
            PDF_links = [PDF_link_page+str(i)+'.pdf' for i in range(start_page, end_page)]
            PDF_download_multiple_links(PDF_links, 'US'+PN.upper()+'_pic.pdf')
            if PDF_download_demand == 3:
                return True, str(int(end_page)-int(start_page)) + ' page(s) drawing PDF & full text PDF are downloaded.'
            else:
                return True, str(int(end_page)-int(start_page)) + ' page(s) of drawing PDF is downloaded.'
    # failed to doanload PDF (unkown reason)
    except:
        return False, 'Failed to download PDF.'



     