# 虚拟教师视频文件

请将以下视频文件放置在此目录：

1. `teacher_idle.mp4` - 教师闲置时的微动态循环视频（3-5秒，呼吸/眨眼）
2. `teacher_speaking.mp4` - 教师说话时的视频（3-5秒，嘴巴在动）

## 生成方法

使用 LivePortrait 在线 Demo 生成：
1. 访问 https://huggingface.co/spaces/KwaiVGI/LivePortrait
2. 上传 `../images/virtual_teacher.png` 作为源图片
3. 上传一个参考动作视频（呼吸/说话）
4. 点击生成，下载结果
5. 命名为对应文件名放在此目录

## 视频规格建议

- 分辨率：512x512 或 720x720
- 帧率：25fps
- 时长：3-5秒（循环播放）
- 编码：H.264 MP4
- 文件大小：< 2MB（确保快速加载）
