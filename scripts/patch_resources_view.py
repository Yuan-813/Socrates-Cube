"""在 ResourcesView.vue 的标题卡片后插入知识库上传卡片。"""
from pathlib import Path

fpath = Path("frontend/src/views/ResourcesView.vue")
content = fpath.read_text(encoding="utf-8")

MARKER = '    </div>\n\n    <!-- ★ 一键全套生成横幅'

UPLOAD_CARD = '''    </div>

    <!-- ★ 知识库上传卡片 -->
    <div class="card">
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <span class="w-5 h-5 rounded bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs font-bold">📤</span>
          上传知识材料到知识库
        </h3>
        <button class="text-xs text-gray-400 hover:text-gray-600 transition-colors" @click="showUploadPanel = !showUploadPanel">
          {{ showUploadPanel ? '收起 ▲' : '展开 ▼' }}
        </button>
      </div>
      <p class="text-xs text-gray-400 mb-3">AI 回答时将自动检索并引用你上传的内容</p>
      <template v-if="showUploadPanel">
        <div class="mb-3">
          <label class="block text-xs text-gray-500 mb-1">来源名称（如文档名）</label>
          <input v-model="uploadSource" type="text" placeholder="如: BGP笔记.md，不填则显示「用户上传」"
            class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-400 transition-all" />
        </div>
        <div class="mb-3">
          <label class="block text-xs text-gray-500 mb-1">粘贴文本内容</label>
          <textarea v-model="uploadContent" rows="6" placeholder="将文本或 Markdown 内容粘贴到这里..."
            class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-400 transition-all resize-y" />
        </div>
        <div class="flex items-center gap-4 flex-wrap">
          <label class="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
            <input type="checkbox" v-model="uploadIsMarkdown" class="accent-emerald-500" />
            Markdown 格式（按标题分割）
          </label>
          <button :disabled="isUploading || !uploadContent.trim()"
            class="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-lg transition-colors"
            :class="isUploading || !uploadContent.trim() ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-700 text-white'"
            @click="handleUpload">
            {{ isUploading ? '处理中...' : '入库' }}
          </button>
        </div>
        <div v-if="uploadResult" class="mt-3 text-xs px-3 py-2 rounded-lg"
          :class="uploadResult.success ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'">
          <span v-if="uploadResult.success">✅ {{ uploadResult.message }}（{{ uploadResult.chunks_added }} 个块）</span>
          <span v-else>❌ {{ uploadResult.message }}</span>
        </div>
      </template>
    </div>

    <!-- ★ 一键全套生成横幅'''

if MARKER in content:
    content = content.replace(MARKER, UPLOAD_CARD, 1)
    fpath.write_text(content, encoding="utf-8")
    print("Success: upload card inserted")
else:
    print("MARKER not found, trying alternate marker...")
    # fallback: insert before one-click banner
    alt = '    <!-- ★ 一键全套生成横幅'
    if alt in content:
        upload_only = UPLOAD_CARD[:UPLOAD_CARD.rfind('\n    <!-- ★ 一键全套生成横幅')] + '\n\n    <!-- ★ 一键全套生成横幅'
        content = content.replace(alt, upload_only, 1)
        fpath.write_text(content, encoding="utf-8")
        print("Success via fallback marker")
    else:
        print("ERROR: Neither marker found")
