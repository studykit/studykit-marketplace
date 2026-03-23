---
topic: "co-think-story/spec 산출물 관리 방법"
date: 2026-03-23
---
# Brainstorming: co-think-story/spec 산출물 관리 방법

## Context
co-think-story와 co-think-spec 스킬이 생성하는 마크다운 산출물(Job Stories, Functional Specs)이 늘어나면서, 이를 체계적으로 관리할 방법이 필요해졌다. 주요 요구사항: 파일이 story용인지 spec용인지 구분, Story→Spec→Dev 워크플로우 추적, 중복/유사/상충 story·spec 탐지, 키워드 검색, 상태 조회. 혼자 사용하는 환경.

## Discussion Journey

1. **GitHub Issues 연동에서 출발**: SCAMPER 기법으로 탐색. Label(`type:story`, `type:spec`)로 구분, sub-issues로 계층 표현, frontmatter→Issue 메타데이터 매핑 등 아이디어 도출.

2. **GitHub Issues의 한계 인식**: 의미적 검색 불가, 관계 표현이 약함, 구조화된 데이터 관리 제한적. 특히 중복/상충 탐지는 단순 텍스트 검색으로 불가능.

3. **GitHub + 로컬 AI 레이어 (4번 방향 선택)**: 혼자 쓰므로 외부 도구 없이 GitHub Issue 원본 + 로컬에서 `gh` CLI로 전체 Issue 가져와 AI 분석하는 방식 선택.

4. **Notion 연동 조사**: GitHub Issues↔Notion 연동 가능성 조사. 공식 연동은 읽기전용·Label 미지원. 양방향 동기화는 Unito(유료) 또는 커스텀 개발만 가능. MCP 조합(Notion MCP + GitHub MCP)으로 온디맨드 동기화는 가능하나 자동화 아님.

5. **Atlassian 스택 검토 (Jira + Confluence + Bitbucket)**: 이슈 계층, JQL 검색, Confluence 연동이 강력. 공식 Atlassian MCP 서버 존재. 그러나 솔로 개발자에겐 과하다는 판단. GitHub↔Jira 연동은 공식 플러그인("GitHub for Atlassian")으로 개발 활동 추적만 가능, Issues 양방향 동기화는 불가.

6. **로컬 마크다운으로 회귀**: 외부 도구 없이 현재 구조로도 충분한지 재검토. 칸반 뷰가 불필요하고 혼자 쓰는 환경이라 로컬 마크다운이 가장 가볍고 적합.

7. **파일 관리 문제 제기 → Obsidian 도입**: 파일이 많아졌을 때 관리 방법이 핵심 과제. Obsidian + Dataview/DataviewJS + Projects + Tasks 조합으로 해결 가능. 기존 git repo를 vault로 열면 마이그레이션 제로.

8. **Excalidraw + ExcaliBrain 추가 검토**: 정적 다이어그램(Excalidraw)과 동적 관계 탐색(ExcaliBrain)을 추가하면 Story↔Spec 관계를 시각적으로 탐색하고, 상태별 색상 구분, 고아 노트 탐지가 가능. 둘 다 Dataview 위에서 동작하므로 기존 스택과 자연스럽게 결합.

## Ideas

### Theme: Architecture Decision
- **로컬 마크다운 + Obsidian이 최적 조합**: 혼자 쓰는 환경에서 외부 서비스(Jira, Notion) 없이 기존 마크다운 파일 + Obsidian 뷰 레이어로 모든 요구사항 커버. 셋업 비용 최소.
- **GitHub Issues는 사용 안 함**: 프로젝트 관리는 로컬 마크다운 + Obsidian이 담당. GitHub은 코드 + PR 전용.

### Theme: Frontmatter Design
- **wikilink 기반 관계 표현**: Story frontmatter에 `spec: "[[path]]"`, Spec에 `stories: ["[[path]]"]`로 양방향 링크. Obsidian 그래프 뷰에서 시각적으로 관계 확인.
- **status 필드로 워크플로우 추적**: `draft → review → final` 상태를 frontmatter에서 관리. Obsidian Projects에서 칸반 뷰로 드래그.
- **topic 필드로 그룹핑**: 같은 topic의 story/spec을 Dataview 쿼리로 묶어서 조회.

### Theme: Obsidian Plugin Stack
- **Dataview/DataviewJS**: 대시보드 쿼리, 상태별 카운트, Spec 없는 Story 탐지, topic별 중복 분석.
- **Obsidian Projects**: frontmatter의 status 필드 기반 칸반 보드. 드래그로 상태 변경 시 frontmatter 자동 업데이트.
- **Obsidian Tasks**: Story/Spec 내부의 할 일 항목 추적. vault 전체에서 미완료 태스크 조회.
- **Excalidraw**: `.excalidraw.md` 형식으로 git diff 가능. 그림 안에 `[[wikilink]]` 사용 가능. ExcalidrawAutomate API로 Dataview와 결합하여 Story/Spec 관계도 자동 생성 가능. 플로우차트, 아키텍처 다이어그램, 와이어프레임 지원.
- **ExcaliBrain**: Excalidraw + Dataview 위에서 동작하는 인터랙티브 관계 그래프. frontmatter 필드(`spec`, `stories`)를 Parent/Child로 매핑하여 Story↔Spec 관계를 계층적으로 시각화. `status` 필드 기반 노드 색상 구분(draft=노랑, review=파랑, final=초록). Spec 링크 없는 Story를 자식 없는 노드로 자동 탐지. 클릭으로 노트 간 탐색.
- **Hover Editor** (선택): ExcaliBrain 노드 위에 마우스 올리면 노트 미리보기 팝업.
- **Obsidian Claude Code MCP**: Claude Code에서 vault 파일 직접 읽기/쓰기. co-think 스킬이 파일 생성하면 Obsidian이 자동 감지.

### Theme: Search & Analysis
- **Dataview DQL로 구조화 검색**: `FROM "A4/story" WHERE status = "final"` 같은 필드 기반 필터링.
- **DataviewJS로 중복/상충 탐지**: 같은 topic에 Story가 2개 이상이면 경고, Spec 없는 Story 자동 발견.
- **Claude Code에게 의미적 분석 요청**: 단순 텍스트 매칭을 넘어선 상충/중복 분석은 Claude Code가 전체 파일을 읽고 AI로 판단.

### Theme: Rejected Alternatives
- **GitHub Issues**: 의미적 검색 불가, 관계 표현 약함, 구조화 데이터 관리 제한적.
- **Notion + GitHub**: 양방향 동기화가 어렵고(Unito 유료 또는 커스텀 개발), 혼자 쓰기엔 오버헤드.
- **Atlassian (Jira + Confluence + Bitbucket)**: 강력하지만 솔로 개발자에겐 과함. 학습 곡선, 셋업 비용.
- **GitHub + 로컬 AI 레이어**: 실현 가능하나 Obsidian이 시각적 뷰까지 제공하므로 더 나은 대안 존재.

## Research Findings

### Notion ↔ GitHub Issues 연동
- Notion 네이티브 연동: 읽기전용, Label 미지원
- Unito: 유일한 진짜 양방향 동기화 도구 (~$19/mo~)
- MCP 조합 (Notion MCP + GitHub MCP): 온디맨드 가능, 자동화 아님

### Atlassian 스택
- 무료 플랜: Jira 10명, Confluence 10명, Bitbucket 5명
- 공식 Atlassian MCP 서버 존재 (`atlassian/atlassian-mcp-server`)
- GitHub↔Jira: "GitHub for Atlassian" 무료 플러그인 (개발 활동 추적만, Issues 동기화 안 됨)
- 양방향 Issues 동기화: Exalate(무료 앱, 라이선스 별도) 또는 Unito(유료)

### Obsidian 연동
- 기존 git repo를 vault로 바로 열 수 있음
- Obsidian Claude Code MCP 서버 존재 (`obsidian-claude-code-mcp`)
- `.obsidian/workspace.json`만 .gitignore에 추가하면 git 공존 가능

### Excalidraw (Obsidian 플러그인)
- `.excalidraw.md` 형식: 마크다운 래퍼 + LZ-String 압축 JSON (256자 줄바꿈으로 git diff 가능)
- 그림 안에 `[[wikilink]]` → 백링크에 잡히고 클릭 이동 가능
- 다른 노트에 `![[diagram.excalidraw]]`로 임베딩
- ExcalidrawAutomate API: JavaScript로 도형/화살표 프로그래밍. Dataview API와 결합하여 frontmatter에서 Story/Spec 관계도 자동 생성 가능
- 50+ 공식 스크립트 라이브러리 (슬라이드쇼, PDF 내보내기, 색상 조작 등)
- Mermaid 다이어그램 임포트 지원

### ExcaliBrain
- Excalidraw + Dataview 위에서 동작하는 인터랙티브 관계 그래프
- 내장 그래프 뷰와의 차이: 한 노트 중심 포커스, 계층 표현(부모 위/자식 아래), frontmatter 읽기, 태그 기반 노드 스타일링
- 관계 타입 5가지: Parents(위), Children(아래), Left Friends, Right Friends, Siblings
- frontmatter 필드를 관계 타입에 매핑 가능: `spec` → Children, `stories` → Parents
- Primary Tag Field로 `status` 설정 시 노드 색상 자동 구분
- Virtual Node로 미존재 링크(깨진 참조) 시각적 표시
- 클릭으로 노트 간 탐색, 브라우저식 뒤로/앞으로 히스토리
- 설치 순서: Dataview → Excalidraw → ExcaliBrain → (선택) Hover Editor

## TODOs
- [ ] co-think-story/spec의 frontmatter에 `spec`, `stories`, `topic` 필드 추가 반영
- [ ] Obsidian vault로 프로젝트 열기 + Dataview, Projects, Tasks 플러그인 설치
- [ ] Excalidraw, ExcaliBrain, Hover Editor 플러그인 설치
- [ ] ExcaliBrain Ontology 설정: `spec` → Children, `stories` → Parents, Primary Tag Field → `status`
- [ ] 대시보드 노트 작성 (DataviewJS 쿼리 + Excalidraw 다이어그램 임베딩)
- [ ] Obsidian Claude Code MCP 설정
- [ ] co-think-story/spec 스킬에서 파일 생성 시 새 frontmatter 스키마 적용
- [ ] ExcalidrawAutomate 스크립트: Story/Spec frontmatter에서 관계도 자동 생성
