@echo off
REM 가상환경 생성 및 설정 스크립트 (Windows CMD)

echo ========================================
echo myproject 가상환경 설정
echo ========================================
echo.

REM 현재 디렉토리 확인
echo 현재 디렉토리: %CD%
echo.

REM 가상환경 생성
echo [1/3] 가상환경 생성 중...
python -m venv robot
if %errorlevel% neq 0 (
    echo [ERROR] 가상환경 생성 실패!
    pause
    exit /b 1
)
echo [OK] 가상환경 생성 완료!
echo.

REM 가상환경 활성화
echo [2/3] 가상환경 활성화 중...
call robot\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] 가상환경 활성화 실패!
    pause
    exit /b 1
)
echo [OK] 가상환경 활성화 완료!
echo.

REM pip 업그레이드
echo [3/3] pip 업그레이드 중...
python -m pip install --upgrade pip
echo.

REM 패키지 설치
echo 패키지 설치 중...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 패키지 설치 실패!
    pause
    exit /b 1
)
echo.

echo ========================================
echo [완료] 가상환경 설정이 완료되었습니다!
echo ========================================
echo.
echo 다음 명령어로 가상환경을 활성화하세요:
echo   robot\Scripts\activate
echo.
echo 또는 이 스크립트를 실행하면 자동으로 활성화됩니다.
echo.
pause

