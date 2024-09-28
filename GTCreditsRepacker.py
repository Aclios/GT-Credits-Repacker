import struct
import sys


class utf16StringStruct:
    def __init__(self,f):
        self.offset = f.tell()
        self.data = bytearray()
        char = f.read(2)
        while char != b"\x00\x00":
            self.data += char
            char = f.read(2)
        self.data = self.data.decode('utf-16')

class utf8StringStruct:
    def __init__(self,f):
        self.offset = f.tell()
        self.data = bytearray()
        char = f.read(1)
        while char != b"\x00":
            self.data += char
            char = f.read(1)
        self.data = self.data.decode('utf-8')

def get_strings_data(start_offset,end_offset_utf16,end_offset_utf8,f):
    f.seek(start_offset)
    utf16string_struct_list = []
    utf8string_struct_list = []
    while f.tell() != end_offset_utf16:
        utf16string_struct_list.append(utf16StringStruct(f))
    while f.tell() != end_offset_utf8:
        utf8string_struct_list.append(utf8StringStruct(f))
    return utf16string_struct_list, utf8string_struct_list

def read_new_string_data(filepath):
    with open(filepath,mode='rb') as f:
        data = f.read()
    data_list = data.replace(b'\x0a',b'').replace(b'\x0d',b'').replace(b'<NewLine>',b'\x0d\x0a').split(b'<string>')
    for idx,data in enumerate(data_list):
        data_list[idx] = data.decode()
    return data_list[1:]

def extract_credits(gui_filepath,txt_filepath):
    start, utf16_string_list, utf8_string_list, end = read_file(gui_filepath)
    with open(txt_filepath,mode='xb') as f:
        for struct in utf16_string_list:
            f.write(('<string>' + struct.data.replace('\x0d\x0a','<NewLine>') + '\n').encode())

def calculate_offset_dict(old_string_struct_list,new_string_list,utf8_string_struct_list,base_offset):
    off_dict = {}
    current_offset = base_offset
    for idx,struct in enumerate(old_string_struct_list):
        off_dict[struct.offset] = current_offset
        current_offset += len(new_string_list[idx].encode('utf-16'))
    off_dict[0xe84b8] = current_offset
    shift = current_offset - 0xe84b8
    for struct in utf8_string_struct_list:
        off_dict[struct.offset] = struct.offset + shift
    off_dict[0xe8fdf] = 0xe8fdf + shift
    return off_dict

def read_file(gui_filepath):
    with open(gui_filepath,mode='rb') as f:
        start = f.read(0xe2b88)
        utf16_string_list, utf8_string_list = get_strings_data(0xe2b88,0xe84b8,0xe8fdf,f)
        f.seek(0xe8fdf)
        end = f.read()
        return start, utf16_string_list, utf8_string_list, end

def repack_script(gui_filepath,txt_filepath):
    start, utf16_string_list, utf8_string_list, end = read_file(gui_filepath)
    new_string_list = read_new_string_data(txt_filepath)
    off_dict = calculate_offset_dict(utf16_string_list,new_string_list,utf8_string_list,0xe2b88)
    with open(gui_filepath + '.new',mode='w+b') as f:
        f.write(start)
        for string in new_string_list:
            f.write((string + '\x00').encode('utf-16')[2:])
        for string_struct in utf8_string_list:
            f.write((string_struct.data + '\x00').encode('utf-8'))
        f.write(end)
        f.seek(0)
        while f.tell() < 0xe2b88:
            value = struct.unpack('<Q',f.read(8))[0]
            if value in list(off_dict.keys()):
                f.seek(-8,1)
                f.write(struct.pack('<Q',off_dict[value]))

if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise Exception("Valid syntax: py GTcreditspacker.py [-e] [-r] <gui_filepath> <credits_txt_filepath>")
    if sys.argv[1] == '-e':
        extract_credits(sys.argv[2],sys.argv[3])
    elif sys.argv[1] == '-r':
        repack_script(sys.argv[2],sys.argv[3])
    else:
        raise Exception("Valid syntax: py GTcreditspacker.py [-e] [-r] <gui_filepath> <credits_txt_filepath>")
    print("Done!")