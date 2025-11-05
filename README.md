# myproject - 영상 기반 좌표 전송 시스템

카메라 영상에서 물체를 감지하고 로봇 좌표로 변환하여 Firebase로 전송하는 시스템입니다.

## 📋 기능

- **테스트 모드**: Sector ID 기반 정답 좌표 전송
- **실제 모드**: 카메라 영상에서 물체 감지 후 좌표 계산 및 전송
- **Firebase 연동**: 실시간 주문 상태 모니터링 및 자동 전송
- **고정밀 좌표 변환**: 픽셀 좌표 → 로봇 좌표 변환 (1mm 단위 정밀도)

## 🚀 설치 및 실행

### 1. 가상환경 생성 및 활성화

**방법 1: 자동 설정 스크립트 사용 (권장)**

**Windows CMD:**
```cmd
# myproject 폴더에서 실행
setup_venv.bat
```

**Windows PowerShell:**
```powershell
# myproject 폴더에서 실행
.\setup_venv.ps1

# 실행 정책 오류 발생 시 (한 번만 실행)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**방법 2: 수동 설정**

**Windows CMD:**
```cmd
# myproject 폴더에서 실행
python -m venv robot
robot\Scripts\activate
pip install -r requirements.txt
```

**Windows PowerShell:**
```powershell
# myproject 폴더에서 실행
python -m venv robot
.\robot\Scripts\Activate.ps1
pip install -r requirements.txt
```

**PowerShell 실행 정책 오류 발생 시:**
```powershell
# 실행 정책 설정 (현재 사용자만, 한 번만 실행)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 또는 일시적으로 실행 정책 우회
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

**Linux/Mac:**
```bash
# 가상환경 생성
python3 -m venv robot

# 가상환경 활성화
source robot/bin/activate
```

### 2. 패키지 설치

가상환경이 활성화된 상태에서:
```bash
# pip 업그레이드 (권장)
python -m pip install --upgrade pip

# 패키지 설치
pip install -r requirements.txt
```

### 3. Firebase 인증 키 준비

`servingstation-firebase-adminsdk-fbsvc-231e400af8.json` 파일이 `myproject` 폴더에 있어야 합니다.

### 4. 설정 파일 확인

`config.json` 파일을 확인하고 다음 항목을 설정하세요:
- 카메라 번호
- 물체의 실제 최단축 길이 (`real_shortest_axis_mm`)
- 캘리브레이션 포인트
- Firebase 자동 전송 설정

## 🎮 실행 방법

### 실행 방법

**Windows (CMD):**
```cmd
# 가상환경 활성화
robot\Scripts\activate

# 실행
python main.py
```

**Windows (PowerShell):**
```powershell
# 가상환경 활성화
.\robot\Scripts\Activate.ps1

# 실행
python main.py
```

**Linux/Mac:**
```bash
# 가상환경 활성화
source robot/bin/activate

# 실행
python main.py
```

### 모드 설정

실행 모드는 `config.json`의 `mode.test_mode` 설정으로 제어합니다:

```json
{
  "mode": {
    "test_mode": false,  // true: 테스트 모드, false: 실제 모드
    "_note_test_mode": "true: 테스트 모드 (Sector ID 기반 정답 좌표 전송), false: 실제 모드 (카메라 영상에서 좌표 계산)"
  }
}
```

#### 테스트 모드 (`test_mode: true`)
- Firebase의 `items[0].id` 값 (1, 2, 3)을 읽어서 해당 섹터의 정답 좌표를 전송
- 웹에서 1/2/3 버튼을 누르면 자동으로 해당 섹터 좌표 전송

#### 실제 모드 (`test_mode: false`)
- 카메라 영상에서 물체 감지 (경계 검출)
- 픽셀 좌표를 로봇 좌표로 변환 (아핀 변환)
- Firebase의 `items[0].id`에서 섹터 ID를 읽어 Z값 및 자세각 결정
- 변환된 좌표를 Firebase로 전송

**동작 방식:**
- 카메라 영상에서 물체 감지 (경계 검출)
- 픽셀 좌표를 로봇 좌표로 변환 (아핀 변환)
- Firebase의 `items[0].id`에서 섹터 ID를 읽어 Z값 및 자세각 결정
- 변환된 좌표를 Firebase로 전송

## ⌨️ 키보드 명령어

| 키 | 기능 |
|---|---|
| **SPACE** | 수동 전송 (현재 감지된 좌표 또는 섹터 좌표 전송) |
| **Q** 또는 **ESC** | 프로그램 종료 |

## 📊 동작 흐름

### 테스트 모드
1. 웹에서 1/2/3 버튼 클릭 → Firebase `items[0].id` 변경
2. 로봇이 `status: "waiting_pose"`, `pose_required: true` 설정
3. 코드에서 Firebase 모니터링 → 섹터 ID 감지
4. `SECTOR_ANSWERS[sector_id]` 정답 좌표 전송

### 실제 모드
1. 카메라 영상에서 물체 감지 (경계 검출)
2. 픽셀 좌표 (cx, cy) 계산
3. Firebase에서 섹터 ID 읽기 (`items[0].id`)
4. 아핀 변환으로 픽셀 XY → 로봇 XY 변환
5. 섹터 ID에 따라 Z값 및 자세각 결정
6. 변환된 좌표를 Firebase로 전송

## 🔧 설정 파일

### `config.json`

주요 설정 항목:
- `mode.test_mode`: 실행 모드 설정 (true: 테스트 모드, false: 실제 모드)
- `camera`: 카메라 번호, 해상도, FOV 설정
- `object`: 물체의 실제 최단축 길이
- `calibration_points`: 픽셀-로봇 좌표 매핑 포인트 (3개 이상)
- `auto_send`: 자동 전송 모드 설정
- `robot_transform`: 기본 자세각 설정

### `constants.py`

Sector별 정답 좌표:
```python
SECTOR_ANSWERS = {
    1: [-298.0, -190.1, 208.1, -170.26, 10.09, 118.35],  # Sector 1
    2: [-298.1,    5.2, 206.2, -178.06, 10.01,  78.67],  # Sector 2
    3: [-216.1,  202.3, 219.1, -174.37,  9.35,  37.71],  # Sector 3
}
```

## 📁 프로젝트 구조

```
myproject/
├── main.py                    # 프로그램 진입점
├── config.json                # 설정 파일
├── constants.py               # Sector별 정답 좌표
├── config_loader.py           # 설정 로더
├── firebase_manager.py         # Firebase 연동
├── vision_processor.py        # 영상 처리 및 좌표 계산
├── coordinate_transform.py    # 픽셀 → 로봇 좌표 변환
├── requirements.txt           # 패키지 의존성
├── README.md                  # 이 파일
└── robot/                    # 가상환경 (생성 필요)
```

## 🔧 캘리브레이션 도구

### 픽셀 대비 실제 길이 비율 측정

19cm 물체를 사용하여 픽셀 대비 실제 길이 비율을 측정할 수 있습니다:

```bash
# 가상환경 활성화 후
python calibration_tool.py
```

**사용 방법:**
1. 19cm 길이의 물체를 카메라 앞에 놓습니다
2. 프로그램이 물체의 가장 긴 축을 자동으로 감지합니다
3. **[SPACE]** 키를 누르면 현재 측정값이 txt 파일에 저장됩니다
4. 여러 번 측정하여 평균값을 구할 수 있습니다

**저장되는 정보:**
- 픽셀 길이 (px)
- 실제 길이 (cm)
- 비율 (cm/px, px/cm)
- 중심 픽셀 좌표
- 각도

**로그 파일:**
- `calibration_log_YYYYMMDD_HHMMSS.txt` 형식으로 저장됩니다

**나중에 조절:**
- 측정된 비율을 사용하여 "2cm 더 가야 해" 같은 지시를 받으면
- 픽셀 좌표에 비율을 곱하여 실제 거리를 계산하고 조절할 수 있습니다

## 🐛 문제 해결

### 가상환경 활성화가 안 될 때 (Windows PowerShell)

PowerShell에서 실행 정책 오류가 발생하면:
```powershell
# 방법 1: 현재 사용자에게 실행 정책 설정 (권장)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 방법 2: 현재 프로세스에만 실행 정책 우회
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# 방법 3: CMD 사용
# CMD에서는 실행 정책이 필요 없으므로 cmd를 열어서 실행
```

**실행 정책 확인:**
```powershell
Get-ExecutionPolicy
```

**PowerShell에서 직접 실행:**
```powershell
# 실행 정책 확인 후, 필요시 위의 명령어로 설정
.\robot\Scripts\Activate.ps1
```

### 카메라가 인식되지 않을 때

1. `config.json`에서 `camera_number` 확인 (보통 0 또는 1)
2. 다른 프로그램이 카메라를 사용 중인지 확인
3. 카메라 드라이버 확인

### Firebase 연결 오류

1. `servingstation-firebase-adminsdk-fbsvc-231e400af8.json` 파일이 `myproject` 폴더에 있는지 확인
2. Firebase 서비스 계정 키 파일이 유효한지 확인

## 📝 참고

- 실제 모드에서는 캘리브레이션 포인트가 정확해야 정확한 좌표 변환이 가능합니다
- 테스트 모드에서는 섹터 ID가 정확히 설정되어 있어야 합니다
- Firebase의 `items[0].id` 값이 1, 2, 3 중 하나여야 합니다

