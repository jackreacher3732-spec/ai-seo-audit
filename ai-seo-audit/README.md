# AI SEO Audit MVP

## Run locally
1. Install Python 3.9+.
2. Open a terminal in this folder.
3. Run: `python server.py`
4. Open `index.html` in your browser.
5. Enter a public website URL and run the audit.

The API crawls the requested homepage and checks HTTPS, title, meta description, H1/H2, image alt text, canonical, robots.txt, sitemap.xml and internal links.

## Next production steps
- Move API behind HTTPS and a backend domain.
- Add SSRF protection, rate limits, robots compliance and crawl budgets.
- Add PageSpeed Insights / Core Web Vitals.
- Add OpenAI-powered explanations and fixes.
- Persist audits and users in PostgreSQL.
- Add authentication, billing and PDF reports.
