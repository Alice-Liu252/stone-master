# 石頭大師 Stone Master

一款結合 AR 實境探索、AI 石頭辨識、石頭角色養成、策略戰鬥與多人社交的手機遊戲。玩家從現實世界掃描石頭，AI 分析外型、顏色、紋理生成專屬 3D 角色，培養、裝扮、戰鬥，成為世界級石頭大師。

- 平台：iOS / Android
- 引擎：Unity + AR Foundation（規劃中，見技術架構文件）

## 文件

- [遊戲設計文件 GDD](docs/GDD.md)
- [技術架構文件](docs/TECHNICAL_ARCHITECTURE.md)
- [開發路線圖](docs/ROADMAP.md)
- [AI 石頭百科種子資料（10 種範例）](docs/species/ENCYCLOPEDIA_SAMPLE.md)
- [AI 石頭百科種子資料（第二批 8 種）](docs/species/ENCYCLOPEDIA_02.md)

## 程式碼

- [backend/](backend/) — Phase 0 掃描 pipeline 邏輯原型（視覺特徵抽取 → 決定性生成 → 同顆石頭辨識），Python，可直接跑、有測試。尚無 Unity/AR 客戶端與正式後端。

## 目前狀態

Phase 0 進行中：掃描/辨識/生成 pipeline 邏輯已驗證（見 [backend/README.md](backend/README.md)）。Unity/AR 客戶端尚未開始，待本機安裝 Unity Hub + Xcode/Android SDK。詳見路線圖。
