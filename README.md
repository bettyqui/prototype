# BIM Prototype 02 Quarto Website

This project is configured as a Quarto website and ready for deployment to GitHub Pages using GitHub Actions.

## Site structure

- `index.qmd`: Homepage.
- `project-log.qmd`: Implementation log.
- `wikidata.qmd`: Wikidata notes and references.
- `wikidata-item.ipynb`: Notebook-backed profile page rendered by Quarto.
- `wikidata_profile.py`: Shared Python helper logic used by the notebook page.
- `_quarto.yml`: Quarto project and navigation configuration.

## Local development

```powershell
quarto preview
```

To render once:

```powershell
quarto render
```

## Update the Wikidata item page

1. Open `wikidata-item.ipynb`.
2. In Cell 3, change `item_id` to the target Wikidata Q-id.
3. Run the notebook cells (or run `quarto render`).
4. Confirm output in `docs/wikidata-item.html`.

The notebook runs a SPARQL query against the Wikidata Query Service, then renders a styled HTML profile with statement cards and summary charts.

## Publish to GitHub Pages

1. Create a GitHub repository and push this folder to the `main` branch.
2. In GitHub, open Settings -> Pages.
3. Under Build and deployment, set Source to **GitHub Actions**.
4. Push changes to `main`.
5. The workflow at `.github/workflows/publish.yml` builds and deploys the `docs` folder.

## Troubleshooting

- If the notebook fetch fails from Wikidata, re-run `quarto render` after a short delay (the service can rate limit).
- If notebook imports fail after code changes in `wikidata_profile.py`, restart the kernel and run notebook cells again.

## First-time git setup (if needed)

```powershell
git init
git add .
git commit -m "Initialize Quarto website project"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```
