PAGE_SIZE=3650+64
FILE_SIZE = PAGE_SIZE * 1000
NUM_FIELDS = 12
MAX_TYPE_NAME_LENGTH = 20
MAX_FIELD_NAME_LENGTH = 20
import time
from os import mkdir
import glob
import os
import sys
from record import Record
from page import Page 
from file import File 
import csv
import datetime
import re
class System():
    def __init__(self):
        try:
            sys_catalog = open('CatalogFile', 'r+')
            #self.catalog = sys_catalog.read()
            users = open('UserFile', 'r+')
        except:
            # Initial boot-up, create the system catalog and the user type
            sys_catalog = open('CatalogFile', 'w+')
            catalog=File.create_file()
            sys_catalog.write(catalog)
            sys_catalog.flush()
            File.add_record('CatalogFile',['','User','Username','Password'])
            users = open('UserFile', 'w+')
            users_rawstring = File.create_file()
            users.write(users_rawstring)
            users.flush()

        self.logs=open('haloLog.csv','a+')
        self.output=open(sys.argv[2],'a+')
        sys_catalog.close()
        users.close()

        self.current_user='null'
        self.current_user_password='null'

        self.process_input()

        self.output.close()

        self.logs.close()
    
    def process_input(self):
        with open(sys.argv[1], 'r') as input:
            queries = input.readlines()
            for query in queries:
                if len(query) != 0:
                    tokens = query.split()
                    if (tokens[0] in {'register', 'login', 'logout'}): self.authHandler(tokens)
                    elif (tokens[1] == 'type'): self.ddlHandler(tokens)
                    elif (tokens[1] == 'record'): self.dmlHandler(tokens)
        
    def authHandler(self, tokens):
        writer = csv.writer(self.logs)
        curr= round(time.time())

        if tokens[0]=='login':

            # There is currently logged in user, new user can't log in
            if self.current_user!='null':
                
                if tokens[1]!=self.current_user:
                    data=[tokens[1], curr,tokens[0],'failure']
                    writer.writerow(data)
                    self.logs.flush()
                    return
            # There is no currently logged in user. If the user is already registered and password is correct, then user can log in
            else:
                user_files=glob.glob("UserFile*")
                user_files.sort()

                # Searches all user files to find if there is an existing user in the system
                for user_file in user_files:
                    header=File.return_file_header(user_file)
                    numOfPages=header["numOfPages"]

                    # Examines each page of the user file one by one
                    for i in range(0,numOfPages):
                        records=File.read_file(user_file,i)
                        for record in records:
                            # If there is such a user with that password in the user file, user logs in
                            if record[0]==tokens[1] and record[1]==tokens[2]:
                                self.current_user=tokens[1]
                                self.current_user_password=tokens[2]
                                data=[self.current_user, curr,tokens[0],'success']
                                writer.writerow(data)
                                self.logs.flush()
                                return
                # There is no currently registered user with that username and/or password
                data=[tokens[1], curr,tokens[0],'failure']
                writer.writerow(data)
                self.logs.flush()
        
        # If the user wants to register
        elif tokens[0]=='register':

            auth=" ".join(tokens[:3])
            # If the password and the repeated passwords match, user can register but still a check is needed 
            # if there is already a user with the same username
            if tokens[3]==tokens[4]:

                user_files=glob.glob("UserFile*")
                user_files.sort()
                record=[tokens[2],tokens[3]]
                for user_file in user_files:
                    check=File.add_record(user_file,record)
                    # There is no user with the same username, user is registered
                    if check==True:
                        data=[self.current_user, curr,auth,'success']
                        writer.writerow(data)
                        self.logs.flush()
                        return
                    # There is already registered user with the same username
                    elif check==False:
                        data=[self.current_user, curr,auth,'failure']
                        writer.writerow(data)
                        self.logs.flush()
                        return
                    # UserFile is full, its last record must be shifted
                    else:
                        record=check

                # New user file is created and user will be added to this file         
                newUserFileName=user_files[-1]+"+"
                f=open(newUserFileName,'w')
                userFile_header=File.create_file()
                f.write(userFile_header)
                f.flush()
                File.add_record(newUserFileName,record)
                f.close()


            # If the password and the repeated password doesn't match, then the user is not registered
            else:
                data=[self.current_user, curr,auth,'success']
                writer.writerow(data)
                self.logs.flush()
        
        # If the user wants to log out
        else:
            data=[self.current_user, curr,tokens[0],'success']
            self.current_user='null'
            self.current_user_password='null'
            writer.writerow(data)
            self.logs.flush()
            
    def ddlHandler(self, tokens):
        writer = csv.writer(self.logs)
        curr= round(time.time())
        ddl=" ".join(tokens)
        # If there is no currently logged in user then write failure to the log file
        if self.current_user=='null':
            
            data=[self.current_user, curr,ddl,'failure']
            writer.writerow(data)
            self.logs.flush()
            return
        
        if tokens[0]=='create':
            if len(tokens)<=4:
                data=[self.current_user,curr,ddl,'failure']
                writer.writerow(data)
                self.logs.flush()
                return
            fields=[]
            fields.append('planet')
            fields.append('id')
            fields+=tokens[4:]
            header=File.create_file()
            fields.insert(0,tokens[2])
            fields.insert(0,'')
            check=None

            catalog_files=glob.glob("CatalogFile*")
            catalog_files.sort()
            
            for catalog_file in catalog_files:
                check=File.add_record(catalog_file,fields)
                if check==True:
                    f=open(tokens[2]+"File",'w')
                    f.write(header)
                    f.close()
                    break
                elif check==False:
                    data=[self.current_user,curr,ddl,'failure']
                    writer.writerow(data)
                    self.logs.flush()
                    return
                else:
                    fields=check

            # New catalog file is created
            if type(check)==list:
                newCatalogName=catalog_files[-1]+"+"
                f=open(newCatalogName,'w')
                catalog_header=File.create_file()
                f.write(catalog_header)
                f.flush()
                catalog_files.append(newCatalogName)

                # New type is added to the new catalog
                File.add_record(newCatalogName,fields)
                f.close()

                # File for the type is created
                type_file=open(tokens[2]+"File",'w')
                type_file.write(header)
                type_file.close()
                
            data=[self.current_user,curr,ddl,'success']
            writer.writerow(data)
            self.logs.flush()
            return

        elif tokens[0]=='delete':
            if len(tokens)!=3:
                data=[self.current_user,curr,ddl,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            success=False
            catalog_files=glob.glob('CatalogFile*')
            catalog_files.sort()
            # Deletes type record from the catalog
            for catalog_file in catalog_files:
                check=File.delete_record(catalog_file,tokens[2])
                if check==True:
                    success=True
                    data=[self.current_user,curr,ddl,'success']
                    writer.writerow(data)
                    self.logs.flush()
                    catalog_header=File.return_file_header(catalog_file)

                    if catalog_header["numOfPages"]==0:
                        os.remove(catalog_file)

                    break

            if not success:   
                data=[self.current_user,curr,ddl,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            file_type=tokens[2]+"File"
            files=glob.glob(file_type+"*")
            files.sort()
               
            if len(files)!=0:
                success=True
                for filename in files:
                    # Deletes file from the system
                    os.remove(filename)
                                   
        elif tokens[0]=='inherit':
            if len(tokens)<4:
                data=[self.current_user,curr,ddl,'failure']
                writer.writerow(data)
                self.logs.flush()
                return
            target=tokens[2]
            source=tokens[3]
            catalog_files=glob.glob("CatalogFile*")
            catalog_files.sort()
            fields=[]
            found=False
            for catalog_file in catalog_files:
                tmp=File.search_record(catalog_file,source)
                if tmp!=False:
                    fields+=tmp[2:]
                    found=True
                    break

            if not found:
                data=[self.current_user,curr,ddl,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            
            for i in range(4,len(tokens)):
                fields.append(tokens[i])

            header=File.create_file()
            fields.insert(0,target)
            fields.insert(0,'')
            for catalog_file in catalog_files:
                check=File.add_record(catalog_file,fields)
                if check==True:
                    f=open(tokens[2]+"File",'w')
                    f.write(header)
                    f.close()
                    break
                elif check==False:
                    data=[self.current_user,curr,ddl,'failure']
                    writer.writerow(data)
                    self.logs.flush()
                    return

            if check==fields:
                newCatalogName=catalog_files[-1]+"+"
                f=open(newCatalogName,'w')
                catalog_header=File.create_file()
                f.write(catalog_header)
                f.flush()
                File.add_record(newCatalogName,fields)
                f.close()
                catalog_files.append(newCatalogName)
                type_file=open(tokens[2]+"File",'w')
                type_file.write(header)
                type_file.close()
                
            data=[self.current_user,curr,ddl,'success']
            writer.writerow(data)
            self.logs.flush()
            return
        # List all types
        else:
            if len(tokens)!=2:
                data=[self.current_user,curr,ddl,'failure']
                writer.writerow(data)
                self.logs.flush()
                return
            catalog_files=glob.glob("CatalogFile*")
            catalog_files.sort()
            records=[]
            result=False
            for catalog_file in catalog_files:
                header=File.return_file_header(catalog_file)
                numOfPages=header["numOfPages"]
                for i in range(numOfPages-1,-1,-1):
                    records=File.read_file(catalog_file,i)
                    for j in range(len(records)-1,-1,-1):
                        if records[j][1]!="User":
                            result=True
                            self.output.write(records[j][1])
                            self.output.write("\n")
            self.output.flush()

            if result:
                data=[self.current_user,curr,ddl,'success']
                writer.writerow(data)
                self.logs.flush()
            else:
                data=[self.current_user,curr,ddl,'failure']
                writer.writerow(data)
                self.logs.flush()

    def dmlHandler(self, tokens):
        writer = csv.writer(self.logs)
        curr= round(time.time())
        dml=" ".join(tokens)
        # If there is no currently logged in user then write failure to the log file
        if self.current_user=='null':
            
            data=[self.current_user, curr,dml,'failure']
            writer.writerow(data)
            self.logs.flush()
            return
        
        if tokens[0]=='create':
            file_type=tokens[2]+"File"
            record_type=tokens[2]
            fields=['E226-S187']
            fields+=tokens[3:]

            files=glob.glob(file_type+"*")
            files.sort()
            
            catalog_files=glob.glob('CatalogFile'+"*")
            catalog_files.sort()
            val=False
            for catalog_file in catalog_files:
                val=File.search_record(catalog_file,record_type)
                if val!=False:
                    if len(val[2:])!=len(fields):
                        data=[self.current_user, curr,dml,'failure']
                        writer.writerow(data)
                        self.logs.flush()
                        return
                    else: 
                        val=True
                        break
            if val==False:
                data=[self.current_user, curr,dml,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            return_val=None
            for filename in files:
                return_val=File.add_record(filename,fields)
                # If there is already a record with the same key then don't add it
                if return_val==False:
                    data=[self.current_user, curr,dml,'failure']
                    writer.writerow(data)
                    self.logs.flush()
                    return
                # If the new record is added but now the last element of the file must be shifted to a new file
                elif type(return_val)==list:
                    fields=return_val

                # If the insertion is completed writes its log and exits 
                else:
                    data=[self.current_user, curr,dml,'success']
                    writer.writerow(data)
                    self.logs.flush()
                    return

            newFileName=files[-1]+"+"
            header=File.create_file()
            f=open(newFileName,'w')
            f.write(header)
            f.close()
            dic={"fileStatus":"0","numOfPages":0,"statusOfPages":"0"*1000}
            # Last record is added to the newly created file
            File.create_page(newFileName,dic,fields,0)
           
        elif tokens[0]=='delete':
            if len(tokens)!=4:
                data=[self.current_user, curr,dml,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            file_type=tokens[2]+"File"

            files=glob.glob(file_type+"*")
            files.sort()

            for filename in files:
                check=File.delete_record(filename,tokens[3])
                if check==True:
                    data=[self.current_user, curr,dml,'success']
                    writer.writerow(data)
                    self.logs.flush()
                    file_header=File.return_file_header(filename)

                    # If the file is empty after removal of the record, delete the file
                    if file_header["numOfPages"]==0:
                        os.remove(filename)
                    
                    return
            
            data=[self.current_user, curr,dml,'failure']
            writer.writerow(data)
            self.logs.flush()

        elif tokens[0]=='search':
            if len(tokens)!=4:
                data=[self.current_user, curr,dml,'failure']
                writer.writerow(data)
                self.logs.flush()
                return
            file_type=tokens[2]+"File"
            key=tokens[3]

            files=glob.glob(file_type+"*")
            files.sort()
            for filename in files:
                record=File.search_record(filename,key)
                if len(record)!=0:
                    self.output.write(" ".join(record)+"\n")
                    data=[self.current_user, curr,dml,'success']
                    writer.writerow(data)
                    self.logs.flush()
                    return
        
            data=[self.current_user, curr,dml,'failure']
            writer.writerow(data)
            self.logs.flush()

        elif tokens[0]=='update':
            file_type=tokens[2]+"File"
            update=['E226-S187']
            update+=tokens[3:]

            files=glob.glob(file_type+"*")
            files.sort()

            catalog_files=glob.glob('CatalogFile'+"*")
            catalog_files.sort()
            val=False
            for catalog_file in catalog_files:
                val=File.search_record(catalog_file,tokens[2])
                if val!=False:
                    if len(val[2:])!=len(update):
                        data=[self.current_user, curr,dml,'failure']
                        writer.writerow(data)
                        self.logs.flush()
                        return
                    else: 
                        break

            for filename in files:
                check=File.update_record(filename,update)
                if check:
                    data=[self.current_user, curr,dml,'success']
                    writer.writerow(data)
                    self.logs.flush()
                    return
            
            data=[self.current_user, curr,dml,'failure']
            writer.writerow(data)
            self.logs.flush()

        elif tokens[0]=='list':
            if len(tokens)!=3:
                data=[self.current_user, curr,dml,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            file_type=tokens[2]+"File"

            files=glob.glob(file_type+"*")
            files.sort()

            success=False

            for filename in files:
                header=File.return_file_header(filename)
                numOfPages=header["numOfPages"]
                for i in range(0,numOfPages):
                    records=File.read_file(filename,i)
                    for r in records:
                        success=True
                        line=" ".join(r)+"\n"
                        self.output.write(line)
        
            if not success:
                data=[self.current_user, curr,dml,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            self.output.flush()
            data=[self.current_user, curr,dml,'success']
            writer.writerow(data)
            self.logs.flush()

        # Filter records
        else:
            if len(tokens)!=4:
                data=[self.current_user, curr,dml,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            record_type=tokens[2]
            condition=tokens[3]
            if "<" in condition:
                operation="<"
            elif ">" in condition:
                operation=">"
            else:
                operation="="
            splitted=re.split(">|<|=",condition)
            field=splitted[0]
            value=splitted[1]

            file_type=tokens[2]+"File"

            catalog_files=glob.glob("CatalogFile*")
            catalog_files.sort()
            fields=[]
            success=False
            files=glob.glob(file_type+"*")
            files.sort()

            for catalog_file in catalog_files:
                
                fields=File.search_record(catalog_file,record_type)
                if fields!=False:
                    fields=fields[2:]
                    break

            for filename in files:
                tmp=File.filter_records(filename,field,operation,value,fields)
                if tmp!=False and len(tmp)!=0:
                    success=True
                    for r in tmp:
                        self.output.write(" ".join(r)+"\n")

            if not success:
                data=[self.current_user, curr,dml,'failure']
                writer.writerow(data)
                self.logs.flush()
                return

            
            self.output.flush()
            data=[self.current_user, curr,dml,'success']
            writer.writerow(data)
            self.logs.flush()

system = System()


