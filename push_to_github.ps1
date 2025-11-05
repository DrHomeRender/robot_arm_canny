# myproject를 GitHub에 푸시하는 스크립트

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "myproject GitHub Push Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 현재 디렉토리 확인
$currentDir = Get-Location
Write-Host "Current directory: $currentDir" -ForegroundColor Yellow
Write-Host ""

# Git 설치 확인
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Git이 설치되어 있지 않거나 PATH에 등록되지 않았습니다!" -ForegroundColor Red
    Write-Host "Git을 설치하거나 PATH에 추가해주세요." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/5] Git 저장소 확인 중..." -ForegroundColor Yellow
if (-not (Test-Path .git)) {
    Write-Host "[INFO] Git 저장소 초기화 중..." -ForegroundColor Yellow
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Git 초기화 실패!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[OK] Git 저장소 이미 존재" -ForegroundColor Green
}
Write-Host ""

Write-Host "[2/5] 원격 저장소 설정 중..." -ForegroundColor Yellow
$remoteUrl = "git@github.com:DrHomeRender/robot_arm_canny.git"
$existingRemote = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[INFO] 기존 원격 저장소: $existingRemote" -ForegroundColor Yellow
    git remote set-url origin $remoteUrl
    Write-Host "[OK] 원격 저장소 URL 업데이트: $remoteUrl" -ForegroundColor Green
} else {
    git remote add origin $remoteUrl
    Write-Host "[OK] 원격 저장소 추가: $remoteUrl" -ForegroundColor Green
}
Write-Host ""

Write-Host "[3/5] 파일 추가 중..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 파일 추가 실패!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] 파일 추가 완료" -ForegroundColor Green
Write-Host ""

Write-Host "[4/5] 커밋 중..." -ForegroundColor Yellow
$commitMessage = "Initial commit: myproject - 영상 기반 좌표 전송 시스템"
git commit -m $commitMessage
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] 커밋 실패 또는 변경사항 없음" -ForegroundColor Yellow
    Write-Host "변경사항이 없으면 스킵됩니다." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "[5/5] GitHub에 푸시 중..." -ForegroundColor Yellow
Write-Host "원격 저장소: $remoteUrl" -ForegroundColor Cyan
Write-Host ""

# main 브랜치로 푸시 (기본 브랜치가 main이 아닐 수 있음)
$currentBranch = git branch --show-current
if (-not $currentBranch) {
    git branch -M main
    $currentBranch = "main"
}

Write-Host "브랜치: $currentBranch" -ForegroundColor Cyan
Write-Host ""

# 푸시 실행
git push -u origin $currentBranch
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 푸시 실패!" -ForegroundColor Red
    Write-Host ""
    Write-Host "가능한 원인:" -ForegroundColor Yellow
    Write-Host "1. SSH 키가 설정되지 않았을 수 있습니다" -ForegroundColor Yellow
    Write-Host "2. GitHub 인증이 필요할 수 있습니다" -ForegroundColor Yellow
    Write-Host "3. 저장소 권한이 없을 수 있습니다" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "HTTPS로 시도하려면 원격 URL을 변경하세요:" -ForegroundColor Yellow
    Write-Host "  git remote set-url origin https://github.com/DrHomeRender/robot_arm_canny.git" -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[완료] GitHub에 푸시 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "저장소 URL: https://github.com/DrHomeRender/robot_arm_canny" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"

