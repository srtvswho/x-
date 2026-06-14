"""金标集 v1(20 条,人工标注) + 评测入口。

金标 schema(每条):
  {
    "post_id": str,
    "has_prediction": bool,
    "predictions": [
      {
        "ticker": str,              # 标准代码(若是 commodity 则 ticker=asset 名如 silver)
        "market": str,              # 美股/A股/SE/OTC/TW/commodity
        "direction": "long"|"short"|"neutral",
        "claim_type": "quantitative"|"directional"|"thematic",
        "horizon": "1w|1m|3m|6m|1y|long_term|event_driven",
        "conviction": int(1-5),
        "thesis_summary": str,
      }
    ],
    "flags": List[str],  # self_reported_returns / victory_lap / position_disclosure / influence_milestone / solicitation
  }

R9 conviction 标尺:
  5:重仓宣言/最高级措辞
  4:完整论据+强结论
  3:明确具体但语气随意
  2:清单/强对冲
  1:顺带一提

样本 20 条都来自 seed=20260612 的分层抽样(高互动,20% 顶)。
"""
from __future__ import annotations

from typing import List, TypedDict


class GoldPrediction(TypedDict, total=False):
    ticker: str
    market: str
    direction: str
    claim_type: str
    horizon: str
    conviction: int
    thesis_summary: str


class GoldEntry(TypedDict, total=False):
    post_id: str
    has_prediction: bool
    predictions: List[GoldPrediction]
    flags: List[str]


# 金标 20 条(按 spec 第 4 节)
GOLD_V1: List[GoldEntry] = [
    # 1) 2062723902728802341: 预测 1 条 688017/A股 long/dir/conv5/long_term
    {
        "post_id": "2062723902728802341",
        "has_prediction": True,
        "predictions": [
            {
                "ticker": "688017",
                "market": "A股",
                "direction": "long",
                "claim_type": "directional",
                "horizon": "long_term",
                "conviction": 5,
                "thesis_summary": "人形机器人谐波减速器国产份额 60%+ 龙头,核心零部件瓶颈供应商",
            },
        ],
        "flags": [],
    },
    # 2) 2059606040417812549: 无预测
    {
        "post_id": "2059606040417812549",
        "has_prediction": False,
        "predictions": [],
        "flags": [],
    },
    # 3) 2064265545529307560: 无预测,flags: position_disclosure;$IREN 为历史引用
    {
        "post_id": "2064265545529307560",
        "has_prediction": False,
        "predictions": [],
        "flags": ["position_disclosure"],
    },
    # 4) 2059292099728859430: 无预测,flags: self_reported_returns
    {
        "post_id": "2059292099728859430",
        "has_prediction": False,
        "predictions": [],
        "flags": ["self_reported_returns"],
    },
    # 5) 2050302664031039691: 无预测,社交内容
    {
        "post_id": "2050302664031039691",
        "has_prediction": False,
        "predictions": [],
        "flags": [],
    },
    # 6) 2004569946492453003: 2 条 AXTI + SMTOY,long/dir;8 语境 ticker 不入
    {
        "post_id": "2004569946492453003",
        "has_prediction": True,
        "predictions": [
            {
                "ticker": "AXTI",
                "market": "美股",
                "direction": "long",
                "claim_type": "directional",
                "horizon": "long_term",
                "conviction": 4,
                "thesis_summary": "InP 衬底全球瓶颈,占 60-70% 产能,AI 光学/激光收发器必备",
            },
            {
                "ticker": "SMTOY",
                "market": "美股",
                "direction": "long",
                "claim_type": "directional",
                "horizon": "long_term",
                "conviction": 3,
                "thesis_summary": "InP 衬底另一家垄断者,跟 AXTI 一起卡住 AI 光学供应链",
            },
        ],
        "flags": [],
    },
    # 7) 2063235166336856251: 无预测,SIVE/AAOI 为持仓引用非新预测
    {
        "post_id": "2063235166336856251",
        "has_prediction": False,
        "predictions": [],
        "flags": ["position_disclosure"],
    },
    # 8) 2058078143559372866: 无预测,flags: self_reported_returns
    {
        "post_id": "2058078143559372866",
        "has_prediction": False,
        "predictions": [],
        "flags": ["self_reported_returns"],
    },
    # 9) 2062729921756278804: 无预测,中文致歉回复
    {
        "post_id": "2062729921756278804",
        "has_prediction": False,
        "predictions": [],
        "flags": [],
    },
    # 10) 2060539775954866386: 4 条 AAOI/SIVE/Foci/Shunsin 市值 quant/1y/conv3;台股需解析
    {
        "post_id": "2060539775954866386",
        "has_prediction": True,
        "predictions": [
            {
                "ticker": "AAOI",
                "market": "美股",
                "direction": "long",
                "claim_type": "quantitative",
                "horizon": "1y",
                "conviction": 3,
                "thesis_summary": "市值目标 $70B(预测)",
            },
            {
                "ticker": "SIVE",
                "market": "SE",
                "direction": "long",
                "claim_type": "quantitative",
                "horizon": "1y",
                "conviction": 3,
                "thesis_summary": "市值目标 $30B(预测)",
            },
            {
                "ticker": "3363.TW",
                "market": "TW",
                "direction": "long",
                "claim_type": "quantitative",
                "horizon": "1y",
                "conviction": 3,
                "thesis_summary": "Foci 市值目标 $15B(预测)",
            },
            {
                "ticker": "6451.TW",
                "market": "TW",
                "direction": "long",
                "claim_type": "quantitative",
                "horizon": "1y",
                "conviction": 3,
                "thesis_summary": "Shunsin 市值目标 $10B(预测)",
            },
        ],
        "flags": [],
    },
    # 11) 2058828045927231640: 无预测,社交回复
    {
        "post_id": "2058828045927231640",
        "has_prediction": False,
        "predictions": [],
        "flags": [],
    },
    # 12) 2061769121134788656: 无预测,"8 SEK"为历史引用
    {
        "post_id": "2061769121134788656",
        "has_prediction": False,
        "predictions": [],
        "flags": [],
    },
    # 13) 2062451355684663399: 无预测,平台费用闲聊
    {
        "post_id": "2062451355684663399",
        "has_prediction": False,
        "predictions": [],
        "flags": [],
    },
    # 14) 2021043159292314111: R3 批评他人空头论点,自身无方向,$PLTR 不入
    {
        "post_id": "2021043159292314111",
        "has_prediction": False,
        "predictions": [],
        "flags": [],
    },
    # 15) 2007387427820978510: ~10 事件驱动 long:CF/CVE/VLO/LDOS/AVAV/HII/LHX/BA/RTX/HON,conv3
    {
        "post_id": "2007387427820978510",
        "has_prediction": True,
        "predictions": [
            {"ticker": "CF", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "委内瑞拉重油/化肥断供受益"},
            {"ticker": "CVE", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "委内瑞拉重油/化肥断供受益"},
            {"ticker": "VLO", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "复杂炼油受益委内瑞拉重质原油短缺"},
            {"ticker": "LDOS", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "委内瑞拉军事介入受益"},
            {"ticker": "AVAV", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "国防无人机/反无人机受益"},
            {"ticker": "HII", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "造船厂委内瑞拉行动受益"},
            {"ticker": "LHX", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "国防电子受益"},
            {"ticker": "BA", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "国防航空受益"},
            {"ticker": "RTX", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "国防导弹受益"},
            {"ticker": "HON", "market": "美股", "direction": "long", "claim_type": "event_driven", "horizon": "event_driven", "conviction": 3, "thesis_summary": "国防工业受益"},
        ],
        "flags": [],
    },
    # 16) 2042187668931616964: 30 条 R7 清单 conv2,horizon=6m;HOOD 双时维取主导 long;
    #     MSFT 带 $375 锚;末尾 AAOI/AEHR 是"other thoughts"非清单一部分,不入
    {
        "post_id": "2042187668931616964",
        "has_prediction": True,
        "predictions": [
            {"ticker": "INTC", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "美国 foundry 国产希望,国家安全"},
            {"ticker": "MRVL", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "未来 Maia ASIC + CPO 增量"},
            {"ticker": "TSM", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "半导/AI 骨干"},
            {"ticker": "COHR", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "垂直整合 + 光学周期"},
            {"ticker": "RKLB", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "太空最终前沿"},
            {"ticker": "DRAM", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "Samsung/SK Hynix 内存敞口"},
            {"ticker": "AVGO", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "Hyperscaler 不满 NVIDIA GPU 税"},
            {"ticker": "AMZN", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "隔夜配送难被击败,机器人降 opex"},
            {"ticker": "ARM", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "AGI CPU 十年内放量"},
            {"ticker": "TSEM", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "光子学 foundry 必备"},
            {"ticker": "IBIT", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "比特币敞口"},
            {"ticker": "NBIS", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "下一个 AWS,自驾车/Uber 合作,数据库/数据标注"},
            {"ticker": "GOOGL", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "YouTube + Gemini + 垂直整合 TPU"},
            {"ticker": "AMKR", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "2027-2028 美国厂上线"},
            {"ticker": "HOOD", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "短期不看好,长期看好(取主导 long);零售捕获 + 银行产品扩张 + 产品创新"},
            {"ticker": "CRCL", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "稳定币 + 支付未来(取决于 Clarity Act)"},
            {"ticker": "META", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "Instagram/WhatsApp 不可替代"},
            {"ticker": "LITE", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "GOOGL TPU 暴露于 BOM,Google AI 持续即受益"},
            {"ticker": "LPTH", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "锗 + 中国出口管制,美国本土替代"},
            {"ticker": "FN", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "光学组装商"},
            {"ticker": "JBL", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "光学组装 + Intel SiPh IP"},
            {"ticker": "MP", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "美国稀土,国家安全类似 INTC"},
            {"ticker": "HIMS", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "$19 全球 DTC 渠道,空头敌意但逆向 long 看好"},
            {"ticker": "SMTC", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "LRO/LPO 转型"},
            {"ticker": "POWL", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "美国开关设备替代 Hammond 瓶颈"},
            {"ticker": "VPG", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "人形机器人传感器 2027-2028"},
            {"ticker": "MOG.A", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "机器人/SpaceX 供应链常见"},
            {"ticker": "MSFT", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "$375 是买入机会(锚)"},
            {"ticker": "CVX", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "战后油价或崩但委内瑞拉金矿重要"},
            {"ticker": "XLU", "market": "美股", "direction": "long", "claim_type": "directional", "horizon": "6m", "conviction": 2, "thesis_summary": "降息重启 + AI 电力需求,CEG/NEE 等公用事业"},
        ],
        "flags": [],
    },
    # 17) 2017669714353537024: 1 thematic/silver/long/conv2 (hedged)
    {
        "post_id": "2017669714353537024",
        "has_prediction": True,
        "predictions": [
            {
                "ticker": "silver",
                "market": "commodity",
                "direction": "long",
                "claim_type": "thematic",
                "horizon": "long_term",
                "conviction": 2,
                "thesis_summary": "5 大银行白银操纵可能被惩罚,主题性 long(对冲措辞)",
            },
        ],
        "flags": [],
    },
    # 18) 2062390116820365350: 无预测,flags: influence_milestone(订阅数第一)
    {
        "post_id": "2062390116820365350",
        "has_prediction": False,
        "predictions": [],
        "flags": ["influence_milestone"],
    },
    # 19) 2058230354063102028: 无预测,flags: self_reported_returns + victory_lap(25 ticker 全不入)
    {
        "post_id": "2058230354063102028",
        "has_prediction": False,
        "predictions": [],
        "flags": ["self_reported_returns", "victory_lap"],
    },
    # 20) 2055401446397690311: 无预测,同上(23 ticker 全不入)
    {
        "post_id": "2055401446397690311",
        "has_prediction": False,
        "predictions": [],
        "flags": ["self_reported_returns", "victory_lap"],
    },
]


# 用于评测时按 post_id 索引
GOLD_BY_POST_ID = {e["post_id"]: e for e in GOLD_V1}


def get_gold_ids() -> List[str]:
    return [e["post_id"] for e in GOLD_V1]


def get_gold_entry(post_id: str):
    return GOLD_BY_POST_ID.get(post_id)
