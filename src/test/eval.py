import json
import pandas as pd
import time
from openpyxl import Workbook

from openai import OpenAI

client = OpenAI(api_key="sk-xxxxx", base_url="https://api.deepseek.com")

def compare_entities(standard_answer, test_result):
    conversation = []
    prompt = '''你是一个实体识别结果的评判官，负责根据标准答案判定模型识别结果是否正确，最后给出评估的得分

## 注意
1. 判断依据来源于标准答案，请不要使用自己的知识
2. 识别结果与标准答案之间的主体一致即认为是正确，忽略大小写，缩写，备注等信息
3. 输出识别结果中的每一行的判定结果

## 数据格式
实体类别|实体名称

## 标准答案
''' + "\n".join(["|".join(ans) for ans in standard_answer]) + '''

## 模型识别结果
''' + "\n".join(["|".join(ans) for ans in test_result]) + '''

## 输出格式
识别类别|实体名称|判定结果
disease|Gliomas|正确
treatment|conventional therapeutic strategies|错误
target|growth factor receptor protein tyrosine kinase (PTK)|正确
'''
    retry = 0
    res = ""
    while retry < 10:
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=8192,
                temperature=0.01,
                stream=False
            )
            res = response.choices[0].message.content
            #print(response)
            break
        except Exception as e:
            retry += 1
            time.sleep(30)
            print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
            print("get deepseek response error! retry!")
            print(e)
    n_true = 0
    result = []
    for line in res.split("\n"):
        if line.startswith("识别类别|实体名称|判定结果"):
            continue
        elif line.startswith("|") or line.find("|") == -1:
            continue
        else:
            line = line.strip()
            line = line.split("|")
            if len(line) == 3:
                if line[2].startswith("正确"):
                    n_true += 1
                result.append([line[0], line[1], line[2]])
    return n_true, result

def compare_relationships(standard_answer, test_result):
    conversation = []
    prompt = '''你是一个知识图谱关系识别结果的评判官，负责根据标准答案判定模型识别结果是否正确，最后给出评估的得分

## 注意
1. 判断依据来源于标准答案，请不要使用自己的知识
2. 识别结果与标准答案之间的实体和关系都一致才能认为是正确，有一项不一致就是错误
3. 实体和关系的名称需要忽略大小写，缩写，备注等信息
4. 输出识别结果中的每一行的判定结果

## 数据格式
实体名称1|关系|实体名称2

## 标准答案
''' + "\n".join(["|".join(ans) for ans in standard_answer]) + '''

## 模型识别结果
''' + "\n".join(["|".join(ans) for ans in test_result]) + '''

## 输出格式
实体名称1|关系|实体名称2|判定结果
Cerebral atherosclerosis (AS)|is_located_in|aged brain|错误
'''
    retry = 0
    res = ""
    while retry < 10:
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=8192,
                temperature=0.01,
                stream=False
            )
            res = response.choices[0].message.content
            #print(response)
            break
        except Exception as e:
            retry += 1
            time.sleep(30)
            print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
            print("get deepseek response error! retry!")
            print(e)
    n_true = 0
    result = []
    for line in res.split("\n"):
        if line.startswith("实体名称1|关系|实体名称2|判定结果"):
            continue
        elif line.startswith("|") or line.find("|") == -1:
            continue
        else:
            line = line.strip()
            line = line.split("|")
            if len(line) == 4:
                if line[3].startswith("正确"):
                    n_true += 1
                result.append([line[0], line[1], line[2], line[3]])
    return n_true, result

def calculate_metrics(true_list, pred_list):
    true_set = set(true_list)
    pred_set = set(pred_list)

    tp = len(true_set & pred_set)
    fp = len(pred_set - true_set)
    fn = len(true_set - pred_set)

    #print(true_set - pred_set)
    print(pred_set - true_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    #print(f"precision:{precision}, tp:{tp}, all:{tp+fp}")
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    #print(f"recall:{recall}, tp:{tp}, all:{tp+fn}")
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1

def calculate_metrics1(n_right, n_std, n_test):
    precision = n_right / n_test if n_test > 0 else 0
    #print(f"precision:{precision}, tp:{tp}, all:{tp+fp}")
    recall = n_right / n_std if n_std > 0 else 0
    #print(f"recall:{recall}, tp:{tp}, all:{tp+fn}")
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1

def print_metrics_table(metrics_dict):
    print(f"{'Metric':<15} {'Precision':<18} {'Recall':<19} {'F-Score':<20}")
    print("-" * 70)
    for key, values in metrics_dict.items():
        print(f"{key:<15} {values[0]:<18.3f} {values[1]:<19.3f} {values[2]:<20.3f}")

def write_lists_to_excel(data, excel_filename):
    """
    将二维列表写入Excel文件
    
    参数:
        data (list of lists): 要写入的二维数据，每个子列表代表一行
        excel_filename (str): 要保存的Excel文件名（包括.xlsx后缀）
    """
    try:
        # 创建一个新的工作簿
        wb = Workbook()
        ws = wb.active
        
        # 遍历数据并写入Excel
        for row in data:
            ws.append(row)
        
        # 保存Excel文件
        wb.save(excel_filename)
        print(f"数据已成功写入到 {excel_filename}")
    except Exception as e:
        print(f"写入Excel文件时出错: {e}")

def compare_json_files(std_answer_file, test_result_file, outputdir='./'):
    std_answer_docs = []
    test_result_docs = []

    with open(std_answer_file, 'r') as f:
        for line in f:
            std_answer_docs.append(json.loads(line.lower()))

    with open(test_result_file, 'r') as f:
        for line in f:
            try:
                test_result_docs.append(json.loads(line.lower()))
            except:
                continue

    #std_answer_docs = std_answer_docs[:5]
    # Filter out documents from the test result that are not present in the standard answer
    test_result_docs = {doc['id']: doc for doc in test_result_docs}
    std_answer_docs = {doc['id']: doc for doc in std_answer_docs}
    common_doc_ids = set(std_answer_docs.keys()) & set(test_result_docs.keys())

    std_answer_docs = [std_answer_docs[doc_id] for doc_id in common_doc_ids]
    test_result_docs = [test_result_docs[doc_id] for doc_id in common_doc_ids]

    docid_2_doc = {}
    for doc in std_answer_docs:
        docid_2_doc[doc['id']] = doc['content']
    #print('len(std_answer_docs):', len(std_answer_docs))
    #print('len(test_result_docs):', len(test_result_docs))
    #print(std_answer_docs[0])
    #print(test_result_docs[0])

    # Initialize empty lists to store ground truth and predicted entities, relationships, and attributes
    true_entities = []
    pred_entities = []
    true_relationships = []
    pred_relationships = []

    n_entity_right = 0
    n_entity_test = 0
    n_entity_std = 0

    n_relationship_right = 0
    n_relationship_test = 0
    n_relationship_std = 0

    entity_results = []
    relationship_results = []

    for std_doc, test_doc in zip(std_answer_docs, test_result_docs):
        std_entities = [[e['entity_type'], e['name']] for e in std_doc['entities']]
        test_entities = [[e['entity_type'], e['name']] for e in test_doc['entities']]

        right, result = compare_entities(std_entities, test_entities)
        n_entity_right += right
        n_entity_std += len(std_entities)
        n_entity_test += len(test_entities)
        entity_results.extend(result)

        for e in test_doc['relationships']:
            if e['relationship'].find("_") > 0:
                e['relationship'] = e['relationship'].replace("_", " ")
        std_relationships = [[e['entity_name1'], e['relationship'], e['entity_name2']] for e in std_doc['relationships']]
        test_relationships = [[e['entity_name1'], e['relationship'], e['entity_name2']] for e in test_doc['relationships']]
        
        right1, result1 = compare_relationships(std_relationships, test_relationships)
        n_relationship_right += right1
        n_relationship_std += len(std_relationships)
        n_relationship_test += len(test_relationships)
        relationship_results.extend(result1)

    # Calculate metrics for entities, relationships, and attributes
    entity_metrics = calculate_metrics1(n_entity_right, n_entity_std, n_entity_test)
    relationship_metrics = calculate_metrics1(n_relationship_right, n_relationship_std, n_relationship_test)

    metrics_dict = {
        "Entities": entity_metrics,
        "Relationships": relationship_metrics
    }
    write_lists_to_excel(entity_results, outputdir + 'entity_results.xlsx')
    write_lists_to_excel(relationship_results, outputdir + 'relationship_results.xlsx')
    print_metrics_table(metrics_dict)

#time.sleep(4000)
# Replace 'std_answer.json' and 'test_result.json' with the actual paths to your JSON files
compare_json_files('../data/test_new.json', '../test/output_deepseek_r1_2.xlsx.json','../result/deepseek-r1-')
#compare_json_files('../data/test_new.json', '../test/output_qwen2.5-7b-grpo1.xlsx.json', '../result/7b-grpo1-')
#compare_json_files('../data/test_new.json', '../test/output_qwen2.5-7b-600-grpo.xlsx.json', '../result/7b-600-grpo-')
#compare_json_files('../data/test_new.json', '../test/output_qwen2.5-7b-grpo.xlsx.json', '../result/7b-grpo-')
#compare_json_files('../data/test_new.json', '../test/output_qwen2.5-0.5b-grpo.xlsx.json', '../result/0.5b-grpo-')
exit()
