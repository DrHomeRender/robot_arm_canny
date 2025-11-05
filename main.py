"""
main.py
------------------------------------
프로그램 진입점 (myproject - 영상 기반 좌표 전송)
- 설정 로드
- Firebase 초기화 및 모니터링 시작
- Vision 루프 실행

사용법:
    python main.py          # 실제 모드: 카메라 영상에서 좌표 계산
    python main.py test     # 테스트 모드: Sector ID 기반 정답 좌표 전송
------------------------------------
"""

import sys
import argparse
import time
from datetime import datetime

# 내부 모듈 임포트
from config_loader import load_config
from firebase_manager import init_firebase, FirebaseMonitor
from vision_processor import run_vision_loop


def main():
    # 인자 파싱
    parser = argparse.ArgumentParser(description="myproject - 영상 기반 좌표 전송")
    parser.add_argument("mode", nargs="?", default=None,
                       help="실행 모드: 'test' (테스트 모드) 또는 생략 (실제 모드)")
    args = parser.parse_args()
    
    # test 인자만 받으면 테스트 모드, 그 외는 모두 실제 모드
    test_mode = (args.mode == "test")
    
    print("=" * 80)
    if test_mode:
        print("🎥 myproject - 테스트 모드 (Sector ID 기반 정답 좌표 전송)")
    else:
        print("🎥 myproject - 실제 모드 (카메라 영상 기반 좌표 계산 및 전송)")
    print("=" * 80)
    print(f"[시작시간] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # 1️⃣ 설정 로드
    config = load_config()
    cam_cfg = config.get('camera', {})
    auto_cfg = config.get('auto_send', {})
    print(f"[Mode] {'테스트 모드 (Sector ID 기반)' if test_mode else '실제 모드 (영상 계산)'}")
    print(f"[Config] 카메라 번호: {cam_cfg.get('camera_number', 0)}")
    print(f"[Config] 자동 전송 모드: {auto_cfg.get('active_spacebar', False)}")
    print("")

    # 2️⃣ Firebase 초기화
    try:
        orders_ref = init_firebase()
    except Exception as e:
        print(f"[ERROR] Firebase 초기화 실패: {e}")
        sys.exit(1)

    # 3️⃣ Firebase 모니터 시작 (자동 모드일 때만)
    monitor = None
    if not auto_cfg.get('active_spacebar', False):
        monitor = FirebaseMonitor(orders_ref)
        monitor.start_monitoring()

    # 4️⃣ Vision 루프 실행
    try:
        run_vision_loop(config, orders_ref, monitor, test_mode=test_mode)
    except KeyboardInterrupt:
        print("\n[INFO] 사용자 인터럽트로 종료")
    except Exception as e:
        print(f"[ERROR] Vision 루프 실행 중 오류: {e}")
    finally:
        # 안전한 종료 처리
        if monitor:
            monitor.stop_monitoring()
        print("\n프로그램을 종료합니다.")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
