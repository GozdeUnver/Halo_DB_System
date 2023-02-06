# First 3 bytes, size of the meta data
# int(first 3 bytes)/3=number of fields
class Record:
    @staticmethod
    def create_rawstring(data_list):
        prev = (len(data_list) + 1) * 3 
        header = f'{prev:03d}'
        data = ''
        for value in data_list:
            prev += len(value)
            data += value
            header += f'{prev:03d}'
        return (header+data).ljust(365, '.')

    @staticmethod
    def read_rawstring(rawstring):
        data = []
        data_index = int(rawstring[0:3]) 
        start_idx = data_index
        for i in range(3, data_index, 3): 
            end_idx = int(rawstring[i:i+3])
            data.append(rawstring[start_idx:end_idx])
            start_idx = end_idx
        return data
    
    @staticmethod
    def read_field(rawstring, k):
        start_idx, end_idx = int(rawstring[(k-1)*3: k*3]), int(rawstring[k*3: (k+1)*3])
        return rawstring[start_idx: end_idx]

    @staticmethod
    def update_field(rawstring, k, value):
        data = Record.read_rawstring(rawstring)
        data[k-1] = value
        return Record.create_rawstring(data)
