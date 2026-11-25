# 维护与发布约定

## 内容分工

- SKILL.md：入口、授权范围、流程与完成条件。
- references/login.md：固定域名、个人卡密登录和会话恢复。
- references/mapping.md：生成包与后台字段对应，适用性和兼容基线。
- references/transport.md：宿主/通道选择、上传预检与有日期的能力证据。
- references/batch.md：临时批量载体、基线/差异合并和本地工具约定。
- references/workflow.md：依赖顺序、批量/表单保存、冲突和部分成功恢复。
- references/verification.md：回读、预览、实播的证据边界。
- scripts/preflight.py、scripts/batch_config.py、tests/：只读预检、离线合并/比较/恢复决策与脱敏合成用例。
- README.md：面向团队的安装/使用说明；CHANGELOG.md：面向用户的中文变更与迁移影响。

仅 UI、弹窗或保存流程变化，更新上传技能；配置语义或生成包约定变化，同时检查 fastdh-live-package 受影响部分。不要复制整份内部手册到公共仓库。事实变更记录来源类型、核对日期和适用范围；静态检查不得写成生产验收。

## 验证

在仓库根目录运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
git diff --check
```

有 Codex skill-creator 时再运行其 quick_validate.py。引用文件、安装路径、版本号和 Markdown 链接需检查；新增功能应补能观察到行为的用例。本版运行本地合成测试，未配置 GitHub Actions；测试不连接 FastDH，不使用卡密或生产会话。未来启用 CI 需维护者配置相应仓库权限。

需要做生产回归时单独取得目标与操作范围授权，使用本人的会话；记录已验证与未验证项，材料留在授权工作区，不发布。实播授权与配置上传授权分开。

## 发版

1. 兼容修复提升修订号，新增流程/能力提升次版本；尚处 0.x，破坏性变化必须明确迁移说明。
2. 同步 VERSION、中文 CHANGELOG、README 的固定安装版本与下载链接；发布说明注明兼容生成包版本和未验证范围。
3. 验证后提交，创建新的标注标签 vX.Y.Z。已发布标签不移动、不覆盖；需要修正发行内容时发布新版本。
4. ZIP 只包含技能源码和维护资料，顶层为 fastdh-console-upload；排除 .git、缓存、真实配置包、媒体、凭证及临时文件。
5. 生成 SHA256SUMS.txt，创建 GitHub Release，附 ZIP 与校验文件。回读远端提交、标签及 Release 附件，再报告成功。
6. 如同步本机安装目录，先比较是否有用户改动，不盲目覆盖。安装版、源码和 Release 的同名文件应一致。

本仓库不提供默认共享账号。默认不配置密钥型 CI，不收集卡密；发布凭证由维护者自己的 GitHub 登录提供。
