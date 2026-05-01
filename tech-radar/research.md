# 子命令：research — AI研究成果前沿

## 搜索目标

搜索机器人与自动驾驶领域的最新AI模型研究成果。

组织方式：**先按应用领域，再按方法范式**，每个领域下列出所有相关范式。

---

## 领域一：🤖 机器人 (Robotics)

### 1. VLA — 视觉-语言-动作模型

将视觉感知、语言指令、动作执行统一到端到端模型，直接输出机器人动作。

- **典型工作**：RT-2, Octo, OpenVLA, π0, RoboFlamingo, ManipLLM, HPT, CROSS
- **搜索关键词**：
  ```
  WebSearch: "VLA vision language action model robotics 2025 2026 ICRA CoRL NeurIPS"
  WebSearch: "end-to-end robot manipulation VLA 2025 2026"
  ```

### 2. VLN — 视觉-语言导航模型

根据自然语言指令在视觉环境中自主导航。

- **典型工作**：VLN-CE, NaVid, LM-Nav, SayNav, ViNT, MapGPT
- **搜索关键词**：
  ```
  WebSearch: "VLN vision language navigation robot 2025 2026 IROS ICRA"
  WebSearch: "embodied navigation foundation model 2025 2026"
  ```

### 3. 模仿学习 (Imitation Learning / Learning from Demonstration)

从人类演示中学习操作策略，包括行为克隆、逆强化学习、扩散策略。

- **典型工作**：ACT, Diffusion Policy, 3D Diffusion Policy, ALOHA, Mobile ALOHA, DAgger
- **搜索关键词**：
  ```
  WebSearch: "imitation learning robot manipulation 2025 2026 CoRL RSS ICRA"
  WebSearch: "diffusion policy robot 2025 2026"
  WebSearch: "learning from demonstration humanoid 2025 2026"
  ```

### 4. 强化学习策略 (RL Policy / Sim2Real)

通过试错学习优化运动策略，重点在仿真到真实的迁移。

- **典型工作**：Isaac Gym locomotion, RoboCasa, Dexterity, Humanoid stand/walk
- **搜索关键词**：
  ```
  WebSearch: "reinforcement learning robot sim2real 2025 2026"
  WebSearch: "humanoid locomotion RL policy 2025 2026"
  WebSearch: "dexterous manipulation reinforcement learning 2025 2026"
  ```

### 5. 世界模型 (World Models for Robotics)

学习环境动态模型，用于机器人仿真、策略预演和数据增广。

- **典型工作**：UniSim, DIAMOND, Genie, IRASim, RoboDreamer
- **搜索关键词**：
  ```
  WebSearch: "world model robotics simulation policy learning 2025 2026"
  WebSearch: "robot world model data augmentation 2025 2026"
  ```

### 6. LLM/VLM 驱动规划 (LLM-as-Planner)

利用大语言/视觉语言模型进行高层任务规划、推理和代码生成。

- **典型工作**：SayCan, Inner Monologue, Code as Policies, VoxPoser, NL2Robot
- **搜索关键词**：
  ```
  WebSearch: "LLM planner robot task planning 2025 2026 ICRA CoRL"
  WebSearch: "large language model embodied agent 2025 2026"
  ```

### 7. 3D 场景理解 (3D Scene Understanding for Robotics)

构建 3D 语义表示，用于场景理解和机器人交互。

- **典型工作**：LERF, ConceptFusion, OpenScene, 3D Gaussian Splatting for robotics
- **搜索关键词**：
  ```
  WebSearch: "3D scene understanding robot 2025 2026"
  WebSearch: "3D Gaussian Splatting robotics manipulation 2025 2026"
  WebSearch: "NeRF semantic scene representation robot 2025 2026"
  ```

### 8. 触觉与灵巧操作 (Tactile Sensing & Dexterous Manipulation)

触觉感知驱动的精细操作、灵巧手控制。

- **典型工作**：TACTILE, DigiTac, AnySkin, LEAP Hand, Allegro
- **搜索关键词**：
  ```
  WebSearch: "tactile sensing robot manipulation 2025 2026"
  WebSearch: "dexterous hand manipulation foundation model 2025 2026"
  ```

### 9. 多机器人协作 (Multi-Agent / Multi-Robot)

多机器人协同规划、通信和任务分配。

- **典型工作**：MARL, LLM-based multi-robot, swarm robotics
- **搜索关键词**：
  ```
  WebSearch: "multi-robot coordination planning 2025 2026"
  WebSearch: "multi-agent reinforcement learning robot 2025 2026"
  ```

### 10. 人形机器人 (Humanoid Robotics)

人形机器人的全身控制、移动操作和人机交互。

- **典型工作**：Unitree H1, Figure 01/02, Tesla Optimus, Xiaomi CyberOne, 1X NEO
- **搜索关键词**：
  ```
  WebSearch: "humanoid robot AI control 2025 2026"
  WebSearch: "humanoid whole-body manipulation 2025 2026"
  ```

---

## 领域二：🚗 自动驾驶 (Autonomous Driving)

### 1. 端到端感知-规划 (End-to-End Perception-Planning)

从原始传感器输入直接输出规划/控制信号，跳过模块化流水线。

- **典型工作**：UniAD, VAD, SparseDrive, GenAD, DriveVLM, ThinkTwice, SparseDrive
- **搜索关键词**：
  ```
  WebSearch: "end-to-end autonomous driving model 2025 2026 CVPR ECCV ICCV"
  WebSearch: "perception planning unified model driving 2025 2026"
  ```

### 2. 世界模型 (World Models for Driving)

学习驾驶场景的动态模型，用于仿真、数据增广和世界模型驱动的规划。

- **典型工作**：GAIA-1, DriveDreamer, OccWorld, Copilot4D, GenAD-world
- **搜索关键词**：
  ```
  WebSearch: "world model autonomous driving 2025 2026 CVPR NeurIPS"
  WebSearch: "driving world model simulation planning 2025 2026"
  ```

### 3. BEV 感知 (Bird's Eye View Perception)

将多摄像头/LiDAR 数据转换为鸟瞰图表示，进行 3D 目标检测和地图构建。

- **典型工作**：BEVFormer, BEVDet, StreamPETR, Far3D
- **搜索关键词**：
  ```
  WebSearch: "BEV perception autonomous driving 2025 2026 CVPR ECCV"
  WebSearch: "bird eye view 3D detection driving 2025 2026"
  ```

### 4. 占据网络 (Occupancy Networks)

对驾驶场景进行体素级 3D 占据预测，替代传统 3D 检测框。

- **典型工作**：OccNet, SurroundOcc, OpenOccupancy, FlashOcc, SparseOcc
- **搜索关键词**：
  ```
  WebSearch: "occupancy network autonomous driving 2025 2026"
  WebSearch: "3D occupancy prediction driving 2025 2026"
  ```

### 5. VLA/VLM 驾驶决策 (VLA/VLM for Driving)

将视觉-语言-动作模型应用于驾驶场景理解和决策。

- **典型工作**：DriveVLM, LMDrive, DriveGPT4, LanguageMPC
- **搜索关键词**：
  ```
  WebSearch: "VLA VLM autonomous driving decision 2025 2026"
  WebSearch: "vision language model driving scene understanding 2025 2026"
  ```

### 6. 轨迹预测 (Trajectory Prediction)

预测道路上其他车辆、行人的未来轨迹。

- **典型工作**：MTR, QCNet, UniTR, Forecast-MAE
- **搜索关键词**：
  ```
  WebSearch: "trajectory prediction autonomous driving 2025 2026 CVPR NeurIPS"
  WebSearch: "motion prediction multi-agent driving 2025 2026"
  ```

### 7. 点云/激光雷达感知 (LiDAR / Point Cloud Perception)

处理 LiDAR 点云数据进行 3D 目标检测和语义分割。

- **典型工作**：CenterPoint, TransFusion, LiDAR-PT, SphereFormer
- **搜索关键词**：
  ```
  WebSearch: "LiDAR point cloud 3D detection autonomous driving 2025 2026"
  WebSearch: "point cloud segmentation driving 2025 2026"
  ```

### 8. 3D 场景重建 (3D Scene Reconstruction for Driving)

对驾驶场景进行 3D 重建和新视角合成。

- **典型工作**：Street Gaussians, DrivingGaussian, UniSim-driving, MARS
- **搜索关键词**：
  ```
  WebSearch: "3D Gaussian Splatting autonomous driving scene 2025 2026"
  WebSearch: "NeRF street scene reconstruction driving 2025 2026"
  ```

### 9. 地图构建与定位 (HD Map / Online Mapping)

实时构建高精地图和在线地图元素检测。

- **典型工作**：MapTR, VectorMapNet, StreamMapNet, ADMap
- **搜索关键词**：
  ```
  WebSearch: "online HD map construction autonomous driving 2025 2026"
  WebSearch: "MapTR vectorized map prediction 2025 2026"
  ```

### 10. 数据闭环与仿真 (Data Engine / Simulation)

自动驾驶数据引擎、仿真平台和合成数据生成。

- **典型工作**：CARLA, nuPlan, Waymo Open Dataset, Bench2Drive
- **搜索关键词**：
  ```
  WebSearch: "autonomous driving simulation data engine 2025 2026"
  WebSearch: "synthetic data generation driving 2025 2026"
  ```

---

## 领域三：🌐 通用基础 (Cross-Domain Foundations)

以下范式同时服务于机器人和自动驾驶，也有独立的通用价值。

### 1. 世界模型 (World Models — General)

视频生成式世界模型，可泛化到机器人和驾驶场景。

- **典型工作**：Sora, Cosmos, MovieGen, Kling, Veo
- **搜索关键词**：
  ```
  WebSearch: "video generation world model Sora Cosmos 2025 2026"
  WebSearch: "world simulator general purpose 2025 2026"
  ```

### 2. 3D 基础模型 (3D Foundation Models)

通用 3D 理解、重建和生成模型。

- **典型工作**：3D Gaussian Splatting, NeRF, Point-E, Shap-E, Wonder3D, Instant3D
- **搜索关键词**：
  ```
  WebSearch: "3D foundation model reconstruction generation 2025 2026"
  WebSearch: "3D Gaussian Splatting latest 2025 2026"
  WebSearch: "NeRF novel view synthesis 2025 2026"
  ```

### 3. 视觉基础模型 (Vision Foundation Models)

通用视觉特征提取和理解，服务于下游机器人/驾驶任务。

- **典型工作**：SAM2, DINOv2, CLIP, SigLIP, GroundingDINO, Florence-2
- **搜索关键词**：
  ```
  WebSearch: "vision foundation model SAM DINOv2 2025 2026"
  WebSearch: "visual representation learning downstream robotics driving 2025 2026"
  ```

### 4. 扩散模型 (Diffusion Models)

扩散模型在机器人策略、驾驶场景生成等领域的应用。

- **典型工作**：Diffusion Policy, DiffusionDrive, DDPM, DiT, Consistency Models
- **搜索关键词**：
  ```
  WebSearch: "diffusion model robotics policy 2025 2026"
  WebSearch: "diffusion model autonomous driving generation 2025 2026"
  ```

### 5. 多模态大模型 (Multimodal LLMs)

多模态大模型作为机器人/驾驶的感知与推理骨干。

- **典型工作**：GPT-5, Gemini 2.5, Qwen-VL, InternVL, LLaVA, CogVLM
- **搜索关键词**：
  ```
  WebSearch: "multimodal LLM robotics autonomous driving 2025 2026"
  WebSearch: "vision language model embodied 2025 2026"
  ```

---

## 覆盖的顶会与期刊

### 🤖 机器人

| 缩写 | 全称 | 类型 |
|------|------|------|
| **ICRA** | IEEE Intl. Conf. on Robotics and Automation | 顶会 |
| **CoRL** | Conference on Robot Learning | 顶会 |
| **IROS** | IEEE/RSJ Intl. Conf. on Intelligent Robots and Systems | 顶会 |
| **RSS** | Robotics: Science and Systems | 顶会 |
| **ISRR** | Intl. Symposium on Robotics Research | 顶会 |
| **RA-L** | IEEE Robotics and Automation Letters | 期刊 |
| **IJRR** | International Journal of Robotics Research | 期刊 |
| **T-RO** | IEEE Transactions on Robotics | 期刊 |
| **Science Robotics** | Science Robotics | 期刊 |
| **AuRob** | Autonomous Robots | 期刊 |

### 🚗 自动驾驶

| 缩写 | 全称 | 类型 |
|------|------|------|
| **ITSC** | IEEE Intl. Conf. on Intelligent Transportation Systems | 顶会 |
| **IV** | IEEE Intelligent Vehicles Symposium | 顶会 |
| **T-ITS** | IEEE Trans. on Intelligent Transportation Systems | 期刊 |
| **T-IV** | IEEE Transactions on Intelligent Vehicles | 期刊 |
| **TR-C** | Transportation Research Part C | 期刊 |

### 🧠 AI / 机器学习

| 缩写 | 全称 | 类型 |
|------|------|------|
| **NeurIPS** | Conference on Neural Information Processing Systems | 顶会 |
| **ICML** | International Conference on Machine Learning | 顶会 |
| **ICLR** | International Conference on Learning Representations | 顶会 |
| **AAAI** | AAAI Conference on Artificial Intelligence | 顶会 |
| **IJCAI** | International Joint Conference on AI | 顶会 |

### 👁️ 计算机视觉

| 缩写 | 全称 | 类型 |
|------|------|------|
| **CVPR** | IEEE/CVF Conf. on Computer Vision and Pattern Recognition | 顶会 |
| **ECCV** | European Conference on Computer Vision | 顶会 |
| **ICCV** | IEEE Intl. Conf. on Computer Vision | 顶会 |
| **WACV** | Winter Conf. on Applications of Computer Vision | 顶会 |
| **T-PAMI** | IEEE Trans. on Pattern Analysis and Machine Intelligence | 期刊 |
| **IJCV** | International Journal of Computer Vision | 期刊 |

### 🗣️ 语音 / NLP / 多模态

| 缩写 | 全称 | 类型 |
|------|------|------|
| **ACL** | Association for Computational Linguistics | 顶会 |
| **EMNLP** | Empirical Methods in NLP | 顶会 |
| **NAACL** | North American Chapter of ACL | 顶会 |
| **INTERSPEECH** | Conference of ISCA | 顶会 |
| **ICASSP** | IEEE Intl. Conf. on Acoustics, Speech and Signal Processing | 顶会 |
| **MM** | ACM Multimedia | 顶会 |
| **TASLP** | IEEE/ACM Trans. on Audio, Speech, and Language Processing | 期刊 |

### 📖 综合期刊与杂志

| 缩写 | 全称 | 类型 |
|------|------|------|
| **Nature** | Nature | 顶刊 |
| **Science** | Science | 顶刊 |
| **Nature Machine Intelligence** | Nature Machine Intelligence | 顶刊子刊 |
| **Nature Communications** | Nature Communications | 顶刊子刊 |
| **IEEE Spectrum** | IEEE Spectrum | 杂志 |
| **CACM** | Communications of the ACM | 杂志 |
| **Artificial Intelligence** | Artificial Intelligence Journal | 期刊 |
| **JMLR** | Journal of Machine Learning Research | 期刊 |

### 📄 预印本与学术平台

| 平台 | 分类 |
|------|------|
| **arXiv cs.RO** | 机器人 |
| **arXiv cs.CV** | 计算机视觉 |
| **arXiv cs.AI** | 人工智能 |
| **arXiv cs.LG** | 机器学习 |
| **arXiv cs.CL** | 计算语言学 |
| **arXiv cs.SD / eess.AS** | 语音/音频 |
| **OpenReview** | ICLR / NeurIPS 论文评审 |
| **Papers with Code** | 论文 + 代码 + SOTA 排行榜 |
| **Semantic Scholar** | AI 驱动学术搜索 |
| **Google Scholar** | 综合学术搜索 |

---

## 搜索流程

### 第一步：按领域搜索

```
# 🤖 机器人
WebSearch: "VLA vision language action robot 2025 2026 ICRA CoRL NeurIPS"
WebSearch: "VLN vision language navigation robot 2025 2026 IROS ICRA"
WebSearch: "imitation learning diffusion policy robot 2025 2026"
WebSearch: "reinforcement learning robot sim2real humanoid 2025 2026"
WebSearch: "world model robot simulation 2025 2026"
WebSearch: "LLM planner embodied robot 2025 2026"
WebSearch: "3D scene understanding robot 2025 2026"
WebSearch: "tactile dexterous manipulation 2025 2026"
WebSearch: "multi-robot coordination 2025 2026"
WebSearch: "humanoid robot AI control 2025 2026"

# 🚗 自动驾驶
WebSearch: "end-to-end autonomous driving 2025 2026 CVPR ECCV"
WebSearch: "world model driving simulation 2025 2026"
WebSearch: "BEV perception autonomous driving 2025 2026"
WebSearch: "occupancy network driving 3D 2025 2026"
WebSearch: "VLA VLM driving decision 2025 2026"
WebSearch: "trajectory prediction driving 2025 2026"
WebSearch: "LiDAR point cloud driving 2025 2026"
WebSearch: "3D Gaussian Splatting driving scene 2025 2026"
WebSearch: "online HD map construction driving 2025 2026"
WebSearch: "driving simulation data engine 2025 2026"

# 🌐 通用基础
WebSearch: "video world model Sora Cosmos 2025 2026"
WebSearch: "3D foundation model 2025 2026"
WebSearch: "vision foundation model SAM DINOv2 2025 2026"
WebSearch: "diffusion model robotics driving 2025 2026"
WebSearch: "multimodal LLM embodied driving 2025 2026"
```

### 第二步：顶会/期刊补充

```
WebSearch: "ICRA 2026 best paper robot"
WebSearch: "CoRL 2025 2026 accepted papers"
WebSearch: "CVPR 2026 autonomous driving 3D"
WebSearch: "NeurIPS 2025 robot embodied AI"
WebSearch: "Science Robotics Nature Machine Intelligence 2025 2026"
WebSearch: "Papers with Code SOTA VLA VLN world model 2026"
```

### 第三步：详情获取

- 对 Top 论文使用 WebFetch 获取 arXiv 摘要
- 从 Papers with Code 获取 SOTA 对比
- 从 Semantic Scholar 获取引用和影响力

---

## 输出格式

```markdown
### 🔬 研究前沿 — {日期}

---

## 🤖 机器人

### VLA — 视觉-语言-动作模型
- **{论文标题}** — {机构} | {会议/期刊} {年份}
  {一句话摘要}
  📎 {URL}

### VLN — 视觉-语言导航模型
...

### 模仿学习
...

### 强化学习策略
...

### 世界模型
...

### LLM/VLM 驱动规划
...

### 3D 场景理解
...

### 触觉与灵巧操作
...

### 多机器人协作
...

### 人形机器人
...

---

## 🚗 自动驾驶

### 端到端感知-规划
...

### 世界模型
...

### BEV 感知
...

### 占据网络
...

### VLA/VLM 驾驶决策
...

### 轨迹预测
...

### 点云/激光雷达感知
...

### 3D 场景重建
...

### 地图构建与定位
...

### 数据闭环与仿真
...

---

## 🌐 通用基础

### 世界模型 (视频生成)
...

### 3D 基础模型
...

### 视觉基础模型
...

### 扩散模型
...

### 多模态大模型
...

---
📊 统计：扫描 {N} 个会议/期刊，覆盖 {K} 个范式，发现 {M} 篇相关论文
```

---

## 搜索策略

- 如用户指定了具体领域（"机器人"/"自动驾驶"），只搜索该领域下的所有范式
- 如用户指定了具体范式（"VLA"/"世界模型"），搜索所有领域下该范式的论文
- 如用户指定了具体会议/期刊，在该范围内搜索所有领域和范式
- 默认优先级：顶会 > 期刊 > 预印本
- 中国机构特别关注：清华、北大、上交、浙大、中科院、港大、港中文、港科大、小米、华为、百度
- 每个范式至少搜索 2-3 个不同来源以保证覆盖度
