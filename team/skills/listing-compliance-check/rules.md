# Listing rules per channel

As of 2026-09-24 (research 10). `[3P]` third-party source only; `[U]` unverified. Current code state in brackets.

## All channels
| Check | Rule | Source |
|---|---|---|
| Human approval | Every AI draft is approved by a person before publish | Amazon BSA Agent Policy 2026-03-04 [U details]; research 12 §1.9 LLM06 |
| Truthful claims | No claims the item can't back; no "best/#1" without proof | FTC Act §5; https://www.ftc.gov/legal-library/browse/ftc-policy-statement-regarding-advertising-substantiation |
| Trademark | Score ≥ 60 blocks publish; 25–59 needs a recorded human review | `src/modules/ai/trademark.ts` `combineRisk`; team rule |
| No training | Marketplace data never trains or tunes models | research 10 R15 |

## Etsy
| Check | Rule | Source | [Code today] |
|---|---|---|---|
| AI disclosure | If the **design or item** was created with AI, say so **in the description**. There is no API field | https://www.etsy.com/legal/creativity | [`AI_DISCLOSURE` in `src/ai/validators/listing.ts` discloses AI *copy*: aimed wrong, M-23] |
| Production partner | Use `production_partner_ids` (ids from `getShopProductionPartners`) when a partner makes the item; text doesn't replace it | research 10 §3 | [`PARTNER_DISCLOSURE` claims a partner for every shop: false for in-house printers, M-23] |
| Templated designs | Designs must come from the seller; clip-art or template bundles risk removal even with a license | Creativity Standards (tightened 2025-06-10) | not checked |
| Title characters | Disallowed: anything outside `[\p{L}\p{Nd}\p{P}\p{Sm}\p{Zs}™©®]` | research 10 §3 | [only $, ^ and backtick rejected, M-24] |
| Title repeats | Each of `%`, `:`, `&`, `+` at most once | research 10 §3 | [not checked, M-24] |
| Title length | 140 chars max (`CHANNEL_RULES.etsy.listing.titleMax`); guidance about 15 words [U] | contracts `channels.ts` | checked |
| Tags | 13 max, 20 chars each; letters, digits, spaces, `-`, `'`, ™©® | research 10 §3 | [™©® not allowed by `ETSY_TAG_RE`] |
| Materials | Letters, digits and spaces only | research 10 §3 | verify |
| Trademark notice | Connect screen and footer show the Etsy notice (exact text in research 10 §3) | Etsy API Terms | [missing, M-26] |
| IP | Repeat infringement ends the shop | https://www.etsy.com/legal/ip | trademark check |

## Amazon
| Check | Rule | Source |
|---|---|---|
| Synthetic performer | From 2026-07-22, images/video/A+ with photoreal AI-generated people carry XMP `dc:subject` keyword `contains-synthetic-performer` | [3P] https://www.geekseller.com/blog/amazon-introduces-new-rules-for-ai-generated-images-july-2026/ |
| Our mockups | Today no generated people. If imaging ever adds them, imaging writes the tag | research 10 §4; M-25 |
| Handmade | Print-on-demand / made-to-order tees are not allowed in Amazon Handmade | research 03 pain 1 |

## TikTok Shop
| Check | Rule | Source |
|---|---|---|
| AI edits | No AI edits showing fictional functions or exaggerated results (Aug 2026 Policy Pulse) | https://seller-us.tiktok.com/university/essay?knowledge_id=6747273381791534&lang=en |
| Claims | No exaggerated or unprovable claims in title, description or images | same |
| AIGC label | Label AI-generated models or scenes: US requirement [U] | research 10 §6 |

## Walmart
| Check | Rule | Source |
|---|---|---|
| AI content | Truthful, rights-held, seller-reviewed; no labeling mandate | https://marketplacelearn.walmart.com/releasenotes/new-compliance-guidelines-for-ai-generated-content |
| Item spec | Spec 5.x required | research 10 §7 |

## Shopify
The shop's own store: no marketplace listing policy, but truthful-claim and trademark checks still apply.
