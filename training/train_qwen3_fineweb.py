#!/usr/bin/env python3
"""
Qwen3-0.6B 在 FineWeb-Edu 数据集上的微调脚本
使用 Unsloth 框架进行高效训练
"""

import os
import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel, is_bfloat16_supported

# ============================================================================
# 配置参数
# ============================================================================

# 模型配置
MODEL_NAME = "Qwen/Qwen3-0.6B"
MAX_SEQ_LENGTH = 2048
LOAD_IN_4BIT = True

# LoRA 配置
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", 
                  "gate_proj", "up_proj", "down_proj"]

# 数据集配置
DATASET_NAME = "HuggingFaceFW/fineweb-edu"
DATASET_SPLIT = "train"
NUM_SAMPLES = 100000  # 采样数量，根据资源调整
TEXT_COLUMN = "text"

# 训练配置
OUTPUT_DIR = "./outputs/qwen3-0.6b-fineweb-edu"
NUM_TRAIN_EPOCHS = 1
PER_DEVICE_TRAIN_BATCH_SIZE = 4
GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 2e-4
WEIGHT_DECAY = 0.01
WARMUP_STEPS = 100
LOGGING_STEPS = 10
SAVE_STEPS = 500

# 优化配置
USE_GRADIENT_CHECKPOINTING = True
OPTIM = "adamw_8bit"
FP16 = not is_bfloat16_supported()
BF16 = is_bfloat16_supported()

# ============================================================================
# 主函数
# ============================================================================

def main():
    print("=" * 80)
    print("Qwen3-0.6B FineWeb-Edu 微调脚本")
    print("=" * 80)
    
    # 1. 加载模型和分词器
    print("\n[1/5] 加载模型和分词器...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # 自动检测
        load_in_4bit=LOAD_IN_4BIT,
    )
    print(f"✓ 模型加载完成: {MODEL_NAME}")
    print(f"  - 最大序列长度: {MAX_SEQ_LENGTH}")
    print(f"  - 4-bit 量化: {LOAD_IN_4BIT}")
    
    # 2. 添加 LoRA 适配器
    print("\n[2/5] 添加 LoRA 适配器...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        target_modules=TARGET_MODULES,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
        use_rslora=False,
        loftq_config=None,
    )
    print(f"✓ LoRA 配置完成")
    print(f"  - Rank (r): {LORA_R}")
    print(f"  - Alpha: {LORA_ALPHA}")
    print(f"  - Dropout: {LORA_DROPOUT}")
    print(f"  - 目标模块: {TARGET_MODULES}")
    
    # 打印可训练参数
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  - 可训练参数: {trainable_params:,} / {total_params:,} "
          f"({100 * trainable_params / total_params:.2f}%)")
    
    # 3. 加载数据集
    print(f"\n[3/5] 加载数据集: {DATASET_NAME}...")
    dataset = load_dataset(
        DATASET_NAME,
        split=DATASET_SPLIT,
        streaming=True  # 流式加载节省内存
    )
    
    # 采样指定数量
    dataset = dataset.take(NUM_SAMPLES)
    
    print(f"✓ 数据集加载完成")
    print(f"  - 采样数量: {NUM_SAMPLES:,}")
    
    # 4. 数据预处理
    print("\n[4/5] 准备数据预处理...")
    
    def formatting_func(examples):
        """格式化函数：将文本包装为训练格式"""
        texts = []
        for text in examples[TEXT_COLUMN]:
            # 确保文本不为空
            if text and len(text.strip()) > 0:
                # 添加 EOS token
                formatted_text = text.strip() + tokenizer.eos_token
                texts.append(formatted_text)
        return texts
    
    print("✓ 数据预处理函数准备完成")
    
    # 5. 配置训练参数
    print("\n[5/5] 配置训练参数...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=PER_DEVICE_TRAIN_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        warmup_steps=WARMUP_STEPS,
        num_train_epochs=NUM_TRAIN_EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=FP16,
        bf16=BF16,
        logging_steps=LOGGING_STEPS,
        optim=OPTIM,
        weight_decay=WEIGHT_DECAY,
        lr_scheduler_type="linear",
        seed=42,
        save_steps=SAVE_STEPS,
        save_total_limit=3,
        logging_dir=f"{OUTPUT_DIR}/logs",
        report_to="none",  # 可改为 "wandb" 或 "tensorboard"
    )
    
    # 创建训练器
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field=TEXT_COLUMN,
        max_seq_length=MAX_SEQ_LENGTH,
        formatting_func=formatting_func,
        args=training_args,
        packing=False,  # Unsloth 自动优化
    )
    
    print("✓ 训练器配置完成")
    print(f"  - Batch size: {PER_DEVICE_TRAIN_BATCH_SIZE}")
    print(f"  - Gradient accumulation: {GRADIENT_ACCUMULATION_STEPS}")
    print(f"  - Effective batch size: {PER_DEVICE_TRAIN_BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS}")
    print(f"  - Learning rate: {LEARNING_RATE}")
    print(f"  - Epochs: {NUM_TRAIN_EPOCHS}")
    print(f"  - Optimizer: {OPTIM}")
    print(f"  - FP16: {FP16}, BF16: {BF16}")
    
    # 开始训练
    print("\n" + "=" * 80)
    print("开始训练...")
    print("=" * 80 + "\n")
    
    gpu_stats = torch.cuda.get_device_properties(0)
    start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
    max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
    print(f"GPU: {gpu_stats.name}")
    print(f"GPU 内存: {start_gpu_memory} GB / {max_memory} GB")
    print()
    
    trainer_stats = trainer.train()
    
    # 训练完成
    print("\n" + "=" * 80)
    print("训练完成!")
    print("=" * 80)
    
    used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
    used_memory_for_lora = round(used_memory - start_gpu_memory, 3)
    used_percentage = round(used_memory / max_memory * 100, 3)
    
    print(f"\n训练统计:")
    print(f"  - 峰值内存使用: {used_memory} GB")
    print(f"  - LoRA 额外内存: {used_memory_for_lora} GB")
    print(f"  - 内存使用率: {used_percentage}%")
    
    # 保存模型
    print(f"\n保存模型到: {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("✓ 模型保存完成")
    
    # 保存为 GGUF 格式（用于树莓派部署）
    print("\n转换为 GGUF 格式...")
    try:
        model.save_pretrained_gguf(
            OUTPUT_DIR + "/gguf",
            tokenizer,
            quantization_method="q4_k_m"  # 推荐用于树莓派
        )
        print("✓ GGUF 模型保存完成")
        print(f"  位置: {OUTPUT_DIR}/gguf")
        print(f"  量化方法: Q4_K_M (推荐用于树莓派)")
    except Exception as e:
        print(f"⚠ GGUF 转换失败: {e}")
        print("  可以稍后使用 llama.cpp 手动转换")
    
    print("\n" + "=" * 80)
    print("全部完成! 🎉")
    print("=" * 80)
    print(f"\n模型保存位置: {OUTPUT_DIR}")
    print("\n下一步:")
    print("1. 在树莓派上安装 llama.cpp 或 Ollama")
    print("2. 将 GGUF 模型传输到树莓派")
    print("3. 运行推理测试")


if __name__ == "__main__":
    main()