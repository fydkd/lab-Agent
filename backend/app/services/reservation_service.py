import asyncio
from app.common.response import PageResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.common.exceptions import BusinessException
from app.database import SessionLocal
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationResponse
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest


def get_reservation_page_list(db: Session, current_user: User, page: int, page_size: int, status: int | None = None):
    """获取用户预约记录"""
    query = db.query(Reservation)
    if current_user.role != "admin":
        query = query.filter(Reservation.user_id == current_user.id)
    if status is not None:
        query = query.filter(Reservation.status == status)
    total = query.count()
    items = (
        query.order_by(Reservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = []
    for item in items:
        res = ReservationResponse.model_validate(item)
        res.user_name = item.user.name if item.user else None
        res.lab_name = item.lab.name if item.lab else None
        res.equipment_name = item.equipment.name if item.equipment else None
        res.type = "设备" if item.equipment_id is not None else "实验室"
        result.append(res)

    return PageResponse(list=result, total=total)


def create_reservation(db: Session, current_user: User, data: ReservationCreateRequest):
    # 验证预约时间是否有效
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    if data.date < current_date:
        raise BusinessException(message="预约日期不能小于当前日期")
    if data.end_time < data.start_time:
        raise BusinessException(message="预约的结束时间不能小于开始时间")
    if data.date == current_date and data.end_time < current_time:
        raise BusinessException(message="预约开始时间不能小于当前时间")
    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    if lab.status != 1:
        raise BusinessException(message="实验室已关闭，不能预约")
    if lab.open_time and data.start_time < lab.open_time:
        raise BusinessException(message="预约时间不能早于实验室开放时间")
    if lab.close_time and data.end_time > lab.close_time:
        raise BusinessException(message="预约时间不能晚于实验室关闭时间")

    if data.equipment_id:
        equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        if not equipment:
            raise BusinessException(message="设备不存在")
        if equipment.status != 1:
            raise BusinessException(message="实验室设备正在维修中，不能预约")
        
    query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id, 
        Reservation.date == data.date,
        Reservation.status.in_([0, 1]),
        Reservation.start_time <= data.end_time,
        Reservation.end_time >= data.start_time
        )
    if data.equipment_id:
        query = query.filter(Reservation.equipment_id == data.equipment_id)
    else:
        query = query.filter(Reservation.equipment_id.is_(None))
    if query.first():
        raise BusinessException(message="实验室该时段已被预约")

    reservation_model = Reservation(
        user_id=current_user.id,
        lab_id=data.lab_id,
        equipment_id=data.equipment_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        remark=data.remark,
        status=0,
        )
    db.add(reservation_model)
    db.commit()


def cancel_reservation(db: Session, current_user: User, reservation_id: int):
    """取消预约"""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise BusinessException(message="预约不存在")
    if reservation.user_id != current_user.id:
        raise BusinessException(message="您没有权限取消该预约", code=403)
    if reservation.status != 0:
        raise BusinessException(message="当前状态不能取消，只能取消待预约状态的预约")
    reservation.status = 3
    db.commit()


def audit_reservation(db: Session, reservation_id: int, status: int):
    """审核预约"""
    if status not in [1, 2]:
        raise BusinessException(message="审核状态只能是通过或拒绝")
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise BusinessException(message="预约不存在")
    if reservation.status != 0:
        raise BusinessException(message="当前状态不能审核，只能审核待预约状态的预约")
    reservation.status = status
    db.commit()


def expire_pending_reservations():
    """过期待预约"""
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M")
        items = db.query(Reservation).filter(Reservation.status == 0).all()
        changed = False
        for item in items:
            if item.date < today or (item.date == today and item.end_time <= time):
                item.status = 3
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()


async def run_expire_scan():
    """异步过期预约扫描, 每分钟扫描一次"""
    try:
        while True:
            await asyncio.to_thread(expire_pending_reservations)
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        return
