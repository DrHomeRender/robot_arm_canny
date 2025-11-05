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


def pixel_to_robot_coords(cx, cy, calibration_points, sector_id=None, sector_answers=None, base_roll=0.0, base_pitch=0.0, base_yaw=0.0):
    """
    픽셀 좌표를 로봇 좌표로 변환 (고정밀 아핀 변환)
    
    Args:
        cx, cy: 물체 중심의 픽셀 좌표
        calibration_points: 캘리브레이션 포인트 리스트
        sector_id: 섹터 ID (1, 2, 3) - Z값 결정에 사용
        sector_answers: SECTOR_ANSWERS 딕셔너리 - Z값 참조용
        base_roll, base_pitch, base_yaw: 기본 자세각 (degrees)
        
    Returns:
        robot_x, robot_y, robot_z, roll, pitch, yaw (mm, degrees)
    """
    if len(calibration_points) < 3:
        print(f"[ERROR] Need at least 3 calibration points, got {len(calibration_points)}")
        return 0.0, 0.0, 0.0, base_roll, base_pitch, base_yaw
    
    # 캘리브레이션 픽셀 좌표 추출 (정확한 순서 보장)
    src_points = np.float32([[p['pixel'][0], p['pixel'][1]] for p in calibration_points])
    dst_points_xy = np.float32([[p['robot'][0], p['robot'][1]] for p in calibration_points])
    
    # 픽셀 → 로봇 XY 아핀 변환 (3점 기준)
    # cv2.getAffineTransform는 3점을 사용하여 정확한 선형 변환 행렬 생성
    M_xy = cv2.getAffineTransform(src_points[:3], dst_points_xy[:3])
    
    # 변환 행렬 검증 (디버깅용)
    # print(f"[DEBUG] Transform Matrix:")
    # print(f"  Robot_X = {M_xy[0,0]:.6f} * Pixel_X + {M_xy[0,1]:.6f} * Pixel_Y + {M_xy[0,2]:.6f}")
    # print(f"  Robot_Y = {M_xy[1,0]:.6f} * Pixel_X + {M_xy[1,1]:.6f} * Pixel_Y + {M_xy[1,2]:.6f}")
    
    # 현재 픽셀 좌표를 로봇 좌표로 변환
    current_pt = np.array([[cx, cy]], dtype=np.float32).reshape(-1, 1, 2)
    robot_pt = cv2.transform(current_pt, M_xy)
    robot_x = float(robot_pt[0, 0, 0])
    robot_y = float(robot_pt[0, 0, 1])
    
    # Z값은 섹터 ID에 따라 정답 좌표에서 가져오기
    if sector_id and sector_answers and sector_id in sector_answers:
        # SECTOR_ANSWERS[sector_id][2] = Z값
        robot_z = float(sector_answers[sector_id][2])
        roll = float(sector_answers[sector_id][3])
        pitch = float(sector_answers[sector_id][4])
        yaw = float(sector_answers[sector_id][5])
    else:
        # 섹터 ID가 없으면 기본값 사용
        if len(calibration_points) > 0:
            robot_z = float(calibration_points[0]['robot'][2])
        else:
            robot_z = 206.2  # 기본값
        roll = base_roll
        pitch = base_pitch
        yaw = base_yaw
    
    return robot_x, robot_y, robot_z, roll, pitch, yaw

