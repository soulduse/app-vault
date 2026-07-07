# App Vault

**모든 앱의 스토어 등록정보를 한 곳에.** 앱 이름, 패키지명, 로케일별 설명,
아이콘, 피처 그래픽, 스크린샷, 정책 URL을 Obsidian 호환 마크다운 vault에 축적하고,
의존성 없는 정적 카탈로그 뷰어로 조회합니다. Claude Code 스킬을 붙이면 수집·생성까지
자동화됩니다.

[English README](README.md)

![카탈로그 그리드](docs/screenshots/grid.png)

앱을 여러 개 운영하다 보면 스토어 자산이 리포마다 흩어집니다 — 어떤 앱은
`docs/store/`, 어떤 앱은 `branding/`, 어떤 설명은 Play Console 안에만 존재하죠.
App Vault는 이것들에게 하나의 집을 줍니다:

- **순수 마크다운 + 이미지** — Obsidian(또는 아무 에디터)에서 읽고 편집, grep 가능, git 친화적
- **오프라인 조회** — 서버 없는 self-contained HTML 한 장
- **자동화 가능** — Claude Code 스킬이 프로젝트를 스캔해 알아서 채워줌

## 빠른 시작

```bash
git clone https://github.com/soulduse/app-vault.git
cd app-vault
python3 scripts/build.py --vault examples/vault --lang ko --open
```

동봉된 데모 vault(가상 앱 2종)를 빌드해 브라우저로 엽니다. Python 3 외에
의존성이 없고, 뷰어는 `file://`로 바로 열리는 정적 HTML 하나입니다.

## 뷰어 기능

![상세 화면](docs/screenshots/detail.png)

- **검색·필터** — 이름/패키지/설명/태그/등록정보 전문 검색 (`/` 키로 포커스)
- **Play 등록정보 탭** — 로케일별(en/ja/ko/…) 앱 이름·간단한 설명·자세한 설명,
  필드마다 **복사 버튼** + Play 글자수 한도 **실시간 카운터** (30/80/4000, 초과 시 빨강)
- **패키지명 복사** — 클릭 한 번으로 콘솔 폼에 붙여넣기
- **자산 다운로드** — 아이콘·피처 그래픽·스크린샷 개별/일괄, 앱 슬러그 프리픽스로 리네임
- **누락 자산 추적** — 카드에 `그래픽 ✗` 뱃지, 빈 슬롯엔 placeholder + *생성 요청* 버튼

## Vault 형식

앱당 폴더 하나. 데이터는 `app.md`(frontmatter + 섹션)와 관례 경로로 자동 발견되는
`assets/` 폴더에 들어갑니다. 구체적인 형식은 [English README](README.md#vault-format)와
[`examples/vault/`](examples/vault/)의 완성 예시 2종을 참고하세요.

```bash
python3 scripts/build.py --vault ~/my-vault/apps --lang ko   # 내 vault 빌드 (한국어 UI)
```

## Claude Code 스킬 (선택)

뷰어·빌더는 단독으로 동작합니다. [Claude Code](https://claude.com/claude-code)를
쓴다면 동봉된 스킬로 파이프라인을 자동화할 수 있습니다:

```bash
mkdir -p ~/.claude/skills/app-vault
cp skill/SKILL.md ~/.claude/skills/app-vault/
cp -r scripts ~/.claude/skills/app-vault/
# 환경변수 APP_VAULT_DIR 설정 또는 SKILL.md 안의 경로 수정
```

- **`/app-vault` (save)** — 현재 프로젝트의 스택(Flutter/네이티브 Android/Capacitor/RN)을
  탐지해 패키지명·버전·스토어 문구·정책 URL·그래픽 자산을 수집하고, **diff-first**로
  `app.md`를 갱신한 뒤 리빌드합니다. 등록정보는 기본 3로케일로 생성(번역 초안 표기).
- **`/app-vault generate <slug> <asset>`** — 역호출 루프. 뷰어의 빈 슬롯에서
  *⚡ 생성 요청 복사* → Claude Code에 붙여넣으면 누락된 아이콘(이미지 생성),
  피처 그래픽(넓은 비율 생성 후 1024×500 크롭), 스크린샷(에뮬레이터 adb 또는
  headless Chrome)을 만들어 vault에 저장하고 리빌드합니다.
- **`list` / `show` / `delete` / `open`** — 카탈로그 관리.

스킬 파일에는 실전에서 겪은 함정들이 기록되어 있습니다 — Play 30/80/4000자 한도,
프롬프트에 "icon"을 넣으면 아이콘 안에 아이콘을 또 그리는 이미지 모델, 2:1 비율을
지원하지 않는 모델 등.

## 라이선스

[MIT](LICENSE)
