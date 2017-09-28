# PyQt package
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem, QMainWindow, QWhatsThis, QLabel, QWidget,\
 QPushButton, QInputDialog, QLineEdit, QFileDialog, QVBoxLayout, QItemDelegate, QFormLayout
from PyQt5.QtCore import Qt, QDir, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from pyqtwindow import Ui_MainWindow as ui # export from Qt Creator
# Web Crawling packages
import  csv, urllib, requests
from bs4 import BeautifulSoup
# data processing
import numpy as np
import time, datetime
import shutil, os, gc 
import Patent_Crawler as ptc

def URL2Soup( search_page ):
    try:
        requested = urllib.request.urlopen(search_page)
        response = requested.read()
    except:
        result = requests.get(search_page) 
        response = result.content
    soup = BeautifulSoup(response, "html5lib")
    return soup

# Get total number of patent and the PNs (at most 50) on the 1st searching page
def getInfofromQuery_1st_page(query, db):
    #QApplication.processEvents()
    search_page = "http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&p=1&f=S&l=50&Query="+query+"&d=" + db
    soup_1st_page = URL2Soup( search_page )
    i = 0
    for aa in soup_1st_page.find_all('strong'):
        i = i + 1
        if i == 3:
            total_PTnumber = int(aa.next_element)
            return total_PTnumber, getPNfromSoup_one_page(soup_1st_page), ''
    # if no patent: only one 'strong' tag can be found
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

class MainWindow(QMainWindow, ui):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        # Additional Initialization
        Initial_path = QDir.currentPath()
        self.PNloc.setText(Initial_path+'/PN.CSV')
        self.Querybox.setVisible(False)
        self.DB.setVisible(False)
        self.PDFloc.setText(Initial_path+'/PDF_Download')
        self.APT.setDate(QtCore.QDate(int(time.strftime("%Y")), int(time.strftime("%m")), int(time.strftime("%d"))))
        self.IDT.setDate(QtCore.QDate(int(time.strftime("%Y")), int(time.strftime("%m")), int(time.strftime("%d"))))
        self.TTL.setChecked(True)
        self.ISD.setChecked(True)
        self.CPC.setChecked(True)
        self.ABST.setChecked(True)
        self.AN.setChecked(True) 
        self.PDF.setChecked(True)
        self.PNbt.setChecked(True) 
        self.ut.setChecked(True)
        self.MODEL = QtGui.QStandardItemModel()   
        self.MODEL.setColumnCount(17) 
        self.MODEL.setHorizontalHeaderLabels(['']*17)
        self.TABLE.setModel(self.MODEL)
        self.TABLE.setShowGrid(True)
        self.TABLE.setAlternatingRowColors(True)
        #setColumnWidth(0, 85)
        #self.TABLE.resizeColumnsToContents()
        #.setRowHeight(row, 18)
        self.webView = QWebEngineView(self.GL)
        self.webView.setGeometry(QtCore.QRect(0, 0, 1011, 491))
        self.webView.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        self.webView.load(QUrl("http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=1&p=1&f=G&l=50&d=PTXT&S1=9532164.PN.&OS=pn/9532164&RS=PN/9532164"))
        self.webView.show()
        
        
        # Events
        self.statusBar.showMessage('Welcome!')
        self.PNbws.clicked.connect(self.FileDialog2Line_PNCSV)
        self.PDFbws.clicked.connect(self.FileDialog2Line_PDF)
        self.DB.currentIndexChanged.connect(self.DB2filter)

        # Execution
        self.IMPORT.clicked.connect(self.importPN)
        self.EXPORT.clicked.connect(self.handleSave)
        self.FILTER.clicked.connect(self.TABLE_FILTER)
        self.PDFD.clicked.connect(self.PDFDOWNLOAD)
        self.INFO.clicked.connect(self.Crawler)
        self.STOPLOOP.clicked.connect(self.stopbool)
        self.web_PDF.clicked.connect(self.showPDF)
        self.web_PAT.clicked.connect(self.showPAT)        
        self.stop = False

    def showPAT(self):
        PN = self.PNweb.text()
        _, PatFT_link, _, _, _ = ptc.PN_str_and_url(PN)
        self.webView.load(QUrl(PatFT_link))
        self.webView.show()

    def showPDF(self):
        PN = self.PNweb.text()
        _, _, _, PDF_link_full, _ = ptc.PN_str_and_url(PN)
        print(PDF_link_full)
        #self.webView.load(QUrl(PDF_link_full))
        #self.webView.show()
        QDesktopServices.openUrl(QUrl(PDF_link_full))

    def stopbool(self):
        self.stop = True

    def PDFDOWNLOAD(self):
        # demand: 0=do not download, 1=download full text, 2=download drawing section, 3=download both
        if self.cs2b(self.PDFfull)==0 and self.cs2b(self.PDFdraw)==0:
            self.statusBar.showMessage('Please select something to download!')
            return
        elif self.cs2b(self.PDFfull)==1 and self.cs2b(self.PDFdraw)==0:
            pdf_demand = 1
        elif self.cs2b(self.PDFfull)==0 and self.cs2b(self.PDFdraw)==1:
            pdf_demand = 2
        elif self.cs2b(self.PDFfull)==1 and self.cs2b(self.PDFdraw)==1:
            pdf_demand = 3

        # return if PN hasn't been imported
        if self.MODEL.headerData(0,Qt.Horizontal) != 'Patent No.':
            self.statusBar.showMessage('Please import Patent Numers first!')
            return

        error_download = 0
        cwd = os.getcwd()
        PDF_loc = self.PDFloc.text()
        if not os.path.exists(PDF_loc):
            os.makedirs(PDF_loc)
        os.chdir(PDF_loc)  

        row = self.MODEL.rowCount()
        for i in range(row):
            if self.stop:
                break
            QApplication.processEvents()
            PN = str(self.MODEL.data(self.MODEL.index(i,0)))
            PN, PatFT_link, PN_PDF, PDF_link_full, PDF_link_page = ptc.PN_str_and_url(PN)
            status, mes = ptc.PDF_download(PN, PatFT_link, PN_PDF, PDF_link_full, PDF_link_page, pdf_demand)
            self.statusBar.showMessage('US' + PN + ' ( ' +  str(i+1) + ' / ' + str(row)+ ' ): ' + mes  )
            if not status:
                error_download += 1
        if self.stop:
            self.stop = False
            self.statusBar.showMessage('The program is stop on your demand.')
        elif error_download == 0:
            self.statusBar.showMessage('PDF downloaded sucessfully!')
        else:
            self.statusBar.showMessage('PDF downloaded, but ' + str(error_download) + 'errors exist')
        os.chdir(cwd)  

    def Crawler(self):
        # return if PN hasn't been imported
        if self.MODEL.headerData(0,Qt.Horizontal) != 'Patent No.':
            self.statusBar.showMessage('Please import Patent Numers first!')
            return        

        self.statusBar.showMessage('Fetching info for you...')
        row = self.MODEL.rowCount()
        Item_b = [self.cs2b(self.TTL),   self.cs2b(self.ISD),  self.cs2b(self.APD),  self.cs2b(self.IN),   self.cs2b(self.AANM),\
                  self.cs2b(self.AN),    self.cs2b(self.CPC),  self.cs2b(self.CPCs), self.cs2b(self.IPC),  self.cs2b(self.IPCs),\
                  self.cs2b(self.REFby), self.cs2b(self.ABST), self.cs2b(self.FMID), self.cs2b(self.ApNo), self.cs2b(self.PAT), self.cs2b(self.PDF)]
        Item = []
        for i in range(16):
            if Item_b[i] == 1:
                Item.append(i)
        del Item_b
        Head = ["Title","Issue Date", "Application Date", "Inventors", "Applicant", "Assignee", "CPC", "CPC-subclass",\
            "IPC", "IPC-subclass","Referenced by","Abstract", "Family ID",  "Appl. No.", "PatFT Link", "PDF Link"]
        Head = ["Patent No."] + [Head[i] for i in Item]
        Head = Head + (17 - len(Head))*[' ']
        self.MODEL.setHorizontalHeaderLabels(Head)
        
        for i in range(row):
            if self.stop:
                break
            QApplication.processEvents()
            PN = str(self.MODEL.data(self.MODEL.index(i,0)))
            if PN == 'Filtered':
                continue
            PN, PatFT_link, PN_PDF, PDF_link_full, PDF_link_page = ptc.PN_str_and_url(PN)
            soup = URL2Soup(PatFT_link)
            j = 1

            #Title
            if 0 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.TTL(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # Issue Date
            if 1 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.ISD(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # Application Date
            if 2 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.APD(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # Inventor
            if 3 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.IN(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            #Applicant
            if 4 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.AANM(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # Assignee
            if 5 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.AN(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()    
            # CPC  
            if 6 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.CPC(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # CPC subclass
            if 7 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.CPCs(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # IPC
            if 8 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.IPC(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # IPC subclass
            if 9 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.IPCs(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # Number of referenced by
            if 10 in Item:
                if 2>1:#try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.REF(PN)))
                if 1>2:#except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # Abstract
            if 11 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.ABST(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents() 
            # Family ID
            if 12 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.FMID(soup)))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # Application Number
            if 13 in Item:
                if 2>1:#try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem(ptc.ApNo(soup)))
                if 1>2 :#except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()
            # PatFT link
            if 14 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('=HYPERLINK("'+PatFT_link+'")'))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error'))
                j += 1
                QApplication.processEvents()                
            # PDF link
            if 15 in Item:
                try:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('=HYPERLINK("'+PDF_link_full+'")'))
                except:
                    self.MODEL.setItem(i,j,QtGui.QStandardItem('error')  )              
                j += 1
                QApplication.processEvents()

        if self.stop:
            self.stop = False
            self.statusBar.showMessage('The program is stopped on your demand.')
        else: 
            self.statusBar.showMessage('Done.')
    
    # Filter PNs and delete them
    def TABLE_FILTER(self):
        PNtype_limit = np.array([self.cs2b(self.ut), self.cs2b(self.ds), self.cs2b(self.pp), self.cs2b(self.ot)]) 
        if self.MODEL.headerData(0,Qt.Horizontal) != 'Patent No.':
            self.statusBar.showMessage('Please import Patent Numers first!')
            return
        if self.cs2b(self.APDdis) == 0 and self.cs2b(self.ISDdis) == 0 and (self.cs2b(self.all) == 1 or sum(PNtype_limit) == 4):
            self.statusBar.showMessage('Nothing will be filtered.')
            return
        row = self.MODEL.rowCount()
        
        #Time range
        Afy, Afm, Afd = self.APF.date().year(), self.APF.date().month(), self.APF.date().day()
        Aty, Atm, Atd = self.APT.date().year(), self.APT.date().month(), self.APT.date().day()
        Ify, Ifm, Ifd = self.IDF.date().year(), self.IDF.date().month(), self.IDF.date().day()
        Ity, Itm, Itd = self.IDT.date().year(), self.IDT.date().month(), self.IDT.date().day()
        APD_limit = np.array([Afy, Afm, Afd, Aty, Atm, Atd])
        ISD_limit = np.array([Ify, Ifm, Ifd, Ity, Itm, Itd])

        delete_list = []
        for i in range(row):
            if self.stop:
                break
            self.statusBar.showMessage('Filtering: ' + str(len(delete_list)) + ' patents are filtered. ( ' + str(i+1) + ' / '+str(row)+ ' )' )
            PN = str(self.MODEL.data(self.MODEL.index(i,0)))
            PN, PatFT_link, _, _, _ = ptc.PN_str_and_url(PN)
            APD_str, ISD_str = '', ''
            # derive soup only if necessary (since it's time consuming)
            if self.cs2b(self.APDdis) != 0 or self.cs2b(self.ISDdis) != 0:
                soup = URL2Soup(PatFT_link)
                QApplication.processEvents()
                APD_str = ptc.APD(soup)
                ISD_str = ptc.ISD(soup)
            now = datetime.datetime.now()
            # Do not filter patent type if 'all' is checked
            if self.cs2b(self.all) != 1:
                if not ptc.PNtype_filter(PN, PNtype_limit):
                    delete_list += [i]
                    self.MODEL.setItem(i,0,QtGui.QStandardItem('Filtered') )
                    continue
            # Do not filter appl. date if (1) user do not want to, (2) appl. date isn't listed, (3) (start time <1790/1/1) AND (end time> now)
            if self.cs2b(self.APDdis)==1 and len(APD_str) > 1 and not (datetime.datetime(Afy, Afm, Afd)<=datetime.datetime(1790,1,1) and datetime.datetime(Aty, Atm, Atd)>=now):
                if not ptc.Date_filter(APD_str, APD_limit):
                    delete_list += [i]
                    self.MODEL.setItem(i,0,QtGui.QStandardItem('Filtered') )
                    continue
            # Do not filter issue date if (1) user do not want to, (2) issue date isn't listed, (3) (start time <1790/1/1) AND (end time> now)                
            if len(ISD_str) > 1 and self.cs2b(self.ISDdis)==1 and not (datetime.datetime(Ify, Ifm, Ifd)<=datetime.datetime(1790,1,1) and datetime.datetime(Ity, Itm, Itd)>=now):
                if not ptc.Date_filter(ISD_str, ISD_limit):
                    delete_list += [i]
                    self.MODEL.setItem(i,0,QtGui.QStandardItem('Filtered') )
                    continue
            QApplication.processEvents()
        if self.stop:
            self.stop = False
            self.statusBar.showMessage('The program is stopped on your demand.')
        # delete unwanted PN
        elif len(delete_list)>0:
            delete_list_arr = np.array(delete_list)
            for row_index in delete_list:
                self.MODEL.removeRow(row_index-len(delete_list_arr[delete_list_arr<row_index]))    
                self.statusBar.showMessage('Deleting the filtered data.....' ) 
        self.statusBar.showMessage('Done Filtering: ' + str(len(delete_list)) + ' out of '  + str(row) + ' patents are filtered.' )   

    # import PN with a existing CSV file
    def import_PNlist_CSV(self, list_loc):
        with open(list_loc) as csvr:
            reader = csv.reader(csvr)
            count = 0
            for row in reader:
                count += 1
                self.statusBar.showMessage('There are %d patent numbers in the list.' % count)
                QApplication.processEvents()
            csvr.seek(0)
            self.MODEL.clear()            
            self.MODEL.setHorizontalHeaderLabels(['Patent No.'] + ['']*16)
            i = 0
            error_count = 0
            for row in reader:  
                if self.stop:
                    break
                PN = str(row[0]).replace(' ','').replace(',','')
                self.MODEL.setItem(i,0,QtGui.QStandardItem(PN) )
                """
                if requests.get("http://patft.uspto.gov/netacgi/nph-Parser?Sect2=PTO1&Sect2=HITOFF&p=1&u=/netahtml/PTO/search-bool.html&r=1&f=G&l=50&d=PALL&RefSrch=yes&Query=PN/"+row[0]).status_code!=200:
                    self.MODEL.setItem(i,1, QtGui.QStandardItem('NO') )
                else:
                    self.MODEL.setItem(i,1, QtGui.QStandardItem('YES') )
                """
                try:
                    int(PN)
                except:
                    try:
                        int(PN[1:])
                        if (PN[0].lower not in ['h','t','d','x']) and (requests.get("http://patft.uspto.gov/netacgi/nph-Parser?Sect2=PTO1&Sect2=HITOFF&p=1&u=/netahtml/PTO/search-bool.html&r=1&f=G&l=50&d=PALL&RefSrch=yes&Query=PN/1"+PN).status_code!=200):
                            self.MODEL.setItem(i,1,QtGui.QStandardItem('Not a proper patent number! Please check again.') )
                            error_count += 1
                    except:
                        try:
                            int(PN[2:])
                            if (PN[0:2].lower not in ['re','rx','pp','ai']) and (requests.get("http://patft.uspto.gov/netacgi/nph-Parser?Sect2=PTO1&Sect2=HITOFF&p=1&u=/netahtml/PTO/search-bool.html&r=1&f=G&l=50&d=PALL&RefSrch=yes&Query=PN/1"+PN).status_code!=200):
                                self.MODEL.setItem(i,1,QtGui.QStandardItem('Not a proper patent number! Please check again.') )
                                error_count += 1
                        except: 
                            self.MODEL.setItem(i,1,QtGui.QStandardItem('Not a proper patent number! Please check again.') )
                            error_count += 1
                QApplication.processEvents()
                i += 1
            if self.stop:
                self.stop = False
                self.statusBar.showMessage('The program is stopped on your demand.')
            elif error_count == 0:
                self.statusBar.showMessage('Patent list is ready! There are %d patents.' % count)
            else:
                self.statusBar.showMessage('Patent list is ready but '+ str(error_count) + 'out of %d patent numbers are not in proper formats.' % count)
                self.MODEL.setHorizontalHeaderLabels(['Patent No.', 'Errors'])

    def importPN(self):
        if self.PNbt.isChecked():
            self.MODEL.clear()  
            list_loc = self.PNloc.text()
            if not os.path.exists(list_loc):
                self.statusBar.showMessage("The path of input PN list doesn't exist. Please check again.")
            elif list_loc[-3:].lower() != 'csv':
                self.statusBar.showMessage('This not a CSV file! Please check again.')
            else:
                self.import_PNlist_CSV(list_loc)
        elif self.Querybt.isChecked():
            self.MODEL.clear()  
            self.statusBar.showMessage('Preparing patent list...')
            if self.DB.currentIndex() == 0:
                db = 'PTXT'
            else:
                db = 'PALL'
            query = self.Querybox.toPlainText()
            total_PTnumber, PN_1st_page, message = getInfofromQuery_1st_page(query, db)
            self.statusBar.showMessage('There are %d patents can be searched with this query.' % total_PTnumber)
            if total_PTnumber == 0:
                self.statusBar.showMessage(message)
            elif total_PTnumber <= 50:      
                self.MODEL.setHorizontalHeaderLabels(['Patent No.'])          
                for i in range(total_PTnumber):
                    self.MODEL.setItem(i,0,QtGui.QStandardItem(PN_1st_page[i]) )
                    QApplication.processEvents()
                self.statusBar.showMessage('Patent list is ready! There are %d patents.' % total_PTnumber)
            else:
                pages = int(total_PTnumber/50)+1 if total_PTnumber % 50 != 0 else int(total_PTnumber/50)
                search_pages = [('http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&p='+str(i+1)+'&f=S&l=50&Query='+query+'&d='+db) for i in range(pages)]
                self.MODEL.setHorizontalHeaderLabels(['Patent No.'])
                i=0
                for link in search_pages:
                    if self.stop:
                        break
                    soup = URL2Soup(link)
                    PN_list = getPNfromSoup_one_page(soup)
                    j=1
                    for PN in PN_list:
                        index = i*50 + j
                        self.MODEL.setItem(index-1,0,QtGui.QStandardItem(PN) )
                        self.statusBar.showMessage(('There are '+str(total_PTnumber)+' patents can be searched with this query. Acquiring patent numbers: '+str(index)+' / '+str(total_PTnumber))  )
                        QApplication.processEvents()
                        j += 1
                    i += 1
                if self.stop:
                    self.stop = False
                    self.statusBar.showMessage('The program is stopped on your demand.')
                else:
                    self.statusBar.showMessage('Patent list is ready! There are %d patents.' % total_PTnumber)
        
    def handleSave(self):
        path = self.FileDialog2Line_OutCSV()
        try:
            os.path.exists(path)
        except:
            return
        if os.path.exists(path):
            with open(path+'\\Result.CSV', 'w', newline='') as stream:
                writer = csv.writer(stream)
                header = []
                for i in range(17):
                    header.append(self.MODEL.headerData(i,Qt.Horizontal))
                writer.writerow(header)
                for row in range(self.MODEL.rowCount()):
                    if self.stop:
                        break
                    rowdata = []
                    for column in range(self.MODEL.columnCount()):
                        item = self.MODEL.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)
                if self.stop:
                    self.stop = False
                    self.statusBar.showMessage('The program is stopped by demand.')
                else:
                    self.statusBar.showMessage('Result.CSV is saved.')

    def FileDialog2Line_PNCSV(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Select a CSV file containing Patent Numbers", "","CSV Files (*.csv);;All Files (*)", options=options)
        del options
        if fileName:
            self.PNloc.setText(fileName)
        del fileName

    def FileDialog2Line_OutCSV(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName = QFileDialog.getExistingDirectory(self,"Saving Result.CSV at:", options=options)
        del options
        if fileName:
            return fileName

    def FileDialog2Line_PDF(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName = QFileDialog.getExistingDirectory(self,"Saving PDF files at:", "",  options=options)
        del options
        if fileName:
            self.PDFloc.setText(fileName)
        del fileName

    def DB2filter(self):
        if self.DB.currentIndex() == 0:
            self.APF.setDate(QtCore.QDate(1976, 1, 1))
            self.IDF.setDate(QtCore.QDate(1976, 1, 1))
        else:
            self.APF.setDate(QtCore.QDate(1790, 1, 1))
            self.IDF.setDate(QtCore.QDate(1790, 1, 1))

    def cs2b(self, box):
        if box.checkState() == 2:
            return 1
        else:
            return 0


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5 import QtCore, QtGui, QtSvg 

    app = QApplication(sys.argv)
    wd = MainWindow()

    wd.show()
    sys.exit(app.exec_())