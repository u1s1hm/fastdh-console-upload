# 包到控制台映射

兼容基线：[生成技能 v0.3.1](https://github.com/u1s1hm/fastdh-live-package/tree/v0.3.1)。输入是该版本的实际产物，不是其 references 目录。无需在队友机器存在原作者的桌面或聊天记录。

| 包内来源 | 控制台位置/操作 | 核对 |
|---|---|---|
| Soul.md | Agent Profile → Soul.md 编辑器 | 正式原文完整保存 |
| Agents.md（旧小写可识别） | Profile → Agents.md 编辑器 | 与角色及安全规则一致 |
| 媒体映射内场景值 | Scenario 名称、Category Live、Status、专属指令、记忆/知识 | 不把整个映射表粘入指令 |
| video_template_*.md | Knowledge library/domain → Upload → 处理成功 | 数量、文档预览、类别与实际媒体别名 |
| LiveScript.md | Live configuration → LiveScript.md | 保存后回读原文，重新计算非空行 |
| LiveScript_Nonempty_Line_Index.md | Programme orchestration / 场景 JSON | 按顺序完整映射所有元素，来源/范围/底板/结束条件 |
| 媒体映射内 W 配置 | 本场指定的互动窗口元素类型 | 有点播才用对应 Queued performances；纯评论窗口可按明确包配置使用 Live section，不由 W 前缀推断类型 |
| 媒体映射内评论策略 | Audience comment selection | 与节目窗口和规则分别保存 |
| 媒体映射逐规则表＋逐动作表 | Rules of interaction | Rule ID→实际规则映射，顺序与每一步 |
| 中文译本 | 本地核对 | 默认不上传，不当英语稿的行号来源 |

## 逐规则与动作

Rule ID 作为本地稳定引用，不虚构后台 ID。字段固定于 v0.3.1 两表：

- 规则：Order / Chinese name / Enabled / Event / Keywords / Match semantics / Property ID / LLM condition / Acknowledgement / Timing / Completion / Failure / Cooldown seconds / Cooldown scope / Expiry seconds / Basis。
- 动作：Rule ID / Step / Action / Text or prompt / Spoken language / Capability / Parameters / Template mode / Template category / Required switch / Switch trigger / Basis。

依手册 §11：Comments/Gifts/Buttons/Cards；第一条命中的启用规则处理事件。关键词是规范化、大小写无关子串，关键词未命中才用语义条件，属性条件始终生效。条件不是可任意组合的全等/AND 表达式。111 会匹配 1111 和 hi111；若要排除它们，记录需求未满足，不能拿文字提示当确定性修复。

动作可为 Speak text、Generate reply、Performance deployment、Internal capability、External capability、Switch template，每规则最多 8 步。Generate reply 必须把实际回复指令和语言落到当前已确认的提示配置入口；没有对应入口不得丢弃或只留在内部映射表。

模板选择仅用于 Speak text、Generate reply、Switch template：Keep current template / Fixed category / LLM-assisted selection。固定类别用本场真实类别；切换必需性逐场设。Switch trigger 的 Before/After this speech 仅用于播报附加模板，独立 Switch template 不填。切模板不是播放指定原视频；固定离线节目当前实现若不明确，要核实新版 performance/Brain 路径，不强行使用旧 video 元素。

Timing：After current speech / Immediately；完成：Resume previous content / Stay active / Finish；失败：Abort remaining steps / Continue optional steps。冷却 0–86400 秒，Per session/Per viewer，后者需稳定观众 ID。规则 Expiry seconds 指事件过期时间，不是规则的生效期限；手册证实数值范围 1–86400。2026-11-25 当前 UI 和 JSON 回读确认空白/null 表示禁用事件过期：包内明确 EMPTY 可映射为 null，更新缺失字段仍保留。其它版本重新核对；此结论不证明排队事件的实播行为。

## 未覆盖字段与默认

包里缺失/互相冲突的字段不是上传端的创作授权。更新时保留已回读现值；新建时非关键字段可使用明确的平台默认并记录实际值，涉及观众承诺、资源、顺序、语言时先问。

运营约定：实时口播优先 Brain reports video ended 并屏蔽观众评论；已配置弹幕规则全部启用；记忆检索关闭、结果限额 6。与源包不同要列出差异再明确采用哪方，不静默改源稿。平台 Live section 新建默认 Script exhausted，和运营约定不是同一件事。窗口参数、模板情感、知识配置、循环和回复指令按本场，不继承案例数值。

Knowledge 开启时 collection_id/domain 同时存在；文档导入须处理成功。能力由配置自动推导，不找已移除的内外部授权勾选项，不手填 Scenario 模型。语音情感开关未有确定含义/默认时保留并标待核。
