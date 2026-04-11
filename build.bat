@echo off
REM ============================================================
REM build.bat – Health-Micro-AI
REM Script khởi động hệ thống tối ưu (dùng shared AI base image)
REM
REM Chạy lần đầu tiên:
REM   build.bat
REM
REM Các lần tiếp theo (không cần rebuild base):
REM   build.bat fast
REM ============================================================

echo.
echo ====================================================
echo   Health-Micro-AI – Smart Build System
echo ====================================================
echo.

REM Kiểm tra xem base image đã tồn tại chưa
docker image inspect health-ai-base:latest >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Base image "health-ai-base:latest" da ton tai.
    IF "%1"=="fast" (
        echo [FAST MODE] Bo qua build base image.
        GOTO COMPOSE
    )
    echo [?] Ban co muon rebuild base image khong? (Y/N - mac dinh N)
    set /p REBUILD="Nhap lua chon: "
    IF /I "%REBUILD%"=="Y" GOTO BUILD_BASE
    GOTO COMPOSE
) ELSE (
    echo [!] Base image chua ton tai. Bat dau build base image...
    echo     (Chi can lam dung 1 lan, cac lan sau se rat nhanh)
    echo.
    GOTO BUILD_BASE
)

:BUILD_BASE
echo.
echo [1/2] Dang build shared AI base image...
echo       (Buoc nay tai PyTorch, FAISS, Transformers ~800MB)
echo       Vui long doi, co the mat 15-40 phut tuy toc do mang...
echo.
docker build -f Dockerfile.ai-base -t health-ai-base:latest .
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Build base image that bai! Kiem tra ket noi mang va thu lai.
    pause
    EXIT /B 1
)
echo.
echo [OK] Base image da san sang!

:COMPOSE
echo.
echo [2/2] Khoi dong toan bo he thong voi Docker Compose...
echo.
docker-compose up --build -d

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] docker-compose that bai. Xem log tren de biet chi tiet.
    pause
    EXIT /B 1
)

echo.
echo ====================================================
echo   He thong da khoi dong thanh cong!
echo   Truy cap: http://localhost:8000
echo.
echo   Kiem tra trang thai container:
echo     docker-compose ps
echo.
echo   Xem log real-time:
echo     docker-compose logs -f [ten-service]
echo ====================================================
echo.
pause
