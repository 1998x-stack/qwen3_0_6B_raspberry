# 🔧 故障排除完整指南

本文档列出了 Qwen3-0.6B 树莓派部署过程中可能遇到的所有问题及其解决方案。

---

## 📋 目录

1. [训练阶段问题](#1-训练阶段问题)
2. [模型转换问题](#2-模型转换问题)
3. [传输问题](#3-传输问题)
4. [编译问题](#4-编译问题)
5. [运行时问题](#5-运行时问题)
6. [性能问题](#6-性能问题)
7. [网络问题](#7-网络问题)
8. [系统问题](#8-系统问题)

---

## 1. 训练阶段问题

### ❌ 问题: CUDA Out of Memory (OOM)

**症状**:
```
RuntimeError: CUDA out of memory. Tried to allocate X.XX MiB
```

**原因**:
- GPU 内存不足
- Batch size 太大
- 模型加载占用过多内存

**解决方案**:

```python
# 方案 1: 减小 batch size
PER_DEVICE_TRAIN_BATCH_SIZE = 2  # 从 4 改为 2
GRADIENT_ACCUMULATION_STEPS = 8  # 从 4 改为 8

# 方案 2: 启用梯度检查点
USE_GRADIENT_CHECKPOINTING = True

# 方案 3: 使用更激进的量化
LOAD_IN_4BIT = True  # 启用 4-bit 量化

# 方案 4: 减小序列长度
MAX_SEQ_LENGTH = 1024  # 从 2048 改为 1024
```

### ❌ 问题: Unsloth 安装失败

**症状**:
```
ERROR: Failed building wheel for unsloth
```

**解决方案**:

```bash
# 方案 1: 使用预编译版本
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# 方案 2: 检查 CUDA 版本
nvidia-smi
# 然后安装对应的 PyTorch 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 方案 3: 使用 conda
conda create -n unsloth python=3.10
conda activate unsloth
conda install pytorch pytorch-cuda=11.8 -c pytorch -c nvidia
pip install unsloth
```

### ❌ 问题: 数据加载太慢

**症状**:
- 训练开始前等待很久
- 数据预处理占用大量时间

**解决方案**:

```python
# 使用流式加载
dataset = load_dataset(
    DATASET_NAME,
    split=DATASET_SPLIT,
    streaming=True  # 关键！
)

# 减少采样数量
NUM_SAMPLES = 50000  # 从 100000 降低

# 使用缓存
dataset = dataset.cache()
```

---

## 2. 模型转换问题

### ❌ 问题: GGUF 转换失败

**症状**:
```
AttributeError: 'FastLanguageModel' object has no attribute 'save_pretrained_gguf'
```

**原因**:
- Unsloth 版本过旧
- llama.cpp 不兼容

**解决方案**:

```bash
# 更新 Unsloth
pip install --upgrade unsloth

# 手动使用 llama.cpp 转换
cd ~/llama.cpp

# 1. 转换为 FP16 GGUF
python convert.py /path/to/pytorch/model --outfile model-f16.gguf

# 2. 量化
./quantize model-f16.gguf model-q4_k_m.gguf Q4_K_M
```

### ❌ 问题: 量化后质量下降严重

**症状**:
- 模型输出不连贯
- 重复内容过多
- 回答质量明显下降

**解决方案**:

```bash
# 使用更高精度的量化
./quantize model-f16.gguf model-q8_0.gguf Q8_0  # 从 Q4 升到 Q8

# 或使用混合量化
./quantize model-f16.gguf model-q5_k_m.gguf Q5_K_M
```

---

## 3. 传输问题

### ❌ 问题: SCP 传输速度慢

**症状**:
- 传输 400MB 需要 30+ 分钟
- 连接不稳定

**解决方案**:

```bash
# 方案 1: 使用压缩传输
tar -czf model.tar.gz *.gguf
scp -C model.tar.gz pi@raspberrypi.local:~/  # -C 启用压缩

# 方案 2: 使用 rsync（更快，可断点续传）
rsync -avz --progress model.gguf pi@raspberrypi.local:~/models/

# 方案 3: 限速但稳定
scp -l 8000 model.gguf pi@raspberrypi.local:~/  # 限速 1MB/s
```

### ❌ 问题: SSH 连接被拒绝

**症状**:
```
ssh: connect to host raspberrypi.local port 22: Connection refused
```

**解决方案**:

```bash
# 1. 检查 SSH 服务
sudo systemctl status ssh
sudo systemctl start ssh
sudo systemctl enable ssh

# 2. 检查防火墙
sudo ufw allow 22

# 3. 使用 IP 地址而非主机名
ssh pi@192.168.1.xxx

# 4. 查找树莓派 IP
# 在树莓派上执行:
hostname -I

# 或在路由器管理界面查看
```

---

## 4. 编译问题

### ❌ 问题: llama.cpp 编译失败

**症状**:
```
make: *** [main] Error 1
```

**解决方案**:

```bash
# 1. 更新编译工具
sudo apt update
sudo apt install -y build-essential cmake git

# 2. 清理后重新编译
make clean
make -j4

# 3. 如果仍然失败，逐个编译
make main
make server

# 4. 检查依赖
gcc --version  # 应该 >= 7.0
cmake --version  # 应该 >= 3.12
```

### ❌ 问题: 缺少依赖库

**症状**:
```
fatal error: curl/curl.h: No such file or directory
```

**解决方案**:

```bash
# 安装缺失的开发库
sudo apt install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    pkg-config
```

---

## 5. 运行时问题

### ❌ 问题: 内存不足（OOM）

**症状**:
```
Killed
```
或
```
Cannot allocate memory
```

**诊断**:
```bash
# 检查内存使用
free -h
# 检查 OOM killer 日志
dmesg | grep -i "out of memory"
```

**解决方案**:

```bash
# 方案 1: 增加 swap
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=4096/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 方案 2: 使用更小的模型
# 使用 Q2_K 而非 Q4_K_M

# 方案 3: 减小上下文长度
./main -m model.gguf -c 1024  # 从 2048 降到 1024

# 方案 4: 减少线程数
./main -m model.gguf -t 2  # 从 4 降到 2

# 方案 5: 关闭桌面环境（仅保留 SSH）
sudo systemctl set-default multi-user.target
sudo reboot
```

### ❌ 问题: 模型加载失败

**症状**:
```
error loading model: unexpected tensor dtype
```

**解决方案**:

```bash
# 1. 检查模型文件完整性
sha256sum model.gguf
ls -lh model.gguf  # 检查大小是否正常

# 2. 重新下载/传输模型

# 3. 检查 llama.cpp 版本
cd ~/llama.cpp
git pull
make clean && make -j4

# 4. 使用 file 命令检查模型
file model.gguf
```

### ❌ 问题: 服务启动后无响应

**症状**:
- `systemctl status llama-server` 显示 active
- 但无法连接到端口

**诊断**:

```bash
# 检查进程
ps aux | grep server

# 检查端口
netstat -tuln | grep 8080
# 或
ss -tuln | grep 8080

# 检查日志
sudo journalctl -u llama-server -n 50
```

**解决方案**:

```bash
# 1. 检查防火墙
sudo ufw status
sudo ufw allow 8080

# 2. 手动启动调试
cd ~/llama.cpp
./server -m ~/models/qwen3-0.6b-q4_k_m.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --verbose  # 查看详细日志

# 3. 检查是否端口被占用
lsof -i :8080
```

---

## 6. 性能问题

### ❌ 问题: 推理速度太慢（< 5 tokens/s）

**诊断**:

```bash
# 检查 CPU 使用率
htop

# 检查温度
vcgencmd measure_temp

# 检查 CPU 频率
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
```

**解决方案**:

```bash
# 方案 1: 启用性能模式
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 方案 2: 降低散热阻碍
# - 检查风扇是否工作
# - 清理灰尘
# - 改善通风

# 方案 3: 优化运行参数
./server -m model.gguf \
    -t 4 \                    # 使用所有 CPU 核心
    --batch-size 512 \        # 增大批处理
    --threads-batch 4 \       # 批处理线程数
    --mlock                   # 锁定内存

# 方案 4: 使用更小的量化
# Q4_K_M -> Q2_K

# 方案 5: 减小上下文
# -c 2048 -> -c 1024
```

### ❌ 问题: CPU 温度过高（> 75°C）

**症状**:
```bash
vcgencmd measure_temp
# temp=80.0'C  # 危险！
```

**解决方案**:

```bash
# 方案 1: 添加散热
# - 安装主动风扇（必须）
# - 添加散热片
# - 改善机箱通风

# 方案 2: 降低负载
# 减少线程数: -t 2
# 降低频率（不推荐）

# 方案 3: 启用节流保护
# 编辑 /boot/config.txt
sudo nano /boot/config.txt
# 添加:
# temp_soft_limit=70

# 方案 4: 监控温度
watch -n 1 'vcgencmd measure_temp && vcgencmd get_throttled'

# 如果看到 throttled=0x50000
# 说明已经降频，必须改善散热！
```

---

## 7. 网络问题

### ❌ 问题: 无法通过局域网访问

**症状**:
- localhost 可以访问
- 但局域网其他设备无法访问

**解决方案**:

```bash
# 1. 确认服务监听所有接口
# 在启动命令中使用 --host 0.0.0.0
./server --host 0.0.0.0 --port 8080

# 2. 检查防火墙
sudo ufw status
sudo ufw allow 8080

# 3. 测试连通性
# 在树莓派上:
netstat -tuln | grep 8080

# 在其他设备上:
ping raspberrypi.local
telnet raspberrypi.local 8080

# 4. 查看树莓派 IP
hostname -I
```

### ❌ 问题: 远程访问延迟高

**症状**:
- 响应时间 > 5 秒
- 频繁超时

**解决方案**:

```bash
# 1. 使用有线连接而非 WiFi
# WiFi 延迟通常 5-20ms
# 有线延迟通常 1-3ms

# 2. 检查网络质量
ping raspberrypi.local
# 理想情况: < 10ms

# 3. 使用 VPN (Tailscale)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# 4. 优化 HTTP 连接
# 使用 HTTP/2 或 WebSocket
```

---

## 8. 系统问题

### ❌ 问题: SD 卡写入速度慢

**症状**:
- 系统响应慢
- 日志显示 I/O 错误

**解决方案**:

```bash
# 1. 测试 SD 卡速度
sudo hdparm -t /dev/mmcblk0
# 应该 > 20 MB/s

# 2. 使用更快的 SD 卡
# 推荐: SanDisk Extreme (A2, UHS-I)

# 3. 迁移到 NVMe SSD
# 购买 NVMe 适配器 + SSD
# 使用 Raspberry Pi Imager 烧录到 SSD

# 4. 减少日志写入
# 编辑 systemd 服务
StandardOutput=null
StandardError=null
```

### ❌ 问题: 系统不稳定/随机重启

**诊断**:

```bash
# 检查电源
vcgencmd get_throttled
# 如果返回非 0，说明电源不足

# 检查系统日志
dmesg | tail -50
sudo journalctl -p 3 -xb  # 查看错误日志
```

**解决方案**:

```bash
# 方案 1: 使用官方电源（27W）
# 或至少 3A 的 5V 电源

# 方案 2: 禁用 USB 设备省电模式
# 编辑 /boot/config.txt
sudo nano /boot/config.txt
# 添加:
# usb_max_current_enable=1

# 方案 3: 降低超频（如果有）
# 移除 config.txt 中的超频设置

# 方案 4: 检查内存
# 运行内存测试
sudo apt install memtester
sudo memtester 1G 1
```

---

## 🔍 调试技巧

### 1. 详细日志模式

```bash
# llama.cpp 详细日志
./server -m model.gguf --verbose --log-file server.log

# systemd 详细日志
sudo journalctl -u llama-server -f --since "5 minutes ago"

# 系统级日志
dmesg -T | tail -50
```

### 2. 性能分析

```bash
# CPU 性能分析
top -H -p $(pgrep server)

# 内存分析
sudo smem -t -k

# I/O 分析
sudo iotop -o
```

### 3. 网络调试

```bash
# 抓包分析
sudo tcpdump -i any port 8080 -w capture.pcap

# HTTP 请求测试
curl -v http://localhost:8080/health

# 延迟测试
time curl http://localhost:8080/health
```

---

## 📞 获取帮助

如果以上方案都无法解决问题：

1. **收集信息**:
```bash
# 系统信息
uname -a
cat /etc/os-release
vcgencmd version

# 硬件信息
cat /proc/cpuinfo | grep Model
free -h
df -h

# 软件版本
cd ~/llama.cpp && git log -1
./main --version
```

2. **创建 Issue**:
   - 提供完整的错误信息
   - 附上系统信息
   - 说明复现步骤

3. **社区支持**:
   - llama.cpp Discussions
   - Raspberry Pi Forums
   - Qwen GitHub Issues

---

## ✅ 预防措施

为了避免问题：

1. ✅ 使用官方电源和配件
2. ✅ 定期更新系统: `sudo apt update && sudo apt upgrade`
3. ✅ 保持良好散热
4. ✅ 备份重要数据
5. ✅ 使用 UPS 防止突然断电
6. ✅ 监控系统健康状态

---

**问题仍未解决？欢迎提交 Issue 或在 Discussions 中讨论！**