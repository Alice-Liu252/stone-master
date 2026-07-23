# 石頭大師 Stone Master

一款結合 AR 實境探索、AI 石頭辨識、石頭角色養成、策略戰鬥與多人社交的手機遊戲。玩家從現實世界掃描石頭，AI 分析外型、顏色、紋理生成專屬 3D 角色，培養、裝扮、戰鬥，成為世界級石頭大師。

- 平台：iOS / Android
- 引擎：Unity 6 (6000.5.4f1) + AR Foundation + URP

## 文件

- [遊戲設計文件 GDD](docs/GDD.md)
- [技術架構文件](docs/TECHNICAL_ARCHITECTURE.md)
- [開發路線圖](docs/ROADMAP.md)
- [AI 石頭百科種子資料（10 種範例）](docs/species/ENCYCLOPEDIA_SAMPLE.md)
- [AI 石頭百科種子資料（第二批 8 種）](docs/species/ENCYCLOPEDIA_02.md)

## 程式碼

- [backend/](backend/) — Phase 0 掃描 pipeline 邏輯原型（視覺特徵抽取 → 決定性生成 → 同顆石頭辨識 → AI 百科/助手 → 戰鬥 → 養成 → 捕捉），Python，可直接跑、有測試。
- [StoneMasterClient/](StoneMasterClient/) — Unity 專案本體，已建置 AR Session + XR Origin 基礎場景，iOS/Android XR 模組已啟用，尚未實作掃描/圖鑑/戰鬥等實際遊戲畫面。

## 目前狀態

Phase 0 進行中：後端 pipeline 邏輯已驗證（見 [backend/README.md](backend/README.md)）。Unity 專案已建立，AR 基礎場景可運作，下一步是把後端 pipeline 邏輯接上實際的手機 AR 掃描介面。詳見路線圖。
