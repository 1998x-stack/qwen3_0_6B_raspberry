# Qwen3-0.6B 树莓派部署完整指南

## 目录
1. [硬件需求](#1-硬件需求)
2. [软件环境准备](#2-软件环境准备)
3. [模型转换与传输](#3-模型转换与传输)
4. [部署方案对比](#4-部署方案对比)
5. [方案A: llama.cpp 部署](#5-方案a-llamacpp-部署)
6. [方案B: Ollama 部署](#6-方案b-ollama-部署)
7. [性能优化](#7-性能优化)
8. [常见问题](#8-常见问题)

---

## 1. 硬件需求

### 1.1 必需设备清单

| 设备 | 规格 | 价格（USD） | 购买链接 | 说明 |
|------|------|------------|---------|------|
| **树莓派 5** | 8GB RAM 版本 | $80 | [官方店](https://www.raspberrypi.com/products/raspberry-pi-5/) | **强烈推荐** 8GB 版本 |
| **电源适配器** | 27W USB-C PD | $12 | 树莓派官方 | 必须使用官方或认证电源 |
| **MicroSD 卡** | 128GB Class 10/A2 | $15 | Amazon / 京东 | 推荐 SanDisk Extreme |
| **散热器** | 主动散热风扇 | $8 | 树莓派官方 | 长时间运行必备 |
| **机箱** | 官方机箱 | $10 | 树莓派官方 | 可选，但推荐 |

**总成本**: ~$125 USD

### 1.2 可选设备

| 设备 | 用途 | 价格 |
|------|------|------|
| NVMe SSD 适配器 | 更快的存储速度 | $15 |
| NVMe SSD (256GB) | 替代 MicroSD | $30 |
| 以太网线 | 稳定网络连接 | $5 |

**推荐配置总成本**: ~$175 USD

### 1.3 为什么选择树莓派 5?

✅ **足够的内存**: 8GB RAM 可运行 Q4/Q8 量化的 0.6B 模型  
✅ **性能提升**: CPU 性能比树莓派 4 提升 2-3 倍  
✅ **ARM 优化**: 新版 llama.cpp 对 ARM64 优化良好  
✅ **低功耗**: 持续运行功耗仅 5-8W  
✅ **社区支持**: 大量教程和优化方案  

### 1.4 不推荐的设备

❌ **树莓派 4 (4GB)**: 内存不足，容易 OOM  
❌ **树莓派 Zero**: 性能太弱  
❌ **树莓派 3**: 不支持 64 位系统（部分模型需要）  

---

## 2. 软件环境准备

### 2.1 操作系统安装

#### Step 1: 下载 Raspberry Pi OS

推荐使用 **Raspberry Pi OS (64-bit) Lite** 或 **Desktop** 版本

```bash
# 下载地址
https://www.raspberrypi.com/software/operating-systems/

# 推荐版本
Raspberry Pi OS Lite (64-bit) - 最新版
```

#### Step 2: 烧录系统

使用 **Raspberry Pi Imager** 工具：

1. 下载 Imager: https://www.raspberrypi.com/software/
2. 选择系统镜像
3. 选择 SD 卡
4. **重要**: 点击设置图标 ⚙️
   - 启用 SSH
   - 设置用户名密码
   - 配置 WiFi（可选）
5. 点击 "Write" 烧录

#### Step 3: 首次启动

```bash
# SSH 连接（替换为你的树莓派 IP）
ssh pi@raspberrypi.local
# 或
ssh pi@192.168.1.xxx

# 首次登录后更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y \
    build-essential \
    git \
    cmake \
    wget \
    curl \
    htop \
    vim \
    python3-pip
```

### 2.2 系统优化

```bash
# 1. 增加 swap 空间（重要！）
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# 修改 CONF_SWAPSIZE=2048 (2GB)
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 2. 启用性能模式（可选）
sudo raspi-config
# 选择 Performance Options -> CPU Governor -> Performance

# 3. 禁用不必要的服务
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon

# 4. 检查系统信息
uname -a  # 确认是 aarch64
free -h   # 确认内存和 swap
```

---

## 3. 模型转换与传输

### 3.1 模型格式说明

| 格式 | 用途 | 大小 (0.6B) | 推理速度 |
|------|------|-------------|---------|
| **PyTorch (.safetensors)** | 原始训练格式 | ~1.2GB | 慢 ❌ |
| **GGUF Q4_K_M** | llama.cpp 推荐 | ~400MB | 快 ✅ |
| **GGUF Q8_0** | 高精度 | ~650MB | 中等 ⚡ |
| **GGUF Q2_K** | 极小尺寸 | ~250MB | 快但质量降低 ⚠️ |

**推荐**: Q4_K_M（质量和速度的最佳平衡）

### 3.2 方法 1: 训练时直接转换（推荐）

在微调脚本中已包含：

```python
# 训练脚本会自动生成 GGUF
model.save_pretrained_gguf(
    OUTPUT_DIR + "/gguf",
    tokenizer,
    quantization_method="q4_k_m"
)
```

### 3.3 方法 2: 使用 llama.cpp 转换

```bash
# 1. 克隆 llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# 2. 编译（在 x86 机器上）
make

# 3. 转换 PyTorch 模型为 GGUF
python3 convert.py /path/to/your/model --outfile qwen3-0.6b-f16.gguf

# 4. 量化为 Q4_K_M
./quantize qwen3-0.6b-f16.gguf qwen3-0.6b-q4_k_m.gguf Q4_K_M
```

### 3.4 传输模型到树莓派

#### 方法 A: SCP 传输

```bash
# 在本地机器上执行
scp qwen3-0.6b-q4_k_m.gguf pi@raspberrypi.local:/home/pi/models/

# 或使用压缩传输（更快）
tar -czf model.tar.gz qwen3-0.6b-q4_k_m.gguf
scp model.tar.gz pi@raspberrypi.local:/home/pi/
ssh pi@raspberrypi.local "cd /home/pi && tar -xzf model.tar.gz"
```

#### 方法 B: USB 传输

1. 将模型文件复制到 U盘
2. U盘插入树莓派
3. 挂载并复制

```bash
# 树莓派上执行
sudo mount /dev/sda1 /mnt
cp /mnt/qwen3-0.6b-q4_k_m.gguf /home/pi/models/
sudo umount /mnt
```

#### 方法 C: Hugging Face Hub

```bash
# 上传到 Hugging Face（私有仓库）
huggingface-cli upload your-username/qwen3-0.6b-finetuned ./gguf

# 在树莓派上下载
huggingface-cli download your-username/qwen3-0.6b-finetuned \
    --local-dir /home/pi/models/
```

---

## 4. 部署方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **llama.cpp** | • 原生 C++ 性能<br>• 完全控制<br>• 无额外依赖 | • 需要编译<br>• API 需要自己实现 | ⭐⭐⭐⭐⭐ |
| **Ollama** | • 一键安装<br>• OpenAI 兼容 API<br>• 易于使用 | • 稍微重量级<br>• 更新较慢 | ⭐⭐⭐⭐ |
| **llama-cpp-python** | • Python 接口<br>• 易于集成 | • 依赖较多<br>• 内存占用高 | ⭐⭐⭐ |

**推荐**: 生产环境用 **llama.cpp**，快速测试用 **Ollama**

---

## 5. 方案A: llama.cpp 部署

### 5.1 编译 llama.cpp

```bash
# SSH 连接到树莓派
ssh pi@raspberrypi.local

# 创建工作目录
mkdir -p ~/ai
cd ~/ai

# 克隆仓库
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# 编译（ARM64 优化）
make -j4

# 验证编译成功
./main --version
```

### 5.2 测试推理

```bash
# 创建模型目录
mkdir -p ~/models

# 假设模型已传输到 ~/models/qwen3-0.6b-q4_k_m.gguf

# 交互式测试
./main -m ~/models/qwen3-0.6b-q4_k_m.gguf \
    -n 128 \
    -p "What is the capital of France?" \
    --color

# 查看详细信息（verbose）
./main -m ~/models/qwen3-0.6b-q4_k_m.gguf \
    -n 128 \
    -p "Explain quantum computing in simple terms." \
    --verbose
```

### 5.3 性能优化参数

```bash
# 推荐配置（树莓派 5）
./main -m ~/models/qwen3-0.6b-q4_k_m.gguf \
    -t 4 \              # 使用 4 个线程（树莓派 5 有 4 个核心）
    -c 2048 \           # 上下文长度
    -n 256 \            # 生成最多 256 tokens
    --temp 0.7 \        # 温度参数
    --top-p 0.9 \       # Top-p 采样
    --repeat-penalty 1.1 \  # 重复惩罚
    -p "你的提示词"
```

### 5.4 启动 HTTP 服务器

```bash
# 启动服务器（监听 8080 端口）
./server -m ~/models/qwen3-0.6b-q4_k_m.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    -t 4 \
    -c 2048

# 测试 API
curl http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }'
```

---

## 6. 方案B: Ollama 部署

### 6.1 安装 Ollama

```bash
# 一键安装（官方脚本）
curl -fsSL https://ollama.com/install.sh | sh

# 或手动安装
wget https://github.com/ollama/ollama/releases/download/v0.1.26/ollama-linux-arm64
sudo mv ollama-linux-arm64 /usr/local/bin/ollama
sudo chmod +x /usr/local/bin/ollama
```

### 6.2 创建 Modelfile

```bash
# 创建 Modelfile
cat > ~/Modelfile << 'EOF'
FROM /home/pi/models/qwen3-0.6b-q4_k_m.gguf

TEMPLATE """{{ .System }}
{{ .Prompt }}"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

SYSTEM """You are Qwen3, a helpful AI assistant fine-tuned on educational content."""
EOF
```

### 6.3 导入模型

```bash
# 创建 Ollama 模型
ollama create qwen3-finetuned -f ~/Modelfile

# 列出模型
ollama list

# 测试模型
ollama run qwen3-finetuned "What is machine learning?"
```

### 6.4 启动服务

```bash
# Ollama 自动在后台运行，默认端口 11434

# 测试 API
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3-finetuned",
  "prompt": "Explain neural networks.",
  "stream": false
}'
```

---

## 7. 性能优化

### 7.1 预期性能

**树莓派 5 (8GB) + Qwen3-0.6B Q4_K_M**

| 指标 | 性能 |
|------|------|
| 提示词处理速度 | ~60 tokens/s |
| 生成速度 | 12-20 tokens/s |
| 首 token 延迟 | 500-1000ms |
| 内存占用 | ~800MB |
| CPU 占用 | 60-80% |
| 温度 | 55-65°C（带风扇） |

### 7.2 调优建议

#### A. 散热优化

```bash
# 监控温度
watch -n 1 'vcgencmd measure_temp'

# 如果温度 > 70°C，考虑：
# 1. 添加散热片
# 2. 安装主动风扇
# 3. 改善机箱通风
```

#### B. 内存管理

```bash
# 监控内存
htop

# 如果内存不足：
# 1. 使用更小的量化（Q4 -> Q2）
# 2. 减小上下文长度（-c 1024）
# 3. 关闭不必要的服务
```

#### C. CPU 优化

```bash
# 设置性能模式
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 查看频率
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
```

### 7.3 批量推理优化

对于批量任务，使用批处理模式：

```bash
# 创建输入文件
cat > prompts.txt << EOF
What is AI?
Explain deep learning.
What is NLP?
EOF

# 批处理
while read -r prompt; do
    ./main -m ~/models/qwen3-0.6b-q4_k_m.gguf \
        -n 100 -p "$prompt" >> results.txt
done < prompts.txt
```

---

## 8. 常见问题

### Q1: 树莓派运行模型很慢怎么办？

**A**: 
1. 确认使用 Q4_K_M 或更小量化
2. 减小上下文长度 (`-c 1024`)
3. 检查是否启用性能模式
4. 确保散热良好

### Q2: 内存不足（OOM）怎么办？

**A**:
1. 增加 swap 空间到 4GB
2. 使用 Q2_K 量化
3. 关闭桌面环境（改用 SSH）
4. 减小线程数 (`-t 2`)

### Q3: 模型输出质量不佳？

**A**:
1. 调整温度参数 (`--temp 0.5-1.0`)
2. 使用 Q8_0 量化（质量更好）
3. 增加上下文长度
4. 检查微调数据质量

### Q4: 如何实现自动启动？

**A**:
```bash
# 创建 systemd 服务
sudo nano /etc/systemd/system/llama-server.service

# 内容:
[Unit]
Description=Llama.cpp Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/llama.cpp
ExecStart=/home/pi/llama.cpp/server -m /home/pi/models/qwen3-0.6b-q4_k_m.gguf --host 0.0.0.0 --port 8080 -t 4
Restart=always

[Install]
WantedBy=multi-user.target

# 启用服务
sudo systemctl enable llama-server
sudo systemctl start llama-server
sudo systemctl status llama-server
```

### Q5: 如何远程访问？

**A**:
```bash
# 方案 1: SSH 隧道
ssh -L 8080:localhost:8080 pi@raspberrypi.local

# 方案 2: 配置防火墙
sudo ufw allow 8080

# 方案 3: Tailscale VPN（推荐）
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

---

## 9. 完整部署脚本

详见后续 artifacts 中的自动化部署脚本。

---

## 10. 参考资源

- **llama.cpp**: https://github.com/ggerganov/llama.cpp
- **Ollama**: https://ollama.com/
- **树莓派官方**: https://www.raspberrypi.com/
- **Qwen3 模型**: https://huggingface.co/Qwen/Qwen3-0.6B
- **优化指南**: https://www.raspberrypi.com/documentation/computers/config_txt.html

---

**祝部署成功！🎉**