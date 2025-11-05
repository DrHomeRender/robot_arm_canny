"""
calibration_tool.py
------------------------------------
픽셀 대비 실제 길이 비율 측정 도구
- 19cm 물체를 영상에 놓고 측정
- 스페이스바를 누르면 txt 파일에 기록
- 나중에 조절 가능하도록 비율 저장
------------------------------------
"""

import cv2
import math
import time
from datetime import datetime
from config_loader import load_config


def find_longest_axis(contour, center):
    """
    컨투어에서 가장 긴 축을 찾는 함수
    Returns: (point_A, point_B, angle_deg, pixel_length)
    """
    # 컨투어의 모든 점들
    points = contour.reshape(-1, 2)
    
    max_length = 0
    best_A = None
    best_B = None
    best_angle = 0
    
    # 모든 점 쌍을 확인하여 가장 긴 거리 찾기
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            pt1 = tuple(points[i])
            pt2 = tuple(points[j])
            
            # 거리 계산
            dx = pt2[0] - pt1[0]
            dy = pt2[1] - pt1[1]
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > max_length:
                max_length = length
                best_A = pt1
                best_B = pt2
                # 각도 계산 (도 단위)
                angle_rad = math.atan2(dy, dx)
                best_angle = math.degrees(angle_rad)
    
    return best_A, best_B, best_angle, max_length


def main():
    # 설정 로드
    config = load_config()
    cam_cfg = config.get('camera', {})
    edge_cfg = config.get('edge_detection', {})
    
    # 실제 물체 길이 (cm)
    REAL_LENGTH_CM = 19.0  # 19cm
    
    # 로그 파일 경로
    log_file = f"calibration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print("=" * 80)
    print("🎯 픽셀 대비 실제 길이 비율 측정 도구")
    print("=" * 80)
    print(f"[설정] 실제 물체 길이: {REAL_LENGTH_CM}cm")
    print(f"[설정] 카메라 번호: {cam_cfg.get('camera_number', 0)}")
    print(f"[설정] 로그 파일: {log_file}")
    print("")
    print("키보드:")
    print("  [SPACE] 현재 측정값을 로그 파일에 저장")
    print("  [Q/ESC] 종료")
    print("")
    
    # 카메라 초기화
    cap = cv2.VideoCapture(cam_cfg.get("camera_number", 0))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg.get("width", 640))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg.get("height", 480))
    
    if not cap.isOpened():
        print("[ERROR] 카메라를 열 수 없습니다.")
        return
    
    print("[Camera] Video stream opened.")
    print("")
    
    measurement_count = 0
    
    while True:
        ok, frame = cap.read()
        if not ok:
            print("[ERROR] 카메라 프레임을 읽을 수 없습니다.")
            break
        
        # 영상 처리
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (edge_cfg.get("gaussian_blur_kernel", 5),) * 2, 0)
        edges = cv2.Canny(blurred, 
                         edge_cfg.get("canny_threshold1", 50), 
                         edge_cfg.get("canny_threshold2", 150))
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        display = frame.copy()
        H, W = frame.shape[:2]
        
        # 중앙선 그리기
        cv2.line(display, (W//2, 0), (W//2, H), (80, 80, 80), 1)
        cv2.line(display, (0, H//2), (W, H//2), (80, 80, 80), 1)
        
        current_measurement = None
        
        if contours:
            # 가장 큰 컨투어 찾기
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            
            if area > edge_cfg.get("min_contour_area", 500):
                # 중심점 계산
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"]/M["m00"])
                    cy = int(M["m01"]/M["m00"])
                    
                    # 가장 긴 축 찾기
                    point_A, point_B, angle_deg, pix_len = find_longest_axis(c, (cx, cy))
                    
                    if point_A and point_B:
                        # 컨투어 그리기
                        cv2.drawContours(display, [c], -1, (0, 255, 0), 2)
                        cv2.circle(display, (cx, cy), 5, (255, 0, 0), -1)
                        cv2.line(display, point_A, point_B, (0, 255, 255), 2)
                        
                        # 픽셀 대비 실제 길이 비율 계산
                        # 픽셀 길이 (pix_len) → 실제 길이 (REAL_LENGTH_CM)
                        ratio_pixel_to_cm = REAL_LENGTH_CM / pix_len if pix_len > 0 else 0
                        ratio_cm_to_pixel = pix_len / REAL_LENGTH_CM if REAL_LENGTH_CM > 0 else 0
                        
                        current_measurement = {
                            "pixel_length": pix_len,
                            "real_length_cm": REAL_LENGTH_CM,
                            "ratio_pixel_to_cm": ratio_pixel_to_cm,
                            "ratio_cm_to_pixel": ratio_cm_to_pixel,
                            "cx": cx,
                            "cy": cy,
                            "angle_deg": angle_deg
                        }
                        
                        # 화면에 정보 표시
                        info_y = 30
                        cv2.putText(display, f"Pixel Length: {pix_len:.1f} px", 
                                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        info_y += 25
                        cv2.putText(display, f"Real Length: {REAL_LENGTH_CM} cm", 
                                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        info_y += 25
                        cv2.putText(display, f"Ratio: {ratio_pixel_to_cm:.4f} cm/px", 
                                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        info_y += 25
                        cv2.putText(display, f"Center: ({cx}, {cy})", 
                                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        info_y += 25
                        cv2.putText(display, f"Angle: {angle_deg:.1f} deg", 
                                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 저장된 측정 횟수 표시
        cv2.putText(display, f"Saved: {measurement_count} measurements", 
                   (10, H - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow("Calibration Tool - Pixel to Real Length Ratio", display)
        key = cv2.waitKey(1) & 0xFF
        
        if key in [27, ord("q")]:
            break
        elif key == ord(" "):
            # 스페이스바: 현재 측정값 저장
            if current_measurement:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Measurement #{measurement_count + 1} - {timestamp}\n")
                    f.write(f"{'='*60}\n")
                    f.write(f"Pixel Length: {current_measurement['pixel_length']:.2f} px\n")
                    f.write(f"Real Length: {current_measurement['real_length_cm']:.2f} cm\n")
                    f.write(f"Ratio (cm/px): {current_measurement['ratio_pixel_to_cm']:.6f}\n")
                    f.write(f"Ratio (px/cm): {current_measurement['ratio_cm_to_pixel']:.6f}\n")
                    f.write(f"Center Pixel: ({current_measurement['cx']}, {current_measurement['cy']})\n")
                    f.write(f"Angle: {current_measurement['angle_deg']:.2f} deg\n")
                    f.write(f"{'='*60}\n")
                
                measurement_count += 1
                print(f"\n[SAVED] Measurement #{measurement_count} saved to {log_file}")
                print(f"  Pixel: {current_measurement['pixel_length']:.2f} px")
                print(f"  Real: {current_measurement['real_length_cm']:.2f} cm")
                print(f"  Ratio: {current_measurement['ratio_pixel_to_cm']:.6f} cm/px\n")
            else:
                print("[WARNING] 물체가 감지되지 않았습니다. 측정값을 저장할 수 없습니다.")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n[INFO] 총 {measurement_count}개의 측정값이 저장되었습니다.")
    print(f"[INFO] 로그 파일: {log_file}")
    print("프로그램을 종료합니다.")


if __name__ == "__main__":
    main()

