#!/bin/bash
################################################################################
# Qwen3-0.6B 树莓派自动部署脚本
# 适用于: Raspberry Pi 5 (8GB) + Raspberry Pi OS 64-bit
# 用途: 自动安装 llama.cpp 并部署微调后的模型
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置参数
LLAMA_CPP_DIR="$HOME/llama.cpp"
MODEL_DIR="$HOME/models"
MODEL_NAME="qwen3-0.6b-q4_k_m.gguf"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"
SERVER_PORT=8080
NUM_THREADS=4
CONTEXT_SIZE=2048

################################################################################
# 辅助函数
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "================================================================================"
    echo "$1"
    echo "================================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 已安装"
        return 0
    else
        print_error "$1 未安装"
        return 1
    fi
}

################################################################################
# 主要功能函数
################################################################################

check_system() {
    print_header "步骤 1: 检查系统环境"
    
    # 检查架构
    ARCH=$(uname -m)
    if [ "$ARCH" != "aarch64" ]; then
        print_error "不支持的架构: $ARCH (需要 aarch64)"
        exit 1
    fi
    print_success "架构: $ARCH"
    
    # 检查内存
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 6 ]; then
        print_error "内存不足: ${TOTAL_MEM}GB (建议至少 8GB)"
        print_info "部署可能失败，是否继续? (y/n)"
        read -r CONTINUE
        if [ "$CONTINUE" != "y" ]; then
            exit 1
        fi
    else
        print_success "内存: ${TOTAL_MEM}GB"
    fi
    
    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_success "操作系统: $PRETTY_NAME"
    fi
    
    # 检查 swap
    SWAP=$(free -g | awk '/^Swap:/{print $2}')
    print_info "Swap: ${SWAP}GB"
    if [ "$SWAP" -lt 2 ]; then
        print_info "建议增加 swap 空间至少 2GB"
    fi
    
    echo ""
}

install_dependencies() {
    print_header "步骤 2: 安装依赖"
    
    print_info "更新软件包列表..."
    sudo apt update
    
    print_info "安装编译工具..."
    sudo apt install -y \
        build-essential \
        git \
        cmake \
        wget \
        curl \
        htop \
        vim \
        python3-pip
    
    print_success "依赖安装完成"
    echo ""
}

setup_swap() {
    print_header "步骤 3: 配置 Swap 空间"
    
    CURRENT_SWAP=$(free -g | awk '/^Swap:/{print $2}')
    if [ "$CURRENT_SWAP" -ge 2 ]; then
        print_success "Swap 已配置: ${CURRENT_SWAP}GB"
        return
    fi
    
    print_info "增加 Swap 到 2GB..."
    
    sudo dphys-swapfile swapoff || true
    
    # 备份原配置
    sudo cp /etc/dphys-swapfile /etc/dphys-swapfile.backup
    
    # 设置为 2GB
    sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
    
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    
    NEW_SWAP=$(free -g | awk '/^Swap:/{print $2}')
    print_success "Swap 配置完成: ${NEW_SWAP}GB"
    echo ""
}

compile_llama_cpp() {
    print_header "步骤 4: 编译 llama.cpp"
    
    if [ -d "$LLAMA_CPP_DIR" ]; then
        print_info "检测到现有 llama.cpp 目录"
        print_info "是否重新编译? (y/n)"
        read -r RECOMPILE
        if [ "$RECOMPILE" = "y" ]; then
            rm -rf "$LLAMA_CPP_DIR"
        else
            print_success "跳过编译"
            return
        fi
    fi
    
    print_info "克隆 llama.cpp 仓库..."
    git clone https://github.com/ggerganov/llama.cpp "$LLAMA_CPP_DIR"
    
    cd "$LLAMA_CPP_DIR"
    
    print_info "开始编译 (可能需要 5-10 分钟)..."
    make -j4
    
    if [ -f "./main" ]; then
        print_success "llama.cpp 编译成功"
        ./main --version
    else
        print_error "编译失败"
        exit 1
    fi
    
    cd - > /dev/null
    echo ""
}

setup_model_dir() {
    print_header "步骤 5: 设置模型目录"
    
    if [ ! -d "$MODEL_DIR" ]; then
        mkdir -p "$MODEL_DIR"
        print_success "创建模型目录: $MODEL_DIR"
    else
        print_success "模型目录已存在: $MODEL_DIR"
    fi
    
    echo ""
}

check_model() {
    print_header "步骤 6: 检查模型文件"
    
    if [ -f "$MODEL_PATH" ]; then
        print_success "找到模型文件: $MODEL_PATH"
        MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
        print_info "模型大小: $MODEL_SIZE"
    else
        print_error "模型文件不存在: $MODEL_PATH"
        print_info ""
        print_info "请将模型文件上传到: $MODEL_DIR"
        print_info "文件名应为: $MODEL_NAME"
        print_info ""
        print_info "上传方法:"
        print_info "1. SCP: scp your-model.gguf pi@raspberrypi.local:$MODEL_DIR/$MODEL_NAME"
        print_info "2. USB: 挂载 U盘后复制"
        print_info "3. 网络下载: wget/curl 下载到该目录"
        print_info ""
        exit 1
    fi
    
    echo ""
}

test_inference() {
    print_header "步骤 7: 测试推理"
    
    print_info "运行简单推理测试..."
    
    cd "$LLAMA_CPP_DIR"
    
    PROMPT="What is artificial intelligence?"
    
    print_info "提示词: $PROMPT"
    print_info "生成中..."
    echo ""
    
    ./main -m "$MODEL_PATH" \
        -n 100 \
        -t "$NUM_THREADS" \
        -c "$CONTEXT_SIZE" \
        -p "$PROMPT" \
        --color
    
    echo ""
    print_success "推理测试完成"
    
    cd - > /dev/null
    echo ""
}

create_systemd_service() {
    print_header "步骤 8: 创建系统服务"
    
    print_info "是否创建自动启动服务? (y/n)"
    read -r CREATE_SERVICE
    
    if [ "$CREATE_SERVICE" != "y" ]; then
        print_info "跳过服务创建"
        return
    fi
    
    SERVICE_FILE="/etc/systemd/system/llama-server.service"
    
    print_info "创建 systemd 服务文件..."
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Llama.cpp HTTP Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$LLAMA_CPP_DIR
ExecStart=$LLAMA_CPP_DIR/server \\
    -m $MODEL_PATH \\
    --host 0.0.0.0 \\
    --port $SERVER_PORT \\
    -t $NUM_THREADS \\
    -c $CONTEXT_SIZE
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "服务文件已创建: $SERVICE_FILE"
    
    # 重载 systemd
    sudo systemctl daemon-reload
    
    # 启用服务
    sudo systemctl enable llama-server
    print_success "服务已设置为开机自启"
    
    # 启动服务
    sudo systemctl start llama-server
    print_success "服务已启动"
    
    sleep 2
    
    # 检查状态
    if sudo systemctl is-active --quiet llama-server; then
        print_success "服务运行正常"
    else
        print_error "服务启动失败"
        print_info "查看日志: sudo journalctl -u llama-server -f"
    fi
    
    echo ""
}

create_helper_scripts() {
    print_header "步骤 9: 创建辅助脚本"
    
    # 创建快速启动脚本
    cat > "$HOME/start_llama.sh" <<'EOF'
#!/bin/bash
cd ~/llama.cpp
./server -m ~/models/qwen3-0.6b-q4_k_m.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    -t 4 \
    -c 2048
EOF
    chmod +x "$HOME/start_llama.sh"
    print_success "创建启动脚本: ~/start_llama.sh"
    
    # 创建交互测试脚本
    cat > "$HOME/test_llama.sh" <<'EOF'
#!/bin/bash
cd ~/llama.cpp
./main -m ~/models/qwen3-0.6b-q4_k_m.gguf \
    -n 256 \
    -t 4 \
    -c 2048 \
    -p "$1" \
    --color
EOF
    chmod +x "$HOME/test_llama.sh"
    print_success "创建测试脚本: ~/test_llama.sh"
    
    # 创建 API 测试脚本
    cat > "$HOME/test_api.sh" <<'EOF'
#!/bin/bash
curl http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
        \"messages\": [
            {\"role\": \"user\", \"content\": \"$1\"}
        ],
        \"temperature\": 0.7,
        \"max_tokens\": 100
    }" | jq
EOF
    chmod +x "$HOME/test_api.sh"
    print_success "创建 API 测试脚本: ~/test_api.sh"
    
    echo ""
}

print_summary() {
    print_header "部署完成! 🎉"
    
    echo -e "${GREEN}部署信息:${NC}"
    echo "  • llama.cpp 目录: $LLAMA_CPP_DIR"
    echo "  • 模型目录: $MODEL_DIR"
    echo "  • 模型文件: $MODEL_PATH"
    echo "  • 服务端口: $SERVER_PORT"
    echo ""
    
    echo -e "${YELLOW}使用方法:${NC}"
    echo "  1. 交互式测试:"
    echo "     cd $LLAMA_CPP_DIR"
    echo "     ./main -m $MODEL_PATH -n 128 -p \"你的问题\""
    echo ""
    echo "  2. 启动 HTTP 服务器:"
    echo "     ~/start_llama.sh"
    echo "     或"
    echo "     sudo systemctl start llama-server"
    echo ""
    echo "  3. 测试 API (需要先启动服务器):"
    echo "     ~/test_api.sh \"Hello, AI!\""
    echo ""
    echo "  4. 快速测试:"
    echo "     ~/test_llama.sh \"What is machine learning?\""
    echo ""
    
    echo -e "${YELLOW}性能监控:${NC}"
    echo "  • 查看 CPU/内存: htop"
    echo "  • 查看温度: vcgencmd measure_temp"
    echo "  • 查看服务日志: sudo journalctl -u llama-server -f"
    echo ""
    
    echo -e "${YELLOW}远程访问:${NC}"
    echo "  • 本地网络: http://raspberrypi.local:$SERVER_PORT"
    echo "  • IP 地址: http://$(hostname -I | awk '{print $1}'):$SERVER_PORT"
    echo ""
    
    echo -e "${GREEN}部署成功完成!${NC}"
}

################################################################################
# 主流程
################################################################################

main() {
    clear
    print_header "Qwen3-0.6B 树莓派自动部署脚本"
    
    print_info "开始部署流程..."
    sleep 2
    
    check_system
    install_dependencies
    setup_swap
    compile_llama_cpp
    setup_model_dir
    check_model
    test_inference
    create_systemd_service
    create_helper_scripts
    print_summary
}

# 运行主函数
main