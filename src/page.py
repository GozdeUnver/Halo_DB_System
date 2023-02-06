# First 3 bytes state the page number inside the file the page is in.
# Following byte states the status of the page. '1' means full, '0' means not full.
# Following 10 bytes state the status of slots in order. '1' means full, '0' means empty.
# Following 6 bytes state the offsets of primary key values for the first and last entry. 2/2/2->end offset of the last primary key value

from record import Record

class Page:

    @staticmethod
    def create_page(records, page_num):
        assert len(records) <= 10
        try:
            records.sort(reverse=True, key=lambda x: int(x[1]))
        except:
            records.sort(reverse=True, key=lambda x: x[1])
        rawstring = f'{page_num:03d}'
        rawstring += '1' if len(records) == 10 else '0'
        rawstring += '1' * len(records) + '0' * (10-len(records))
        rawstring += '20'
        if (len(records)==0): rawstring += '2020'
        else: 
            rawstring += str(20 + len(records[0][1]))
            rawstring += str(20 + len(records[0][1]) + len(records[-1][1]))
            rawstring += records[0][1] + records[-1][1]
        rawstring = rawstring.ljust(64, '.')
        for rec in records: rawstring += Record.create_rawstring(rec)
        return rawstring.ljust(3714, '.')
    
    @staticmethod
    def read_page(rawstring): 
        records = []
        page_num = int(rawstring[:3])
        start_val, end_val = rawstring[int(rawstring[14:16]): int(rawstring[16:18])], rawstring[int(rawstring[16:18]): int(rawstring[18:20])]
        for i in range(64, 3714, 365):
            record = rawstring[i:i+365]
            if record[0] == '.': break
            else: records.append(Record.read_rawstring(record))
        return records, page_num, start_val, end_val

    @staticmethod
    def insert(rawstring, record):
        records, page_num, _, _ = Page.read_page(rawstring)
        records+=record
        #records.sort(reverse=True, key=lambda x: x[1])
        return Page.create_page(records, page_num)

    @staticmethod
    def delete(rawstring, key):
        records, page_num, _, _ = Page.read_page(rawstring)
        return Page.create_page(list(filter(lambda x: x[1] != key, records)), page_num)

