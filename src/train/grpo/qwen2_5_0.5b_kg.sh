set -x

MODEL_PATH=/datadisk/LLaMA-Factory/saves/qwen2.5-0.5B/full/sft  # replace it with your local file path

FORMAT_PROMPT="""You are a helpful AI Assistant that provides well-reasoned and detailed responses. You first think about the reasoning process as an internal monologue and then provide the user with the answer. 
Think for maximum 4000 tokens.
Respond in the following format
<think>...</think><answer>...</answer>"""

python3 -m verl.trainer.main \
    config=examples/config.yaml \
    data.train_files=/datadisk/data/train_new.parquet \
    data.val_files=/datadisk/data/test_new.parquet \
    data.format_prompt="${FORMAT_PROMPT}" \
    worker.actor.model.model_path=${MODEL_PATH} \
    trainer.experiment_name=qwen2_5_0.5b_kg3 \
    trainer.n_gpus_per_node=4
