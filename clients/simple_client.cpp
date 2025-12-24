/**
 * simple_client.cpp
 * 简单的 HTTP 客户端，用于与 llama.cpp server 交互
 * 
 * 编译:
 *   g++ -std=c++17 -o simple_client simple_client.cpp -lcurl
 * 
 * 使用:
 *   ./simple_client "What is AI?"
 *   ./simple_client "Explain machine learning" 8080
 */

#include <iostream>
#include <string>
#include <curl/curl.h>
#include <sstream>
#include <cstring>

// 回调函数：处理 HTTP 响应
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// 发送聊天请求
bool sendChatRequest(const std::string& prompt, const std::string& host = "localhost", int port = 8080) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;
    
    // 初始化 curl
    curl = curl_easy_init();
    if (!curl) {
        std::cerr << "❌ 无法初始化 CURL" << std::endl;
        return false;
    }
    
    // 构建 URL
    std::string url = "http://" + host + ":" + std::to_string(port) + "/v1/chat/completions";
    
    // 构建 JSON 请求体
    std::ostringstream jsonStream;
    jsonStream << "{"
               << "\"messages\":["
               << "{\"role\":\"user\",\"content\":\"" << prompt << "\"}"
               << "],"
               << "\"temperature\":0.7,"
               << "\"max_tokens\":256,"
               << "\"stream\":false"
               << "}";
    std::string jsonData = jsonStream.str();
    
    // 设置 HTTP 头
    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    // 配置 CURL 选项
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonData.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 60L);  // 60 秒超时
    
    // 发送请求
    std::cout << "📤 发送请求到: " << url << std::endl;
    std::cout << "💬 提示词: " << prompt << std::endl;
    std::cout << "⏳ 等待响应...\n" << std::endl;
    
    res = curl_easy_perform(curl);
    
    // 检查结果
    if (res != CURLE_OK) {
        std::cerr << "❌ 请求失败: " << curl_easy_strerror(res) << std::endl;
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        return false;
    }
    
    // 获取 HTTP 状态码
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
    
    if (http_code != 200) {
        std::cerr << "❌ HTTP 错误: " << http_code << std::endl;
        std::cerr << "响应: " << readBuffer << std::endl;
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
        return false;
    }
    
    // 解析响应（简单版本，只提取 content）
    std::cout << "✅ 收到响应\n" << std::endl;
    
    // 查找 "content" 字段
    size_t contentPos = readBuffer.find("\"content\":\"");
    if (contentPos != std::string::npos) {
        contentPos += 11;  // 跳过 "content":"
        size_t endPos = readBuffer.find("\"", contentPos);
        
        if (endPos != std::string::npos) {
            std::string content = readBuffer.substr(contentPos, endPos - contentPos);
            
            // 简单的转义字符处理
            size_t pos = 0;
            while ((pos = content.find("\\n", pos)) != std::string::npos) {
                content.replace(pos, 2, "\n");
                pos += 1;
            }
            
            std::cout << "🤖 AI 回复:\n" << std::endl;
            std::cout << content << std::endl;
        } else {
            std::cout << "完整响应: " << readBuffer << std::endl;
        }
    } else {
        std::cout << "完整响应: " << readBuffer << std::endl;
    }
    
    // 清理
    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    
    return true;
}

// 打印使用说明
void printUsage(const char* progName) {
    std::cout << "使用方法:" << std::endl;
    std::cout << "  " << progName << " <提示词> [端口]" << std::endl;
    std::cout << std::endl;
    std::cout << "示例:" << std::endl;
    std::cout << "  " << progName << " \"What is AI?\"" << std::endl;
    std::cout << "  " << progName << " \"Explain quantum computing\" 8080" << std::endl;
}

int main(int argc, char* argv[]) {
    // 检查参数
    if (argc < 2) {
        std::cerr << "❌ 错误: 缺少提示词参数" << std::endl;
        printUsage(argv[0]);
        return 1;
    }
    
    std::string prompt = argv[1];
    int port = 8080;
    
    // 如果提供了端口参数
    if (argc >= 3) {
        try {
            port = std::stoi(argv[2]);
        } catch (const std::exception& e) {
            std::cerr << "❌ 无效的端口号: " << argv[2] << std::endl;
            return 1;
        }
    }
    
    std::cout << "================================" << std::endl;
    std::cout << "    Qwen3 推理客户端 (C++)     " << std::endl;
    std::cout << "================================\n" << std::endl;
    
    // 初始化 curl 全局环境
    curl_global_init(CURL_GLOBAL_DEFAULT);
    
    // 发送请求
    bool success = sendChatRequest(prompt, "localhost", port);
    
    // 清理 curl 全局环境
    curl_global_cleanup();
    
    std::cout << "\n================================" << std::endl;
    
    return success ? 0 : 1;
}