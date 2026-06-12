@echo off
echo ========================================
echo  角色扮演游戏后端服务启动脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查依赖...
python -m pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
) else (
    echo 依赖已安装
)

echo.
echo [2/3] 启动服务...
echo.
echo 服务将在 http://localhost:8000 启动
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python main.py

pause
