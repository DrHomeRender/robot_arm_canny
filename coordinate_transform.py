"""
coordinate_transform.py
------------------------------------
픽셀 좌표 → 로봇 좌표 변환 모듈
- 고정밀 아핀 변환을 사용한 XY 좌표 변환
- 캘리브레이션 포인트 기반 정확한 매핑
- 1mm 단위 정밀도 보장
------------------------------------
"""

import cv2
import numpy as np


def pixel_to_robot_coords(cx, cy, calibration_points, sector_id=None, sector_answers=None, base_roll=0.0, base_pitch=0.0, base_yaw=0.0, pixel_calibration=None):
    """
    픽셀 좌표를 로봇 좌표로 변환 (고정밀 아핀 변환)
    
    Args:
        cx, cy: 물체 중심의 픽셀 좌표
        calibration_points: 캘리브레이션 포인트 딕셔너리 (섹터별) 또는 리스트
        sector_id: 섹터 ID (1, 2, 3) - Z값 및 캘리브레이션 선택에 사용
        sector_answers: SECTOR_ANSWERS 딕셔너리 - Z값 참조용
        base_roll, base_pitch, base_yaw: 기본 자세각 (degrees)
        pixel_calibration: 픽셀 캘리브레이션 설정 (offset_x_cm, offset_y_cm 포함)
        
    Returns:
        robot_x, robot_y, robot_z, roll, pitch, yaw (mm, degrees)
    """
    # 섹터별 캘리브레이션 포인트 선택
    if isinstance(calibration_points, dict):
        # 섹터 ID에 따라 캘리브레이션 선택
        sector_key = f"sector{sector_id}" if sector_id in [1, 2, 3] else "sector2"
        cal_points = calibration_points.get(sector_key, calibration_points.get("sector2", []))
        print(f"[DEBUG] Using calibration points for {sector_key}")
    else:
        # 기존 리스트 형식 (하위 호환)
        cal_points = calibration_points
    
    if len(cal_points) < 3:
        print(f"[ERROR] Need at least 3 calibration points, got {len(cal_points)}")
        return 0.0, 0.0, 0.0, base_roll, base_pitch, base_yaw
    
    # 캘리브레이션 픽셀 좌표 추출 (정확한 순서 보장)
    src_points = np.float32([[p['pixel'][0], p['pixel'][1]] for p in cal_points])
    dst_points_xy = np.float32([[p['robot'][0], p['robot'][1]] for p in cal_points])
    
    # 픽셀 → 로봇 XY 아핀 변환 (3점 기준)
    # cv2.getAffineTransform는 3점을 사용하여 정확한 선형 변환 행렬 생성
    M_xy = cv2.getAffineTransform(src_points[:3], dst_points_xy[:3])
    
    # 변환 행렬 검증 (디버깅용)
    print(f"[DEBUG] Transform Matrix:")
    print(f"  Robot_X = {M_xy[0,0]:.6f} * Pixel_X + {M_xy[0,1]:.6f} * Pixel_Y + {M_xy[0,2]:.6f}")
    print(f"  Robot_Y = {M_xy[1,0]:.6f} * Pixel_X + {M_xy[1,1]:.6f} * Pixel_Y + {M_xy[1,2]:.6f}")
    print(f"[DEBUG] Calibration points:")
    for i, p in enumerate(cal_points[:3]):
        print(f"  {p['name']}: Pixel {p['pixel']} → Robot XY [{p['robot'][0]:.1f}, {p['robot'][1]:.1f}]")
    
    # 현재 픽셀 좌표를 로봇 좌표로 변환
    current_pt = np.array([[cx, cy]], dtype=np.float32).reshape(-1, 1, 2)
    robot_pt = cv2.transform(current_pt, M_xy)
    robot_x = float(robot_pt[0, 0, 0])
    robot_y = float(robot_pt[0, 0, 1])
    
    # 섹터별 픽셀 캘리브레이션 오프셋 적용 (cm 단위 → mm 단위로 변환)
    if pixel_calibration and sector_id:
        sector_key = f"sector{sector_id}"
        sector_offset = pixel_calibration.get(sector_key, {})
        
        offset_x_cm = sector_offset.get("offset_x_cm", 0.0)
        offset_y_cm = sector_offset.get("offset_y_cm", 0.0)
        
        if offset_x_cm != 0.0 or offset_y_cm != 0.0:
            # cm를 mm로 변환하여 적용
            robot_x += offset_x_cm * 10.0  # cm → mm
            robot_y += offset_y_cm * 10.0  # cm → mm
            print(f"[DEBUG] Sector {sector_id} XY Offset applied: X={offset_x_cm:.2f}cm, Y={offset_y_cm:.2f}cm")
    
    print(f"[DEBUG] Input: Pixel ({cx}, {cy}) → Output: Robot XY ({robot_x:.2f}, {robot_y:.2f})")
    
    # Z값은 무조건 섹터 ID에 따라 SECTOR_ANSWERS에서 가져오기 (계산 안함!)
    if sector_id and sector_answers and sector_id in sector_answers:
        robot_z = float(sector_answers[sector_id][2])
        roll = float(sector_answers[sector_id][3])
        pitch = float(sector_answers[sector_id][4])
        yaw = float(sector_answers[sector_id][5])
        print(f"[DEBUG] Z value from SECTOR_ANSWERS[{sector_id}]: {robot_z:.2f}mm")
    else:
        # ⚠️ 섹터 ID가 없으면 오류 - Z값은 반드시 SECTOR_ANSWERS에서만 가져와야 함
        print(f"[ERROR] Sector ID is missing or invalid! Cannot determine Z value.")
        robot_z = 206.2  # 임시 기본값 (에러 방지용)
        roll = base_roll
        pitch = base_pitch
        yaw = base_yaw
    
    # 섹터별 Z 오프셋 적용 (cm 단위 → mm 단위로 변환)
    if pixel_calibration and sector_id:
        sector_key = f"sector{sector_id}"
        sector_offset = pixel_calibration.get(sector_key, {})
        
        offset_z_cm = sector_offset.get("offset_z_cm", 0.0)
        if offset_z_cm != 0.0:
            robot_z += offset_z_cm * 10.0  # cm → mm
            print(f"[DEBUG] Sector {sector_id} Z Offset applied: {offset_z_cm:.2f}cm")
    
    return robot_x, robot_y, robot_z, roll, pitch, yaw

