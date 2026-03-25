---
topic: "co-think 산출물 관리 체계"
date: 2026-03-23
source:
  - "[[2026-03-23-story-requirement-management]]"
---
# co-think 산출물 관리 체계

## Decisions

### 관리 방법: 로컬 마크다운 + Obsidian
- 외부 서비스(Jira, Notion, GitHub Issues) 없이 기존 마크다운 파일 유지
- Obsidian을 뷰 레이어로 사용 (기존 git repo를 vault로 열기)
- 이유: 혼자 쓰는 환경, 셋업 비용 최소, 마이그레이션 제로

### Frontmatter 스키마

**diverse** (brainstorming — 시작점)
```yaml
---
topic: "<topic>"
date: <YYYY-MM-DD>
---
```
- status 없음, source 없음

**story** (Job Stories)
```yaml
---
topic: "<topic>"
date: <YYYY-MM-DD>
source:
  - "[[<diverse-file-name>]]"
---
```
- source: diverse 파일 wikilink 배열 (없으면 생략)
- 개별 story에 `[status:: draft|final]` inline field

**requirement** (Functional Requirement)
```yaml
---
topic: "<topic>"
date: <YYYY-MM-DD>
source:
  - "[[<story-file-name>]]"
type: <ui | non-ui | mixed>
---
```
- source: story 파일 wikilink 배열
- 개별 FR에 `[status:: draft|final]` inline field
- 개별 FR에 `[story:: [[file]]#heading]` inline field (복수 가능)

### 공통 규칙
- 관계 방향: `source`로 상위 출처 참조, 역방향은 Obsidian 백링크
- 링크 형식: 파일명만 쓰는 wikilink `[[파일명]]`
- 항목 간 링크: `[[파일명]]#헤딩`으로 특정 항목 참조
- status: 파일 레벨이 아닌 개별 항목 레벨 (Dataview inline field)

### Obsidian Plugin Stack
- Dataview/DataviewJS: 대시보드 쿼리, 상태별 카운트, 중복 분석
- Obsidian Projects: status 기반 칸반 보드
- Obsidian Tasks: vault 전체 미완료 태스크 조회
- Excalidraw: 다이어그램, 와이어프레임 (.excalidraw.md로 git diff 가능)
- ExcaliBrain: frontmatter 기반 인터랙티브 관계 그래프
- Hover Editor (선택): 노드 위 노트 미리보기

## Progress

- [x] 관리 방법 결정 (2026-03-23)
- [x] Frontmatter 스키마 확정 (2026-03-24)
- [x] co-think-story SKILL.md 반영 (2026-03-24)
- [x] co-think-requirement SKILL.md 반영 (2026-03-24)
- [ ] Obsidian vault 열기 + 플러그인 설치 (Dataview, Projects, Tasks)
- [ ] Excalidraw, ExcaliBrain, Hover Editor 설치
- [ ] ExcaliBrain Ontology 설정
- [ ] 대시보드 노트 작성 (DataviewJS 쿼리)
- [ ] Obsidian Claude Code MCP 설정
- [ ] ExcalidrawAutomate 스크립트: 관계도 자동 생성

## Re-discussion Needed

### ExcaliBrain Ontology 매핑
기존 논의에서는 `requirement` → Children, `stories` → Parents로 매핑했으나, 스키마가 변경되어 재설계 필요:
- `source` frontmatter field → Parent 관계 (diverse→story, story→requirement)
- `story` inline field → FR이 참조하는 story 항목 링크
- ExcaliBrain이 inline field(`[story::]`)를 관계로 인식할 수 있는지 확인 필요
