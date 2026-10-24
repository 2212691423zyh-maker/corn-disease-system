-- ============================================================
-- 滦州玉米病害识别与管理系统 —— 数据库初始化脚本
-- docker-entrypoint-initdb.d 自动执行
-- ============================================================

USE crop_doctor;

SET NAMES utf8mb4;

-- ===== 1. 玉米病害字典表 =====
CREATE TABLE IF NOT EXISTS diseases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(128) NOT NULL COMMENT '病害名称',
    alias VARCHAR(256) COMMENT '别名（逗号分隔）',
    crop_type VARCHAR(64) DEFAULT '玉米' COMMENT '作物类型',
    description TEXT COMMENT '病害描述',
    symptoms TEXT COMMENT '症状表现',
    causes TEXT COMMENT '发病原因',
    prevention TEXT COMMENT '防治方法',
    severity VARCHAR(32) COMMENT '危害程度：轻度/中度/重度',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_crop (crop_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玉米病害字典';

-- ===== 2. 病害识别记录表 =====
CREATE TABLE IF NOT EXISTS recognition_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    image_path VARCHAR(512) NOT NULL COMMENT '图片存储路径',
    disease_id BIGINT COMMENT '关联病害 ID',
    confidence FLOAT COMMENT '识别置信度 0-1',
    lesion_description TEXT COMMENT '病灶区域描述',
    model_used VARCHAR(128) COMMENT '使用的模型名称',
    demo_mode TINYINT(1) DEFAULT 0 COMMENT '是否演示模式',
    top_candidates JSON COMMENT '候选病害列表 [{name, confidence}]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (disease_id) REFERENCES diseases(id),
    INDEX idx_created (created_at),
    INDEX idx_disease (disease_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='病害识别记录';

-- ===== 3. RAG 对话会话表 =====
CREATE TABLE IF NOT EXISTS chat_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(128) UNIQUE NOT NULL COMMENT '会话唯一标识 UUID',
    title VARCHAR(256) COMMENT '会话标题',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RAG 对话会话';

-- ===== 4. RAG 对话消息表 =====
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(128) NOT NULL COMMENT '关联会话 session_id',
    role VARCHAR(16) NOT NULL COMMENT 'user / assistant',
    content TEXT NOT NULL COMMENT '消息内容',
    citations JSON COMMENT '引用来源 [{doc_id, doc_name, chunk_text, score}]',
    retrieval_score FLOAT COMMENT '检索平均置信度',
    has_evidence TINYINT(1) DEFAULT 1 COMMENT '是否有检索证据支撑',
    model_used VARCHAR(128) COMMENT '使用的模型',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RAG 对话消息';

-- ===== 5. 知识库文档表 =====
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(256) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(512) NOT NULL COMMENT '存储路径',
    doc_type VARCHAR(32) NOT NULL COMMENT '文档类型：pdf/word/txt',
    chunk_count INT DEFAULT 0 COMMENT '分块数量',
    file_size BIGINT COMMENT '文件大小（字节）',
    status VARCHAR(32) DEFAULT 'uploaded' COMMENT 'uploaded/processing/indexed/failed',
    version VARCHAR(32) DEFAULT 'v1.0' COMMENT '版本号',
    error_msg TEXT COMMENT '失败时的错误信息',
    metadata JSON COMMENT '附加元数据',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_filename (filename)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档';

-- ===== 6. 知识库分块表 =====
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    document_id BIGINT NOT NULL COMMENT '关联文档 ID',
    chunk_index INT NOT NULL COMMENT '分块序号',
    chunk_id VARCHAR(128) COMMENT 'FAISS 向量库中的 chunk 标识',
    content TEXT NOT NULL COMMENT '分块文本内容',
    token_count INT COMMENT 'Token 数量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    INDEX idx_doc (document_id),
    INDEX idx_chunk_id (chunk_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档分块';

-- ===== 7. 文档版本表 =====
CREATE TABLE IF NOT EXISTS document_versions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    document_id BIGINT NOT NULL COMMENT '关联文档 ID',
    version VARCHAR(32) NOT NULL COMMENT '版本号',
    file_path VARCHAR(512) NOT NULL COMMENT '该版本文件路径',
    change_log TEXT COMMENT '变更说明',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档版本历史';

-- ===== 8. 防治方案表 =====
CREATE TABLE IF NOT EXISTS prevention_plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    recognition_id BIGINT COMMENT '关联识别记录',
    disease_id BIGINT COMMENT '关联病害',
    plan_title VARCHAR(256) NOT NULL COMMENT '方案标题',
    medication_plan JSON COMMENT '用药方案 [{drug, dosage, frequency, precautions}]',
    fertilization_plan JSON COMMENT '施肥方案 [{type, dosage, timing}]',
    prevention_tips TEXT COMMENT '综合防治建议',
    agricultural_operations TEXT COMMENT '农业操作建议',
    rag_evidence JSON COMMENT 'RAG 支撑证据 [{doc_name, chunk_text, citation}]',
    status VARCHAR(16) DEFAULT 'draft' COMMENT 'draft / final',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (recognition_id) REFERENCES recognition_records(id),
    FOREIGN KEY (disease_id) REFERENCES diseases(id),
    INDEX idx_recognition (recognition_id),
    INDEX idx_disease_plan (disease_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='防治方案';

-- ===== 9. 方案导出记录表 =====
CREATE TABLE IF NOT EXISTS plan_exports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plan_id BIGINT NOT NULL COMMENT '关联方案 ID',
    format VARCHAR(16) NOT NULL COMMENT 'pdf / word',
    file_path VARCHAR(512) NOT NULL COMMENT '导出文件路径',
    file_size BIGINT COMMENT '文件大小',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES prevention_plans(id) ON DELETE CASCADE,
    INDEX idx_plan (plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='方案导出记录';


-- ============================================================
-- 预置滦州玉米常见病害数据（20 条）
-- ============================================================

INSERT INTO diseases (name, alias, crop_type, description, symptoms, causes, prevention, severity) VALUES
('玉米大斑病', '大斑病、条斑病', '玉米', '玉米大斑病是由大斑病凸脐蠕孢引起的一种叶部真菌性病害，主要危害叶片，严重时危害叶鞘和苞叶。', '叶片出现大型梭形或长梭形病斑，灰褐色，边缘颜色较深。严重时病斑连片，叶片枯死。', '病菌以菌丝体或分生孢子在病残体上越冬，翌年产生分生孢子随风传播。高温高湿条件下易暴发。', '1. 选用抗病品种；2. 发病初期喷施75%百菌清可湿性粉剂500-800倍液；3. 秋收后清除病残体；4. 合理密植，改善通风条件。', '重度'),
('玉米小斑病', '小斑病', '玉米', '玉米小斑病由玉蜀黍平脐蠕孢引起，主要危害叶片，也可危害叶鞘、苞叶和果穗。', '叶片上出现小型椭圆形病斑，黄褐色，有同心轮纹，病斑周围有黄色晕圈。', '病菌在病残体上越冬，分生孢子借风雨传播。高温高湿、管理粗放时发病重。', '1. 选用抗病品种；2. 发病初期喷施50%多菌灵可湿性粉剂500倍液；3. 加强田间管理，增施磷钾肥。', '中度'),
('玉米纹枯病', '纹枯病、茎腐病', '玉米', '玉米纹枯病是由立枯丝核菌引起的一种土传病害，主要危害茎基部和叶鞘。', '茎基部出现云纹状褐色病斑，逐渐扩大，后期茎秆变软倒伏。叶鞘上也有类似病斑。', '病菌以菌核或菌丝在土壤和病残体中越冬，高温高湿条件下发病重。', '1. 合理密植；2. 发病初期喷施5%井冈霉素A水剂1500倍液；3. 深翻土壤，减少菌源。', '重度'),
('玉米南方锈病', '南方锈病、热带锈病', '玉米', '玉米南方锈病是由多堆柄锈菌引起的一种气传性叶部病害，滦州市夏季高温多雨时易暴发。', '叶片正面产生橙黄色粉状孢子堆，后期变成黑褐色。严重时叶片布满病斑，枯死。', '病菌随气流远距离传播，夏季高温多雨是主要诱因。滦州市7-8月为高发期。', '1. 选用抗病品种如农大372、登海605；2. 发病初期喷施25%三唑酮可湿性粉剂1000-1500倍液；3. 7月中下旬重点巡查防治。', '重度'),
('玉米丝黑穗病', '丝黑穗病、黑粉病', '玉米', '玉米丝黑穗病是由玉米丝黑穗菌引起的系统侵染性病害，病菌从幼芽侵入，破坏穗部发育。', '病株矮小，果穗被破坏成黑粉包状，内部充满黑色孢子。雄穗也可被侵染形成黑粉。', '病菌以冬孢子在土壤、种子表面和病残体上越冬，种子带菌是远距离传播的主要途径。', '1. 精选无病种子；2. 播种前用25%多菌灵可湿性粉剂拌种；3. 轮作倒茬；4. 及时拔除病株。', '中度'),
('玉米黑粉病', '黑粉病、瘤黑粉病', '玉米', '玉米黑粉病是由玉米黑粉菌引起的局部侵染性病害，可侵染玉米地上部任何幼嫩组织。', '受害部位形成大小不一的瘤状突起，初期白色，后期变成黑色，内部充满黑色粉状物。', '病菌以冬孢子在土壤和病残体上越冬，通过风雨传播，从伤口侵入。', '1. 选用抗病品种；2. 及时清除病瘤并深埋或烧毁；3. 避免机械损伤；4. 深翻土壤。', '轻度'),
('玉米锈病', '普通锈病、北方锈病', '玉米', '玉米锈病是由玉米柄锈菌引起的叶部病害，在滦州市秋季多雨时易发生。', '叶片两面产生黄褐色粉状小疱（夏孢子堆），后期变成黑色（冬孢子堆），严重时叶片枯死。', '病菌以夏孢子在南方玉米上越冬，随气流北迁传播。秋凉多雨时发病重。', '1. 选用抗病品种；2. 发病初期喷施15%三唑酮可湿性粉剂1000倍液；3. 增施磷钾肥提高抗性。', '中度'),
('玉米褐斑病', '褐斑病', '玉米', '玉米褐斑病是由玉蜀黍尾孢菌引起的叶部病害，在玉米中后期常发生。', '叶片上出现黄褐色小圆形病斑，后期隆起成疱状，破裂后散出褐色粉末。严重时叶片枯死。', '病菌在病残体上越冬，高温高湿、氮肥过多时易发病。', '1. 选用抗病品种；2. 发病初期喷施70%甲基硫菌灵可湿性粉剂1000倍液；3. 合理施肥，避免偏施氮肥。', '轻度'),
('玉米霜霉病', '霜霉病、疯顶病', '玉米', '玉米霜霉病是由多种卵菌引起的系统性病害，属于检疫性病害。', '病株矮化，叶片变厚变脆，有白色霜状霉层。雄穗或雌穗畸形。', '病菌随土壤和种子传播，低温高湿条件下易发病。', '1. 严格检疫，使用无病种子；2. 选用抗病品种；3. 及时拔除病株销毁。', '中度'),
('玉米矮化病', '粗缩病、矮缩病', '玉米', '玉米矮化病由玉米粗缩病毒引起，由灰飞虱传播的病毒病。', '病株严重矮化，节间缩短，叶片浓绿、宽厚，状如君子兰。不能正常抽穗结实。', '病毒由灰飞虱带毒传播，灰飞虱在麦田越冬后迁入玉米田传毒。', '1. 调整播期，避开灰飞虱传毒高峰期；2. 防治灰飞虱；3. 选用耐病品种；4. 及时拔除病株。', '重度'),
('玉米蚜虫', '玉米蚜、腻虫', '玉米', '玉米蚜虫是危害玉米的主要刺吸式口器害虫，不仅直接危害还能传播病毒。', '多聚集在叶片背面、心叶和雄穗上刺吸汁液，造成叶片变黄卷曲。分泌的蜜露诱发煤污病。', '蚜虫以卵在杂草上越冬，春季迁入玉米田。干旱年份发生重。', '1. 黄板诱杀有翅蚜；2. 喷施10%吡虫啉可湿性粉剂2000倍液；3. 保护瓢虫、草蛉等天敌。', '中度'),
('玉米螟', '玉米钻心虫、螟虫', '玉米', '玉米螟是危害玉米的主要蛀茎害虫，在滦州市一年发生2-3代。', '幼虫蛀入茎秆、叶鞘和果穗，造成排孔、风折、籽粒缺损。果穗受害严重影响产量。', '玉米螟以老熟幼虫在茎秆、穗轴内越冬，翌年化蛹羽化。', '1. 释放赤眼蜂生物防治；2. 心叶末期喷施Bt乳剂；3. 秋季深翻灭茬消灭越冬幼虫；4. 使用性诱剂诱杀成虫。', '重度'),
('玉米粘虫', '粘虫、行军虫', '玉米', '玉米粘虫是迁飞性暴食害虫，在玉米叶片上取食，大发生时可将叶片吃光。', '幼虫取食叶片，1-2龄群集取食叶肉，3龄后分散，4-5龄暴食期可将叶片吃成缺刻或吃光。', '粘虫是迁飞性害虫，从南方飞来，在适宜条件下大量繁殖。', '1. 糖醋液或性诱剂诱杀成虫；2. 低龄幼虫期喷施20%氰戊菊酯乳油2000倍液；3. 清晨人工捕捉。', '重度'),
('玉米红蜘蛛', '叶螨、红蜘蛛', '玉米', '玉米红蜘蛛是蛛形纲蜱螨目害虫，在叶片背面吸食汁液。', '受害叶片出现黄白色小点，严重时叶片灰白、干枯脱落。叶背面可见红色小螨虫。', '以成螨或卵在杂草、土缝中越冬，高温干旱年份发生重。', '1. 清除田边杂草减少虫源；2. 喷施1.8%阿维菌素乳油3000倍液；3. 合理灌溉，避免干旱。', '中度'),
('玉米蓟马', '蓟马', '玉米', '玉米蓟马是缨翅目害虫，以锉吸式口器刮破表皮吸食汁液。', '叶片上出现银白色斑点，严重时叶片变形扭曲，心叶受害最重，影响幼苗生长。', '蓟马以成虫或若虫在杂草上越冬，春旱年份发生重。', '1. 适时灌溉增加田间湿度；2. 喷施10%吡虫啉可湿性粉剂2000倍液或5%啶虫脒乳油1500倍液；3. 清除田边杂草。', '轻度'),
('玉米叶螨', '叶螨、白蜘蛛', '玉米', '玉米叶螨又叫二斑叶螨，在滦州市夏玉米中后期常暴发。', '叶片正面出现黄白色小斑点，严重时叶片变白干枯。叶背面有白色或浅黄色小螨虫。', '以雌成螨在杂草、土壤缝隙中越冬，高温干旱年份暴发。', '1. 清除田边杂草；2. 喷施0.3%印楝素乳油1000倍液或1.8%阿维菌素3000倍液；3. 增加田间湿度。', '中度'),
('玉米茎腐病', '茎腐病、青枯病', '玉米', '玉米茎腐病是由多种病原菌复合侵染引起的土传病害，在灌浆期开始发病。', '植株突然青枯死亡，叶片保持绿色但失水萎蔫。茎秆基部变软，内部变褐腐烂，果穗倒挂。', '病原菌在土壤中越冬，通过根系或茎基部伤口侵入。灌浆期多雨易暴发。', '1. 选用抗病品种；2. 适期晚播；3. 合理密植；4. 防止虫害造成伤口；5. 轮作倒茬。', '重度'),
('玉米穗腐病', '穗腐病、霉变', '玉米', '玉米穗腐病是由多种真菌引起的果穗病害，可导致籽粒霉变，部分产生毒素。', '果穗局部或全部变色变腐，籽粒发霉，有白色、红色、绿色霉层。严重时整穗腐烂。', '病原菌广泛存在于土壤中，通过花丝、伤口或灌浆期侵染。后期多雨易发病。', '1. 选用抗穗腐品种；2. 防治玉米螟减少伤口；3. 适时收获；4. 收获后及时晾晒；5. 秸秆还田需深翻。', '中度'),
('玉米灰斑病', '灰斑病、尾孢菌叶斑病', '玉米', '玉米灰斑病由玉米尾孢菌引起，是近年来北方玉米产区上升较快的叶部病害。', '叶片上出现矩形灰色病斑，边缘褐色，与叶脉平行扩展，后期病斑连片导致叶片枯死。', '病菌在病残体上越冬，分生孢子借风雨传播。多雨高湿、连作时发病重。', '1. 选用抗病品种；2. 秋收后深翻灭茬；3. 发病初期喷施70%甲基硫菌灵可湿性粉剂1000倍液；4. 合理密植。', '中度'),
('玉米细菌性茎腐病', '细菌性茎腐病', '玉米', '玉米细菌性茎腐病由欧文氏杆菌等细菌引起，高温高湿条件下发病重。', '茎秆中部出现水渍状病斑，后变褐软化，有恶臭味。叶片萎蔫下垂，植株易倒伏。', '细菌在病残体和种子上越冬，通过昆虫伤口或暴风雨造成的伤口侵入。', '1. 选用抗病品种；2. 防治玉米螟等害虫减少伤口；3. 暴风雨后及时检查清除病株；4. 避免大水漫灌。', '重度');
