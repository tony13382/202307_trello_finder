import pandas as pd
import pyexcel_ods3
import glob

import re

def split_and_strip(input_string):
    # 使用正则表达式去除数字前缀和多余的空格
    cleaned_string = re.sub(r'\d+\.', '', input_string)
    # 使用正则表达式删除括号内的内容
    cleaned_string = re.sub(r'〔[^〔〕]*〕', '', cleaned_string)
    # 使用正则表达式将字符串拆分成不同的部分
    #parts = re.split(r'[，；]', cleaned_string)
    #parts = re.split(r'；|(?=〔)|(?<=〕)', cleaned_string)
    parts = re.split(r'[，;,；（）〔〕]', cleaned_string)
    # 去除多余的空格和〔〕字符
    result_list = [part.strip('〔〕') for part in parts if part.strip()]

    result_list = [str for str in result_list if "之字首" not in  str and "之字尾" not in str and "一種" not in str and "的字首" not in str and "的字尾" not in str]

    return result_list

input_string1 = '地球層圈，地球圈層'
input_string2 = '1.盾面〔牙形石類〕；2.小盾片〔昆蟲類鞘翅目〕；3.盾紋面〔雙殼類〕'

result_list1 = split_and_strip(input_string1)
result_list2 = split_and_strip(input_string2)

print(result_list1)
print(result_list2)

files = glob.glob('*.ods')
file_txt = ""
for file in files:
    print(f"{file} - Start")
    import pandas as pd
    import pyexcel_ods3

    # 读取ODS文件
    data = pyexcel_ods3.get_data(file)
    # 选择您想要的工作表（这里假设您的ODS文件只包含一个工作表）
    # 将数据转换为DataFrame
    df = pd.DataFrame(data[list(data.keys())[0]])
    # 将第一行设置为标题
    w_list = df.iloc[1:,2].to_list()
    for word in w_list:
        re_list = split_and_strip(word.replace(" ", ""))
        for kw in re_list:
            file_txt = file_txt + f"{kw} 100 NER\n"

    print(f"{file} - End")


# Specify the file path where you want to save the string
file_path = "output1.txt"

with open(file_path, 'w') as file:
    file.write(file_txt) # Open the file in write mode and save the string 