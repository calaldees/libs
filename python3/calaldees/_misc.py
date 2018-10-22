

def read_file_list(filename):
    data = []
    with open(filename, 'r') as source:
        for line in source:
            data.append(line.strip())
    return data



