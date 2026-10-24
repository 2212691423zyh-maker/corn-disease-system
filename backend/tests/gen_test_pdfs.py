"""
生成测试用中文 PDF 文件（供知识库上传测试）。
使用 reportlab 生成符合 PDF 1.4 标准的真实 PDF，中文字体采用 STSong-Light。
不再降级为纯文本伪 PDF。
"""
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.pdfmetrics import stringWidth

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(TEST_DIR, exist_ok=True)

FONT_NAME = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))

KNOWLEDGE_DOCS = [
    {
        "filename": "玉米南方锈病防控手册.pdf",
        "content": """玉米南方锈病防控手册

一、病害概述
玉米南方锈病（Southern Corn Rust）是由多堆柄锈菌（Puccinia polysora Underw.）引起的气传性真菌病害，
是夏玉米主产区最严重的叶部病害之一。在我国河北省滦州市等夏玉米主产区，7-8月高温多雨季节
（气温25-30℃，相对湿度>90%）极易暴发流行。

二、症状识别
主要危害叶片，也可危害叶鞘、苞叶。叶片正面产生橙黄色至黄褐色粉状夏孢子堆，圆形或卵圆形，
直径1-3mm。后期在叶片背面产生黑褐色粉状冬孢子堆。严重时病斑密布，叶片枯死，
导致籽粒不饱满，产量损失可达30%-50%。

三、发病条件
1. 温度：夏孢子萌发最适温度15-25℃
2. 湿度：高湿（叶面结露）是侵染的必要条件
3. 品种：不同玉米品种抗性差异显著
4. 栽培：氮肥过量、密植、通风不良有利于发病

四、防治方法
（一）农业防治
1. 选用抗病品种：农大372、登海605、郑单958、先玉335等抗性较好
2. 合理密植：行距60cm，株距28-30cm，保证通风透光
3. 科学施肥：增施磷钾肥，避免偏施氮肥，亩施氯化钾10-15kg
4. 轮作倒茬：与小麦、大豆轮作，减少菌源积累

（二）化学防治
发病初期（7月中下旬）开始喷药防治，间隔7-10天1次，连喷2-3次。

推荐药剂：
1. 25%三唑酮可湿性粉剂 1000-1500倍液 叶面喷雾
2. 43%戊唑醇悬浮剂 3000倍液 叶面喷雾
3. 10%苯醚甲环唑微乳剂 2000倍液 叶面喷雾
4. 25%丙环唑乳油 1500倍液 叶面喷雾

注意事项：
- 药剂交替使用，防止产生抗药性
- 避免高温时段（正午）施药
- 雨后要及时补喷
- 安全间隔期21天以上

（三）生物防治
- 施用木霉菌制剂改善土壤微生物环境
- 释放捕食螨类防治传毒害虫

五、防治适期
- 预警期（7月中旬）：田间巡查3-5叶，发现病斑立即喷药保护
- 发病初期（7月下旬）：全面喷药防治
- 灌浆期（8月中下旬）：重点喷施戊唑醇+苯醚甲环唑复配液
""",
    },
    {
        "filename": "玉米常见病虫害识别图谱.pdf",
        "content": """玉米常见病虫害识别图谱

======================
真菌性病害
======================

1. 玉米大斑病
症状：叶片出现大型梭形或长梭形病斑，灰褐色，边缘颜色较深。病斑中央灰褐色，
外部暗褐色，周围有时有黄色晕圈。多个病斑可愈合成大斑块，后期枯死。
病原：大斑病凸脐蠕孢（Exserohilum turcicum）
防治：75%百菌清可湿性粉剂500-800倍液

2. 玉米小斑病
症状：叶片上出现小型椭圆形病斑，黄褐色，有同心轮纹，病斑周围有明显的黄色晕圈。
后期病斑可连成一片，叶片枯死。
病原：玉蜀黍平脐蠕孢（Bipolaris maydis）
防治：50%多菌灵可湿性粉剂500倍液，或70%甲基硫菌灵1000倍液

3. 玉米纹枯病
症状：茎基部出现云纹状褐色病斑，病斑中央灰褐色，边缘深褐色，界限清晰。
严重时病斑扩展到茎秆中部，导致茎秆变软倒伏。叶鞘上也有类似云纹状病斑。
病原：立枯丝核菌（Rhizoctonia solani）
防治：5%井冈霉素A水剂1500倍液喷雾茎基部

4. 玉米丝黑穗病
症状：系统侵染性病害，病株矮小，果穗被破坏成黑粉包状，内部充满黑色粉状孢子。
雄穗也可被侵染形成黑色粉状物，有时呈畸形分枝状。
病原：玉米丝黑穗菌（Sporisorium reilianum）
防治：25%多菌灵可湿性粉剂拌种（种子重量的0.3%）

======================
害虫
======================

5. 玉米螟
危害：以幼虫蛀入茎秆、叶鞘和果穗，造成排孔、风折、籽粒缺损。
在滦州市一年发生2-3代，第一代幼虫在6月下旬危害心叶，
第二代在8月危害果穗，第三代在9月蛀茎越冬。
防治：释放赤眼蜂（1万头/亩）；心叶末期喷Bt乳剂；秋季深翻灭茬

6. 玉米蚜虫
危害：多聚集在叶片背面、心叶和雄穗上刺吸汁液，造成叶片变黄卷曲。
分泌的蜜露诱发煤污病，影响光合作用。还能传播玉米粗缩病毒。
防治：10%吡虫啉可湿性粉剂2000倍液；黄板诱杀有翅蚜

7. 玉米粘虫
危害：迁飞性暴食害虫，大发生时可将叶片吃光，仅剩叶脉。
1-2龄幼虫群集取食叶肉，3龄后分散，4-5龄进入暴食期。
防治：糖醋液+性诱剂诱杀成虫；20%氰戊菊酯乳油2000倍液

======================
病毒病
======================

8. 玉米粗缩病
症状：病株严重矮化，节间缩短，叶片浓绿、宽厚，状如君子兰。
叶背沿脉产生白色蜡条。不能正常抽穗结实。
病原：玉米粗缩病毒（MRDV），由灰飞虱带毒传播
防治：调整播期避开灰飞虱传毒高峰；选用耐病品种；清除田边杂草
""",
    },
    {
        "filename": "滦州市2024年玉米病虫害防控预案.pdf",
        "content": """滦州市2024年夏玉米病虫害防控预案

一、监测预警
1. 重点监测对象：玉米南方锈病、大斑病、玉米螟、粘虫、蚜虫
2. 监测站点：全市设10个固定监测点，覆盖主要玉米主产区
3. 监测频率：从6月中旬开始，每5天巡查一次
4. 预警发布：达到经济阈值时发布预警信息

二、2024年防控重点
根据气象预测，2024年滦州市夏季气温偏高、降水偏多，
玉米南方锈病和大斑病暴发风险较高。

三、防控技术方案

（一）7月（营养生长期）
- 重点防治：玉米螟第一代、蚜虫
- 防治措施：释放赤眼蜂，喷施吡虫啉防蚜虫
- 巡查重点：心叶有没有虫粪排孔

（二）8月（抽雄灌浆期）
- 重点防治：玉米南方锈病、大斑病、玉米螟第二代
- 防治措施：
  1. 发病初期喷施三唑酮+戊唑醇（防锈病）
  2. 叶部喷施百菌清（防大斑病）
  3. 重点保护雌穗，喷施Bt乳剂或氰戊菊酯（防玉米螟）
- 防治指标：病株率达10%时立即施药

（三）9月（成熟期）
- 重点防治：玉米螟第三代、纹枯病
- 防治措施：深翻灭茬，减少越冬虫源；发现纹枯病植株及时喷井冈霉素

四、绿色防控技术
1. 性诱剂诱杀：每亩挂3-5个玉米螟性诱芯
2. 杀虫灯诱杀：每50亩挂1台频振式杀虫灯
3. 生物农药：Bt乳剂、春雷霉素、井冈霉素
4. 天敌保护：减少广谱杀虫剂使用，保护瓢虫、草蛉、食蚜蝇

五、应急防控
当突发大发生时，组织群防群治，统一药剂，统一时间喷施。
建立应急药剂储备：三唑酮、戊唑醇、百菌清、氰戊菊酯、吡虫啉等。

六、验收标准
1. 主要病虫危害损失率控制在5%以下
2. 病斑发病率控制在20%以下
3. 农药使用量较上年减少10%
""",
    },
]


def wrap_line(text: str, font: str, size: int, max_width: float) -> list:
    """按像素宽度把单行折成多行（中文按字符切割）"""
    if not text:
        return [""]
    result = []
    current = ""
    for ch in text:
        trial = current + ch
        if stringWidth(trial, font, size) <= max_width:
            current = trial
        else:
            if current:
                result.append(current)
            current = ch
    if current:
        result.append(current)
    return result


def generate_pdf(filepath: str, text: str) -> None:
    """用 reportlab 生成符合 PDF 1.4 标准的中文 PDF"""
    width, height = A4
    margin_x = 50
    max_width = width - 2 * margin_x
    font_size = 10
    line_height = 16

    c = canvas.Canvas(filepath, pagesize=A4, pdfVersion=(1, 4))
    c.setTitle(os.path.basename(filepath))
    c.setFont(FONT_NAME, font_size)

    y = height - margin_x
    for raw_line in text.split("\n"):
        for line in wrap_line(raw_line, FONT_NAME, font_size, max_width):
            if y < margin_x:
                c.showPage()
                c.setFont(FONT_NAME, font_size)
                y = height - margin_x
            c.drawString(margin_x, y, line)
            y -= line_height

    c.save()


if __name__ == "__main__":
    for doc in KNOWLEDGE_DOCS:
        fp = os.path.join(TEST_DIR, doc["filename"])
        generate_pdf(fp, doc["content"])
        size = os.path.getsize(fp)
        print(f"[OK] {doc['filename']}  ({size} bytes)")

    print(f"\n共生成 {len(KNOWLEDGE_DOCS)} 个测试 PDF，目录: {TEST_DIR}")
