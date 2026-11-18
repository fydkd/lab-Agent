<template>
    <div style="width: 50%">
        <el-card>
            <template #header>
                <div style="font-size: 16px; font-weight: bold">
                    <span>个人信息</span>
                </div>
            </template>
            <el-form 
            ref="formRef" 
            :rules="rules" 
            :model="form" 
            label-width="80px" 
            style="width: 100%; padding-right: 50px"
            v-loading="loading"
            >
                <el-form-item label="头像">
                    <el-upload
                        class="avatar-uploader"
                        :http-request="handleUploadFile"
                        :show-file-list="false"
                        accept="image/jpeg, image/png, image/gif, image/webp"
                        :before-upload="beforeAvatarUpload"
                    >
                        <img v-if="form.avatar" :src="form.avatar" class="avatar" />
                        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
                    </el-upload>
                </el-form-item>
                <el-form-item label="账号 :">
                    <el-input disabled v-model="form.username" placeholder="请输入账号"></el-input>
                </el-form-item>
                <el-form-item label="名称 :" prop="name">
                    <el-input v-model="form.name" placeholder="请输入名称" />
                </el-form-item>
                <el-form-item label="角色 :">
                    <el-input disabled v-model="roleLabel" />
                </el-form-item>
                <el-form-item label="邮箱 :" prop="email">
                    <el-input v-model="form.email" placeholder="请输入邮箱" />
                </el-form-item>
                <el-form-item label="手机号 :" prop="phone">
                    <el-input v-model="form.phone" placeholder="请输入手机号" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" :loading="submitting" @click="handleSubmit">保存修改</el-button>
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { getUserInfo, updateUserInfo } from '@/api/user'
import { ElMessage } from 'element-plus'
import { useUser } from '@/utils/user'
import { beforeAvatarUpload, handleUploadFile as uploadFile } from '@/utils/upload'

const {updateUser} = useUser()

const loading = ref(false)
const submitting = ref(false)

const form = ref({
    username: '',
    name: '',
    email: '',
    phone: '',
    avatar: '',
    role: ''
})

const rules = reactive({
    name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
    email: [{ type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }],
    phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的11位数字手机号', trigger: 'blur' }]
})

const roleLabel = computed(() => {
    return form.value.role === 'admin' ? '管理员' : form.value.role === 'student' ? '学生' : '未知角色'
})

const formRef = ref()

const loadUserInfo = async () => {
    loading.value = true
    try {
        const res = await getUserInfo()
        if (res.code === 200) {
            Object.assign(form.value, res.data)
        }
    } finally {
        loading.value = false
    }
}

const handleUploadFile = async (options) => {
    const url = await uploadFile(options)
    if (url) {
        form.value.avatar = url
    }
}



const handleSubmit = async () => {
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
    submitting.value = true
    try {
        const res = await updateUserInfo(form.value)
        if (res.code === 200) {
            updateUser(res.data)
            ElMessage.success('修改成功')
        } else {
            ElMessage.error(res.msg || '修改失败')
        }
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    loadUserInfo()
})
</script>

<style scoped>
.avatar-uploader .avatar {
  width: 100px;
  height: 100px;
  display: block;
}
</style>
<style>
.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}
.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}
.el-icon.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  text-align: center;
}
</style>
