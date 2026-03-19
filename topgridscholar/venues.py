"""
期刊/会议分组白名单。

三个来源组：
- IEEE Trans: 搜 IEEE 平台，按 journal 子串匹配白名单过滤
- CCF-A/B: 用 Semantic Scholar API 搜索，按 venue 名过滤
- Nature 系列: 搜 Nature 平台，不做额外过滤
"""

from collections import OrderedDict

VENUE_GROUPS = OrderedDict({
    # ==================== IEEE Trans ====================
    # AI + 电力/能源 合并为一个大组
    # pub_titles: IEEE Xplore 上的 Publication Title，用于逐期刊精确搜索
    "IEEE Trans": {
        "platform": "ieee",
        "pub_titles": [
            # --- AI / ML / CV / NLP ---
            "IEEE Transactions on Pattern Analysis and Machine Intelligence",
            "IEEE Transactions on Neural Networks and Learning Systems",
            "IEEE Transactions on Image Processing",
            "IEEE Transactions on Knowledge and Data Engineering",
            "IEEE Transactions on Evolutionary Computation",
            "IEEE Transactions on Fuzzy Systems",
            "IEEE Transactions on Affective Computing",
            "IEEE Transactions on Cybernetics",
            "IEEE Transactions on Artificial Intelligence",
            "IEEE/ACM Transactions on Audio, Speech and Language Processing",
            "IEEE Transactions on Multimedia",
            "IEEE Transactions on Cognitive and Developmental Systems",
            "IEEE Transactions on Emerging Topics in Computational Intelligence",
            "IEEE Transactions on Big Data",
            # --- 电力 / 能源 / 控制 ---
            "IEEE Transactions on Power Systems",
            "IEEE Transactions on Smart Grid",
            "IEEE Transactions on Industrial Electronics",
            "IEEE Transactions on Power Electronics",
            "IEEE Transactions on Sustainable Energy",
            "IEEE Transactions on Energy Conversion",
            "IEEE Transactions on Industrial Informatics",
            "IEEE Transactions on Automatic Control",
            "IEEE Transactions on Control Systems Technology",
            "IEEE Transactions on Power Delivery",
            "IEEE Transactions on Vehicular Technology",
            # --- 机器人 ---
            "IEEE Transactions on Robotics",
        ],
    },

    # ==================== CCF-A/B ====================
    # 与 AI/ML/NLP/CV/机器人/电力/能源/控制 相关的 CCF-A/B 期刊和会议
    # 使用 Semantic Scholar API 的 venue 参数值
    "CCF-A/B": {
        "platform": "semantic_scholar",
        "venues": [
            # --- CCF-A 会议 ---
            "AAAI",                  # AAAI Conference on Artificial Intelligence
            "NeurIPS",               # Neural Information Processing Systems
            "ICML",                  # International Conference on Machine Learning
            "CVPR",                  # IEEE/CVF Conference on Computer Vision and Pattern Recognition
            "ICCV",                  # IEEE/CVF International Conference on Computer Vision
            "ACL",                   # Annual Meeting of the Association for Computational Linguistics
            "IJCAI",                 # International Joint Conference on Artificial Intelligence
            "SIGKDD",               # ACM SIGKDD Conference on Knowledge Discovery and Data Mining
            # --- CCF-A 期刊 ---
            "Artificial Intelligence",           # AIJ
            "IEEE Trans. Pattern Anal. Mach. Intell.",  # TPAMI
            "International Journal of Computer Vision",  # IJCV
            # --- CCF-B 会议 ---
            "ECCV",                  # European Conference on Computer Vision
            "NAACL",                 # North American Chapter of the ACL
            "EMNLP",                 # Empirical Methods in Natural Language Processing
            "COLING",                # International Conference on Computational Linguistics
            "ICRA",                  # IEEE International Conference on Robotics and Automation
            "IROS",                  # IEEE/RSJ International Conference on Intelligent Robots and Systems
            "ICDM",                  # IEEE International Conference on Data Mining
            "ECAI",                  # European Conference on Artificial Intelligence
            "AAMAS",                 # International Conference on Autonomous Agents and Multi-Agent Systems
            "COLT",                  # Conference on Learning Theory
            "UAI",                   # Conference on Uncertainty in Artificial Intelligence
            "ACMMM",                 # ACM Multimedia
            "ICLR",                  # International Conference on Learning Representations
            # --- CCF-B 期刊 ---
            "Machine Learning",                  # ML (Springer)
            "Neural Networks",                   # Elsevier
            "Pattern Recognition",               # Elsevier
            "Journal of Machine Learning Research",  # JMLR
            "Neural Computation",                # MIT Press
            "Computational Linguistics",         # MIT Press
            "Knowledge and Information Systems",  # KAIS
        ],
        # Semantic Scholar 返回的 venue 全称白名单，用于本地二次过滤
        "venue_fullnames": [
            # --- CCF-A 会议 ---
            "AAAI Conference on Artificial Intelligence",
            "Neural Information Processing Systems",
            "International Conference on Machine Learning",
            "Computer Vision and Pattern Recognition",
            "IEEE/CVF Conference on Computer Vision and Pattern Recognition",
            "IEEE International Conference on Computer Vision",
            "IEEE/CVF International Conference on Computer Vision",
            "Annual Meeting of the Association for Computational Linguistics",
            "International Joint Conference on Artificial Intelligence",
            "Knowledge Discovery and Data Mining",
            "ACM SIGKDD International Conference on Knowledge Discovery and Data Mining",
            # --- CCF-A 期刊 ---
            "Artificial Intelligence",
            "IEEE Transactions on Pattern Analysis and Machine Intelligence",
            "International Journal of Computer Vision",
            # --- CCF-B 会议 ---
            "European Conference on Computer Vision",
            "North American Chapter of the Association for Computational Linguistics",
            "Conference on Empirical Methods in Natural Language Processing",
            "International Conference on Computational Linguistics",
            "IEEE International Conference on Robotics and Automation",
            "IEEE/RJS International Conference on Intelligent RObots and Systems",
            "IEEE/RSJ International Conference on Intelligent Robots and Systems",
            "IEEE International Conference on Data Mining",
            "European Conference on Artificial Intelligence",
            "International Conference on Autonomous Agents and Multi-Agent Systems",
            "Adaptive Agents and Multi-Agent Systems",
            "Conference on Learning Theory",
            "Conference on Uncertainty in Artificial Intelligence",
            "ACM Multimedia",
            "International Conference on Learning Representations",
            # --- CCF-B 期刊 ---
            "Machine Learning",
            "Neural Networks",
            "Pattern Recognition",
            "Journal of Machine Learning Research",
            "Neural Computation",
            "Computational Linguistics",
            "Knowledge and Information Systems",
        ],
    },

    # ==================== Nature 系列 ====================
    "Nature 系列": {
        "platform": "nature",
        "keywords": [],  # Nature 不做过滤
    },
})
