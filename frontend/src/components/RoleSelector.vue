<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { authApi } from '@/api/auth'

const emit = defineEmits<{
  (e: 'done', data: { roleType: string; meta: Record<string, unknown> }): void
}>()

const authStore = useAuthStore()
const step = ref<'role' | 'profile' | 'assessment'>('role')
const selectedRole = ref('')
const loading = ref(false)

const profileForm = ref({
  age: '',
  background: '',
  goal: '',
  weeklyHours: '5',
  experience: 'beginner',
})

const roles = [
  {
    key: 'student',
    label: '在校学生',
    icon: '🎓',
    desc: '正在学习计算机网络课程，准备应付考试或深化理解',
    color: '#4f46e5',
    bg: '#eef2ff',
  },
  {
    key: 'professional',
    label: '职场人士',
    icon: '💼',
    desc: '已参加工作，希望系统补充计算机网络知识，提升竞争力',
    color: '#0891b2',
    bg: '#ecfeff',
  },
  {
    key: 'self_learner',
    label: '自学爱好者',
    icon: '📚',
    desc: '凭兴趣学习网络知识，按自己的节奏探索',
    color: '#059669',
    bg: '#ecfdf5',
  },
  {
    key: 'job_seeker',
    label: '求职冲刺者',
    icon: '🚀',
    desc: '准备面试网络工程师等岗位，需要快速掌握重点考点',
    color: '#dc2626',
    bg: '#fff1f2',
  },
]

const experienceLevels = [
  { key: 'beginner', label: '入门级（刚接触）' },
  { key: 'intermediate', label: '中级（有一定基础）' },
  { key: 'advanced', label: '进阶级（深度学习）' },
]

function selectRole(roleKey: string) {
  selectedRole.value = roleKey
}

function nextToProfile() {
  if (!selectedRole.value) return
  step.value = 'profile'
}

async function submitProfile() {
  if (!profileForm.value.goal) return
  loading.value = true
  try {
    const meta = {
      age: profileForm.value.age,
      background: profileForm.value.background,
      goal: profileForm.value.goal,
      weekly_hours: profileForm.value.weeklyHours,
      experience: profileForm.value.experience,
    }
    // 更新后端用户档案
    if (authStore.user?.userId) {
      await authApi.updateProfile(authStore.user.userId, {
        role_type: selectedRole.value,
        meta_json: meta,
        is_first_login: 0,
      })
      // 同步更新本地 authStore
      if (authStore.user) {
        authStore.setUser({ ...authStore.user, roleType: selectedRole.value, isFirstLogin: 0 })
      }
    }
    emit('done', { roleType: selectedRole.value, meta })
  } catch (err) {
    console.error('[RoleSelector] 更新档案失败:', err)
    // 即使失败也继续
    emit('done', { roleType: selectedRole.value, meta: {} })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="role-overlay">
    <div class="role-card">
      <!-- 步骤指示 -->
      <div class="step-bar">
        <div class="step" :class="{ active: step === 'role', done: step !== 'role' }">
          <span class="step-num">{{ step !== 'role' ? '✓' : '1' }}</span>
          <span class="step-label">选择角色</span>
        </div>
        <div class="step-line"></div>
        <div class="step" :class="{ active: step === 'profile' }">
          <span class="step-num">2</span>
          <span class="step-label">填写档案</span>
        </div>
      </div>

      <!-- Step 1: 角色选择 -->
      <template v-if="step === 'role'">
        <div class="card-header">
          <h2>你是哪种学习者？</h2>
          <p>选择最符合你当前情况的角色，系统将为你个性化内容</p>
        </div>
        <div class="roles-grid">
          <div
            v-for="role in roles"
            :key="role.key"
            class="role-item"
            :class="{ selected: selectedRole === role.key }"
            :style="selectedRole === role.key ? `border-color: ${role.color}; background: ${role.bg}` : ''"
            @click="selectRole(role.key)"
          >
            <div class="role-icon" :style="selectedRole === role.key ? `color: ${role.color}` : ''">
              {{ role.icon }}
            </div>
            <div class="role-info">
              <div class="role-name" :style="selectedRole === role.key ? `color: ${role.color}` : ''">
                {{ role.label }}
              </div>
              <div class="role-desc">{{ role.desc }}</div>
            </div>
            <div v-if="selectedRole === role.key" class="check-mark" :style="`color: ${role.color}`">✓</div>
          </div>
        </div>
        <button
          class="main-btn"
          :disabled="!selectedRole"
          @click="nextToProfile"
        >
          下一步：填写学习档案 →
        </button>
      </template>

      <!-- Step 2: 档案表单 -->
      <template v-else-if="step === 'profile'">
        <div class="card-header">
          <h2>告诉我们更多关于你</h2>
          <p>这些信息帮助 AI 更好地个性化你的学习体验</p>
        </div>
        <div class="profile-form">
          <div class="form-row">
            <div class="form-field">
              <label>年龄段</label>
              <select v-model="profileForm.age">
                <option value="">请选择</option>
                <option value="16-20">16-20岁（高中/大一）</option>
                <option value="20-25">20-25岁（大学/研究生）</option>
                <option value="25-30">25-30岁（初级工程师）</option>
                <option value="30+">30岁以上</option>
              </select>
            </div>
            <div class="form-field">
              <label>每周可用时长</label>
              <select v-model="profileForm.weeklyHours">
                <option value="2">2小时以内</option>
                <option value="5">3-5小时</option>
                <option value="10">5-10小时</option>
                <option value="20">10小时以上</option>
              </select>
            </div>
          </div>

          <div class="form-field">
            <label>计算机网络基础</label>
            <div class="radio-group">
              <label v-for="lv in experienceLevels" :key="lv.key" class="radio-item">
                <input type="radio" :value="lv.key" v-model="profileForm.experience" />
                {{ lv.label }}
              </label>
            </div>
          </div>

          <div class="form-field">
            <label>学习目标 <span class="required">*</span></label>
            <textarea
              v-model="profileForm.goal"
              placeholder="例如：通过期末考试 / 准备华为 HCIA 认证 / 了解 TCP/IP 协议原理..."
              rows="3"
              required
            ></textarea>
          </div>

          <div class="form-field">
            <label>背景说明（可选）</label>
            <input
              v-model="profileForm.background"
              type="text"
              placeholder="例如：计算机科学大三在读 / 网络工程师 2 年经验..."
            />
          </div>
        </div>

        <div class="btn-row">
          <button class="back-btn" @click="step = 'role'">← 返回</button>
          <button
            class="main-btn"
            :disabled="!profileForm.goal || loading"
            @click="submitProfile"
          >
            <span v-if="loading" class="spinner"></span>
            完成设置，开始学习 🎉
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.role-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(4px);
  z-index: 999;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.role-card {
  width: 100%; max-width: 600px;
  background: white; border-radius: 24px;
  padding: 36px 32px;
  box-shadow: 0 24px 80px rgba(0,0,0,0.2);
  max-height: 90vh; overflow-y: auto;
}

/* 步骤条 */
.step-bar {
  display: flex; align-items: center; gap: 0;
  margin-bottom: 28px;
}
.step {
  display: flex; align-items: center; gap: 8px;
  color: #94a3b8; font-size: 13px;
}
.step.active { color: #4f46e5; }
.step.done { color: #10b981; }
.step-num {
  width: 24px; height: 24px;
  border-radius: 50%;
  background: currentColor;
  color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
}
.step-line { flex: 1; height: 1px; background: #e2e8f0; margin: 0 12px; }

/* 标题 */
.card-header { margin-bottom: 24px; }
.card-header h2 { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0 0 6px; }
.card-header p { font-size: 14px; color: #64748b; margin: 0; }

/* 角色卡片 */
.roles-grid { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
.role-item {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.role-item:hover { border-color: #c7d2fe; background: #fafbff; }
.role-item.selected { box-shadow: 0 2px 12px rgba(79,70,229,0.15); }
.role-icon { font-size: 28px; flex-shrink: 0; }
.role-name { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 3px; }
.role-desc { font-size: 12px; color: #64748b; }
.check-mark { position: absolute; right: 16px; font-size: 18px; font-weight: 700; }

/* 表单 */
.profile-form { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-field label { font-size: 13px; font-weight: 500; color: #374151; }
.required { color: #ef4444; }
.form-field input, .form-field select, .form-field textarea {
  padding: 9px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 13px; color: #1e293b;
  outline: none;
  font-family: inherit;
  transition: border-color 0.2s;
}
.form-field input:focus, .form-field select:focus, .form-field textarea:focus {
  border-color: #4f46e5;
}
.form-field textarea { resize: vertical; }
.radio-group { display: flex; gap: 16px; flex-wrap: wrap; }
.radio-item {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #374151; cursor: pointer;
}

/* 按钮 */
.btn-row { display: flex; gap: 12px; }
.main-btn {
  flex: 1; padding: 13px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none; border-radius: 12px;
  color: white; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.main-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.main-btn:not(:disabled):hover { filter: brightness(1.1); transform: translateY(-1px); }
.back-btn {
  padding: 13px 20px;
  background: #f1f5f9; border: none;
  border-radius: 12px; color: #475569;
  font-size: 14px; cursor: pointer;
  transition: all 0.2s;
}
.back-btn:hover { background: #e2e8f0; }

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
