# FastDH 团队上传技能

[发行版与安装包](https://github.com/u1s1hm/fastdh-console-upload/releases) · [更新日志](CHANGELOG.md) · [维护约定](MAINTAINING.md) · [技能入口](SKILL.md)

与 fastdh-live-package v0.3.1 配套：生成技能负责内容包；本技能负责将包应用到 FastDH 控制台。版本 0.1.0。

## 安装

推荐向 Codex 发送以下请求，用固定版本安装：

```text
请使用 skill-installer 安装 https://github.com/u1s1hm/fastdh-console-upload。
仓库根目录是技能目录，名称 fastdh-console-upload，固定到 v0.1.0。
若已安装，请先检查本地修改，再更新。
```

手动安装请从 [v0.1.0 Release](https://github.com/u1s1hm/fastdh-console-upload/releases/tag/v0.1.0) 下载 `fastdh-console-upload-v0.1.0.zip`，可用同页 `SHA256SUMS.txt` 核验完整性。GitHub 自动生成的 Source code 压缩包也可用，但需将顶层文件夹改名为 `fastdh-console-upload`。

将压缩包解压，把整个 `fastdh-console-upload` 文件夹放进 Codex 的 `$CODEX_HOME/skills`（未设置时为 `~/.codex/skills`）。确保 SKILL.md 直接在该文件夹下。无需复制原作者的工作目录或桌面手册；不含共享账号和卡密。其它支持 SKILL.md 的 Agent 可放其技能目录，仍需该宿主可用的浏览器工具和文件上传能力。

需要 Python 3（只读预检使用标准库，无 pip 依赖）、可读本地文件的 Agent，以及浏览器自动化/文件上传工具。缺工具时技能会说明要连接的工具和作用；不会自装 CLI 或修改系统设置。它是由 Agent 执行的自动化技能，不是脱离 Agent 单独运行的一键软件。

## 使用

向 Agent 发送：

```text
使用 $fastdh-console-upload。
请先引导我用自己的卡密登录。
我的配置包目录：<绝对路径>。
本次新建 Agent 和独立 Live 场景，中文名为 <名称>。
请自动填写、上传模板知识、保存并回读，完成后设为 active，不开播。
```

登录入口固定为 https://www.vivalive.ai/fastdh-front/ops/fastdh 。在网页登录表单输入自己的卡密，不需要发在聊天里。登录成功后补充包目录、新建/更新目标、发布状态和媒体登记情况。已有本人登录可复用。

局部更新示例：“更新 Agent ID … / Scenario ID …，只修改 R02 回复规则，其它值保留。”同名对象需选清楚。执行中仅对缺失信息、影响结果的冲突或登录提出问题，常规填表/保存/回读自动完成。

原视频仍由运营在数字人执行端上传并按映射命名；本技能上传的是 FastDH 配置和模板知识。模板绑定未确认、精确触发不被支持等项会明确停在待核，不假称上线完成。

## 验证范围

依据已有操作记录与 Native 手册制作，2026-11-24 本地验证结构、预检器和合成规则用例；未用新的团队卡密重跑完整生产上传。浏览器版本、权限、卡密和运行时效果仍以使用时为准。保存回读、规则预览、实播分开报告。

开发检查：`python -m unittest discover -s tests -v`。本包预检不替代逐字段审阅与页面回读。

## 升级与问题反馈

`VERSION`、Git 标签与 Release 对应；固定标签适合团队统一版本，`main` 可能包含未发布改动。升级先看 [更新日志](CHANGELOG.md)，保护本地修改，不覆盖自定义内容。升级技能不自动改已有 FastDH 场景。

配套生成技能：[fastdh-live-package v0.3.1](https://github.com/u1s1hm/fastdh-live-package/tree/v0.3.1)。两个技能独立发布；未来兼容版本须经验证后更新说明，不能只按版本号推断兼容。

反馈请在 [Issues](https://github.com/u1s1hm/fastdh-console-upload/issues) 提供技能版本、宿主/浏览器、失败板块、脱敏的预期与实际结果，并区分保存回读、规则预览和实播。不要提交卡密、Cookie、真实媒体或包含账号资料的后台截图。
