# 🚀 Qwen3-0.6B 树莓派部署 - 快速入门指南

## 📋 前置检查清单

在开始之前，请确保：

- ✅ 树莓派 5 (8GB RAM)
- ✅ Raspberry Pi OS 64-bit 已安装
- ✅ 至少 10GB 可用空间
- ✅ 稳定的网络连接
- ✅ SSH 已启用（推荐）

---

## 🎯 5 分钟快速部署

### Step 1: 训练模型（在 GPU 机器上）

```bash
# 1. 克隆项目
git clone <your-repo>
cd qwen3-finetune

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行微调（大约 4-12 小时，取决于 GPU）
python train_qwen3_fineweb.py

# 4. 模型会自动保存到 ./outputs/qwen3-0.6b-fineweb-edu/gguf/
```

### Step 2: 传输模型到树莓派

```bash
# 在本地机器上执行
scp outputs/qwen3-0.6b-fineweb-edu/gguf/*.gguf \
    pi@raspberrypi.local:/home/pi/models/qwen3-0.6b-q4_k_m.gguf
```

### Step 3: 自动部署（在树莓派上）

```bash
# SSH 连接到树莓派
ssh pi@raspberrypi.local

# 下载部署脚本
wget https://raw.githubusercontent.com/<your-repo>/deploy_raspberry_pi.sh

# 添加执行权限
chmod +x deploy_raspberry_pi.sh

# 运行部署脚本（自动完成所有配置）
./deploy_raspberry_pi.sh
```

### Step 4: 测试推理

```bash
# 方法 1: 命令行测试
~/test_llama.sh "What is artificial intelligence?"

# 方法 2: 启动 HTTP 服务器
~/start_llama.sh

# 方法 3: 使用 C++ 客户端
cd ~/
wget <simple_client.cpp>
make
./simple_client "Hello, AI!"
```

---

## 📊 预期性能

| 指标 | 数值 |
|------|------|
| 首 token 延迟 | ~500-1000ms |
| 生成速度 | 12-20 tokens/s |
| 内存占用 | ~800MB |
| CPU 使用率 | 60-80% |

---

## 🔧 常用命令

### 服务管理

```bash
# 启动服务
sudo systemctl start llama-server

# 停止服务
sudo systemctl stop llama-server

# 查看状态
sudo systemctl status llama-server

# 查看日志
sudo journalctl -u llama-server -f
```

### 性能监控

```bash
# CPU 和内存
htop

# 温度
watch -n 1 vcgencmd measure_temp

# GPU 内存（树莓派）
vcgencmd get_mem arm && vcgencmd get_mem gpu
```

### API 测试

```bash
# 简单测试
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hi!"}],
    "max_tokens": 100
  }'

# 使用 jq 格式化输出
~/test_api.sh "Explain quantum computing"
```

---

## 🐛 故障排除

### 问题 1: 内存不足

```bash
# 增加 swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# 设置 CONF_SWAPSIZE=4096
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 问题 2: 温度过高

```bash
# 检查温度
vcgencmd measure_temp

# 如果 > 70°C:
# 1. 添加风扇
# 2. 改善通风
# 3. 降低线程数: 编辑 ~/start_llama.sh，改 -t 4 为 -t 2
```

### 问题 3: 推理速度慢

```bash
# 优化方案:
# 1. 使用更小的量化（Q4 -> Q2）
# 2. 减小上下文长度
# 3. 启用性能模式
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### 问题 4: 服务无法启动

```bash
# 查看错误日志
sudo journalctl -u llama-server -n 50 --no-pager

# 手动测试
cd ~/llama.cpp
./server -m ~/models/qwen3-0.6b-q4_k_m.gguf --port 8080 -t 4
```

---

## 🌐 远程访问设置

### 方法 1: SSH 隧道（最安全）

```bash
# 在本地机器上执行
ssh -L 8080:localhost:8080 pi@raspberrypi.local

# 然后访问: http://localhost:8080
```

### 方法 2: 局域网访问

```bash
# 在树莓派上查看 IP
hostname -I

# 在同一局域网的设备上访问
# http://<树莓派IP>:8080
```

### 方法 3: Tailscale VPN（推荐）

```bash
# 在树莓派上安装 Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# 在其他设备上也安装 Tailscale
# 然后可以通过 Tailscale IP 访问
```

---

## 📚 进阶配置

### 自定义提示词模板

编辑 `~/Modelfile` 添加系统提示词：

```
SYSTEM """You are a helpful AI assistant specialized in [your domain].
Please provide concise and accurate answers."""
```

### 调整生成参数

```bash
# 在启动脚本中添加参数
./server -m model.gguf \
    --temp 0.8 \           # 创意度（0.0-2.0）
    --top-p 0.95 \         # 采样多样性
    --repeat-penalty 1.1 \ # 减少重复
    --ctx-size 4096        # 更长的上下文
```

### 批量推理

```bash
# 创建批处理脚本
cat > batch_inference.sh << 'EOF'
#!/bin/bash
while IFS= read -r prompt; do
    echo "处理: $prompt"
    ~/test_llama.sh "$prompt" >> results.txt
    echo "---" >> results.txt
done < prompts.txt
EOF

chmod +x batch_inference.sh
```

---

## 🔗 有用的链接

- **llama.cpp 文档**: https://github.com/ggerganov/llama.cpp
- **Qwen3 模型卡**: https://huggingface.co/Qwen/Qwen3-0.6B
- **树莓派官方论坛**: https://forums.raspberrypi.com/
- **FineWeb-Edu**: https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu

---

## 🎓 下一步

1. ✅ **优化性能**: 调整线程数、上下文大小
2. ✅ **集成应用**: 构建 Web UI 或语音助手
3. ✅ **持续学习**: 收集反馈数据进行增量训练
4. ✅ **集群部署**: 多个树莓派负载均衡

---

## 💡 提示

- 首次运行可能需要预热，后续推理会更快
- 定期清理日志避免占满存储：`sudo journalctl --vacuum-time=7d`
- 使用 `screen` 或 `tmux` 保持长时间运行
- 备份重要的模型文件到外部存储

---

**🎉 享受你的本地 AI 助手！**

如有问题，请查阅完整文档或提交 Issue。