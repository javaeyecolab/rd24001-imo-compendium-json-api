param(
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "rd24001-imo-compendium-json-api",

    [Parameter(Mandatory=$false)]
    [ValidateSet("public", "private")]
    [string]$Visibility = "public"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

Require-Command git
Require-Command gh

Write-Host "[1/7] Checking GitHub authentication..."
gh auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

Write-Host "[2/7] Validating JSON samples..."
if (Get-Command python -ErrorAction SilentlyContinue) {
    python .\scripts\validate_samples.py
    if ($LASTEXITCODE -ne 0) { throw "Sample validation failed." }
} else {
    Write-Warning "Python was not found. Skipping local validation; GitHub Actions will validate after push."
}

Write-Host "[3/7] Initializing Git repository..."
if (-not (Test-Path .git)) {
    git init
}
git add .
$changes = git status --porcelain
if ($changes) {
    git commit -m "Publish IMO Compendium JSON sample API"
} else {
    Write-Host "No uncommitted changes."
}
git branch -M main

Write-Host "[4/7] Creating or using GitHub repository..."
$origin = git remote get-url origin 2>$null
if (-not $origin) {
    if ($Visibility -eq "public") {
        gh repo create $RepoName --public --source=. --remote=origin --push
    } else {
        gh repo create $RepoName --private --source=. --remote=origin --push
    }
    if ($LASTEXITCODE -ne 0) { throw "Failed to create/push GitHub repository." }
} else {
    Write-Host "Using existing origin: $origin"
    git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw "git push failed." }
}

Write-Host "[5/7] Resolving repository identity..."
$RepoFullName = gh repo view --json nameWithOwner --jq '.nameWithOwner'
if (-not $RepoFullName) { throw "Could not resolve GitHub repository name." }

Write-Host "[6/7] Configuring GitHub Pages for Actions workflow..."
$null = gh api "repos/$RepoFullName/pages" 2>$null
if ($LASTEXITCODE -eq 0) {
    gh api --method PUT "repos/$RepoFullName/pages" -f build_type=workflow | Out-Null
} else {
    gh api --method POST "repos/$RepoFullName/pages" -f build_type=workflow | Out-Null
}
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not configure Pages automatically. In GitHub: Settings > Pages > Source > GitHub Actions."
}

Write-Host "[7/7] Triggering Pages workflow..."
gh workflow run pages.yml --repo $RepoFullName
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Workflow may already have been triggered by the push. Check the Actions tab."
}

$Owner = $RepoFullName.Split('/')[0]
$Repo = $RepoFullName.Split('/')[1]
$Base = "https://$Owner.github.io/$Repo/api/v1"

Write-Host ""
Write-Host "Repository: https://github.com/$RepoFullName"
Write-Host "Expected API base after Pages deployment: $Base"
Write-Host "Ships index: $Base/ships/index.json"
Write-Host "Datasets index: $Base/datasets/index.json"
