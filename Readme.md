## LCODR-KE: Long Chain-of-Thought for Drug Repositioning Knowledge Extraction
### 📖 Introduction
This study proposes Long Chain-of-Thought for Drug Repositioning Knowledge Extraction (LCoDR-KE), a lightweight and domain-specific framework to enhance LLMs’ accuracy and adaptability in extracting structured biomedical knowledge for drug repositioning. The framework combines:
- Long chain-of-thought prompting for step-wise reasoning
- Supervised fine-tuning (SFT) and reinforcement learning (GPRO)
- A dual-level reward mechanism (accuracy reward + structural format reward)
- A high-quality drug repositioning corpus (DrugReC) curated from PubMed
Together, these components significantly improve biomedical knowledge extraction, supporting novel indication discovery and drug repositioning research.

### 📂 Repository Contents
- /data/  
  This directory contains training datasets for GRPO (Group Preference Optimization) and SFT (Supervised Fine-Tuning), along with the script for acquiring SFT data from DeepSeek.

- /src/  
  - /train/  
    Includes the implementation of training procedures for both SFT and GRPO.
  - /test/  
    Contains code for model testing and performance evaluation.

### ⚙️ Setup & Usage
1. Environment Setup
``` bash
git clone https://github.com/kang-hongyu/LCoDR-KE.git
cd LCoDR-KE
conda create -n lcodr-ke python=3.10
conda activate lcodr-ke
pip install -r requirements.txt
```

Then download qwen2.5-7B models for training

2. Training - SFT
Run supervised fine-tuning with:
``` bash
sh src/train/sft/run.sh
```

3. Training - GRPO
The reward function is in src/train/grpo/score_function/kg.py
Run GRPO:
``` bash
sh src/train/grpo/qwen2_5_7b_kg.sh
```

4. Inference
``` python
python src/test/eval.py
```


### 📊 Results
Key results are reported in the manuscript, including:
- Entity extraction F1 up to 81.46%
- Triplet extraction F1 up to 69.04%
- Strong generalization on external benchmarks (e.g., BC5CDR) 
- Rivaling larger LLMs (DeepSeek-R1: entity F1=84.64%, triplet F1=69.02%)
