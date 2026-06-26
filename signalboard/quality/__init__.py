"""signalboard.quality — KOL 评估标准流程包

把 Serenity 9 轮人工核对的所有陷阱固化为自动管道:
1. tier 分层 (按论证字数/单条标的数)
2. 标的解析增强 (别名 + 国别/挂牌地)
3. direction + 条件抽取规则 (prompt v2 + 后处理)
4. outlier 与集中度自动体检
5. 追高自动检验
6. kol_eval 主入口 (handle → 标准记分牌)

对外使用:
    from signalboard.quality.kol_eval import evaluate_kol
    report = evaluate_kol(handle='aleabitoreddit', db_path='...')
"""