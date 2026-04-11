@echo off
REM ============================================================
REM build.bat – Health-Micro-AI
REM Script khởi động hệ thống tối ưu (dùng shared AI base image)
REM
REM Chạy lần đầu tiên (hoặc chạy bình thường):
REM   build.bat
REM
REM Muốn ép tải lại thư viện AI từ đầu:
REM   build.bat rebuild
REM ============================================================

echo.
echo ====================================================
echo   Health-Micro-AI
echo ====================================================
echo.

REM Kiểm tra xem base image đã tồn tại chưa
docker image inspect health-ai-base:latest >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] He thong da cai dat loi AI - Base Image - tu truoc.
    IF /I "%1"=="rebuild" (
        echo [REBUILD MODE] Nhan lenh yeu cau xoa va tai lai loi AI.
        GOTO BUILD_BASE
    ) ELSE (
        echo          ^=^> Bo qua buoc tai nang, tien hanh khoi dong may chu ngay...
        GOTO COMPOSE
    )
) ELSE (
    echo [!] Day la lan khoi dong dau tien hoac he thong chua hoan thien.
    echo [!] Dang bat dau qua trinh tai Loi Tri Tue Nhan Tao - AI Base...
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
echo [2/4] Khoi dong toan bo he thong voi Docker Compose...
echo.
docker-compose up --build -d

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] docker-compose that bai. Xem log tren de biet chi tiet.
    pause
    EXIT /B 1
)

echo.
echo [3/4] Dang cho cac service on dinh va thiet lap CSDL (10 giay)...
timeout /t 10 /nobreak >nul

echo ----------------------------------------------------
echo Dang tao Migrations cho cac Django service...
docker-compose exec -T pharmacy-service python manage.py makemigrations app
docker-compose exec -T patient-service python manage.py makemigrations app
docker-compose exec -T medical-catalog-service python manage.py makemigrations app
docker-compose exec -T dispensing-service python manage.py makemigrations app
docker-compose exec -T medical-review-service python manage.py makemigrations app
docker-compose exec -T api-gateway python manage.py makemigrations app

echo.
echo Dang thuc thi Migrate...
docker-compose exec -T pharmacy-service python manage.py migrate
docker-compose exec -T patient-service python manage.py migrate
docker-compose exec -T medical-catalog-service python manage.py migrate
docker-compose exec -T dispensing-service python manage.py migrate
docker-compose exec -T medical-review-service python manage.py migrate
docker-compose exec -T api-gateway python manage.py migrate
echo [OK] Hoan tat khoi tao CSDL quy mo Microservices!

echo.
echo [4/4] Nap du lieu ban dau (Seeding) vao Tri Nhien Tao...
echo ----------------------------------------------------
echo Luu y: Script can kiem tra cac thu vien: requests, neo4j, faiss-cpu, google-genai
python seed_all.py
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Tool nap tri thuc bi gian doan (Co the do chua khai bao API_KEY hoac thieu Thu vien tren may).
    echo Ban hay tu cai dat thu vien va chay lai bang lenh: "python seed_all.py" sau nhe!
) ELSE (
    echo.
    echo [OK] Nap Tri Tue Nhan Tao vao he thong thanh cong!
    echo Dang Reload lai khoi AI de thuc tinh bien nho moi...
    docker-compose restart clinical-advisory-service
)

echo.
echo ====================================================
echo   HOAN TAT - HE THONG Health-Micro-AI DA SAN SANG!
echo   Website: http://localhost:8000
echo ====================================================
echo.
pause
