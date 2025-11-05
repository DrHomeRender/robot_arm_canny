"""
firebase_manager.py
------------------------------------
Firebase 연동 모듈
- 초기화
- Pose 전송
- 주문 상태 모니터링 (waiting_pose 감지)
------------------------------------
"""

import os
import time
import threading
import firebase_admin
from firebase_admin import credentials, db


# ✅ Firebase 초기화
def init_firebase():
    """Firebase 초기화 및 /orders 참조 반환"""
    base = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base, "servingstation-firebase-adminsdk-fbsvc-231e400af8.json")

    if not firebase_admin._apps:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://servingstation-default-rtdb.asia-southeast1.firebasedatabase.app"
        })
        print("[Firebase] Initialized successfully!")
    else:
        print("[Firebase] Already initialized (using existing app)")

    return db.reference("/orders")


# ✅ Pose 데이터 전송
def send_to_firebase(orders_ref, order_id, x, y, z, roll, pitch, yaw):
    """Firebase에 로봇 팔 pose 데이터 전송"""
    pose_data = {
        "type": "coords",
        "values": [
            round(x, 2),
            round(y, 2),
            round(z, 2),
            round(roll, 2),
            round(pitch, 2),
            round(yaw, 2)
        ]
    }

    orders_ref.child(order_id).update({"pose": pose_data})
    print(f"[Firebase] Sent pose to {order_id}:")
    print(f"           X={x:.1f}, Y={y:.1f}, Z={z:.1f}, R={roll:.1f}, P={pitch:.1f}, Y={yaw:.1f}")


# ✅ 주문 상태 모니터링
class FirebaseMonitor:
    """Firebase /orders 구조 모니터링 (waiting_pose 감지)"""

    def __init__(self, orders_ref):
        self.orders_ref = orders_ref
        self.auto_detect_flag = {"enabled": False}
        self.target_order_id = None
        self.sector_id = None  # items[0].id 값 (1, 2, 3)
        self.monitoring = False

    def start_monitoring(self):
        """백그라운드 모니터링 시작"""
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
        print("[Monitor] Firebase monitoring started (detecting status=waiting_pose + pose_required=true)")

    def stop_monitoring(self):
        """모니터링 종료"""
        self.monitoring = False
        print("[Monitor] Firebase monitoring stopped")

    def _monitor_loop(self):
        """주기적으로 Firebase 상태 확인"""
        while self.monitoring:
            orders_data = self.orders_ref.get() or {}

            found_waiting = False
            for order_id, order_data in orders_data.items():
                if not isinstance(order_data, dict):
                    continue

                status = order_data.get("status", "").lower()
                pose_required = order_data.get("pose_required", False)

                # waiting_pose 상태이면 감지 활성화
                if status == "waiting_pose" and pose_required:
                    found_waiting = True
                    
                    # items[0].id 값 읽기 (섹터 ID: 1, 2, 3)
                    items = order_data.get("items", [])
                    sector_id = None
                    if items and len(items) > 0 and isinstance(items[0], dict):
                        item_id = items[0].get("id")
                        if item_id:
                            try:
                                sector_id = int(item_id)
                            except (ValueError, TypeError):
                                sector_id = None
                    
                    if not self.auto_detect_flag["enabled"]:
                        print(f"\n{'='*60}")
                        print(f"[AUTO DETECT ACTIVATED]")
                        print(f"Order ID: {order_id}")
                        print(f"Status: {status}, pose_required=True")
                        if sector_id:
                            print(f"Sector ID: {sector_id} (from items[0].id)")
                        else:
                            print(f"⚠️  Sector ID not found in items[0].id")
                        print(f"{'='*60}\n")

                        self.target_order_id = order_id
                        self.sector_id = sector_id
                        self.auto_detect_flag["enabled"] = True
                    else:
                        # 이미 활성화된 상태에서 섹터 ID가 변경되었을 수 있음
                        if sector_id != self.sector_id:
                            self.sector_id = sector_id
                            if sector_id:
                                print(f"[Monitor] Sector ID updated: {sector_id}")
                    break

            # waiting_pose가 없으면 비활성화
            if not found_waiting and self.auto_detect_flag["enabled"]:
                print("\n[AUTO DETECT DEACTIVATED] No waiting orders")
                self.auto_detect_flag["enabled"] = False
                self.target_order_id = None
                self.sector_id = None

            time.sleep(0.5)
