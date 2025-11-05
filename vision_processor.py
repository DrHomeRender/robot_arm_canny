"""
vision_processor.py
------------------------------------
영상 입력, 경계 검출, 좌표 계산 및 Firebase 전송 루프
(main.py에서 호출)
------------------------------------
"""

import cv2
import math
import time
import numpy as np
from datetime import datetime
from firebase_manager import send_to_firebase
from constants import SECTOR_ANSWERS
from coordinate_transform import pixel_to_robot_coords


# 윤곽선 기반 최단축 계산
def find_shortest_axis(contour, center, angle_tolerance_rad=0.26):
    """윤곽선의 중심에서 가장 가까운 점(A)과 그 반대쪽 점(B)을 찾아 각도/길이 계산"""
    distances = [(np.sqrt((pt[0][0] - center[0])**2 + (pt[0][1] - center[1])**2), pt[0]) for pt in contour]
    distances.sort(key=lambda x: x[0])
    point_A = distances[0][1]

    angle_to_A = math.atan2(point_A[1] - center[1], point_A[0] - center[0])
    opposite_angle = angle_to_A + math.pi

    point_B = point_A
    best_dist = float("inf")
    for point in contour:
        pt = point[0]
        angle = math.atan2(pt[1] - center[1], pt[0] - center[0])
        diff = abs(angle - opposite_angle)
        if diff > math.pi:
            diff = 2 * math.pi - diff
        if diff < angle_tolerance_rad:
            dist = np.sqrt((pt[0] - center[0])**2 + (pt[1] - center[1])**2)
            if dist < best_dist:
                best_dist = dist
                point_B = pt

    dx, dy = point_B[0] - point_A[0], point_B[1] - point_A[1]
    angle_deg = math.degrees(math.atan2(dy, dx))
    length = np.sqrt(dx**2 + dy**2)
    return point_A, point_B, angle_deg, length


# 거리 계산 (삼각측량)
def calculate_distance(pixel_length, real_length_mm, img_width, hfov_deg, fov_correction=1.0):
    if pixel_length <= 0:
        return 0.0
    hfov_rad = math.radians(hfov_deg) * fov_correction
    return (real_length_mm * img_width) / (2.0 * pixel_length * math.tan(hfov_rad / 2.0))


# Vision 메인 루프
def run_vision_loop(config, orders_ref, monitor, test_mode=False):
    """
    카메라 → 감지 → Firebase 전송 전체 루프
    
    Args:
        config: 설정 딕셔너리
        orders_ref: Firebase orders 참조
        monitor: FirebaseMonitor 인스턴스
        test_mode: True면 테스트 모드 (Sector ID 기반), False면 실제 모드 (영상 계산)
    """

    cam_cfg = config["camera"]
    obj_cfg = config["object"]
    edge_cfg = config["edge_detection"]
    axis_cfg = config["axis_detection"]
    auto_cfg = config["auto_send"]
    calibration_points = config.get("calibration_points", [])
    robot_transform = config.get("robot_transform", {})
    send_interval = auto_cfg["send_interval_sec"]
    
    # 기본 자세각
    base_roll = robot_transform.get("base_roll", 0.0)
    base_pitch = robot_transform.get("base_pitch", 0.0)
    base_yaw = robot_transform.get("base_yaw", 0.0)

    cap = cv2.VideoCapture(cam_cfg["camera_number"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg["height"])

    last_detection = None
    last_send_time = 0

    print("\n[Camera] Video stream opened.")
    if test_mode:
        print("[Mode] 테스트 모드: Sector ID 기반 정답 좌표 전송")
    else:
        print("[Mode] 실제 모드: 카메라 영상에서 좌표 계산 및 전송")
    print("키보드: [SPACE] 수동 전송, [Q/ESC] 종료")
    print("자동 모드: Firebase status=waiting_pose 감지 시 자동 전송\n")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[ERROR] 카메라 프레임을 읽을 수 없습니다.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (edge_cfg["gaussian_blur_kernel"],) * 2, 0)
        edges = cv2.Canny(blurred, edge_cfg["canny_threshold1"], edge_cfg["canny_threshold2"])

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        display = frame.copy()
        H, W = frame.shape[:2]

        if contours:
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            if area > edge_cfg["min_contour_area"]:
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                    point_A, point_B, angle_deg, pix_len = find_shortest_axis(c, (cx, cy), math.radians(axis_cfg["angle_tolerance_deg"]))
                    distance = calculate_distance(pix_len, obj_cfg["real_shortest_axis_mm"], W, cam_cfg["hfov_degree"], cam_cfg["fov_correction_factor"])

                    cv2.drawContours(display, [c], -1, (0, 255, 0), 2)
                    cv2.circle(display, (cx, cy), 5, (255, 0, 0), -1)
                    cv2.line(display, tuple(point_A), tuple(point_B), (0, 255, 255), 2)

                    last_detection = {"cx": cx, "cy": cy, "angle": angle_deg, "dist": distance}

        # 중앙 십자선
        cv2.line(display, (W//2, 0), (W//2, H), (80, 80, 80), 1)
        cv2.line(display, (0, H//2), (W, H//2), (80, 80, 80), 1)

        # Firebase waiting_pose 감지 시 자동 전송
        if monitor and monitor.auto_detect_flag["enabled"]:
            now = time.time()
            if now - last_send_time > send_interval:
                order_id = monitor.target_order_id
                
                if test_mode:
                    # 테스트 모드: Sector ID 기반 정답 좌표 전송
                    sector_id = monitor.sector_id
                    
                    if sector_id and sector_id in SECTOR_ANSWERS:
                        coords = SECTOR_ANSWERS[sector_id]
                        send_to_firebase(orders_ref, order_id, *coords)
                        print(f"\n[AUTO] 전송 완료")
                        print(f"Order ID: {order_id}")
                        print(f"Sector: {sector_id} → X={coords[0]:.1f}, Y={coords[1]:.1f}, Z={coords[2]:.1f}")
                        print(f"Roll={coords[3]:.2f}, Pitch={coords[4]:.2f}, Yaw={coords[5]:.2f}\n")
                        last_send_time = now
                    elif sector_id:
                        print(f"[AUTO] ⚠️  Invalid Sector ID: {sector_id} (expected 1, 2, or 3)")
                    else:
                        print(f"[AUTO] ⚠️  Sector ID not found in Firebase items[0].id")
                else:
                    # 실제 모드: 카메라 영상에서 계산한 좌표 전송
                    if last_detection:
                        cx = last_detection["cx"]
                        cy = last_detection["cy"]
                        distance = last_detection["dist"]
                        
                        # 섹터 ID 가져오기 (Z값 결정용)
                        sector_id = monitor.sector_id if monitor else None
                        
                        # 픽셀 좌표 → 로봇 좌표 변환 (고정밀)
                        robot_x, robot_y, robot_z, roll, pitch, yaw = pixel_to_robot_coords(
                            cx, cy, calibration_points,
                            sector_id=sector_id,
                            sector_answers=SECTOR_ANSWERS,
                            base_roll=base_roll,
                            base_pitch=base_pitch,
                            base_yaw=base_yaw
                        )
                        
                        send_to_firebase(orders_ref, order_id, robot_x, robot_y, robot_z, roll, pitch, yaw)
                        print(f"\n[AUTO] 전송 완료")
                        print(f"Order ID: {order_id}")
                        print(f"Pixel: ({cx}, {cy}) → Robot: X={robot_x:.2f}, Y={robot_y:.2f}, Z={robot_z:.2f}")
                        if sector_id:
                            print(f"Sector ID: {sector_id} (Z값: {robot_z:.2f}mm)")
                        print(f"Roll={roll:.2f}, Pitch={pitch:.2f}, Yaw={yaw:.2f}\n")
                        last_send_time = now
                    else:
                        print(f"[AUTO] ⚠️  물체가 감지되지 않았습니다")

        cv2.imshow("Camera2", display)
        key = cv2.waitKey(1) & 0xFF

        if key in [27, ord("q")]:
            break
        elif key == ord(" "):
            # 수동 전송 모드
            order_id = monitor.target_order_id if monitor else auto_cfg["firebase_order_id"]
            
            if test_mode:
                # 테스트 모드: Firebase에서 현재 섹터 ID 읽기
                sector_id = monitor.sector_id if monitor else None
                
                if sector_id and sector_id in SECTOR_ANSWERS:
                    coords = SECTOR_ANSWERS[sector_id]
                    send_to_firebase(orders_ref, order_id, *coords)
                    print(f"\n[MANUAL] 전송 완료")
                    print(f"Order ID: {order_id}")
                    print(f"Sector: {sector_id} → X={coords[0]:.1f}, Y={coords[1]:.1f}, Z={coords[2]:.1f}")
                    print(f"Roll={coords[3]:.2f}, Pitch={coords[4]:.2f}, Yaw={coords[5]:.2f}\n")
                    last_send_time = time.time()
                elif sector_id:
                    print(f"[MANUAL] ⚠️  Invalid Sector ID: {sector_id}")
                else:
                    print(f"[MANUAL] ⚠️  Sector ID not found. Check Firebase items[0].id")
            else:
                # 실제 모드: 카메라 영상에서 계산한 좌표 전송
                if last_detection:
                    cx = last_detection["cx"]
                    cy = last_detection["cy"]
                    distance = last_detection["dist"]
                    
                    # 섹터 ID 가져오기 (Z값 결정용)
                    sector_id = monitor.sector_id if monitor else None
                    
                    # 픽셀 좌표 → 로봇 좌표 변환 (고정밀)
                    robot_x, robot_y, robot_z, roll, pitch, yaw = pixel_to_robot_coords(
                        cx, cy, calibration_points,
                        sector_id=sector_id,
                        sector_answers=SECTOR_ANSWERS,
                        base_roll=base_roll,
                        base_pitch=base_pitch,
                        base_yaw=base_yaw
                    )
                    
                    send_to_firebase(orders_ref, order_id, robot_x, robot_y, robot_z, roll, pitch, yaw)
                    print(f"\n[MANUAL] 전송 완료")
                    print(f"Order ID: {order_id}")
                    print(f"Pixel: ({cx}, {cy}) → Robot: X={robot_x:.2f}, Y={robot_y:.2f}, Z={robot_z:.2f}")
                    if sector_id:
                        print(f"Sector ID: {sector_id} (Z값: {robot_z:.2f}mm)")
                    print(f"Roll={roll:.2f}, Pitch={pitch:.2f}, Yaw={yaw:.2f}\n")
                    last_send_time = time.time()
                else:
                    print(f"[MANUAL] ⚠️  물체가 감지되지 않았습니다")

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Vision loop 종료 완료.")
