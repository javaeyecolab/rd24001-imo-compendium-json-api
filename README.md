# RD24001 IMO Compendium JSON Sample API

IMO Compendium **FAL.5/Circ.56 (FAL 50, 2026)**의 선박 입출항/FAL·MSW 관련 12개 데이터셋을 대상으로 만든 **합성(synthetic) JSON 샘플 저장소**입니다.

- 데이터셋: 12개
- 시험선: 10척
- 원본 샘플: 120개 JSON
- 조회 방식: 선박 IMO 번호 기준 / 데이터셋 기준
- 게시 방식: GitHub Pages 정적 JSON GET API
- JSON 표현: UN/CEFACT JSON Schema NDR의 방향(일관된 lowerCamelCase, CCTS형 값+메타데이터 표현)을 참고한 **RD24001 구현 프로파일**

> 중요: 이 저장소의 JSON 구조는 IMO가 발행한 공식 normative JSON syntax가 아닙니다. IMO Compendium의 데이터셋과 확인 가능한 데이터 요소를 바탕으로 API 실증을 위해 구성한 예제 프로파일입니다. 모든 선박·인명·연락처·화물 값은 가상 데이터입니다.

## 1. 데이터셋

| 코드 | 데이터셋 | 샘플 수 |
|---|---|---:|
| `FAL1` | General Declaration | 10 |
| `FAL2` | Cargo Declaration | 10 |
| `FAL3` | Ship's Stores Declaration | 10 |
| `FAL4` | Crew's Effects Declaration | 10 |
| `FAL5` | Crew List | 10 |
| `FAL6` | Passenger List | 10 |
| `FAL7` | Dangerous Goods Manifest | 10 |
| `MAIL` | Delivery Bill for Mail Consignment | 10 |
| `MDH` | Maritime Declaration of Health | 10 |
| `SSC` | Ship Sanitation Certificate | 10 |
| `SEC` | Security Report | 10 |
| `WASTE` | Advance Notification for Waste Delivery | 10 |

## 2. 디렉터리

```text
samples/datasets/<dataset-slug>/<IMO>.json      # 데이터셋별 10개 원본 샘플
docs/api/v1/ships/<IMO>/<dataset-slug>.json    # 선박 중심 API
docs/api/v1/datasets/<dataset-slug>/<IMO>.json # 데이터셋 중심 API
docs/schemas/                                  # JSON Schema 예제
docs/openapi.yaml                              # 정적 GET API 설명
```

## 3. GitHub 업로드 및 Pages API 게시

이 저장소에는 `.github/workflows/pages.yml`이 포함되어 있어 `main` 브랜치에 push될 때:

1. `scripts/validate_samples.py`로 120개 샘플을 검증하고
2. `docs/` 폴더를 GitHub Pages artifact로 업로드한 뒤
3. GitHub Pages에 정적 JSON API를 배포합니다.

GitHub 저장소의 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 설정합니다.

Pages 주소가 `https://<USER>.github.io/<REPO>/`라면 API base URL은 다음과 같습니다.

```text
https://<USER>.github.io/<REPO>/api/v1
```

Windows에서 GitHub CLI(`gh`)가 설치되고 로그인되어 있다면 저장소 루트에서 다음 스크립트로 repository 생성/업로드/Pages 설정을 한 번에 수행할 수 있습니다.

```powershell
.\scripts\publish_to_github.ps1 -RepoName rd24001-imo-compendium-json-api -Visibility public
```

> GitHub Pages는 Python/FastAPI 서버를 실행하는 서비스가 아니므로 이 저장소의 API는 **read-only 정적 GET API**입니다. POST/검색/DB 연계가 필요하면 동일 JSON을 FastAPI 등의 런타임에 배포해야 합니다.

## 4. API 예시

전체 시험선:

```text
GET /api/v1/ships/index.json
```

특정 선박의 보고서 목록:

```text
GET /api/v1/ships/9300013/index.json
```

특정 선박의 Cargo Declaration:

```text
GET /api/v1/ships/9300013/fal2-cargo-declaration.json
```

Cargo Declaration 데이터셋의 10척 목록:

```text
GET /api/v1/datasets/fal2-cargo-declaration/index.json
```

Cargo Declaration에서 한 선박 조회:

```text
GET /api/v1/datasets/fal2-cargo-declaration/9300013.json
```

PowerShell 호출 예:

```powershell
$base = "https://<USER>.github.io/<REPO>/api/v1"
Invoke-RestMethod "$base/ships/index.json"
Invoke-RestMethod "$base/ships/9300013/fal1-general-declaration.json"
```

## 5. GitHub CLI 수동 업로드

자동 게시 스크립트를 사용하지 않는 경우 다음과 같이 직접 업로드할 수 있습니다.

```powershell
git init
git add .
git commit -m "Initial IMO Compendium JSON sample API"
git branch -M main
gh repo create rd24001-imo-compendium-json-api --public --source=. --remote=origin --push
```

업로드 후 **Settings → Pages → Source → GitHub Actions**를 선택합니다. 포함된 Pages workflow를 수동 실행하거나 `main`에 다시 push하면 배포됩니다.

## 6. 검증

```powershell
python .\scripts\validate_samples.py
```

검증 항목은 12개 데이터셋 각각 10개 파일 존재 여부, 동일 10개 IMO 번호 사용 여부, IMO 체크디지트, 공통 필드 및 `syntheticSample=true` 여부입니다.

## 7. 적용성 주의

12개 데이터셋이 한 항차에서 모두 항상 제출되는 것은 아닙니다. Passenger List, Dangerous Goods Manifest, Mail Consignment 등은 선박·화물·운항 상황에 따라 적용 여부가 달라집니다. 이 저장소는 API와 데이터 모델 실증을 위해 각 데이터셋에 10개 예시를 의도적으로 제공합니다.
