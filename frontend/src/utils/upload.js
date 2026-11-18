import { uploadFileApi } from '@/api/file'
import { ElMessage } from 'element-plus'

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
const MAX_IMAGE_SIZE = 1024 * 1024 * 2 // 2MB

/**
 * 头像/图片上传前的统一校验：格式 + 大小
 */
export function beforeAvatarUpload(file) {
  if (!IMAGE_TYPES.includes(file.type)) {
    ElMessage.error('上传图片只能是 JPG/PNG/GIF/WEBP 格式!')
    return false
  }
  if (file.size > MAX_IMAGE_SIZE) {
    ElMessage.error('上传图片大小不能超过 2MB!')
    return false
  }
  return true
}

/**
 * 统一图片上传逻辑，返回上传后的访问 url，失败返回空串
 */
export async function handleUploadFile(options) {
  try {
    const res = await uploadFileApi(options.file)
    if (res.code === 200) {
      return res.data?.url || ''
    }
  } catch (error) {
    ElMessage.error(error.message || '上传失败')
  }
  return ''
}
