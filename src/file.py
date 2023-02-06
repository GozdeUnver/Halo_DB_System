# file is full(1) or not full (0) 
# number of pages in the file (represented in 4 bytes)
# 1000 bytes for the status of the pages. 0 if empty, 1 if partially full, 2 if completely full
import math
from record import Record 
from page import Page 
PAGE_SIZE = 3650 + 64
class File:
    @staticmethod
    def create_file():
        
        rawstring='00000'+'0'*1000
        return rawstring

    @staticmethod
    def read_file(filename,page_num):
        """ Reads a page of a file according to the given filename and page number. Returns records in the page.
        """
        f=open(filename,"r")
        f.seek(1005+page_num*PAGE_SIZE,0)
        page=f.read(PAGE_SIZE)
        records,_,_,_=Page.read_page(page)
        f.close()
        return records

    @staticmethod
    def helper(page,record,available_page,filename,header):
        index=1005
        l=[]
        l[:]=header["statusOfPages"]
        if l[999]!='0':
            f=open(filename,"r+")
            read,_,_,_=Page.read_page(page)
            lastElement=read.pop()
            read.append(record)
            f.seek(index+available_page*PAGE_SIZE,0)
            f.write(Page.create_page(read,available_page))

            for i in range(available_page+1,1000):

                f.seek(index+i*PAGE_SIZE,0)
                page=f.read(PAGE_SIZE)

                read,_,_,_=Page.read_page(page)
                if page[3]=='1':
                    tmp=read.pop()
                    read.append(lastElement)
                    lastElement=tmp
                    f.seek(index+i*PAGE_SIZE,0)
                    f.write(Page.create_page(read,i))
                    continue
                else:
                    read.append(lastElement)
                    f.seek(index+i*PAGE_SIZE,0)
                    page=Page.create_page(read,i)
                    f.write(page)
                    if l[i]=='1':
                        l[i]='2'
                    elif l[i]=='0':
                        l[i]='1'
                    # Page status from the file header is calculated
                    newPageStatus=''.join(l)
                    
                    # Number of non empty pages is stored
                    num=l.count('1')+l.count('2')
                    if newPageStatus=='2'*1000:
                        filestatus='1'
                    else:
                        filestatus=header["fileStatus"]
                    f.seek(0,0)
                    # file is remodified
                    f.write(filestatus+f'{num:04d}'+newPageStatus)
                    f.close()
                    return True
            f.close()
            return lastElement
        else:
            records,_,_,_=Page.read_page(page)
            lastElement=records.pop()
            records.append(record)
            curr=Page.create_page(records,available_page+1)

            l[available_page]='2'

            f=open(filename,"r+")
            f.seek(index+available_page*PAGE_SIZE,0)
            f.write(curr)

            # Latter pages are collected with shifted page numbers
            for j in range(available_page+1,header["numOfPages"]+1):
                
                try:
                    f.seek(index+j*PAGE_SIZE,0)
                    curr=f.read(PAGE_SIZE)
                    data,_,_,_=Page.read_page(curr)
                    if curr[3]=='1':
                        tmp=data.pop()
                        data.append(lastElement)
                        lastElement=tmp
                        curr=Page.create_page(data,j)
                        f.seek(index+j*PAGE_SIZE,0)
                        f.write(curr)
                        l[j]='2'
                    else:
                        data.append(lastElement)
                        curr=Page.create_page(data,j)
                        f.seek(index+j*PAGE_SIZE,0)
                        f.write(curr)
                        if len(data)==10:
                            l[j]='2'
                        else:
                            l[j]='1'
                        break
                except:
                    l[j]='1'
                    curr=Page.create_page([lastElement,],j)
                    f.seek(0,2)
                    f.write(curr)
                    break

            
            # Page status from the file header is calculated
            newPageStatus=''.join(l)
            
            # Number of non empty pages is stored
            num=l.count('1')+l.count('2')
            if newPageStatus=='2'*1000:
                filestatus='1'
            else:
                filestatus=header["fileStatus"]
            f.seek(0,0)
            # file is remodified
            f.write(filestatus+f'{num:04d}'+newPageStatus)
            f.close()
        return True
    
    @staticmethod
    def check(page,key):
        """ Checks if the key of the record is already in the given page of the file. Return True if it doesn't
        exist, return False if it exists already.
        """
        records,_,_,_=Page.read_page(page)
        for el in records:
            if el[1]==key:
                return False
        return True

    @staticmethod
    def add_record(filename,record):
        """ Adds record to the file if the key of the new record is in the range of the pages in the file.
        """
        header=File.return_file_header(filename)
        pageStatus=header["statusOfPages"]
        index=1005
        f=open(filename,"r+")
        returned_record=''

        # Each page of the file is checked if it is available for the new record
        for available_page in range(0,1005):

            # If the page is full and the new record belongs to that page, the last record of this page will be shifted to the next page
            if pageStatus[available_page]=='2':

                # Current page is read
                f.seek(index+available_page*PAGE_SIZE,0)
                page=f.read(PAGE_SIZE)

                # If the record is not already in the page, it checks if it is the right page to insert the new record
                if File.check(page,record[1]):
                    
                    pageHeader=page[:64]
                    # Smallest key value in the page is read to compare with the new record
                    small=pageHeader[int(page[16:18]):int(page[18:20])]
                    # If the keys can be converted to integer, the comparison with the new record and the biggest key is done here
                    try:
                        # If the new record has a bigger key than the smallest key in the page, then it is inserted
                        if int(record[1])>int(small):
                            returned_record=File.helper(page,record,available_page,filename,header)
                            f.close()

                            # If after the insert of the new record helper function returns a record, then it means that the file is full
                            # and the last record returned by the helper function must be inserted to the next file
                            if type(returned_record)==list:
                                return returned_record
                            else:
                                return True
                    # If the keys cannot be converted to integers, the comparison with the new record and the biggest key is done here
                    except:
                        # If the new record has a bigger key than the smallest key in the page, then it is inserted
                        if record[1]>small:
                            returned_record=File.helper(page,record,available_page,filename,header)
                            f.close()

                            # If after the insert of the new record helper function returns a record, then it means that the file is full
                            # and the last record returned by the helper function must be inserted to the next file
                            if type(returned_record)==list:
                                return returned_record
                            else:
                                return True

                # There is already a record with the same key
                else:
                    f.close()
                    return False
                    
            # If the page is not full but contains some records, no shifting of the records will occur
            elif pageStatus[available_page]=='1':

                # It reads the current page
                f.seek(index+available_page*PAGE_SIZE,0)
                page=f.read(PAGE_SIZE)
                pageHeader=page[:64]

                # If there is not already a record with the same key then it checks if this page is suitable for the new record
                if File.check(page,record[1]):
                    
                    # The smallest key value in the page
                    small=pageHeader[int(pageHeader[16:18]):int(pageHeader[18:20])]

                    # If the key values can be converted to integer and the biggest key in the page is bigger thsn the new records'
                    # the record in not inserted into this page, next page will be checked
                    try:
                        if int(small)>int(record[1]):
                            continue
                    # If the key values cannot be converted to integer and the biggest key in the page is bigger thsn the new records'
                    # the record in not inserted into this page, next page will be checked
                    except:
                        if small>record[1]:
                            continue
                    # New record is inserted into the page
                    inserted=Page.insert(page,[record,])

                    # After the insert, page status is checked. 1 if not full, 2 if full
                    if inserted[3]=='1':
                        status='2'
                    else:
                        status='1'
                    
                    # Pages status in the file header is created
                    pageStatus=pageStatus[:available_page]+status+pageStatus[available_page+1:]

                    # After the insert, if all the pages become full, then the file status will be 1
                    if pageStatus=='2'*1000:
                        fileStatus='1'
                    else:
                        fileStatus='0'

                    # File header is updated
                    f.seek(0,0)
                    f.write(fileStatus+f'{header["numOfPages"]:04d}'+pageStatus)

                    # Page in the file is updated
                    f.seek(index+available_page*PAGE_SIZE,0)
                    f.write(inserted)
                    f.close()
                    return True

                # There is already a record with the same key
                else:
                    f.close()
                    return False
            
            # A new page will be created for the new record
            else:
                File.create_page(filename,header,record,available_page)
                f.close()
                return True

        f.close()
        
        # Go to next file, new record is smaller than the smallest record in this file
        return record
        
    @staticmethod
    def return_file_header(filename):
        """ Returns information in the file header as a dictionary
        """
        # Header is read
        f=open(filename,"r")
        header=f.read(1005)
        f.close()

        filestatus=header[0]
        numOfPages=int(header[1:5])
        statusOfPages=header[5:1005]
        
        dic={"fileStatus":filestatus,"numOfPages":numOfPages,"statusOfPages":statusOfPages}
        return dic

    @staticmethod
    def update_record(filename,record):
        """ Updates the fields of the record by first deleting the record then inserting the record with updated fields
        """
        check=File.delete_record(filename,record[1])
        if check:
            File.add_record(filename,record)
            return True
        else:
            return False

    @staticmethod
    def create_page(filename,header,record,page_num):
        f=open(filename,"r+")
        page=Page.create_page([record,],page_num)
        statusOfPages=header["statusOfPages"]

        # File header is updated since a new page is inserted
        f.seek(0,0)
        f.write(header["fileStatus"]+f'{header["numOfPages"]+1:04d}'+statusOfPages[:page_num]+'1')

        # New page is inserted at the end of the file
        f.seek(0,2)
        f.write(page)
        f.close()

    @staticmethod
    def delete_record(filename,key):
        f=open(filename,"r+")
        # Pages come after the header end index, 1005
        index=1005
        header=File.return_file_header(filename)
        statusOfPages=header["statusOfPages"]
        delete=False

        for i in range(0,1005):

            # If the page is not empty
            if statusOfPages[i]!='0':
                
                # Page is read
                f.seek(index+i*PAGE_SIZE,0)
                page=f.read(PAGE_SIZE)
                
                records,_,_,_=Page.read_page(page)
                
                # Each record in the page is checked if it is the record to be deleted
                for el in records:

                    # If the record in this page
                    if el[1]==key:

                        # Record is deleted from the page
                        delete=True
                        deleted=Page.delete(page,key)
                        
                        # Page used to have 1 record
                        if deleted[3:13]=='0'*10:

                            # This file has only 1 page and 1 record, it modifies header filled with zeros so this file will be
                            # deleted in haloSoftware.py
                            if header["numOfPages"]==1:
                                # Deletes the page
                                f.seek(index+i*PAGE_SIZE,0)
                                f.truncate()
                                # Modifies header so that pge status will be all zero
                                f.seek(0,0)
                                f.write('0'*1005)
                                break
                            
                            # This file has more than 1 pages so the rest of the pages will be shifted left
                            else:
                                # Header is updated, number of pages decrease by 1, page status of the deleted page becomes 0
                                f.seek(0,0)
                                f.write('0'+f'{header["numOfPages"]-1:04d}'+statusOfPages[:i]+statusOfPages[i+1:]+'0')
                                
                                # Page numbers are updated, pages are shifted to left
                                for p in range(i+1,header["numOfPages"]):
                                    # Page is read
                                    f.seek(index+p*PAGE_SIZE,0)
                                    page=f.read(PAGE_SIZE)
                                    # Page is shifted to left with new page number
                                    f.seek(index+(p-1)*PAGE_SIZE,0)
                                    f.write(f'{int(page[:2])-1:02d}'+page[2:])

                                # Last page is deleted since all pages are shifted left
                                f.seek(index+(header["numOfPages"]-1)*PAGE_SIZE,0)
                                f.truncate()

                                break
                        # Page had more than 1 record, deletes this record and no pages are shifted
                        else:
                            f.seek(index+i*PAGE_SIZE,0)
                            f.write(deleted)
                            f.seek(0,0)
                            f.write('0'+f'{header["numOfPages"]:04d}'+statusOfPages[:i]+'1'+statusOfPages[i+1:])
                            
                            break
                
                if delete==True:
                    break
            
            # Record is not in this file
            else:
                return False

        f.close()

        # The record was not in this file so deletion did not occur 
        if delete==False:
            return False

        # If the record used to be in this file, it is deleted successfully
        else:
            return True
                 
    @staticmethod
    def search_record(filename,key):
        """ Searches to fin a record with the given key. 
        If it exists, returns the record or else returns false
        """
        f=open(filename,"r")
        header=File.return_file_header(filename)
        numOfPages=header["numOfPages"]
        index=1005

        for i in range(0,numOfPages):
            # Each page is checked one by one to find the record
            f.seek(index+i*PAGE_SIZE,0)
            page=f.read(PAGE_SIZE)
            records,_,start,end=Page.read_page(page)
            # If the given key is in the key range of this page, examine the records of the page
            if key<=start and key>=end:
                for r in records:
                    if r[1]==key:
                        f.close()
                        return r
            
        f.close()
        return False

    @staticmethod
    def filter_records(filename,field,operation,value,fields):
        """ Returns records satisfying the given condition. 
        Returns empty list if no record in this file satisfies
        """
        header=File.return_file_header(filename)
        numOfFields=len(fields)
        fieldIndex=0
        # Rank of the field is found so that while examining the records, field at that location is checked
        for i in range(0,numOfFields):
            if field==fields[i]:
                break
            fieldIndex+=1
        
        results=[]
        index=1005
        f=open(filename,"r")
        for i in range(0,header["numOfPages"]):
            # Each page is read one by one
            f.seek(index+i*PAGE_SIZE,0)
            page=f.read(PAGE_SIZE)
            records,_,_,_=Page.read_page(page)

            for record in records:
                # If the field is not of type integer, then it returns false
                try:
                    val=int(record[fieldIndex])
                except:
                    return False
                
                # If the given condition is satisfied, that record is added to the results list
                if operation=='<':
                    if val<int(value):
                        results.append(record)
                elif operation=='=':
                    if val==int(value):
                        results.append(record)
                else:
                    if val>int(value):
                        results.append(record)
        f.close()
        return results
                

