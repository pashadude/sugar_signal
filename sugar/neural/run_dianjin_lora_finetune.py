import os
import json
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

MODEL_NAME = "./DianJin-R1-32B"
OUTPUT_DIR = "dianjin_lora_adapter"
LOG_FILE = "dianjin_lora_training.log"

# Load model and tokenizer
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype="auto",
    device_map="auto",
    local_files_only=True
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)

# LoRA config
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)

# Load and preprocess training data
def load_jsonl(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]
    return lines

def csv_2_josn(csv_file, jsonl_file):
    import pandas as pd
    df = pd.read_csv(csv_file)
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            json_line = row.to_json()
            f.write(json_line + "\n")


TRAIN_FILE = csv_2_josn("source_of_truth_sugar.csv")


data = load_jsonl(TRAIN_FILE)
# Expecting each line to have a "text" field
texts = [item["text"] for item in data if "text" in item]
dataset = Dataset.from_dict({"text": texts})

def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512)

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=1,
    per_device_train_batch_size=2,
    logging_dir="./logs",
    logging_steps=10,
    save_steps=50,
    save_total_limit=2,
    report_to="none",
    deepspeed=None,
    fp16=True,
    dataloader_num_workers=4,
    gradient_accumulation_steps=1,
    torch_compile=False,
    ddp_find_unused_parameters=False,
    ddp_backend="nccl",
    # Use all available GPUs
    _n_gpu=1
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# Train and save logs
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

with open(LOG_FILE, "w") as log_f:
    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    log_f.write("Training completed. LoRA adapter weights saved to '{}'.\n".format(OUTPUT_DIR))

print(f"LoRA fine-tuning complete. Adapter weights saved to '{OUTPUT_DIR}'. Training log: '{LOG_FILE}'")