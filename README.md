# JobMatch — Plateforme de matching CV ↔ offres d'emploi

Dépose ton CV, le système l'analyse et recherche automatiquement les offres d'emploi les plus pertinentes à partir de sources d'offres d'emploi (APIs officielles).

---

## Stack technique

| Composant | Choix | Pourquoi |
|---|---|---|
| Backend API | **FastAPI** (Python 3.12) | async natif, typage Pydantic, doc OpenAPI auto-générée, écosystème scraping/OCR en Python |
| Frontend | **Next.js 14** (TypeScript, App Router) | SSR pour le SEO de la page d'accueil, bon écosystème UI |
| Base de données | **PostgreSQL** | relationnel adapté (users, CV, offres, matches), support JSONB pour données semi-structurées |
| Queue asynchrone | **Redis + Celery** (ou RQ, plus simple) | scraping/appels API et parsing CV sont longs → doivent être des jobs en arrière-plan |
| Extraction CV | **pdfplumber / python-docx** + **Tesseract OCR** (fallback si CV scanné en image) | pas besoin de LLM pour extraire texte structuré d'un PDF/Word standard |
| Matching | **rank-bm25** ou **scikit-learn TF-IDF + cosine similarity**, boosté par extraction de mots-clés via **spaCy** (NER + POS tagging) | pas de coût API, résultats corrects pour du matching lexical/sémantique léger |
| Sources d'offres | **httpx** (clients HTTP vers APIs officielles) | intégration de providers d'offres d'emploi via API |
| Stockage fichiers | **S3-compatible** (MinIO en local/self-hosted, S3 en prod) | stocker les CV uploadés |
| Auth | **JWT** (fastapi-users ou implémentation maison) | simple, stateless |
| Déploiement | **Docker + docker-compose** (dev), Kubernetes ou simple VPS (prod) | reproductible |
| Monitoring | **Prometheus + Grafana** (optionnel v2) | suivre les taux de succès/échec des providers |

---

## Architecture générale

```
                    ┌─────────────┐
                    │   Next.js   │  (upload CV, dashboard résultats)
                    │  (Frontend) │
                    └──────┬──────┘
                           │ REST/JSON
                    ┌──────▼──────┐
                    │   FastAPI   │  (auth, endpoints CRUD, orchestration)
                    │  (Backend)  │
                    └──┬───────┬──┘
                       │       │
          ┌────────────▼─┐   ┌▼─────────────────┐
          │  PostgreSQL   │   │   Redis (broker)  │
          │ (users, cv,   │   └────────┬──────────┘
          │  offres, match)│            │
          └───────────────┘   ┌─────────▼─────────┐
                               │  Celery Workers    │
                               ├────────────────────┤
                               │ 1. CV Parser Worker │ → extrait texte + structure du CV
                               │ 2. Provider Workers  │ → un worker par source d'offres
                               │    (API officielle) │
                               │ 3. Matching Worker   │ → calcule le score CV ↔ offre
                               └────────────────────┘
                                        │
                               ┌────────▼─────────┐
                               │  MinIO / S3       │ (fichiers CV bruts)
                               └────────────────────┘
```

---

## Modules techniques

### Module 1 — CV Parser
Transforme un CV (PDF/DOCX/image scannée) en JSON structuré.

- PDF texte → `pdfplumber`
- PDF scanné/image → `pytesseract` (OCR)
- DOCX → `python-docx`
- Extraction structurée via règles + regex + spaCy NER : compétences (matchées contre un référentiel type ESCO/O*NET), expériences, formations, langues

Format de sortie :
```json
{
  "skills": ["Python", "React", "Docker"],
  "titles": ["Développeur Full Stack", "Ingénieur logiciel"],
  "years_experience": 4,
  "languages": ["français", "anglais"],
  "raw_text": "..."
}
```

### Module 2 — Job Providers
Interface commune pour interroger différentes sources d'offres via leurs APIs officielles.

```python
class JobProvider(ABC):
    @abstractmethod
    async def search(self, keywords: list[str], location: str | None) -> list[JobOffer]:
        ...
```

Chaque provider retourne un format normalisé `JobOffer` (titre, entreprise, description, lieu, url, date_publication, source).

### Module 3 — Matching Engine
Score chaque offre par rapport au CV, sans LLM.

- Vectorisation CV et offres avec **TF-IDF** ou **BM25** sur les textes nettoyés (skills + titres + description), puis cosine similarity
- Boost de score si overlap direct sur compétences extraites (Module 1) et titre de poste
- Filtre optionnel par localisation / séniorité (regex sur "junior/senior/X ans d'expérience")
- Sortie : liste d'offres triées avec score 0-100 et justification simple ("matché sur : Python, Docker, 3 ans exp")

### Module 4 — API Backend (FastAPI)
Endpoints principaux :
```
POST   /api/cv/upload          → upload + déclenche parsing async
GET    /api/cv/{id}/status     → statut parsing (pending/done/error)
GET    /api/cv/{id}/profile    → JSON structuré extrait
POST   /api/search              → déclenche recherche multi-provider
GET    /api/search/{id}/results → offres triées par score
GET    /api/offers/{id}         → détail d'une offre
POST   /api/auth/register|login
```

### Module 5 — Frontend (Next.js)
- Page upload CV (drag & drop, preview extraction)
- Dashboard résultats (liste d'offres, filtres, score de match visible)
- Page profil (CV structuré éditable manuellement pour corriger l'extraction)

---

## Modèle de données (simplifié)

```
users(id, email, password_hash, created_at)
cvs(id, user_id, file_url, parsed_json, status, created_at)
job_offers(id, source, external_id, title, company, description, location, url, posted_at, scraped_at)
matches(id, cv_id, job_offer_id, score, matched_keywords, created_at)
```

---

## Variables d'environnement clés

```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
S3_ENDPOINT / S3_BUCKET / S3_KEY / S3_SECRET
FRANCE_TRAVAIL_CLIENT_ID / FRANCE_TRAVAIL_CLIENT_SECRET
ADZUNA_APP_ID / ADZUNA_APP_KEY
JWT_SECRET
```
