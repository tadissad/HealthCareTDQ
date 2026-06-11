@echo off
setlocal EnableDelayedExpansion
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
echo [2/5] Khoi dong toan bo he thong voi Docker Compose...
echo.
docker-compose up --build -d

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] docker-compose that bai. Xem log tren de biet chi tiet.
    pause
    EXIT /B 1
)

echo.
echo [3/5] Dang cho cac service on dinh va thiet lap CSDL (10 giay)...
timeout /t 10 /nobreak >nul

echo ----------------------------------------------------
echo Dang tao Migrations cho cac Django service...
docker-compose exec -T pharmacy-service python manage.py makemigrations app
docker-compose exec -T patient-service python manage.py makemigrations app
docker-compose exec -T medical-catalog-service python manage.py makemigrations app
docker-compose exec -T dispensing-service python manage.py makemigrations app
docker-compose exec -T medical-review-service python manage.py makemigrations app
docker-compose exec -T prescription-service python manage.py makemigrations app
docker-compose exec -T api-gateway python manage.py makemigrations app

echo.
echo Dang thuc thi Migrate...
docker-compose exec -T pharmacy-service python manage.py migrate
docker-compose exec -T patient-service python manage.py migrate
docker-compose exec -T medical-catalog-service python manage.py migrate
docker-compose exec -T dispensing-service python manage.py migrate
docker-compose exec -T medical-review-service python manage.py migrate
docker-compose exec -T prescription-service python manage.py migrate
docker-compose exec -T api-gateway python manage.py migrate
docker-compose exec -T api-gateway python manage.py ensure_admin
docker-compose exec -T api-gateway python manage.py ensure_staff
echo [OK] Hoan tat khoi tao CSDL quy mo Microservices!

echo.
echo [4/5] Tao cac Category (Danh muc) cho medical-catalog-service...
echo ----------------------------------------------------
docker-compose exec -T medical-catalog-service python ../seed_catalog_10categories.py
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Khong the tao 10 categories. Hay chay thu cong:
    echo   cd medical-catalog-service
    echo   python ../seed_catalog_10categories.py
) ELSE (
    echo [OK] Hoan tat khoi tao 10 categories moi!
)

echo.
echo [5/6] Nap du lieu ban dau (Seeding) vao Tri Nhien Tao...
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
    echo Dang dong bo danh muc 50 san pham theo unified_kb va tat san pham du...
    python sync_pharmacy_catalog.py --kb-path ai-service/kb/unified_kb.json --pharmacy-url http://localhost:8002 --deactivate-stale
    IF %ERRORLEVEL% NEQ 0 (
        echo [CANH BAO] Dong bo 50 san pham that bai, ban co the chay lai thu cong:
        echo   python sync_pharmacy_catalog.py --kb-path ai-service/kb/unified_kb.json --pharmacy-url http://localhost:8002 --deactivate-stale
    ) ELSE (
        echo [OK] Da dong bo catalog ve bo du lieu chuan (50 san pham).
    )

    echo.
    echo [6/6] Kiem tra so luong du lieu sau khi seed...
    for /f %%A in ('powershell -NoProfile -Command "try { ((Invoke-WebRequest -Uri http://localhost:8002/products/ -UseBasicParsing).Content ^| ConvertFrom-Json).Count } catch { -1 }"') do set PRODUCT_COUNT=%%A
    for /f %%A in ('powershell -NoProfile -Command "try { ((Invoke-WebRequest -Uri http://localhost:8003/categories/ -UseBasicParsing).Content ^| ConvertFrom-Json).Count } catch { -1 }"') do set CATEGORY_COUNT=%%A
    echo [CHECK] products_active=!PRODUCT_COUNT! ^| categories=!CATEGORY_COUNT!
    IF "!PRODUCT_COUNT!" NEQ "50" (
        echo [CANH BAO] So luong san pham hien tai khong phai 50. Hay kiem tra lai seed/sync.
    )
    IF "!CATEGORY_COUNT!" NEQ "10" (
        echo [CANH BAO] So luong category hien tai khong phai 10. Hay kiem tra lai seed category.
    )

    echo Dang Reload lai khoi AI de thuc tinh bien nho moi...
    docker-compose restart ai-service
)

echo.
echo ====================================================
echo   HOAN TAT - HE THONG Health-Micro-AI DA SAN SANG!
echo   Website: http://localhost:8000
echo ====================================================
echo.
pause
