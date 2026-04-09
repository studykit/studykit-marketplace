---
type: brainstorm
pipeline: spark
topic: "co-think artifact feedback & revision history management"
date: 2026-03-28
status: draft
tags: []
---
# Brainstorming: co-think artifact feedback & revision history management

## Context

co-think pipeline은 story -> requirement -> domain -> architecture 순서로 산출물을 생성하지만, 사람의 사고는 단방향이 아니다. 각 단계에서 이전 단계의 산출물에 문제를 발견하거나 새로운 요구사항이 생기는 경우가 빈번하다. 현재는 domain -> requirement (Spec Feedback TODO + co-revise-requirement-with-domain)만 유일한 역방향 피드백 경로이고, revision history도 관리되지 않아 "왜 바뀌었는지" 추적이 불가능하다.

## Discussion Journey

1. **Revision history 부족 문제부터 논의 시작** — 산출물이 Write tool로 매번 전체 덮어쓰기되어 변경 맥락이 사라지는 문제 인식
2. **3가지 방안 검토**: (A) 파일 내 changelog 섹션, (B) frontmatter revision metadata, (C) 별도 changelog 파일 → B+C 조합 채택
3. **산출물별 변경 단위 차이 인식** — story/requirement는 개별 항목 단위로 변경되는데 파일은 전체 묶음 단위라 granularity 불일치 → story/requirement는 Git Issue, domain/architecture는 changelog로 이원화 결정
4. **Label 체계 논의** — 처음에 3축(artifact/from/change) 상세 label 제안했으나, issue body와 comment로 충분하므로 산출물 종류만 구분하는 최소 label로 축소
5. **domain/architecture도 issue로 통일** — changelog 파일 대신 모든 산출물의 변경 이력을 Git Issue로 일원화. 단, domain/architecture는 로컬에 최신 파일 유지 필요
6. **frontmatter `issues` 필드 제거** — 본문에서 수정된 부분 옆에 issue 링크를 직접 기록하면 되므로 불필요
7. **역방향 피드백 경로 일반화** — 6개 역방향 경로를 개별 메커니즘이 아닌 하나의 통일된 흐름(issue + co-revise)으로 처리
8. **downstream 전파** — co-revise 수정 완료 후 downstream 영향 분석 → downstream issue 자동 생성(사용자 승인 후) → 연쇄 co-revise

## Ideas

### Theme: 변경 이력 관리
- **Git Issue 기반 통일 관리**: 모든 산출물(story, requirement, domain, architecture)의 변경 이력을 Git Issue로 일원화. 산출물 본문에 관련 issue 링크를 직접 기록하여 맥락 유지
- **최소 Label 체계**: `story`, `requirement`, `domain`, `architecture` 4개 label만 사용. 변경 유형이나 피드백 출처는 issue body/comment/issue 간 링크로 관리
- **frontmatter revision 필드**: `revision`, `last_revised` 두 필드만 추가. issue 목록은 본문에서 관리

### Theme: 역방향 피드백 메커니즘
- **co-revise 일반화**: 현재 co-revise-requirement-with-domain을 범용 co-revise 스킬로 일반화. Issue를 입력으로 받아 label과 내용을 보고 대상 산출물을 판단하여 수정
- **6개 역방향 경로 통일**: requirement->story, domain->requirement, domain->story, architecture->requirement, architecture->domain, architecture->story 모두 동일한 흐름(issue 생성 -> co-revise)으로 처리

### Theme: Downstream 전파
- **영향 분석 + 연쇄 issue 생성**: co-revise가 산출물 수정 완료 후 downstream 영향 분석 수행. 영향이 있으면 downstream issue를 자동 생성(사용자 승인 후). upstream issue에서 downstream issue로 링크 연결
- **연쇄 co-revise 흐름**: 생성된 downstream issue를 다시 co-revise로 처리하는 반복 흐름. 변경이 전체 pipeline을 통해 전파됨

### Theme: 로컬 산출물 파일
- **4개 산출물 모두 최신 파일 유지**: story, requirement, domain, architecture 모두 로컬에 최신 상태 파일 유지. co-revise 수정 시 로컬 파일도 함께 업데이트

## TODOs
- [x] co-revise 범용 스킬 설계 — issue 입력 기반 워크플로우 정의 ✅ 2026-03-28
- [x] downstream 영향 분석 로직 설계 — 어떤 변경이 어떤 downstream에 영향을 주는지 판단 기준 ✅ 2026-03-28
- [x] 기존 co-revise-requirement-with-domain을 범용 co-revise로 대체하는 마이그레이션 계획 ✅ 2026-03-28
- [x] 각 co-think 스킬에서 역방향 피드백 발견 시 issue 생성 흐름 추가 ✅ 2026-03-28
