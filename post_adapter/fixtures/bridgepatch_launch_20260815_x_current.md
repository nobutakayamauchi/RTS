BridgePatch: 販売導線の本番スモークで旧Stripe明細名の残留を検出し、専用Price/Payment Linkへ切り替えて再検証しました。

• BridgePatchは2026-08-15にPUBLIC_SALE_APPROVEDを受け、公開販売状態へ移行しました。
• 専用Payment Link v2はliveかつactiveで、公開URLは販売ページのproduction configに設定されています。
• v2のline itemは「BridgePatch 暫定ツール実装設計書」、数量1、合計10,000円で検証済みです。
• 旧Payment Linkは旧商品名がline itemに残っていたためinactive化しました。
• Payment Link差替え後のGitHub Pages buildはhotfix commitに対して成功し、build errorはありませんでした。
• この更新で顧客への請求やSNSへの自動投稿は実行していません。

BridgePatchでは、まず無料で『この作業は小さく切って直せるか』を確認できます。
