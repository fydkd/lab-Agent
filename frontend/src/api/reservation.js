import request from "@/utils/request"

/**
 * 新增预约
 */
export function createReservation(data) {
    return request({
        url: '/api/reservation',    
        method: 'post',
        data
    })
}

/**
 * 获取预约分页列表
 */
export function getReservationPageList(params) {
    return request({
        url: '/api/reservation/list',    
        method: 'get',
        params
    })
}

/**
 * 审核预约
 */
export function auditReservation(reservation_id, status) {
    return request({
        url: `/api/reservation/${reservation_id}/audit`,    
        method: 'put',
        data: { status }    
    })
}

/**
 * 取消预约
 */
export function cancelReservation(reservation_id) {
    return request({
        url: `/api/reservation/${reservation_id}/cancel`,    
        method: 'put'
    })
}