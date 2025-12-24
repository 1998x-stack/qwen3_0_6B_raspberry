# Makefile for Qwen3 Raspberry Pi Client
# 用于编译 simple_client.cpp

# 编译器配置
CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra
LDFLAGS = -lcurl

# 目标文件
TARGET = simple_client
SOURCE = simple_client.cpp

# 默认目标
all: $(TARGET)

# 编译规则
$(TARGET): $(SOURCE)
	@echo "🔨 编译 $(TARGET)..."
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE) $(LDFLAGS)
	@echo "✅ 编译完成: $(TARGET)"

# 清理
clean:
	@echo "🧹 清理编译文件..."
	rm -f $(TARGET)
	@echo "✅ 清理完成"

# 安装（复制到 /usr/local/bin）
install: $(TARGET)
	@echo "📦 安装 $(TARGET) 到 /usr/local/bin..."
	sudo cp $(TARGET) /usr/local/bin/
	sudo chmod +x /usr/local/bin/$(TARGET)
	@echo "✅ 安装完成"

# 卸载
uninstall:
	@echo "🗑️  卸载 $(TARGET)..."
	sudo rm -f /usr/local/bin/$(TARGET)
	@echo "✅ 卸载完成"

# 测试
test: $(TARGET)
	@echo "🧪 运行测试..."
	./$(TARGET) "What is 2+2?"

# 帮助
help:
	@echo "Makefile 使用说明:"
	@echo "  make          - 编译程序"
	@echo "  make clean    - 清理编译文件"
	@echo "  make install  - 安装到系统"
	@echo "  make uninstall- 从系统卸载"
	@echo "  make test     - 运行测试"
	@echo "  make help     - 显示此帮助"

.PHONY: all clean install uninstall test help