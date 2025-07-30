# 🧪 Docker 測試使用指南

## 🚀 快速開始

### Windows 用戶：
```cmd
# 雙擊執行或在命令提示字元中運行
run_tests.bat
```

### Linux/Mac 用戶：
```bash
# 給腳本執行權限
chmod +x run_tests.sh

# 運行腳本
./run_tests.sh
```

### 手動方式：

1. **確保容器運行：**
   ```bash
   docker-compose up -d
   ```

2. **進入容器運行測試：**
   ```bash
   # 快速測試（推薦）
   docker-compose exec agentic-app python test/test_docker_simple.py
   
   # 或進入容器互動模式
   docker-compose exec agentic-app bash
   # 然後在容器內執行：
   python test/test_docker_simple.py
   ```

## 📊 測試結果解讀

✅ **成功輸出示例：**
```
🐳 Starting Docker Environment Tests
==================================================
test_python_environment ... ok
test_language_type_enum ... ok
test_chinese_agent_creation ... ok
test_docker_environment_detection ... ok
==================================================
✅ All Docker tests passed!
```

❌ **失敗時的處理：**
- 檢查 Docker 是否正常運行
- 確認容器內的路徑設置
- 查看具體錯誤訊息進行調試

## 🔧 進階用法

### 運行特定測試：
```bash
docker-compose exec agentic-app python -m unittest test.test_docker_simple.TestCoreModels -v
```

### 安裝額外測試工具：
```bash
docker-compose exec agentic-app pip install pytest coverage
docker-compose exec agentic-app python -m pytest test/test_docker_simple.py -v
```

### 生成測試報告：
```bash
docker-compose exec agentic-app python test/run_docker_tests.py
```

## 🐛 常見問題

**Q: 容器無法啟動？**
A: 檢查 Docker Desktop 是否運行，端口是否被占用

**Q: 模組導入失敗？**
A: 確認 PYTHONPATH 環境變數已正確設置

**Q: 測試掛掉？**  
A: 查看容器日誌：`docker-compose logs agentic-app`

## 📁 相關文件

- `test/test_docker_simple.py` - 簡化測試腳本
- `test/run_docker_tests.py` - 完整測試腳本  
- `test/DOCKER_TESTING.md` - 詳細測試文檔
- `docker-compose-test.yml` - 專用測試配置
