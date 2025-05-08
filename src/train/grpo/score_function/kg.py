# Copyright 2024 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import json
from typing import Dict, List, Tuple
from collections import defaultdict

def accuracy_reward(predict_str: str, ground_truth: str) -> float:
    """
    计算预测结果与标注结果之间的准确率奖励得分，基于实体和关系的F1-score
    
    参数:
        predict_str: 预测字符串，包含<answer>标签
        ground_truth: 标注的JSON字符串
        
    返回:
        float: 0到1之间的分数，表示预测准确率
    """
    try:
        # 提取预测结果中的answer内容
        #print(predict_str)
        content_match = re.search(r"<answer>(.*?)</answer>", predict_str, re.DOTALL)
        if not content_match:
            return 0.0
            
        pred_content = content_match.group(1).strip()
        
        # 解析预测和标注的JSON
        pred_data = json.loads(pred_content)
        gt_data = json.loads(ground_truth)
        
        # 计算实体识别的F1分数
        entity_f1 = calculate_entity_f1(pred_data.get("Entities", {}), 
                                      gt_data.get("Entities", {}))
        
        # 计算关系抽取的F1分数
        relation_f1 = calculate_relation_f1(pred_data.get("Relationships", []), 
                                           gt_data.get("Relationships", []))
        
        # 返回平均F1分数
        return (entity_f1 + relation_f1) / 2
        
    except (json.JSONDecodeError, AttributeError, KeyError):
        # 如果JSON解析失败或格式不正确，返回0分
        return 0.0

def calculate_entity_f1(pred_entities: Dict[str, str], 
                       gt_entities: Dict[str, str]) -> float:
    """
    计算实体识别的F1分数
    
    参数:
        pred_entities: 预测的实体字典 {entity_name: entity_type}
        gt_entities: 标注的实体字典 {entity_name: entity_type}
        
    返回:
        float: F1分数
    """
    try:
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        # 检查预测实体
        for entity, pred_type in pred_entities.items():
            if entity in gt_entities:
                if pred_type == gt_entities[entity]:
                    true_positives += 1  # 完全匹配
                else:
                    false_positives += 1  # 边界正确但类型错误
            else:
                false_positives += 1  # 错误识别
        
        # 检查遗漏的实体
        for entity in gt_entities:
            if entity not in pred_entities:
                false_negatives += 1  # 遗漏
        
        # 计算precision和recall
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        # 计算F1分数
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        return f1
    except:
        return 0.0

def calculate_relation_f1(pred_relations: List[List], 
                         gt_relations: List[List]) -> float:
    """
    计算关系抽取的F1分数
    
    参数:
        pred_relations: 预测的关系列表 [[entity1, type1, rel, type2, complication]]
        gt_relations: 标注的关系列表 [[entity1, type1, rel, type2, complication]]
        
    返回:
        float: F1分数
    """
    try:
        # 将关系转换为元组以便比较
        pred_tuples = {tuple(rel) for rel in pred_relations}
        gt_tuples = {tuple(rel) for rel in gt_relations}
        
        true_positives = len(pred_tuples & gt_tuples)
        false_positives = len(pred_tuples - gt_tuples)
        false_negatives = len(gt_tuples - pred_tuples)
        
        # 计算precision和recall
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        # 计算F1分数
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        return f1
    except:
        return 0.0

def format_reward(predict_str: str) -> float:
    pattern = re.compile(r"<think>.*?</think>\s*<answer>.*?</answer>", re.DOTALL)
    format_match = re.fullmatch(pattern, predict_str)
    return 1.0 if format_match else 0.0

def think_length_reward(predict_str: str, max_length: int) -> int:
    # Find all content between <think> and </think> tags (non-greedy match)
    think_contents = re.findall(r'<think>(.*?)</think>', predict_str)
    
    # Sum the lengths of all found think contents
    total_length = sum(len(content) for content in think_contents)

    score = 1 - abs(total_length - max_length)/max_length
    score = 0.0 if score < 0.0 else score
    
    return score

def compute_score(predict_str: str, ground_truth: str, format_weight: float = 0.5) -> Dict[str, float]:
    lenght_score = think_length_reward(predict_str, 4000)
    format_score = (format_reward(predict_str) + lenght_score)/2
    accuracy_score = accuracy_reward(predict_str, ground_truth)
    return {
        "overall": (1 - format_weight) * accuracy_score + format_weight * format_score,
        "format": format_score,
        "accuracy": accuracy_score,
    }

if __name__ == "__main__":
    # 标注数据
    ground_truth = """
    {
        "Entities": {
            "headache": "Symptom",
            "fever": "Symptom"
        },
        "Relationships": [
            ["headache", "Symptom", "caused_by", "Virus", "influenza"]
        ]
    }
    """

    # 预测数据1 - 完全正确
    predict_str1 = "<answer>{\n    \"Entities\": {\n        \"headache\": \"Symptom\",\n        \"fever\": \"Symptom\"\n    },\n    \"Relationships\": [\n        [\"headache\", \"Symptom\", \"caused_by\", \"Virus\", \"influenza\"]\n    ]\n}</answer>"
    print(accuracy_reward(predict_str1, ground_truth))  # 应该返回较高分数
    print(compute_score(predict_str1, ground_truth))

    # 预测数据2 - 部分正确
    predict_str2 = "<answer>{\n    \"Entities\": {\n        \"headache\": \"Symptom\"\n    },\n    \"Relationships\": []\n}</answer>"
    print(accuracy_reward(predict_str2, ground_truth))  # 应该返回中等分数
    print(compute_score(predict_str2, ground_truth))

    # 预测数据3 - 格式错误
    predict_str3 = "<answer>Invalid JSON</answer>"
    print(accuracy_reward(predict_str3, ground_truth))  # 应该返回0.0

    print(compute_score(predict_str3, ground_truth))
    predict_str4 = "<think>fslajldfkjajflajsfejoqiwefjlwjfekasjdflaksdfljaljdsfkasfdjlajfkajsfd</think>\n<answer>Invalid JSON</answer>"
    print(think_length_reward(predict_str4, 70))
