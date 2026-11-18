import os
from fastapi import APIRouter, File, UploadFile
import time
import uuid
import shutil
from pathlib import Path
from app.common.response import Response
from app.common.exceptions import BusinessException
from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from app.schemas.file import FileResponse

router = APIRouter(prefix="/files", tags=["文件管理"])


@router.post("/upload")
def upload(file: UploadFile = File(...)):
    """上传文件"""
    if not file.filename:
        raise BusinessException(message="文件名不能为空")

    # 原始文件名, 用户头像.jpg
    original_name = os.path.basename(file.filename)
    # 文件后缀 .jpg
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessException(message=f"文件扩展名错误, 仅支持: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    # 文件大小校验
    if file.size and file.size > MAX_FILE_SIZE:
        raise BusinessException(message="文件大小超过限制, 最大支持: 100MB")

    # 文件名校验，唯一性
    disk_name = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}{ext}"
    # 文件存储路径
    save_path = UPLOAD_DIR / disk_name

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return Response.success(
        data=FileResponse(
            original_name=original_name,
            disk_name=disk_name,
            size=file.size,
            url=f"/uploads/{disk_name}"
        )
    )
