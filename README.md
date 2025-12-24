# Qwen3-0.6B FineWeb-Edu 微调与树莓派部署完整项目

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-C51A4A.svg)](https://www.raspberrypi.com/)

> 🎯 **目标**: 在 FineWeb-Edu 数据集上微调 Qwen3-0.6B 模型，并部署到树莓派 5 上运行

---

## 📖 项目概述

本项目提供了一套完整的解决方案，从模型微调到边缘设备部署：

1. ✅ 使用 **Unsloth** 在 FineWeb-Edu 上微调 Qwen3-0.6B
2. ✅ 自动转换为 GGUF 格式（树莓派优化）
3. ✅ 一键部署到树莓派 5
4. ✅ 提供多种推理接口（CLI、HTTP API、Web UI）

### 🌟 特点

- **高效训练**: 使用 Unsloth 框架，速度提升 2-5 倍，内存减少 80%
- **质量数据**: FineWeb-Edu 1.3T tokens 教育级数据集
- **边缘优化**: 针对 ARM64 架构优化，运行流畅
- **易于部署**: 全自动化脚本，5 分钟完成部署
- **多种接口**: CLI、REST API、Web UI 任选

---

## 📁 项目结构

```
qwen3-raspberry-pi-deployment/
├── README.md                          # 本文件
├── QUICKSTART.md                      # 快速入门指南
├── requirements.txt                   # Python 依赖
│
├── training/                          # 训练相关
│   ├── train_qwen3_fineweb.py        # 主训练脚本
│   └── data_exploration.ipynb         # 数据探索（可选）
│
├── deployment/                        # 部署相关
│   ├── deploy_raspberry_pi.sh        # 自动部署脚本
│   ├── start_llama.sh                # 快速启动
│   ├── test_llama.sh                 # 测试脚本
│   └── test_api.sh                   # API 测试
│
├── clients/                           # 客户端
│   ├── simple_client.cpp             # C++ HTTP 客户端
│   ├── Makefile                      # 编译配置
│   └── web_ui.py                     # Python Web 界面
│
└── docs/                              # 文档
    ├── FINEWEB_EDU_REPORT.md         # 数据集调查
    ├── FRAMEWORK_COMPARISON.md        # 框架对比
    ├── DEPLOYMENT_GUIDE.md            # 部署详细指南
    └── TROUBLESHOOTING.md             # 故障排除
```

---

## 🚀 快速开始

### 阶段 1: 模型微调（GPU 服务器）

```bash
# 1. 克隆仓库
git clone <repository-url>
cd qwen3-raspberry-pi-deployment

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 开始训练
cd training
python train_qwen3_fineweb.py
```

**训练时间**: 根据 GPU 性能，约 4-12 小时

**输出**: 
- PyTorch 模型: `./outputs/qwen3-0.6b-fineweb-edu/`
- GGUF 模型: `./outputs/qwen3-0.6b-fineweb-edu/gguf/*.gguf`

### 阶段 2: 传输模型

```bash
# 方法 1: SCP 传输
scp outputs/qwen3-0.6b-fineweb-edu/gguf/*.gguf \
    pi@raspberrypi.local:/home/pi/models/qwen3-0.6b-q4_k_m.gguf

# 方法 2: 上传到 Hugging Face（推荐）
huggingface-cli upload your-username/qwen3-0.6b-finetuned \
    outputs/qwen3-0.6b-fineweb-edu/gguf
```

### 阶段 3: 树莓派部署

```bash
# SSH 连接到树莓派
ssh pi@raspberrypi.local

# 下载并运行部署脚本
wget <deploy_script_url>
chmod +x deploy_raspberry_pi.sh
./deploy_raspberry_pi.sh
```

**部署时间**: 约 15-20 分钟（包括编译）

### 阶段 4: 测试运行

```bash
# 命令行测试
~/test_llama.sh "What is machine learning?"

# 启动 HTTP 服务
~/start_llama.sh

# 启动 Web UI
python3 web_ui.py
# 访问: http://raspberrypi.local:5000
```

---

## 📊 性能指标

### 训练性能（Unsloth on GPU）

| GPU 型号 | 训练速度 | 内存占用 | 时间（10k steps） |
|----------|----------|----------|-------------------|
| RTX 4090 | ~8000 tokens/s | ~8GB | ~3h |
| RTX 3090 | ~6000 tokens/s | ~10GB | ~4h |
| A100 80GB | ~12000 tokens/s | ~12GB | ~2h |
| T4 (Colab) | ~2000 tokens/s | ~15GB | ~12h |

### 推理性能（树莓派 5）

| 指标 | Q4_K_M | Q8_0 |
|------|--------|------|
| 首 token 延迟 | 500-800ms | 700-1000ms |
| 生成速度 | 15-20 tokens/s | 12-16 tokens/s |
| 内存占用 | ~800MB | ~1.2GB |
| 模型大小 | 400MB | 650MB |

---

## 🛠️ 系统要求

### 训练环境

- **GPU**: NVIDIA GPU with CUDA 11.8+（至少 8GB VRAM）
- **RAM**: 16GB+
- **存储**: 50GB+
- **系统**: Linux / Windows with WSL2

### 部署环境

- **硬件**: Raspberry Pi 5 (8GB RAM) **（强烈推荐）**
- **存储**: 128GB MicroSD / NVMe SSD
- **系统**: Raspberry Pi OS 64-bit
- **散热**: 主动散热风扇
- **电源**: 27W USB-C PD 电源

---

## 📚 详细文档

| 文档 | 说明 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 5 分钟快速入门 |
| [FINEWEB_EDU_REPORT.md](docs/FINEWEB_EDU_REPORT.md) | FineWeb-Edu 数据集详解 |
| [FRAMEWORK_COMPARISON.md](docs/FRAMEWORK_COMPARISON.md) | 微调框架对比 |
| [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | 完整部署指南 |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 常见问题解决 |

---

## 🔧 配置选项

### 训练配置

编辑 `training/train_qwen3_fineweb.py`:

```python
# 数据量调整
NUM_SAMPLES = 100000  # 增加以获得更好效果

# LoRA 参数
LORA_R = 16           # 增加以提高容量
LORA_ALPHA = 32       # 通常为 2*r

# 训练参数
LEARNING_RATE = 2e-4  # 降低以提高稳定性
NUM_TRAIN_EPOCHS = 1  # 增加以充分训练
```

### 部署配置

编辑 `deployment/deploy_raspberry_pi.sh`:

```bash
# 推理参数
NUM_THREADS=4         # CPU 线程数
CONTEXT_SIZE=2048     # 上下文长度
SERVER_PORT=8080      # HTTP 服务端口
```

---

## 🎯 使用示例

### Python API 客户端

```python
import requests

response = requests.post('http://raspberrypi.local:8080/v1/chat/completions',
    json={
        'messages': [
            {'role': 'user', 'content': 'Explain quantum computing'}
        ],
        'max_tokens': 200
    }
)

print(response.json()['choices'][0]['message']['content'])
```

### C++ 客户端

```bash
cd clients
make
./simple_client "What is deep learning?"
```

### Curl 命令

```bash
curl http://raspberrypi.local:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

---

## 🐛 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 内存不足 | 增加 swap 到 4GB，使用 Q2_K 量化 |
| 温度过高 | 添加风扇，改善散热 |
| 推理慢 | 减少线程数，启用性能模式 |
| 服务无法启动 | 检查模型路径，查看日志 |

详细排查请参考 [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- **Qwen Team**: 提供优秀的 Qwen3 模型
- **Hugging Face**: FineWeb-Edu 数据集和生态
- **Unsloth Team**: 高效的微调框架
- **llama.cpp**: 强大的推理引擎
- **Raspberry Pi Foundation**: 优秀的硬件平台

---

## 📞 联系方式

- **Issues**: 请在 GitHub 提交 Issue
- **Discussions**: 欢迎在 Discussions 中交流
- **Email**: your-email@example.com

---

## 🗺️ 路线图

- [x] 基础微调流程
- [x] 树莓派部署
- [x] Web UI 界面
- [ ] 语音输入/输出
- [ ] 多模型支持
- [ ] 分布式推理
- [ ] 模型量化优化
- [ ] Docker 容器化

---

## 📈 更新日志

### v1.0.0 (2025-01-xx)
- ✅ 初始版本发布
- ✅ 完整的训练和部署流程
- ✅ 多种客户端支持

---

**⭐ 如果觉得有用，请给个 Star！**

---

Made with ❤️ for the AI and Raspberry Pi community