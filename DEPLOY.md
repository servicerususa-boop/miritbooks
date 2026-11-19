# Deploy miritbooks.com (GitHub Pages, free)

## 1. Push the site
Create a GitHub repo `miritbooks` (public). From inside the unzipped `site/` folder:
    git init && git add -A && git commit -m "Miritbooks.com launch"
    git branch -M main && git remote add origin https://github.com/<YOU>/miritbooks.git && git push -u origin main
Repo Settings > Pages > Source: Deploy from branch `main` / root. Custom domain: miritbooks.com (the CNAME file is already included). Tick "Enforce HTTPS" once available.

## 2. DNS at Hostinger (Domains > miritbooks.com > DNS / Nameservers)
Delete any default parking A/AAAA/CNAME records for @ and www, then add:
    A      @    185.199.108.153
    A      @    185.199.109.153
    A      @    185.199.110.153
    A      @    185.199.111.153
    CNAME  www  <YOU>.github.io
Propagation: minutes to a few hours.

## 3. After it is live
- Add real covers: put `bat-cover.jpg` and `102-likes-cover.jpg` (about 500x720) in site/assets/img/, run `python3 src/build.py`, push.
- Google Search Console: add the domain, submit https://miritbooks.com/sitemap.xml.
- Bing Webmaster Tools: import from Search Console.
- Google Business Profile / social profiles: link to miritbooks.com.

## 4. Confirm with Mirit before launch
- PayBox link amounts: Bat 45, 102 Likes 39, bundle 79 (not verified).
- Shipping NIS 15, free in Ashkelon area; delivery time is confirmed by WhatsApp (no promise on site).
- Bundle with dedication NIS 79; 10 copies of 102 Likes NIS 250 pack; author meetings.
- Blog posts are drafts for her approval.
