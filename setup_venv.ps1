# 가상환경 생성 및 설정 스크립트 (Windows PowerShell)

# UTF-8 인코딩 설정 (한글 깨짐 방지)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "myproject 가상환경 설정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 현재 디렉토리 확인
Write-Host "현재 디렉토리: $PWD" -ForegroundColor Yellow
Write-Host ""

# Python 설치 확인
Write-Host "[0/3] Python 설치 확인 중..." -ForegroundColor Yellow
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    $pythonVersion = python --version 2>&1
    Write-Host "Python 발견: $pythonVersion" -ForegroundColor Green
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
    $pythonVersion = python3 --version 2>&1
    Write-Host "Python3 발견: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다!" -ForegroundColor Red
    Write-Host "Python을 설치하거나 PATH에 추가해주세요." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# 가상환경 생성
Write-Host "[1/3] 가상환경 생성 중..." -ForegroundColor Yellow
$venvOutput = & $pythonCmd -m venv robot 2>&1
$venvExitCode = $LASTEXITCODE
if ($venvExitCode -ne 0) {
    Write-Host "[ERROR] 가상환경 생성 실패! (종료 코드: $venvExitCode)" -ForegroundColor Red
    Write-Host "오류 메시지: $venvOutput" -ForegroundColor Red
    Write-Host ""
    Write-Host "해결 방법:" -ForegroundColor Yellow
    Write-Host "1. Python이 제대로 설치되어 있는지 확인" -ForegroundColor Yellow
    Write-Host "2. 'python --version' 명령어로 버전 확인" -ForegroundColor Yellow
    Write-Host "3. 관리자 권한이 필요한지 확인" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] 가상환경 생성 완료!" -ForegroundColor Green
Write-Host ""

# 가상환경 활성화
Write-Host "[2/3] 가상환경 활성화 중..." -ForegroundColor Yellow
& .\robot\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] 가상환경 활성화 실패 (실행 정책 문제일 수 있음)" -ForegroundColor Yellow
    Write-Host "실행 정책 설정: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
} else {
    Write-Host "[OK] 가상환경 활성화 완료!" -ForegroundColor Green
}
Write-Host ""

# pip 업그레이드
Write-Host "[3/3] pip 업그레이드 중..." -ForegroundColor Yellow
& $pythonCmd -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] pip 업그레이드 실패 (계속 진행)" -ForegroundColor Yellow
}
Write-Host ""

# 패키지 설치
Write-Host "패키지 설치 중..." -ForegroundColor Yellow
& $pythonCmd -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 패키지 설치 실패!" -ForegroundColor Red
    Write-Host "오류 코드: $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[완료] 가상환경 설정이 완료되었습니다!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 명령어로 가상환경을 활성화하세요:" -ForegroundColor Yellow
Write-Host "  .\robot\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "또는 이 스크립트를 실행하면 자동으로 활성화됩니다." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"

