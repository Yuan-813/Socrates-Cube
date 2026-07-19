<script setup lang="ts">
import ProfileRadarScheme1 from '@/components/ProfileRadarScheme1.vue'
import MistakeBook from '@/components/MistakeBook.vue'
import { ref, onMounted, reactive } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()

const activeTab = ref<'radar' | 'mistakes' | 'account'>('radar')

// ── 账户信息表单 ──────────────────────────────────────────────
const userInfo = reactive({
  username: '',
  email: '',
  phone: '',
  role_type: 'student',
  create_time: '',
})

const infoLoading = ref(false)
const infoSaving = ref(false)

const roleOptions = [
  { label: '本科学生', value: 'student' },
  { label: '专业人士', value: 'professional' },
  { label: '自学者', value: 'self_learner' },
  { label: '求职者', value: 'job_seeker' },
]

async function loadUserInfo() {
  const uid = authStore.user?.userId
  if (!uid) return
  infoLoading.value = true
  try {
    const info = await authApi.getUserInfo(uid)
    userInfo.username = info.username
    userInfo.email = info.email
    userInfo.phone = info.phone
    userInfo.role_type = info.role_type
    userInfo.create_time = info.create_time
  } catch {
    // 降级使用 authStore 已知信息
    userInfo.username = authStore.user?.username || ''
    userInfo.role_type = authStore.user?.roleType || 'student'
  } finally {
    infoLoading.value = false
  }
}

async function saveUserInfo() {
  const uid = authStore.user?.userId
  if (!uid) return
  infoSaving.value = true
  try {
    await authApi.updateProfile(uid, {
      role_type: userInfo.role_type,
      meta_json: { email: userInfo.email },
    })
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    infoSaving.value = false
  }
}

// ── 修改密码表单 ──────────────────────────────────────────────
const pwdForm = reactive({
  oldPwd: '',
  newPwd: '',
  confirmPwd: '',
})

const pwdSaving = ref(false)

async function changePassword() {
  if (!pwdForm.oldPwd || !pwdForm.newPwd) {
    ElMessage.warning('请填写完整密码信息')
    return
  }
  if (pwdForm.newPwd.length < 6) {
    ElMessage.warning('新密码至少 6 个字符')
    return
  }
  if (pwdForm.newPwd !== pwdForm.confirmPwd) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  const uid = authStore.user?.userId
  if (!uid) return
  pwdSaving.value = true
  try {
    await authApi.changePassword({
      user_id: uid,
      old_password: pwdForm.oldPwd,
      new_password: pwdForm.newPwd,
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdForm.oldPwd = ''
    pwdForm.newPwd = ''
    pwdForm.confirmPwd = ''
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '修改失败')
  } finally {
    pwdSaving.value = false
  }
}

onMounted(() => {
  // 切换到账户设置Tab时才加载数据
})

function onTabChange(tab: typeof activeTab.value) {
  activeTab.value = tab
  if (tab === 'account' && !userInfo.username) {
    loadUserInfo()
  }
}
</script>

<template>
  <div class="profile-view">
    <div class="profile-header">
      <div class="ph-title-row">
        <div>
          <h2 class="ph-title">学生能力画像</h2>
          <p class="ph-sub">基于对话交互自动构建的 8 维协议能力评估，实时追踪学习成长</p>
        </div>
        <div class="ph-right-group">
          <!-- Tab 切换 -->
          <div class="ph-tabs">
            <button
              class="ph-tab"
              :class="{ active: activeTab === 'radar' }"
              @click="onTabChange('radar')"
            >
              📊 能力雷达图
            </button>
            <button
              class="ph-tab"
              :class="{ active: activeTab === 'mistakes' }"
              @click="onTabChange('mistakes')"
            >
              📓 智能错题本
            </button>
            <button
              class="ph-tab"
              :class="{ active: activeTab === 'account' }"
              @click="onTabChange('account')"
            >
              ⚙️ 账户设置
            </button>
          </div>
        </div>
      </div>
    </div>

    <ProfileRadarScheme1 v-if="activeTab === 'radar'" />

    <!-- 错题本区块 -->
    <div v-if="activeTab === 'mistakes'" class="mistake-section">
      <MistakeBook />
    </div>

    <!-- 账户设置区块 -->
    <div v-if="activeTab === 'account'" class="account-section">
      <!-- 个人信息卡片 -->
      <div class="setting-card">
        <div class="setting-card-head">
          <span class="setting-card-title">👤 个人信息</span>
          <span class="setting-card-sub">注册时间：{{ userInfo.create_time || '未知' }}</span>
        </div>
        <div v-if="infoLoading" class="loading-tip">加载中...</div>
        <div v-else class="setting-form">
          <div class="form-row">
            <label class="form-label">用户名</label>
            <el-input :model-value="userInfo.username" disabled placeholder="用户名不可修改" />
            <span class="form-tip">用户名不可修改</span>
          </div>
          <div class="form-row">
            <label class="form-label">邮箱</label>
            <el-input v-model="userInfo.email" placeholder="请输入邮箱" clearable />
          </div>
          <div class="form-row">
            <label class="form-label">手机号</label>
            <el-input :model-value="userInfo.phone" disabled placeholder="与手机号绑定后显示" />
          </div>
          <div class="form-row">
            <label class="form-label">学习身份</label>
            <el-select v-model="userInfo.role_type" style="width: 100%;">
              <el-option
                v-for="opt in roleOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>
          <div class="form-actions">
            <button class="save-btn" :disabled="infoSaving" @click="saveUserInfo">
              {{ infoSaving ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 密码安全卡片 -->
      <div class="setting-card">
        <div class="setting-card-head">
          <span class="setting-card-title">🔒 密码安全</span>
          <span class="setting-card-sub">建议定期修改密码</span>
        </div>
        <div class="setting-form">
          <div class="form-row">
            <label class="form-label">旧密码</label>
            <el-input v-model="pwdForm.oldPwd" type="password" placeholder="请输入当前密码" show-password />
          </div>
          <div class="form-row">
            <label class="form-label">新密码</label>
            <el-input v-model="pwdForm.newPwd" type="password" placeholder="新密码（至少6位）" show-password />
          </div>
          <div class="form-row">
            <label class="form-label">确认新密码</label>
            <el-input v-model="pwdForm.confirmPwd" type="password" placeholder="再次输入新密码" show-password />
          </div>
          <div class="form-actions">
            <button class="save-btn" :disabled="pwdSaving" @click="changePassword">
              {{ pwdSaving ? '修改中...' : '确认修改密码' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

.profile-header {
  padding: 4px 0 0;
}

.ph-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.ph-right-group {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}



.ph-title {
  font-size: 20px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}

.ph-sub {
  font-size: 13px;
  color: #64748b;
}

.ph-tabs {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.ph-tab {
  padding: 8px 16px;
  border-radius: 10px;
  border: 1.5px solid #e2e8f0;
  background: #fafbff;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
}

.ph-tab:hover {
  border-color: #a5b4fc;
  color: #6366f1;
}

.ph-tab.active {
  border-color: #6366f1;
  background: linear-gradient(135deg, #eff6ff, #f5f3ff);
  color: #6366f1;
  box-shadow: 0 2px 8px rgba(99,102,241,0.15);
}

.mistake-section {
  background: white;
  border-radius: 16px;
  border: 1px solid #e8eef8;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* 账户设置 */
.account-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-card {
  background: white;
  border-radius: 16px;
  border: 1px solid #e8eef8;
  padding: 22px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.setting-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f1f5f9;
}

.setting-card-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}

.setting-card-sub {
  font-size: 12px;
  color: #94a3b8;
}

.loading-tip {
  font-size: 13px;
  color: #94a3b8;
  padding: 20px 0;
  text-align: center;
}

.setting-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 480px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.form-tip {
  font-size: 11px;
  color: #94a3b8;
}

.form-actions {
  padding-top: 6px;
}

.save-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(99,102,241,0.3);
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99,102,241,0.4);
}

.save-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}
</style>
