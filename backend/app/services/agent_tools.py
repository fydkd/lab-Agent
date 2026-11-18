import datetime
from app.common.exceptions import BusinessException
from app.schemas.reservation import ReservationCreateRequest
from app.services import lab_service, reservation_service
from sqlalchemy.orm import Session
from langchain_core.tools import tool
from app.models.user import User
from app.services import kb_service, equipment_service
from app.database import SessionLocal
import json


def build_tools(db: Session, current_user: User):

    @tool
    def search_lab_docs(query: str) -> str:
        """搜索实验室相关文档"""
        try:
            return kb_service.search(query) or "没有找到相关资料"
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

    @tool
    def list_open_labs(keywords: str = "") -> str:
        """查询所有开放的实验室列表"""
        try:
            keywords = keywords.strip() or None
            session = SessionLocal()
            try:
                page = lab_service.get_lab_page_list(
                    session, keywords=keywords, page=1, page_size=10, status=1
                )
                rows = [
                    {
                        "id": item.id,
                        "name": item.name,
                        "location": item.location,
                        "capacity": item.capacity,
                        "open_time": item.open_time,
                        "close_time": item.close_time,
                    }
                    for item in page.list
                ]
            finally:
                session.close()
            return json.dumps({"total": page.total, "labs": rows}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

    @tool
    def list_lab_equipment(lab_id: int, keywords: str = "") -> str:
        """查询实验室下的设备列表"""
        try:
            keywords = keywords.strip() or None
            session = SessionLocal()
            try:
                page = equipment_service.get_equipment_page_list(
                    session, page=1, page_size=10, lab_id=int(lab_id), keywords=keywords
                )
                rows = [
                    {
                        "id": item.id,
                        "name": item.name,
                        "lab_id": item.lab_id,
                        "lab_name": item.lab_name,
                        "spec": item.spec,
                        "quantity": item.quantity,
                        "status": item.status,
                    }
                    for item in page.list
                ]
            finally:
                session.close()
            return json.dumps({"total": page.total, "equipments": rows}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

    @tool
    def create_lab_reservation(
        lab_id: int, 
        date: str,
        start_time: str,
        end_time: str,
        lab_name: str = "",
        equipment_id: int | None = None,
        remark: str | None = None,
        ) -> str:
        """创建实验室或设备预约
        
        Args:
            lab_id: 实验室ID，必须从 list_open_labs 返回结果中准确复制
            date: 预约日期，格式 YYYY-MM-DD
            start_time: 开始时间，格式 HH:MM
            end_time: 结束时间，格式 HH:MM
            lab_name: 实验室名称，用于交叉校验 lab_id 是否正确
            equipment_id: 设备ID，可选
            remark: 备注，可选
        """
        try:
            session = SessionLocal()
            try:
                lab = lab_service.get_lab(session, lab_id)
                if lab_name and lab_name.strip() not in lab.name:
                    return json.dumps(
                        {
                            "ok": False,
                            "error": f"lab_id={lab_id} 对应的实验室是「{lab.name}」，与「{lab_name}」不匹配，请重新调用 list_open_labs 确认正确的 lab_id",
                            "actual_lab_name": lab.name,
                        },
                        ensure_ascii=False,
                    )
                reservation = ReservationCreateRequest(
                    lab_id=lab_id,
                    equipment_id=equipment_id,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    remark=remark,
                )
                reservation_service.create_reservation(session, current_user, reservation)
            finally:
                session.close()
            return json.dumps(
                {
                    "ok": True, 
                    "message": "预约成功,请等待管理员审核", 
                    "lab_id": lab_id, 
                    "equipment_id": equipment_id,
                    "date": date,
                    "start_time": start_time,
                    "end_time": end_time
                    }, ensure_ascii=False)
        except BusinessException as e:
            return json.dumps({"ok": False, "error": e.message}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

    @tool
    def get_today() -> str:
        """查询当前日期"""
        return datetime.datetime.now().strftime("%Y-%m-%d")

    return [search_lab_docs, list_open_labs, list_lab_equipment, create_lab_reservation, get_today]