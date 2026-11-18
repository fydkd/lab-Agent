<template>
    <div>
        <el-card>
            <template #header>
                <div style="font-size: 16px; font-weight: bold">
                    <span>设备管理</span>
                </div>
            </template>
            <div style="margin-bottom: 10px">
                <el-input 
                placeholder="请输入设备名称查询" 
                v-model="params.keywords"
                style="width: 240px; margin-right: 8px"
                clearable
                @keyup.enter="handleSearch"
                @clear="handleSearch"
                ></el-input>
                <el-select 
                placeholder="请选择实验室"
                v-model="params.lab_id"
                style="width: 200px; margin-right: 8px" 
                clearable
                @change="handleSearch"
                @clear="handleSearch"
                >
                    <el-option 
                    v-for="item in labOptions" 
                    :key="item.id" 
                    :value="item.id" 
                    :label="item.name"></el-option>
                </el-select>
                <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
                <el-button type="success" :icon="Plus" @click="handleAdd">新增</el-button>
            </div>
            <el-table 
            :header-cell-style="{ background: '#f5f7fa', color: '#303133' }" 
            :data="tableData" 
            style="width: 100%" 
            v-loading="loading"
            >
                <el-table-column prop="lab_name" label="所属实验室"></el-table-column>
                <el-table-column prop="name" label="设备名称"></el-table-column>
                <el-table-column prop="img" label="设备图片" width="90">
                    <template #default="{ row }">
                        <div style="min-height: 50px;">
                            <img 
                            v-if="row.img"
                            style="display: block; width: 50px; height: 50px; border-radius: 6px"
                            :src="row.img"
                            alt=""
                            />
                        </div>  
                    </template>
                </el-table-column>
                <el-table-column prop="spec" label="设备规格"></el-table-column>
                <el-table-column prop="quantity" label="设备数量" width="80"></el-table-column>
                <el-table-column prop="status" label="设备状态" width="90">
                    <template #default="{ row }">
                        <el-tag :type="row.status === 1 ? 'success' : 'danger'">
                            {{row.status === 1 ? '正常' : '维修'}}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="160">
                    <template #default="{ row }">
                        <el-button type="primary" text bg @click="handleEdit(row)">编辑</el-button>
                        <el-button type="danger" text bg @click="handleDelete(row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <div style="margin-top: 10px; display: flex; justify-content: flex-end;">
                <el-pagination
                v-model:current-page="params.page"
                v-model:page-size="params.page_size"
                :total="total"
                background 
                layout="total, prev, pager, next" 
                @current-change="load"
                >
                </el-pagination>
            </div>
        </el-card>
        <el-dialog v-model="dialogVisible" :title="form.id ? '编辑设备' : '新增设备'" width="450px">
            <el-form 
            :model="form" 
            :rules="rules" 
            ref="formRef" 
            label-width="100px"
            style="width: 100%; padding-right: 30px; padding-top: 16px"
            v-loading="loading"
            >
                <el-form-item label="所属实验室">
                    <el-select 
                    placeholder="请选择实验室"
                    v-model="form.lab_id"
                    style="width: 100%" 
                    clearable
                    >
                        <el-option 
                        v-for="item in labOptions" 
                        :key="item.id" 
                        :value="item.id" 
                        :label="item.name"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="设备名称" prop="name">
                    <el-input v-model="form.name" placeholder="请输入设备名称"></el-input>
                </el-form-item>
                <el-form-item label="设备简介">
                    <el-input type="textarea" v-model="form.description" placeholder="请输入设备简介"></el-input>
                </el-form-item>
                <el-form-item label="设备图片">
                    <el-upload
                        class="avatar-uploader"
                        :http-request="handleUploadFile"
                        :show-file-list="false"
                        accept="image/jpeg, image/png, image/gif, image/webp"
                        :before-upload="beforeAvatarUpload"
                    >
                        <img v-if="form.img" :src="form.img" class="avatar" />
                        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
                    </el-upload>
                </el-form-item>
                <el-form-item label="设备规格">
                    <el-input v-model="form.spec" placeholder="例如 RTX4090 24G"></el-input>
                </el-form-item>
                <el-form-item label="设备数量" prop="quantity">
                    <el-input-number :min="1" v-model="form.quantity" placeholder="请输入设备数量"></el-input-number>
                </el-form-item>
                <el-form-item label="设备状态" prop="status">
                    <el-radio-group v-model="form.status">
                        <el-radio :value="1">正常</el-radio>
                        <el-radio :value="0">维修</el-radio>
                    </el-radio-group>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button type="primary" :loading="formloading" @click="handleSubmit">确定</el-button>
                <el-button @click="dialogVisible = false">取消</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getEquipmentPageList, createEquipment, updateEquipment, deleteEquipment } from '@/api/equipment'
import { getLabPageList } from '@/api/lab'
import { Search, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { beforeAvatarUpload, handleUploadFile as uploadFile } from '@/utils/upload'

const params = reactive({
    page: 1,
    page_size: 10,
    keywords: '',
    lab_id: null
})

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const labOptions = ref([])
const dialogVisible = ref(false)
const form = reactive({
    id: null,
    lab_id: null,
    name: '',
    description: '',
    img: '',
    spec: '',
    quantity: 1,
    status: 1
})
const rules = reactive({
    lab_id: [{ required: true, message: '请选择实验室', trigger: 'change' }],
    name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
    quantity: [{ required: true, message: '请输入设备数量', trigger: 'blur' }]
})
const resetForm = () => {
    Object.assign(form, {
        id: null,
        lab_id: null,
        name: '',
        description: '',
        img: '',
        spec: '',
        quantity: 1,
        status: 1
    })
}
const formRef = ref(null)
const formloading = ref(false)
const handleAdd = () => {
    resetForm()
    dialogVisible.value = true
}
const handleEdit = (row) => {
    resetForm()
    Object.assign(form, {
        id: row.id,
        lab_id: row.lab_id,
        name: row.name,
        description: row.description,
        img: row.img,
        spec: row.spec,
        quantity: row.quantity,
        status: row.status
    })
    dialogVisible.value = true
}
const handleDelete = async (row) => {
    ElMessageBox.confirm(`确认删除设备${row.name}吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(async () => {
        const res = await deleteEquipment(row.id)
        if (res.code === 200) {
            ElMessage.success('删除成功')
            load()
        }
    })
}
const handleSubmit = async () => {
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
    formloading.value = true
    try {
        const res = form.id ? await updateEquipment(form.id, form) : await createEquipment(form)
        if (res.code === 200) {
            ElMessage.success('操作成功')
            dialogVisible.value = false
            load()
        }
    } finally {
        formloading.value = false
    }
}

const load = async () => {
    loading.value = true
    try {
        const res = await getEquipmentPageList(params)
        if (res.code === 200) {
            tableData.value = res.data?.list
            total.value = res.data?.total
        }
    } finally {
        loading.value = false
    }
}
const handleSearch = () => {
    params.page = 1
    load()
}

const handleUploadFile = async (options) => {
    const url = await uploadFile(options)
    if (url) {
        form.img = url
    }
}

const loadLabs = async () => {
    const res = await getLabPageList({
        page: 1,
        page_size: 100
    })
    if (res.code === 200) {
        labOptions.value = res.data?.list
    }
}

onMounted(() => {
    loadLabs()
    load()
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