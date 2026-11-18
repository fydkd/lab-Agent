// 预约状态常量，集中维护避免各页面重复定义且不一致
export const RESERVATION_STATUS = {
  PENDING: 0, // 待审核
  APPROVED: 1, // 已通过
  REJECTED: 2, // 已拒绝
  CANCELED: 3, // 已取消
}

export const RESERVATION_STATUS_TEXT = {
  [RESERVATION_STATUS.PENDING]: '待审核',
  [RESERVATION_STATUS.APPROVED]: '已通过',
  [RESERVATION_STATUS.REJECTED]: '已拒绝',
  [RESERVATION_STATUS.CANCELED]: '已取消',
}

// Element Plus tag 类型
export const RESERVATION_STATUS_TAG_TYPE = {
  [RESERVATION_STATUS.PENDING]: 'warning',
  [RESERVATION_STATUS.APPROVED]: 'success',
  [RESERVATION_STATUS.REJECTED]: 'danger',
  [RESERVATION_STATUS.CANCELED]: 'info',
}

export function getReservationStatusText(status) {
  return RESERVATION_STATUS_TEXT[status] || '-'
}

export function getReservationStatusTagType(status) {
  return RESERVATION_STATUS_TAG_TYPE[status] || '-'
}
